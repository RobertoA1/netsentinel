from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Body, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.deps import AuditCtx, Principal, audited, require
from app.core.pagination import PageParams, page_params, paginate
from app.db.session import get_db
from app.models import IngestRun, Source
from app.schemas.common import Page
from app.schemas.findings import DatasetIn, DetectIn, DetectOut, IngestRunIn, IngestRunOut, IngestStatus
from app.services import ingest as ingest_svc
from app.services import pipeline

router = APIRouter(tags=["ingestion"])


def run_out(db: Session, r: IngestRun) -> IngestRunOut:
    o = IngestRunOut.model_validate(r)
    if r.source_id:
        s = db.get(Source, r.source_id)
        o.source_name = s.name if s else None
    elif r.trigger in ("n8n", "manual"):
        o.source_name = "Todas las fuentes"
    return o


@router.post("/ingest/upload", response_model=IngestRunOut)
def upload(file: UploadFile = File(...), source_id: int = Form(...), run_detection: bool = Form(True),
           db: Session = Depends(get_db), _=Depends(require("ingestion:execute")),
           audit: AuditCtx = Depends(audited("execute", "ingestion", "ingest_run"))):
    source = db.get(Source, source_id)
    if source is None:
        raise HTTPException(404, "Fuente no encontrada")
    run = ingest_svc.ingest_upload(db, source, file.file, file.filename or "upload", run_detection)
    audit.set(run.id, f"Carga manual de {file.filename} en {source.name}",
              {"status": run.status, "logs_inserted": run.logs_inserted, "parse_errors": run.parse_errors})
    return run_out(db, run)


@router.post("/ingest/run", response_model=IngestRunOut)
def run_ingest(body: IngestRunIn | None = Body(None), db: Session = Depends(get_db),
               p: Principal = Depends(require("ingestion:execute", api_key=True)),
               audit: AuditCtx = Depends(audited("execute", "ingestion", "ingest_run"))):
    sid = body.source_id if body else None
    if sid is not None and db.get(Source, sid) is None:
        raise HTTPException(404, "Fuente no encontrada")
    run = ingest_svc.ingest_directory(db, "n8n" if p.is_api_key else "manual", sid)
    audit.set(run.id, "Ejecución de ingesta desde INGEST_DIR",
              {"status": run.status, "logs_inserted": run.logs_inserted, "findings_created": run.findings_created})
    return run_out(db, run)


@router.post("/ingest/dataset", response_model=IngestRunOut)
def ingest_dataset(body: DatasetIn | None = Body(None), db: Session = Depends(get_db),
                   _=Depends(require("ingestion:execute")),
                   audit: AuditCtx = Depends(audited("execute", "ingestion", "dataset"))):
    if not ingest_svc.dataset_files():
        raise HTTPException(404, f"No hay archivos del dataset (*.binetflow, *.csv) en {get_settings().dataset_dir}")
    body = body or DatasetIn()
    run = ingest_svc.ingest_dataset(db, body.rebase_time, body.max_rows)
    audit.set(run.id, "Importación del dataset CTU-13",
              {"status": run.status, "logs_inserted": run.logs_inserted, "rebase_time": body.rebase_time})
    return run_out(db, run)


@router.post("/detect/run", response_model=DetectOut)
def detect(body: DetectIn | None = Body(None), db: Session = Depends(get_db),
           _=Depends(require("detection:execute", api_key=True)),
           audit: AuditCtx = Depends(audited("execute", "detection", "detection"))):
    res = pipeline.run_detection(db, body.window_hours if body else None)
    audit.set(None, "Ejecución manual de detección",
              {"created": res.findings_created, "updated": res.findings_updated, "noise": res.findings_noise})
    return DetectOut(findings_created=res.findings_created, findings_updated=res.findings_updated,
                     findings_noise=res.findings_noise, duration_ms=res.duration_ms)


@router.get("/ingest/runs", response_model=Page[IngestRunOut])
def runs(pp: PageParams = Depends(page_params), db: Session = Depends(get_db), _=Depends(require("ingestion:view"))):
    page = paginate(db, select(IngestRun), pp, {"id": IngestRun.id, "started_at": IngestRun.started_at,
                                                "status": IngestRun.status}, "-started_at")
    page["items"] = [run_out(db, r) for r in page["items"]]
    return page


@router.get("/ingest/status", response_model=IngestStatus)
def status(db: Session = Depends(get_db), _=Depends(require("ingestion:view", api_key=True))):
    last = db.execute(select(IngestRun).order_by(IngestRun.id.desc()).limit(1)).scalar_one_or_none()
    loaded = db.execute(select(func.count()).select_from(IngestRun).where(
        IngestRun.trigger == "dataset", IngestRun.status == "success", IngestRun.logs_inserted > 0)).scalar_one() > 0
    pending = 0
    for s in db.execute(select(Source).where(Source.enabled.is_(True))).scalars():
        pending += len(ingest_svc.pending_files(db, s))
    return IngestStatus(last_run=run_out(db, last) if last else None,
                        dataset_available=bool(ingest_svc.dataset_files()), dataset_loaded=loaded,
                        pending_files=pending)
