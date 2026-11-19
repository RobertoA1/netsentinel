"""Ciclo de vida de los trabajos ML (cola en BD): ejecución, progreso, registro, cancelación y errores."""
from __future__ import annotations

import logging
import time
import traceback
from datetime import timedelta

import optuna
from sqlalchemy import select

from app.core.config import get_settings
from app.db.base import utcnow
from app.db.session import new_session
from app.ml.nested import Cancelled, Ctx, TimeLimit
from app.ml.store import lib_versions
from app.models import MlJob

log = logging.getLogger("netsentinel.ml.jobs")
LOG_LIMIT = 60_000
TERMINAL = {"succeeded", "failed", "cancelled"}


def storage_for_url(url: str):
    """Almacenamiento RDB de Optuna: esquema propio `optuna` en PostgreSQL; archivo SQLite si la BD es SQLite."""
    if url.startswith("sqlite"):
        from app.ml.data import ml_root

        return optuna.storages.RDBStorage(url=f"sqlite:///{ml_root() / 'optuna.db'}")
    from sqlalchemy import create_engine, text

    eng = create_engine(url, isolation_level="AUTOCOMMIT")
    with eng.connect() as c:
        c.execute(text("CREATE SCHEMA IF NOT EXISTS optuna"))
    eng.dispose()
    return optuna.storages.RDBStorage(url=url, engine_kwargs={"connect_args": {"options": "-csearch_path=optuna"},
                                                              "pool_pre_ping": True, "pool_size": 3})


def default_storage():
    return storage_for_url(get_settings().database_url)


class JobRunner:
    def __init__(self, job_id: int):
        self.job_id = job_id
        self._log: list[str] = []
        self._last_flush = 0.0
        self._last_cancel_check = 0.0
        self._cancel = False
        self._progress: dict = {}
        self.t0 = time.monotonic()
        db = new_session()
        try:
            j = db.get(MlJob, job_id)
            if j is None:
                raise ValueError(f"Trabajo {job_id} inexistente")
            self.params = dict(j.params or {})
            self.kind, self.seed = j.kind, j.seed
            self.time_limit = j.time_limit_s
            self._log = [j.log] if j.log else []
            self._progress = dict(j.progress or {})
            self.dataset_version_id = j.dataset_version_id
        finally:
            db.close()

    # ---- registro y progreso
    def log(self, msg: str) -> None:
        line = f"[{utcnow():%H:%M:%S}] {msg}"
        self._log.append(line)
        log.info("job %s: %s", self.job_id, msg)
        self.flush()

    def progress(self, **patch) -> None:
        self._progress.update(patch)
        self._progress["elapsed_s"] = round(time.monotonic() - self.t0, 1)
        self.flush()

    def flush(self, force: bool = False) -> None:
        now = time.monotonic()
        if not force and now - self._last_flush < 0.7:
            return
        self._last_flush = now
        text = "\n".join(self._log)
        if len(text) > LOG_LIMIT:
            text = text[-LOG_LIMIT:]
            self._log = [text]
        db = new_session()
        try:
            j = db.get(MlJob, self.job_id)
            if j is not None:
                j.log, j.progress, j.heartbeat_at = text, dict(self._progress), utcnow()
                db.commit()
        finally:
            db.close()

    def cancel_requested(self) -> bool:
        if self._cancel:
            return True
        now = time.monotonic()
        if now - self._last_cancel_check < 1.0:
            return False
        self._last_cancel_check = now
        db = new_session()
        try:
            st = db.execute(select(MlJob.status).where(MlJob.id == self.job_id)).scalar_one_or_none()
        finally:
            db.close()
        self._cancel = st in ("cancel_requested", "cancelled")
        return self._cancel

    def ctx(self, study_prefix: str, storage=None) -> Ctx:
        deadline = self.t0 + self.time_limit if self.time_limit else None
        return Ctx(emit=self.on_event, cancel_check=self.cancel_requested, deadline=deadline, storage=storage,
                   study_prefix=study_prefix, t0=self.t0)

    # eventos del entrenamiento -> progreso agregado
    def on_event(self, ev: dict) -> None:
        pr = self._progress
        t = ev.get("type")
        if t == "trial":
            pr["units_done"] = pr.get("units_done", 0) + 1
            pr["best_value"] = ev.get("best")
            pr["current"] = {"model": ev["model"], "outer": ev["outer"], "trial": ev["trial"],
                             "n_trials": ev["n_trials"]}
            recent = pr.setdefault("recent_trials", [])
            recent.append({k: ev.get(k) for k in ("model", "outer", "trial", "value", "best", "state")})
            del recent[:-40]
            key = f"{ev['model']}|{ev['outer']}"
            pr.setdefault("curves", {}).setdefault(key, []).append(ev.get("best"))
            done, total = pr.get("units_done", 0), pr.get("units_total") or 0
            el = time.monotonic() - self.t0
            if done and total:
                pr["eta_s"] = round(max(0.0, el / done * (total - done)), 1)
        elif t == "outer_done":
            pr["outer_done"] = pr.get("outer_done", 0) + 1
            self.log(f"Pliegue externo {ev['outer']} de {ev['model']}: valor externo {_f(ev.get('outer_value'))} "
                     f"(interno {_f(ev.get('inner_best'))})")
        elif t == "outer_start":
            pr["phase"], pr["current_outer"], pr["current_model"] = "outer", ev["outer"], ev["model"]
        elif t == "final_start":
            pr["phase"], pr["current_model"] = "final", ev["model"]
            self.log(f"Modelo final de {ev['model']}: búsqueda sobre todo Desarrollo")
        elif t == "final_done":
            self.log(f"Modelo final de {ev['model']} listo (mejor interno {_f(ev.get('best'))})")
        self.progress()


def _f(x) -> str:
    return "n/d" if x is None else f"{x:.4f}"


def run_job(job_id: int, fn) -> int:
    """Ejecuta fn(JobRunner) y deja el estado final del trabajo. Código de salida: 0 ok, 1 error, 2 cancelado."""
    runner = JobRunner(job_id)
    db = new_session()
    try:
        j = db.get(MlJob, job_id)
        j.status, j.started_at, j.heartbeat_at, j.libs = "running", utcnow(), utcnow(), lib_versions()
        j.attempts = (j.attempts or 0) + 1
        j.finished_at, j.error = None, None
        db.commit()
    finally:
        db.close()
    runner.log(f"Inicio ({runner.kind}); semilla {runner.seed}")
    status, error, result, code = "succeeded", None, None, 0
    try:
        result = fn(runner)
    except Cancelled:
        status, code = "cancelled", 2
        runner.log("Cancelado por el usuario")
    except TimeLimit:
        status, code, error = "failed", 1, f"Se superó el tiempo límite de {runner.time_limit} s"
        runner.log(error)
    except Exception as e:  # registro completo del error
        status, code, error = "failed", 1, f"{type(e).__name__}: {e}"
        runner.log("ERROR: " + error + "\n" + traceback.format_exc()[-1800:])
    finally:
        runner.flush(force=True)
        db = new_session()
        try:
            j = db.get(MlJob, job_id)
            if j.status == "cancel_requested" and status != "failed":
                status = "cancelled"
            j.status, j.error, j.finished_at = status, error, utcnow()
            if result is not None:
                j.result = result
            db.commit()
        finally:
            db.close()
    return code


def enqueue(db, kind: str, params: dict, *, name: str, user: str, user_id: int | None, seed: int,
            dataset_version_id: int | None, time_limit_s: int | None = None) -> MlJob:
    j = MlJob(kind=kind, status="queued", name=name, params=params, seed=seed, created_by=user,
              created_by_id=user_id, dataset_version_id=dataset_version_id,
              time_limit_s=min(int(time_limit_s or get_settings().ml_job_time_limit_seconds),
                               get_settings().ml_job_time_limit_seconds))
    db.add(j)
    db.commit()
    db.refresh(j)
    return j
