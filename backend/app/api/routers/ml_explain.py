"""Fase 4 — Explicabilidad (trabajos `explain` en el worker)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.routers import _ml
from app.core.deps import AuditCtx, Principal, audited, require
from app.db.session import get_db
from app.ml import jobs as J
from app.models import MlJob, MlModel, MlRun

router = APIRouter(prefix="/ml/explain", tags=["ml-explain"])


class ExplainIn(BaseModel):
    model_id: int
    force: bool = False


@router.post("/jobs", status_code=201)
def create(body: ExplainIn, db: Session = Depends(get_db), p: Principal = Depends(require("ml_explain:execute")),
           audit: AuditCtx = Depends(audited("execute", "ml_explain", "job"))):
    m = db.get(MlModel, body.model_id)
    if m is None:
        raise HTTPException(404, "Modelo no encontrado")
    if m.is_baseline:
        raise HTTPException(422, "La línea base trivial no tiene explicaciones")
    if not body.force:
        for j in db.execute(select(MlJob).where(MlJob.kind == "explain", MlJob.status.in_(("succeeded", "queued", "running")))
                            .order_by(MlJob.id.desc())).scalars():
            if j.params.get("model_id") == m.id:
                return _ml.job_out(j)
    run = db.get(MlRun, m.run_id)
    j = J.enqueue(db, "explain", {"model_id": m.id}, name=f"Explicabilidad de {m.name}", user=p.username,
                  user_id=p.user_id, seed=run.config.get("seed", 42), dataset_version_id=m.dataset_version_id,
                  time_limit_s=3600)
    audit.set(j.id, f"Explicabilidad ML solicitada para el modelo #{m.id}", {"model_id": m.id})
    return _ml.job_out(j)


@router.get("/models/{model_id}")
def latest(model_id: int, db: Session = Depends(get_db), _=Depends(require("ml_explain:view"))):
    jobs = db.execute(select(MlJob).where(MlJob.kind == "explain").order_by(MlJob.id.desc())).scalars().all()
    for j in jobs:
        if j.params.get("model_id") == model_id:
            return _ml.job_out(j, with_log=True) | {"result": j.result if j.status == "succeeded" else None}
    return {"status": "none", "result": None}
