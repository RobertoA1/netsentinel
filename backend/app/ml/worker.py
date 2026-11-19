"""ml-worker: toma trabajos en cola (tabla ml_jobs) y ejecuta los scripts de línea de comandos reutilizables.

    python -m app.ml.worker            # servicio (docker compose: ml-worker)
    python -m app.ml.worker --once     # procesa lo pendiente y sale
"""
from __future__ import annotations

import argparse
import logging
import os
import signal
import subprocess
import sys
import time

import psutil
from sqlalchemy import select, update

from app.core.config import get_settings
from app.db.base import utcnow
from app.db.session import new_session
from app.models import MlJob

log = logging.getLogger("netsentinel.ml.worker")
SCRIPTS = {"train": "app.ml.scripts.train", "evaluate": "app.ml.scripts.evaluate", "explain": "app.ml.scripts.explain",
           "optimize": "app.ml.scripts.optimize"}
MAX_ATTEMPTS = 2
_stop = False


def _sig(*_):
    global _stop
    _stop = True


def recover_orphans() -> int:
    """Trabajos que quedaron 'running' porque el worker se reinició: se reencolan (hasta 2 intentos) o fallan."""
    db = new_session()
    try:
        rows = db.execute(select(MlJob).where(MlJob.status.in_(["running", "cancel_requested"]))).scalars().all()
        for j in rows:
            if j.pid and psutil.pid_exists(j.pid) and _is_ours(j.pid):
                continue
            if j.status == "cancel_requested":
                j.status, j.finished_at = "cancelled", utcnow()
            elif (j.attempts or 0) < MAX_ATTEMPTS:
                j.status = "queued"
                j.log = (j.log or "") + f"\n[{utcnow():%H:%M:%S}] Worker reiniciado: el trabajo se reencola"
            else:
                j.status, j.finished_at = "failed", utcnow()
                j.error = "El worker se reinició durante la ejecución y se agotaron los reintentos"
        db.commit()
        return len(rows)
    finally:
        db.close()


def _is_ours(pid: int) -> bool:
    try:
        return "app.ml.scripts" in " ".join(psutil.Process(pid).cmdline())
    except psutil.Error:
        return False


def claim() -> MlJob | None:
    db = new_session()
    try:
        j = db.execute(select(MlJob).where(MlJob.status == "queued").order_by(MlJob.id).limit(1)).scalar_one_or_none()
        if j is None:
            return None
        res = db.execute(update(MlJob).where(MlJob.id == j.id, MlJob.status == "queued")
                         .values(status="running", started_at=utcnow(), heartbeat_at=utcnow()))
        db.commit()
        if res.rowcount != 1:
            return None
        db.refresh(j)
        return j
    finally:
        db.close()


def run_one(j: MlJob) -> None:
    kind, jid, limit = j.kind, j.id, j.time_limit_s or get_settings().ml_job_time_limit_seconds
    if kind not in SCRIPTS:
        _finish(jid, "failed", f"Tipo de trabajo desconocido: {kind}")
        return
    cmd = [sys.executable, "-m", SCRIPTS[kind], "--job-id", str(jid)]
    log.info("Ejecutando %s", " ".join(cmd))
    t0 = time.monotonic()
    proc = subprocess.Popen(cmd, env={**os.environ, "OMP_NUM_THREADS": str(get_settings().ml_n_jobs)})
    _set(jid, pid=proc.pid)
    ps = psutil.Process(proc.pid)
    ps.cpu_percent(None)
    term_sent = None
    while proc.poll() is None:
        time.sleep(1.0)
        try:
            kids = ps.children(recursive=True)
            cpu = ps.cpu_percent(None) + sum(c.cpu_percent(None) for c in kids)
            rss = ps.memory_info().rss + sum(c.memory_info().rss for c in kids if c.is_running())
            _set(jid, resources={"cpu_percent": round(cpu, 1), "rss_mb": round(rss / 1e6, 1), "pid": proc.pid,
                                 "cpu_count": psutil.cpu_count(), "mem_total_mb": round(psutil.virtual_memory().total / 1e6)})
        except psutil.Error:
            pass
        db = new_session()
        try:
            st = db.execute(select(MlJob.status).where(MlJob.id == jid)).scalar_one()
        finally:
            db.close()
        if st == "cancel_requested" and term_sent is None:
            term_sent = time.monotonic()
        if term_sent is not None and time.monotonic() - term_sent > 25:
            proc.terminate()  # el script no respondió a la cancelación cooperativa
        if time.monotonic() - t0 > limit + 90:
            log.error("Trabajo %s superó el límite: se mata el proceso", jid)
            proc.kill()
            _finish(jid, "failed", f"Se superó el tiempo límite de {limit} s")
            return
        if _stop:
            proc.terminate()
    code = proc.returncode
    db = new_session()
    try:
        st = db.execute(select(MlJob.status).where(MlJob.id == jid)).scalar_one()
    finally:
        db.close()
    if st in ("running", "cancel_requested", "queued"):  # el script murió sin dejar estado final
        _finish(jid, "cancelled" if st == "cancel_requested" else "failed",
                None if st == "cancel_requested" else f"El proceso terminó con código {code} sin registrar resultado")


def _set(jid: int, **kw) -> None:
    db = new_session()
    try:
        db.execute(update(MlJob).where(MlJob.id == jid).values(**kw))
        db.commit()
    finally:
        db.close()


def _finish(jid: int, status: str, error: str | None) -> None:
    _set(jid, status=status, error=error, finished_at=utcnow())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true")
    a = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    signal.signal(signal.SIGTERM, _sig)
    signal.signal(signal.SIGINT, _sig)
    n = recover_orphans()
    if n:
        log.info("Se revisaron %d trabajos huérfanos", n)
    poll = get_settings().ml_worker_poll_seconds
    while not _stop:
        j = claim()
        if j is None:
            if a.once:
                return 0
            time.sleep(poll)
            continue
        try:
            run_one(j)
        except Exception:
            log.exception("Fallo del worker en el trabajo %s", j.id)
            _finish(j.id, "failed", "Error interno del worker")
    return 0


if __name__ == "__main__":
    sys.exit(main())
