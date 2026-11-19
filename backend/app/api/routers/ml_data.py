"""Fase 1 — Datos del Laboratorio ML."""
from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.routers._ml import get_version
from app.core.deps import AuditCtx, Principal, audited, require
from app.db.session import get_db
from app.ml import dataset_service as DS
from app.ml.features import feature_spec
from app.models import FirewallLog, MlDataset, MlDatasetVersion, MlJob, Source
from app.services import settings_service

router = APIRouter(prefix="/ml/data", tags=["ml-data"])


class DatasetIn(BaseModel):
    name: str = Field(min_length=2, max_length=128)
    source_id: int
    description: str | None = None
    unit: str | None = None
    window_minutes: float | None = None
    group_key: str | None = None
    time_block_seconds: float | None = None


class MetaChange(BaseModel):
    note: str = ""
    name: str | None = None
    description: str | None = None
    provenance: str | None = None
    license: str | None = None
    label_map: dict[str, str] | None = None
    unit: str | None = None
    window_minutes: float | None = None
    group_key: str | None = None
    time_block_seconds: float | None = None
    notes: str | None = None


def _ds_out(ds: MlDataset, v: MlDatasetVersion) -> dict:
    return {"id": ds.id, "name": ds.name, "origin": ds.origin, "source_id": ds.source_id, "n_rows": ds.n_rows,
            "n_duplicates_dropped": ds.n_duplicates_dropped, "current_version": ds.current_version,
            "current_version_id": v.id, "created_by": ds.created_by, "created_at": ds.created_at, "meta": v.meta,
            "snapshot_sha256": ds.snapshot_sha256}


def _current(db: Session, ds: MlDataset) -> MlDatasetVersion:
    return db.execute(select(MlDatasetVersion).where(MlDatasetVersion.dataset_id == ds.id,
                                                    MlDatasetVersion.version == ds.current_version)).scalar_one()


def _get(db: Session, ds_id: int) -> MlDataset:
    ds = db.get(MlDataset, ds_id)
    if ds is None:
        raise HTTPException(404, "Dataset no encontrado")
    return ds


@router.get("/datasets")
def list_datasets(db: Session = Depends(get_db), _=Depends(require("ml_data:view"))):
    rows = db.execute(select(MlDataset).order_by(MlDataset.id.desc())).scalars().all()
    return [_ds_out(d, _current(db, d)) for d in rows]


@router.get("/sources")
def eligible_sources(db: Session = Depends(get_db), _=Depends(require("ml_data:view"))):
    out = []
    for s in db.execute(select(Source).where(Source.format == "ctu13_binetflow")).scalars():
        n = db.execute(select(func.count()).select_from(FirewallLog).where(FirewallLog.source_id == s.id)).scalar_one()
        out.append({"id": s.id, "name": s.name, "format": s.format, "logs": n})
    return out


@router.post("/datasets", status_code=201)
def create_dataset(body: DatasetIn, db: Session = Depends(get_db), p: Principal = Depends(require("ml_data:create")),
                   audit: AuditCtx = Depends(audited("create", "ml_data", "dataset"))):
    kw = {k: v for k, v in body.model_dump().items() if k not in ("name", "source_id") and v is not None}
    try:
        ds, v = DS.create_from_source(db, body.name, body.source_id, p.username, **kw)
    except (DS.DatasetError, ValueError) as e:
        raise HTTPException(422, str(e))
    audit.set(ds.id, f"Dataset ML creado: {ds.name} ({ds.n_rows} filas, {ds.n_duplicates_dropped} duplicados de carga descartados)",
              {"source_id": body.source_id, "rows": ds.n_rows})
    return _ds_out(ds, v)


@router.post("/datasets/upload", status_code=201)
async def upload_dataset(file: UploadFile = File(...), name: str = Form(...), description: str = Form(""),
                         db: Session = Depends(get_db), p: Principal = Depends(require("ml_data:create")),
                         audit: AuditCtx = Depends(audited("create", "ml_data", "dataset"))):
    from app.core.config import get_settings

    max_b = get_settings().ml_max_upload_mb * 1024 * 1024
    content = await file.read(max_b + 1)
    if len(content) > max_b:
        raise HTTPException(413, f"El archivo supera el máximo de {get_settings().ml_max_upload_mb} MB")
    cidrs = settings_service.get_setting(db, "detection").internal_cidrs
    try:
        ds, v = DS.create_from_upload(db, name.strip(), content, file.filename or "archivo", p.username, cidrs,
                                      description=description or None)
    except (DS.DatasetError, ValueError) as e:
        raise HTTPException(422, str(e))
    audit.set(ds.id, f"Dataset ML creado desde archivo: {ds.name} ({ds.n_rows} filas)", {"filename": file.filename})
    return _ds_out(ds, v)


@router.get("/datasets/{ds_id}")
def get_dataset(ds_id: int, db: Session = Depends(get_db), _=Depends(require("ml_data:view"))):
    ds = _get(db, ds_id)
    vs = db.execute(select(MlDatasetVersion).where(MlDatasetVersion.dataset_id == ds.id)
                    .order_by(MlDatasetVersion.version.desc())).scalars().all()
    out = _ds_out(ds, _current(db, ds))
    out["versions"] = [{"id": v.id, "version": v.version, "change_note": v.change_note, "created_by": v.created_by,
                        "created_at": v.created_at, "content_hash": v.content_hash, "meta": v.meta} for v in vs]
    return out


@router.put("/datasets/{ds_id}")
def edit_dataset(ds_id: int, body: MetaChange, db: Session = Depends(get_db),
                 p: Principal = Depends(require("ml_data:update")),
                 audit: AuditCtx = Depends(audited("update", "ml_data", "dataset"))):
    ds = _get(db, ds_id)
    ch = body.model_dump(exclude={"note"})
    try:
        v = DS.update_meta(db, ds, ch, body.note, p.username)
    except (DS.DatasetError, ValueError) as e:
        raise HTTPException(422, str(e))
    audit.set(ds.id, f"Dataset ML «{ds.name}»: nueva versión v{v.version}", {"changed": [k for k, x in ch.items() if x is not None]})
    return _ds_out(ds, v)


@router.delete("/datasets/{ds_id}", status_code=204)
def delete_dataset(ds_id: int, db: Session = Depends(get_db), _=Depends(require("ml_data:delete")),
                   audit: AuditCtx = Depends(audited("delete", "ml_data", "dataset"))):
    ds = _get(db, ds_id)
    vids = [v for (v,) in db.execute(select(MlDatasetVersion.id).where(MlDatasetVersion.dataset_id == ds.id))]
    if db.execute(select(func.count()).select_from(MlJob).where(MlJob.dataset_version_id.in_(vids))).scalar_one():
        raise HTTPException(409, "El dataset tiene trabajos de entrenamiento asociados; no se puede borrar")
    audit.set(ds.id, f"Dataset ML eliminado: {ds.name}")
    db.delete(ds)
    db.commit()


@router.get("/versions/{vid}/summary")
def version_summary(vid: int, refresh: bool = False, db: Session = Depends(get_db), _=Depends(require("ml_data:view"))):
    ds, v = get_version(db, vid)
    try:
        return DS.summary(ds, v, refresh)
    except (DS.DatasetError, ValueError) as e:
        raise HTTPException(422, str(e))


@router.get("/versions/{vid}/validation")
def version_validation(vid: int, refresh: bool = False, db: Session = Depends(get_db),
                       _=Depends(require("ml_data:view"))):
    ds, v = get_version(db, vid)
    try:
        return DS.validation(ds, v, refresh)
    except (DS.DatasetError, ValueError) as e:
        raise HTTPException(422, str(e))


@router.get("/feature-spec")
def spec(unit: str = "flow", window_minutes: float | None = None, _=Depends(require("ml_data:view"))):
    if unit not in ("flow", "window"):
        raise HTTPException(422, "Unidad inválida")
    return feature_spec(unit, window_minutes)
