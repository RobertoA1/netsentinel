"""Fase 3 — Evaluación: comparación de modelos, matrices de confusión, pruebas estadísticas y promoción de modelo."""
from __future__ import annotations

import numpy as np
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.api.routers import _ml
from app.core.deps import AuditCtx, Principal, audited, require
from app.db.base import utcnow
from app.db.session import get_db
from app.ml import interpret as I
from app.ml import jobs as J
from app.ml import models as M
from app.ml.metrics import compute_metrics
from app.ml.store import load_json
from app.models import MlJob, MlModel, MlRun

router = APIRouter(prefix="/ml/evaluation", tags=["ml-evaluation"])


class EvalIn(BaseModel):
    job_id: int | None = None
    run_ids: list[int] | None = None


def model_out(m: MlModel, run: MlRun | None = None) -> dict:
    return {"id": m.id, "run_id": m.run_id, "name": m.name, "model_type": m.model_type, "unit": m.unit,
            "window_minutes": m.window_minutes, "threshold": m.threshold, "calibration_method": m.calibration_method,
            "feature_spec_version": m.feature_spec_version, "metrics": m.metrics, "uncertainty": m.uncertainty,
            "is_baseline": m.is_baseline, "is_active": m.is_active, "promoted_by": m.promoted_by,
            "promoted_at": m.promoted_at, "created_at": m.created_at, "dataset_version_id": m.dataset_version_id,
            "sha256": m.sha256, "job_id": run.job_id if run else None}


@router.get("/models")
def models(db: Session = Depends(get_db), _=Depends(require("ml_evaluation:view", "ml_inference:view", "ml_explain:view"))):
    rows = db.execute(select(MlModel, MlRun).join(MlRun, MlRun.id == MlModel.run_id).order_by(MlModel.id.desc())).all()
    return [model_out(m, r) for m, r in rows]


@router.post("/evaluations", status_code=201)
def create_evaluation(body: EvalIn, db: Session = Depends(get_db), p: Principal = Depends(require("ml_evaluation:view")),
                      audit: AuditCtx = Depends(audited("execute", "ml_evaluation", "evaluation"))):
    if body.run_ids:
        run_ids = sorted(set(body.run_ids))
    elif body.job_id:
        run_ids = [r for (r,) in db.execute(select(MlRun.id).where(MlRun.job_id == body.job_id, MlRun.status == "succeeded")
                                              .order_by(MlRun.id))]
    else:
        raise HTTPException(422, "Indique job_id o run_ids")
    runs = [db.get(MlRun, r) for r in run_ids]
    if not runs or any(r is None or r.status != "succeeded" for r in runs):
        raise HTTPException(422, "Todas las ejecuciones deben existir y haber terminado")
    if len({r.job_id for r in runs}) != 1:
        raise HTTPException(422, "Las ejecuciones deben provenir del mismo trabajo de entrenamiento (misma partición)")
    # reutiliza una evaluación idéntica ya calculada
    for j in db.execute(select(MlJob).where(MlJob.kind == "evaluate", MlJob.status.in_(("succeeded", "queued", "running")))
                        .order_by(MlJob.id.desc())).scalars():
        if sorted(j.params.get("run_ids", [])) == run_ids:
            return _ml.job_out(j)
    j = J.enqueue(db, "evaluate", {"run_ids": run_ids}, name=f"Evaluación de {len(run_ids)} modelos (trabajo #{runs[0].job_id})",
                  user=p.username, user_id=p.user_id, seed=runs[0].config.get("seed", 42),
                  dataset_version_id=runs[0].dataset_version_id, time_limit_s=1800)
    audit.set(j.id, f"Evaluación ML solicitada (trabajo #{j.id})", {"run_ids": run_ids})
    return _ml.job_out(j)


@router.get("/evaluations/{job_id}")
def get_evaluation(job_id: int, db: Session = Depends(get_db), _=Depends(require("ml_evaluation:view"))):
    j = _ml.get_job(db, job_id, "evaluate")
    return _ml.job_out(j, with_log=True) | {"result": j.result if j.status == "succeeded" else None}


@router.get("/runs/{run_id}/confusion")
def confusion(run_id: int, threshold: float | None = None, db: Session = Depends(get_db),
              _=Depends(require("ml_evaluation:view"))):
    """Matriz de confusión (absoluta y normalizada) en PRUEBA, con el umbral que se pida (por defecto el elegido en Validación)."""
    run = db.get(MlRun, run_id)
    m = db.execute(select(MlModel).where(MlModel.run_id == run_id)).scalar_one_or_none()
    if run is None or m is None or run.status != "succeeded":
        raise HTTPException(404, "Ejecución no encontrada")
    thr = m.threshold if threshold is None else float(threshold)
    if not 0.0 <= thr <= 1.0:
        raise HTTPException(422, "El umbral debe estar entre 0 y 1")
    t = load_json(f"{run.artifact_dir}/preds.json")["test"]
    y, p = np.array(t["y"]), np.array(t["p"])
    met = compute_metrics(y, p, thr)
    c = {k: met[k] for k in ("tp", "fp", "fn", "tn")}
    rows = ["Normal real", "Botnet real"]
    cols = ["Normal predicho", "Botnet predicho"]
    absolute = [[c["tn"], c["fp"]], [c["fn"], c["tp"]]]
    norm = [[c["tn"] / max(c["tn"] + c["fp"], 1), c["fp"] / max(c["tn"] + c["fp"], 1)],
            [c["fn"] / max(c["fn"] + c["tp"], 1), c["tp"] / max(c["fn"] + c["tp"], 1)]]
    name = M.MODEL_ES[run.model_type]
    fig_abs = I.fig("confusion_abs", "heatmap", f"Matriz de confusión (absoluta) — {name}",
                    {"rows": rows, "cols": cols, "values": absolute, "vlabel": "Casos", "scale": "seq", "vmin": 0,
                     "vmax": max(max(r) for r in absolute), "annotate": True, "fmt": "int"},
                    f"Prueba, n = {met['n']} ({met['n_pos']} Botnet); umbral {I.n(thr)}.", I.confusion_text(c, thr, name))
    fig_norm = I.fig("confusion_norm", "heatmap", f"Matriz de confusión (normalizada por fila) — {name}",
                     {"rows": rows, "cols": cols, "values": norm, "vlabel": "Proporción de la clase real", "scale": "seq",
                      "vmin": 0, "vmax": 1, "annotate": True, "fmt": "pct"},
                     f"Cada fila suma 100 %; exhaustividad = celda Botnet/Botnet; especificidad = Normal/Normal. Umbral {I.n(thr)}.",
                     I.confusion_text(c, thr, name))
    # efecto del umbral
    grid = np.linspace(0, 1, 51)
    sweep = [compute_metrics(y, p, float(g)) for g in grid]
    return {"threshold": thr, "model_threshold": m.threshold, "metrics": met, "figures": [fig_abs, fig_norm],
            "sweep": {"threshold": grid.round(3).tolist(), "precision": [s["precision"] for s in sweep],
                      "recall": [s["recall"] for s in sweep], "f1": [s["f1"] for s in sweep]}}


@router.post("/models/{model_id}/promote")
def promote(model_id: int, db: Session = Depends(get_db), p: Principal = Depends(require("ml_evaluation:update")),
            audit: AuditCtx = Depends(audited("update", "ml_evaluation", "model"))):
    m = db.get(MlModel, model_id)
    if m is None:
        raise HTTPException(404, "Modelo no encontrado")
    if m.is_baseline:
        raise HTTPException(422, "La línea base trivial no se puede promover")
    db.execute(update(MlModel).where(MlModel.is_active.is_(True)).values(is_active=False))
    m.is_active, m.promoted_by, m.promoted_at = True, p.username, utcnow()
    db.commit()
    audit.set(m.id, f"Modelo ML promovido a activo: {m.name}", {"model_id": m.id, "sha256": m.sha256})
    return model_out(m)


@router.post("/models/deactivate")
def deactivate(db: Session = Depends(get_db), p: Principal = Depends(require("ml_evaluation:update")),
               audit: AuditCtx = Depends(audited("update", "ml_evaluation", "model"))):
    n = db.execute(update(MlModel).where(MlModel.is_active.is_(True)).values(is_active=False)).rowcount
    db.commit()
    audit.set(None, "Modelo ML activo desactivado", {"models": n})
    return {"deactivated": n}
