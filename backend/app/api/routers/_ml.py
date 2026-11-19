"""Utilidades compartidas por los routers del Laboratorio ML."""
from __future__ import annotations

from typing import Any

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import Principal
from app.db.base import utcnow
from app.models import MlDataset, MlDatasetVersion, MlJob

KIND_MODULE = {"train": "ml_training", "evaluate": "ml_evaluation", "explain": "ml_explain", "optimize": "ml_optuna"}
ACTIVE = ("queued", "running", "cancel_requested")


def job_out(j: MlJob, with_log: bool = False) -> dict:
    d = {"id": j.id, "kind": j.kind, "status": j.status, "name": j.name, "params": j.params, "progress": j.progress,
         "resources": j.resources, "error": j.error, "attempts": j.attempts, "seed": j.seed, "libs": j.libs,
         "created_by": j.created_by, "created_at": j.created_at, "started_at": j.started_at,
         "finished_at": j.finished_at, "heartbeat_at": j.heartbeat_at, "dataset_version_id": j.dataset_version_id,
         "time_limit_s": j.time_limit_s}
    if with_log:
        d["log"] = j.log
    return d


def get_job(db: Session, job_id: int, kind: str | None = None) -> MlJob:
    j = db.get(MlJob, job_id)
    if j is None or (kind and j.kind != kind):
        raise HTTPException(404, "Trabajo no encontrado")
    return j


def get_version(db: Session, version_id: int) -> tuple[MlDataset, MlDatasetVersion]:
    v = db.get(MlDatasetVersion, version_id)
    if v is None:
        raise HTTPException(404, "Versión de dataset no encontrada")
    return db.get(MlDataset, v.dataset_id), v


def cancel_job(db: Session, j: MlJob) -> MlJob:
    if j.status == "queued":
        j.status, j.finished_at = "cancelled", utcnow()
    elif j.status == "running":
        j.status = "cancel_requested"
    elif j.status != "cancel_requested":
        raise HTTPException(409, "El trabajo ya terminó")
    db.commit()
    return j


def retry_job(db: Session, j: MlJob) -> MlJob:
    if j.status not in ("failed", "cancelled"):
        raise HTTPException(409, "Solo se reintentan trabajos fallidos o cancelados")
    j.status, j.error, j.finished_at, j.started_at = "queued", None, None, None
    j.progress, j.result, j.log = {}, {}, (j.log or "")[-2000:] + f"\n[{utcnow():%H:%M:%S}] Reintento solicitado"
    db.commit()
    return j


def require_perm(p: Principal, perm: str) -> None:
    if not p.can(perm):
        raise HTTPException(403, f"No tiene permiso para esta acción ({perm})")


def log_tail(j: MlJob, since: int) -> dict:
    text = j.log or ""
    return {"text": text[since:] if 0 <= since <= len(text) else text, "length": len(text), "status": j.status}
