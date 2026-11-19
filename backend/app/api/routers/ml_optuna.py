"""Fase 7 — Optimización con Optuna: estudios persistidos (esquema `optuna` de PostgreSQL), monitoreo y gráficos."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.routers import _ml
from app.core.deps import AuditCtx, Principal, audited, require
from app.core.pagination import PageParams, page_params, paginate
from app.db.session import get_db
from app.ml import jobs as J
from app.ml import models as M
from app.ml import optuna_viz as V
from app.ml.metrics import METRIC_ES, OBJECTIVES
from app.ml.optimizing import MAX_TRIALS, PRUNERS, SAMPLERS, study_name
from app.models import MlJob

router = APIRouter(prefix="/ml/optuna", tags=["ml-optuna"])


class StudyIn(BaseModel):
    dataset_version_id: int
    model_type: str
    space: dict | None = None
    n_trials: int = Field(30, ge=1, le=MAX_TRIALS)
    timeout_s: int | None = Field(None, ge=10, le=14400)
    sampler: str = "tpe"
    pruner: str = "median"
    metric: str = "pr_auc"
    direction: str = "maximize"
    seed: int = Field(42, ge=0, le=2**31 - 1)
    n_folds: int = Field(3, ge=2, le=M.MAX_FOLDS_HARD)


@router.get("/options")
def options(_=Depends(require("ml_optuna:view"))):
    return {"samplers": list(SAMPLERS), "pruners": list(PRUNERS), "metrics": OBJECTIVES, "max_trials": MAX_TRIALS,
            "models": [m for m in M.space_catalog() if m["model"] != "dummy"],
            "notes": {"direction": "Todas las métricas disponibles se maximizan.",
                      "cmaes": "CMA-ES solo aplica a espacios numéricos (sin categorías); si hay categorías se usa TPE multivariado."}}


@router.post("/studies", status_code=201)
def create(body: StudyIn, db: Session = Depends(get_db), p: Principal = Depends(require("ml_optuna:create")),
           audit: AuditCtx = Depends(audited("create", "ml_optuna", "study"))):
    ds, v = _ml.get_version(db, body.dataset_version_id)
    if body.model_type not in M.MODEL_TYPES or body.model_type == "dummy":
        raise HTTPException(422, "Modelo no optimizable")
    if body.metric not in OBJECTIVES or body.sampler not in SAMPLERS or body.pruner not in PRUNERS:
        raise HTTPException(422, "Métrica, muestreador o podador no soportado")
    if body.direction != "maximize":
        raise HTTPException(422, "Solo se admite dirección «maximize» (todas las métricas son de mayor-es-mejor)")
    try:
        M.effective_space(body.model_type, body.space)
    except ValueError as e:
        raise HTTPException(422, str(e))
    j = J.enqueue(db, "optimize", body.model_dump(exclude={"seed"}), name=f"{M.MODEL_ES[body.model_type]} · {ds.name} v{v.version}",
                  user=p.username, user_id=p.user_id, seed=body.seed, dataset_version_id=v.id,
                  time_limit_s=(body.timeout_s or 3600) + 600)
    audit.set(j.id, f"Estudio Optuna creado (trabajo #{j.id})", {"model": body.model_type, "n_trials": body.n_trials,
                                                                  "sampler": body.sampler, "pruner": body.pruner})
    return _ml.job_out(j)


@router.get("/studies")
def list_studies(pp: PageParams = Depends(page_params), db: Session = Depends(get_db), _=Depends(require("ml_optuna:view"))):
    page = paginate(db, select(MlJob).where(MlJob.kind == "optimize"), pp,
                    {"id": MlJob.id, "created_at": MlJob.created_at, "status": MlJob.status}, "-id")
    page["items"] = [_ml.job_out(j) | {"best_value": (j.result or {}).get("best_value")} for j in page["items"]]
    return page


def _space_for(j: MlJob) -> list[dict]:
    return M.effective_space(j.params["model_type"], j.params.get("space"))


@router.get("/studies/{job_id}")
def detail(job_id: int, db: Session = Depends(get_db), _=Depends(require("ml_optuna:view"))):
    j = _ml.get_job(db, job_id, "optimize")
    out = _ml.job_out(j, with_log=True) | {"result": j.result, "space": _space_for(j)}
    try:
        st = V.load_study(J.default_storage(), study_name(j.id))
        rows = V.trials_rows(st)
        out["trials"] = rows[-300:]
        out["summary"] = V.summary(st, rows)
    except Exception:
        out["trials"], out["summary"] = [], None
    return out


@router.get("/studies/{job_id}/viz")
def viz(job_id: int, db: Session = Depends(get_db), _=Depends(require("ml_optuna:view"))):
    j = _ml.get_job(db, job_id, "optimize")
    try:
        st = V.load_study(J.default_storage(), study_name(j.id))
    except Exception:
        raise HTTPException(404, "El estudio aún no tiene datos")
    rows = V.trials_rows(st)
    return {"figures": V.figures(st, rows, _space_for(j), METRIC_ES.get(j.params.get("metric", "pr_auc"), "métrica")),
            "summary": V.summary(st, rows)}


@router.get("/studies/{job_id}/best")
def best(job_id: int, db: Session = Depends(get_db), _=Depends(require("ml_optuna:view"))):
    j = _ml.get_job(db, job_id, "optimize")
    res = j.result or {}
    if not res.get("best_params"):
        raise HTTPException(409, "El estudio aún no tiene un mejor trial")
    # el rango de búsqueda se acota alrededor del mejor trial para reentrenar con esos hiperparámetros
    return {"job_id": j.id, "model_type": j.params["model_type"], "best_params": res["best_params"],
            "best_value": res["best_value"], "dataset_version_id": j.dataset_version_id, "metric": res.get("metric")}


@router.delete("/studies/{job_id}", status_code=204)
def delete(job_id: int, db: Session = Depends(get_db), _=Depends(require("ml_optuna:delete")),
           audit: AuditCtx = Depends(audited("delete", "ml_optuna", "study"))):
    j = _ml.get_job(db, job_id, "optimize")
    if j.status in _ml.ACTIVE:
        raise HTTPException(409, "Cancele el estudio antes de borrarlo")
    try:
        st = J.default_storage()
        st.delete_study(st.get_study_id_from_name(study_name(j.id)))
    except Exception:
        pass
    audit.set(j.id, f"Estudio Optuna #{j.id} eliminado")
    db.delete(j)
    db.commit()
