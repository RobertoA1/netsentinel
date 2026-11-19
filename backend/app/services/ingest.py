"""Ingesta: parseo, normalización y carga por lotes en firewall_logs."""
from __future__ import annotations

import io
import json
import logging
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable, Iterator

from sqlalchemy import insert, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.base import utcnow
from app.models import FirewallLog, IngestedFile, IngestRun, Source
from app.services import pipeline, settings_service
from app.services.parsers import DirectionClassifier, ParseStats, get_parser, parse_stream
from app.services.parsers.ctu13 import quick_start_time

log = logging.getLogger("netsentinel.ingest")
BATCH = 5000
DATASET_EXTS = (".binetflow", ".csv")
CTU_NETWORK = "147.32.0.0/16"  # red universitaria de la captura CTU-13

COLS = ["ts", "source_id", "log_type", "action", "proto", "src_ip", "src_port", "dst_ip", "dst_port", "direction",
        "bytes_out", "bytes_in", "packets", "duration", "signature", "signature_id", "category", "ids_severity",
        "label", "raw"]


def _copy_value(col: str, v):
    """PostgreSQL rechaza NUL en texto/jsonb: se eliminan antes de COPY."""
    if col == "raw":
        return json.dumps(v, default=str, ensure_ascii=False).replace("\\u0000", "")
    return v.replace("\x00", "") if isinstance(v, str) else v


def bulk_insert(db: Session, rows: list[dict]) -> int:
    if not rows:
        return 0
    if db.get_bind().dialect.name == "postgresql":
        raw = db.connection().connection.driver_connection
        with raw.cursor() as cur:
            with cur.copy(f"COPY firewall_logs ({', '.join(COLS)}) FROM STDIN") as cp:
                for r in rows:
                    cp.write_row([_copy_value(c, r.get(c)) for c in COLS])
    else:
        db.execute(insert(FirewallLog), rows)
    return len(rows)


def load_stream(db: Session, source: Source, lines: Iterable[str], run: IngestRun, classifier: DirectionClassifier,
                max_rows: int | None = None, shift: timedelta | None = None) -> None:
    """Parsea y carga; actualiza los contadores de `run`. No hace commit del run final."""
    stats = ParseStats()
    parser = get_parser(source.format)
    batch: list[dict] = []
    inserted = 0
    for rec in parse_stream(parser, lines, stats):
        if max_rows is not None and inserted + len(batch) >= max_rows:
            break
        if shift:
            rec["ts"] = rec["ts"] + shift
        rec["source_id"] = source.id
        rec["direction"] = classifier.classify(rec["src_ip"], rec["dst_ip"])
        batch.append(rec)
        if len(batch) >= BATCH:
            inserted += bulk_insert(db, batch)
            batch = []
            db.commit()
    inserted += bulk_insert(db, batch)
    run.lines_read += stats.lines_read
    run.parse_errors += stats.parse_errors
    run.logs_inserted += inserted
    if stats.error_samples:
        log.warning("Errores de parseo en %s (muestra): %s", source.name, stats.error_samples[:3])


def new_run(db: Session, trigger: str, source: Source | None, filename: str | None) -> IngestRun:
    run = IngestRun(started_at=utcnow(), status="running", trigger=trigger,
                    source_id=source.id if source else None, filename=filename)
    db.add(run)
    db.commit()
    return run


def finish_run(db: Session, run: IngestRun, error: str | None = None) -> IngestRun:
    run.finished_at = utcnow()
    run.status = "error" if error else "success"
    run.error = error[:2000] if error else None
    db.commit()
    return run


def _classifier(db: Session) -> DirectionClassifier:
    return DirectionClassifier(settings_service.get_setting(db, "detection").internal_cidrs)


def ingest_upload(db: Session, source: Source, fileobj, filename: str, run_detection: bool = True) -> IngestRun:
    run = new_run(db, "upload", source, filename[:500])
    try:
        text = io.TextIOWrapper(fileobj, encoding="utf-8", errors="replace", newline="")
        load_stream(db, source, text, run, _classifier(db))
        source.last_ingest_at = utcnow()
        db.commit()
        if run_detection and run.logs_inserted:
            _detect_into(db, run)
        return finish_run(db, run)
    except Exception as e:  # el run queda registrado con el error
        db.rollback()
        log.exception("Fallo de ingesta")
        run = db.get(IngestRun, run.id)
        return finish_run(db, run, f"{type(e).__name__}: {e}")


def _detect_into(db: Session, run: IngestRun) -> None:
    res = pipeline.run_detection(db)
    run.findings_created = res.findings_created
    run.findings_noise = res.findings_noise
    db.commit()


def _complete_lines(path: Path, offset: int) -> tuple[list[str], int]:
    """Lee desde `offset`; solo consume líneas completas (o todo si el archivo lleva >10 s sin cambios)."""
    size = path.stat().st_size
    if size < offset:
        offset = 0  # rotación/truncado
    with path.open("rb") as fh:
        fh.seek(offset)
        data = fh.read()
    if not data:
        return [], offset
    stale = (datetime.now().timestamp() - path.stat().st_mtime) > 10
    if not data.endswith(b"\n") and not stale:
        cut = data.rfind(b"\n")
        if cut < 0:
            return [], offset
        data = data[: cut + 1]
    return data.decode("utf-8", errors="replace").splitlines(), offset + len(data)


def pending_files(db: Session, source: Source) -> list[tuple[Path, int]]:
    d = Path(get_settings().ingest_dir) / str(source.id)
    if not d.is_dir():
        return []
    out = []
    for p in sorted(d.iterdir()):
        if not p.is_file() or p.name.startswith("."):
            continue
        rec = db.execute(select(IngestedFile).where(IngestedFile.source_id == source.id,
                                                    IngestedFile.path == str(p))).scalar_one_or_none()
        off = rec.offset if rec else 0
        if p.stat().st_size != off:
            out.append((p, off))
    return out


def ingest_directory(db: Session, trigger: str, source_id: int | None = None) -> IngestRun:
    q = select(Source).where(Source.enabled.is_(True))
    if source_id is not None:
        q = select(Source).where(Source.id == source_id)
    sources = list(db.execute(q.order_by(Source.id)).scalars())
    single = sources[0] if len(sources) == 1 else None
    run = new_run(db, trigger, single, None)
    try:
        classifier = _classifier(db)
        names = []
        for s in sources:
            for p, off in pending_files(db, s):
                lines, new_off = _complete_lines(p, off)
                if not lines and new_off == off:
                    continue
                load_stream(db, s, lines, run, classifier)
                rec = db.execute(select(IngestedFile).where(IngestedFile.source_id == s.id,
                                                            IngestedFile.path == str(p))).scalar_one_or_none()
                if rec is None:
                    db.add(IngestedFile(source_id=s.id, path=str(p), offset=new_off))
                else:
                    rec.offset, rec.processed_at = new_off, utcnow()
                s.last_ingest_at = utcnow()
                names.append(p.name)
                db.commit()
        run.filename = ", ".join(names)[:500] if names else None
        db.commit()
        if run.logs_inserted:
            _detect_into(db, run)
        return finish_run(db, run)
    except Exception as e:
        db.rollback()
        log.exception("Fallo de ingesta de directorio")
        run = db.get(IngestRun, run.id)
        return finish_run(db, run, f"{type(e).__name__}: {e}")


# ---- dataset CTU-13 -----------------------------------------------------

def dataset_files() -> list[Path]:
    d = Path(get_settings().dataset_dir)
    if not d.is_dir():
        return []
    return sorted(p for p in d.iterdir() if p.is_file() and p.suffix.lower() in DATASET_EXTS)


def _iter_lines(files: list[Path]) -> Iterator[str]:
    for f in files:
        with f.open("r", encoding="utf-8", errors="replace", newline="") as fh:
            for line in fh:
                yield line


def dataset_source(db: Session) -> Source:
    s = db.execute(select(Source).where(Source.format == "ctu13_binetflow").order_by(Source.id)).scalars().first()
    if s is None:
        s = Source(name="CTU-13 Dataset", format="ctu13_binetflow", description="Dataset real CTU-13 (demo)")
        db.add(s)
        db.commit()
    return s


def ingest_dataset(db: Session, rebase_time: bool = True, max_rows: int | None = None) -> IngestRun:
    files = dataset_files()
    max_rows = max_rows or 500_000
    source = dataset_source(db)
    run = new_run(db, "dataset", source, ", ".join(f.name for f in files)[:500])
    try:
        shift = None
        if rebase_time:
            # El formato "YYYY/MM/DD HH:MM:SS.ffffff" ordena igual como texto: se compara sin parsear cada fila.
            latest_txt, seen = None, 0
            for line in _iter_lines(files):
                head = line.split(",", 1)[0].strip()
                if len(head) < 19 or head[4] != "/":
                    continue
                seen += 1
                if latest_txt is None or head > latest_txt:
                    latest_txt = head
                if seen >= max_rows:
                    break
            latest = quick_start_time(latest_txt) if latest_txt else None
            if latest is not None:
                shift = datetime.now(timezone.utc) - latest - timedelta(seconds=5)
        det = settings_service.get_setting(db, "detection")
        if CTU_NETWORK not in det.internal_cidrs:
            det.internal_cidrs = list(det.internal_cidrs) + [CTU_NETWORK]
            settings_service.put_setting(db, "detection", det)
        classifier = DirectionClassifier(det.internal_cidrs)
        load_stream(db, source, _iter_lines(files), run, classifier, max_rows=max_rows, shift=shift)
        source.last_ingest_at = utcnow()
        db.commit()
        if run.logs_inserted:
            _detect_into(db, run)
        return finish_run(db, run)
    except Exception as e:
        db.rollback()
        log.exception("Fallo al importar el dataset")
        run = db.get(IngestRun, run.id)
        return finish_run(db, run, f"{type(e).__name__}: {e}")
