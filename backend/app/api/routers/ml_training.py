"""Fase 2 — Entrenamiento: trabajos en cola, monitoreo por sondeo corto, ejecuciones y análisis."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.routers import _ml
from app.core.deps import AuditCtx, Principal, audited, require
from app.core.pagination import PageParams, page_params, paginate
from app.db.session import get_db
from app.ml import analysis, dataset_service as DS, jobs as J
from app.ml import models as M
from app.ml.groups import validate_key
from app.ml.metrics import OBJECTIVES
from app.ml.features import feature_columns
from app.ml import prepare as P
from app.models import MlFoldResult, MlJob, MlRun

router = APIRouter(prefix="/ml/training", tags=["ml-training"])


class ModelReq(BaseModel):
    type: str
    n_trials: int | None = Field(None, ge=1, le=M.MAX_TRIALS_HARD)
    space: dict | None = None


class TrainIn(BaseModel):
    dataset_version_id: int
    models: list[ModelReq] = Field(min_length=1, max_length=5)
    metric: str = "pr_auc"
    n_outer: int = Field(5, ge=2, le=M.MAX_FOLDS_HARD)
    n_inner: int = Field(3, ge=2, le=M.MAX_FOLDS_HARD)
    n_trials: int = Field(20, ge=1, le=M.MAX_TRIALS_HARD)
    seed: int = Field(42, ge=0, le=2**31 - 1)
    sampler: str = "tpe"
    pruner: str = "median"
    time_limit_s: int | None = Field(None, ge=60, le=86400)
    from_study: int | None = None


@router.get("/spaces")
def spaces(_=Depends(require("ml_training:view"))):
    return {"models": M.space_catalog(), "metrics": OBJECTIVES, "max_trials": M.MAX_TRIALS_HARD,
            "protocol": {"n_outer": 5, "n_inner": 3, "sampler": "TPE", "pruner": "mediana",
                         "split": "Desarrollo 70 % / Validación 15 % / Prueba 15 % por grupos, estratificado"}}


@router.post("/jobs", status_code=201)
def create_job(body: TrainIn, db: Session = Depends(get_db), p: Principal = Depends(require("ml_training:execute")),
               audit: AuditCtx = Depends(audited("execute", "ml_training", "job"))):
    ds, v = _ml.get_version(db, body.dataset_version_id)
    if body.metric not in OBJECTIVES:
        raise HTTPException(422, "Métrica objetivo no soportada")
    if body.sampler not in ("tpe", "random", "cmaes") or body.pruner not in ("median", "hyperband", "none"):
        raise HTTPException(422, "Muestreador o podador no soportado")
    models = []
    for m in body.models:
        if m.type not in M.MODEL_TYPES:
            raise HTTPException(422, f"Modelo desconocido: {m.type}")
        try:
            M.effective_space(m.type, m.space)
        except ValueError as e:
            raise HTTPException(422, str(e))
        models.append(m.model_dump())
    # BLOQUEO: la configuración de grupos debe ser viable para 5x3 pliegues
    try:
        g = DS.validation(ds, v)
    except (DS.DatasetError, ValueError) as e:
        raise HTTPException(422, str(e))
    chosen = g["keys"][v.meta["group_key"]]
    if body.n_outer == 5 and body.n_inner == 3 and not chosen.get("viable"):
        raise HTTPException(422, "Entrenamiento bloqueado: la agrupación «" + chosen["label"] + "» es inviable. "
                            + " ".join(chosen.get("blocking", [])[:3])
                            + (f" Recomendación: usar «{g['recommended']}»." if g.get("recommended") else ""))
    j = J.enqueue(db, "train", {"models": models, "metric": body.metric, "n_outer": body.n_outer, "n_inner": body.n_inner,
                                "n_trials": body.n_trials, "sampler": body.sampler, "pruner": body.pruner,
                                "from_study": body.from_study},
                  name=f"{', '.join(M.MODEL_ES[m['type']] for m in models)} · {ds.name} v{v.version}", user=p.username,
                  user_id=p.user_id, seed=body.seed, dataset_version_id=v.id, time_limit_s=body.time_limit_s)
    audit.set(j.id, f"Entrenamiento ML lanzado (trabajo #{j.id})", {"dataset_version_id": v.id, "models": [m["type"] for m in models],
                                                                     "seed": body.seed, "group_key": v.meta["group_key"]})
    return _ml.job_out(j)


@router.get("/jobs")
def list_jobs(kind: str = "train", status: str | None = None, pp: PageParams = Depends(page_params),
              db: Session = Depends(get_db), p: Principal = Depends(require("ml_training:view", "ml_evaluation:view",
                                                                            "ml_explain:view", "ml_optuna:view"))):
    stmt = select(MlJob).where(MlJob.kind == kind)
    if status:
        stmt = stmt.where(MlJob.status == status)
    page = paginate(db, stmt, pp, {"id": MlJob.id, "created_at": MlJob.created_at, "status": MlJob.status}, "-id")
    page["items"] = [_ml.job_out(j) | {"runs": _runs_brief(db, j)} for j in page["items"]]
    return page


def _runs_brief(db: Session, j: MlJob) -> list[dict]:
    if j.kind != "train":
        return []
    rs = db.execute(select(MlRun).where(MlRun.job_id == j.id).order_by(MlRun.id)).scalars().all()
    return [{"id": r.id, "model_type": r.model_type, "status": r.status, "duration_s": r.duration_s,
             "pr_auc_cv": (r.summary.get("cv", {}).get("pr_auc", {}) or {}).get("mean"),
             "pr_auc_test": (r.test_metrics or {}).get("pr_auc")} for r in rs]


@router.get("/jobs/{job_id}")
def job_detail(job_id: int, db: Session = Depends(get_db), _=Depends(require("ml_training:view", "ml_evaluation:view",
                                                                              "ml_explain:view", "ml_optuna:view"))):
    j = _ml.get_job(db, job_id)
    return _ml.job_out(j) | {"runs": _runs_brief(db, j), "result": j.result}


@router.get("/jobs/{job_id}/log")
def job_log(job_id: int, since: int = 0, db: Session = Depends(get_db), _=Depends(require(
        "ml_training:view", "ml_evaluation:view", "ml_explain:view", "ml_optuna:view"))):
    return _ml.log_tail(_ml.get_job(db, job_id), since)


@router.post("/jobs/{job_id}/cancel")
def cancel(job_id: int, db: Session = Depends(get_db), p: Principal = Depends(require(
        "ml_training:execute", "ml_optuna:execute", "ml_explain:execute", "ml_evaluation:update")),
        audit: AuditCtx = Depends(audited("execute", "ml_training", "job"))):
    j = _ml.get_job(db, job_id)
    _ml.require_perm(p, _ml.KIND_MODULE[j.kind] + (":update" if j.kind == "evaluate" else ":execute"))
    _ml.cancel_job(db, j)
    audit.set(j.id, f"Trabajo ML #{j.id} ({j.kind}) cancelado", {"kind": j.kind})
    audit.module = _ml.KIND_MODULE[j.kind]
    return _ml.job_out(j)


@router.post("/jobs/{job_id}/retry")
def retry(job_id: int, db: Session = Depends(get_db), p: Principal = Depends(require(
        "ml_training:execute", "ml_optuna:execute", "ml_explain:execute", "ml_evaluation:update")),
        audit: AuditCtx = Depends(audited("execute", "ml_training", "job"))):
    j = _ml.get_job(db, job_id)
    _ml.require_perm(p, _ml.KIND_MODULE[j.kind] + (":update" if j.kind == "evaluate" else ":execute"))
    _ml.retry_job(db, j)
    audit.set(j.id, f"Trabajo ML #{j.id} ({j.kind}) reintentado", {"kind": j.kind})
    audit.module = _ml.KIND_MODULE[j.kind]
    return _ml.job_out(j)


def run_dict(db: Session, r: MlRun) -> dict:
    folds = db.execute(select(MlFoldResult).where(MlFoldResult.run_id == r.id).order_by(MlFoldResult.outer_fold)).scalars().all()
    return {"run_id": r.id, "model_type": r.model_type, "config": r.config, "summary": r.summary, "final_params": r.final_params,
            "status": r.status, "duration_s": r.duration_s, "val_metrics": r.val_metrics, "test_metrics": r.test_metrics,
            "folds": [{"outer": f.outer_fold, "best_params": f.best_params, "inner": f.inner_best_value, "metrics": f.outer_metrics,
                       "curve": f.curve, "n_trials": f.n_trials, "n_pruned": f.n_pruned, "sizes": f.sizes,
                       "duration_s": f.duration_s} for f in folds]}


@router.get("/jobs/{job_id}/analysis")
def job_analysis(job_id: int, db: Session = Depends(get_db), _=Depends(require("ml_training:view", "ml_evaluation:view"))):
    j = _ml.get_job(db, job_id, "train")
    runs = [run_dict(db, r) for r in db.execute(select(MlRun).where(MlRun.job_id == j.id, MlRun.status == "succeeded")
                                                 .order_by(MlRun.id)).scalars()]
    out = analysis.training_analysis(j.params, (j.progress or {}).get("partition"), runs)
    out["job"] = _ml.job_out(j)
    out["runs"] = [{"run_id": r["run_id"], "model_type": r["model_type"], "duration_s": r["duration_s"],
                    "summary": r["summary"], "final_params": r["final_params"], "test_metrics": r["test_metrics"]} for r in runs]
    return out


@router.get("/runs/{run_id}")
def run_detail(run_id: int, db: Session = Depends(get_db), _=Depends(require("ml_training:view", "ml_evaluation:view"))):
    r = db.get(MlRun, run_id)
    if r is None:
        raise HTTPException(404, "Ejecución no encontrada")
    return run_dict(db, r)
