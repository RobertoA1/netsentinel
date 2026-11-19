"""Fase 6 — Inferencia: predicción individual con incertidumbre, severidad, explicación y flujo operativo."""
from __future__ import annotations

import numpy as np
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.routers._ml import require_perm
from app.api.routers.ml_evaluation import model_out
from app.core.deps import AuditCtx, Principal, audited, require
from app.core.pagination import PageParams, page_params, paginate
from app.db.session import get_db
from app.ml import interpret as I
from app.ml import serve
from app.ml.metrics import reliability
from app.ml.store import load_json
from app.models import MlModel, MlPrediction, MlRun
from app.services import ml_inference as svc

router = APIRouter(prefix="/ml/inference", tags=["ml-inference"])


class PredictIn(BaseModel):
    model_id: int | None = None
    kind: str = Field(pattern="^(flow|window|finding|manual)$")
    log_id: int | None = None
    src_ip: str | None = None
    window_end: str | None = None
    minutes: float | None = Field(None, ge=0.25, le=240)
    finding_id: int | None = None
    values: dict | None = None


class SeverityIn(BaseModel):
    weights: dict | None = None
    thresholds: dict | None = None
    uncertainty: dict | None = None
    asset_bump: dict | None = None
    ood_cap: str | None = None


class PipelineIn(BaseModel):
    enabled: bool


def _pred_out(pr: MlPrediction) -> dict:
    return {"id": pr.id, "ts": pr.ts, "model_id": pr.model_id, "username": pr.username, "input_kind": pr.input_kind,
            "input_ref": pr.input_ref, "finding_id": pr.finding_id, "probability": pr.probability,
            "interval": [pr.interval_low, pr.interval_high], "predicted_class": pr.predicted_class, "severity": pr.severity,
            "narrative": pr.narrative, "narrative_source": pr.narrative_source, "features": pr.features, **(pr.detail or {})}


@router.get("/active")
def active(db: Session = Depends(get_db), _=Depends(require("ml_inference:view", "detection:view"))):
    m = svc.active_model(db)
    return {"model": model_out(m, db.get(MlRun, m.run_id)) if m else None, "pipeline_enabled": svc.pipeline_enabled(db)}


@router.put("/pipeline")
def set_pipeline(body: PipelineIn, db: Session = Depends(get_db), p: Principal = Depends(require("detection:update")),
                 audit: AuditCtx = Depends(audited("update", "detection", "ml_pipeline"))):
    if body.enabled and svc.active_model(db) is None:
        raise HTTPException(422, "No hay modelo ML activo: promueva uno desde Evaluación antes de activar la integración")
    svc.set_pipeline_enabled(db, body.enabled)
    audit.set(None, "Integración ML en la detección " + ("activada" if body.enabled else "desactivada"),
              {"enabled": body.enabled})
    return {"pipeline_enabled": body.enabled}


@router.get("/severity-config")
def get_sev(db: Session = Depends(get_db), _=Depends(require("ml_inference:view"))):
    return {"config": svc.get_severity_config(db), "default": serve.DEFAULT_SEVERITY_CONFIG}


@router.put("/severity-config")
def put_sev(body: SeverityIn, db: Session = Depends(get_db), _=Depends(require("ml_inference:update")),
            audit: AuditCtx = Depends(audited("update", "ml_inference", "severity_config"))):
    try:
        cfg = svc.put_severity_config(db, body.model_dump(exclude_none=True))
    except ValueError as e:
        raise HTTPException(422, str(e))
    audit.set(None, "Regla de severidad ML actualizada", {"config": cfg})
    return {"config": cfg}


@router.post("/predict", status_code=201)
def predict(body: PredictIn, db: Session = Depends(get_db), p: Principal = Depends(require("ml_inference:execute")),
            audit: AuditCtx = Depends(audited("execute", "ml_inference", "prediction"))):
    m = db.get(MlModel, body.model_id) if body.model_id else svc.active_model(db)
    if m is None:
        raise HTTPException(422, "Indique un modelo o promueva uno como activo")
    ref = body.model_dump(exclude={"model_id", "kind"}, exclude_none=True)
    need = {"flow": "log_id", "window": "src_ip", "finding": "finding_id", "manual": "values"}[body.kind]
    if need not in ref:
        raise HTTPException(422, f"Falta el campo {need} para la entrada «{body.kind}»")
    try:
        rec = svc.predict(db, m, body.kind, ref, p.username, p.user_id)
    except svc.InferenceError as e:
        raise HTTPException(422, str(e))
    audit.set(rec["id"], f"Predicción ML #{rec['id']} ({body.kind}): {rec['predicted_class']} {rec['probability']:.3f}",
              {"model_id": m.id, "kind": body.kind, "severity": rec["severity"]})
    rec["model"] = {"id": m.id, "name": m.name, "unit": m.unit, "threshold": m.threshold}
    rec["interpretation"] = I.severity_text(rec["severity"], rec["severity_steps"])
    return rec


@router.get("/predictions")
def predictions(model_id: int | None = None, kind: str | None = None, severity: str | None = None,
                pp: PageParams = Depends(page_params), db: Session = Depends(get_db),
                _=Depends(require("ml_inference:view"))):
    stmt = select(MlPrediction)
    if model_id:
        stmt = stmt.where(MlPrediction.model_id == model_id)
    if kind:
        stmt = stmt.where(MlPrediction.input_kind == kind)
    if severity:
        stmt = stmt.where(MlPrediction.severity == severity)
    page = paginate(db, stmt, pp, {"id": MlPrediction.id, "ts": MlPrediction.ts, "probability": MlPrediction.probability,
                                   "severity": MlPrediction.severity}, "-ts")
    page["items"] = [_pred_out(x) for x in page["items"]]
    return page


@router.get("/predictions/{pid}")
def prediction(pid: int, db: Session = Depends(get_db), _=Depends(require("ml_inference:view"))):
    pr = db.get(MlPrediction, pid)
    if pr is None:
        raise HTTPException(404, "Predicción no encontrada")
    return _pred_out(pr)


@router.post("/predictions/{pid}/narrative")
def narrative(pid: int, db: Session = Depends(get_db), _=Depends(require("ml_inference:execute")),
              audit: AuditCtx = Depends(audited("execute", "ml_inference", "prediction"))):
    """Narración bajo demanda (en CPU Ollama tarda ~30 s: por eso NO se genera en la predicción)."""
    pr = db.get(MlPrediction, pid)
    if pr is None:
        raise HTTPException(404, "Predicción no encontrada")
    text, src = svc.narrative_for(db, pr)
    audit.set(pid, f"Narración {src} generada para la predicción #{pid}", {"source": src})
    return {"narrative": text, "source": src}


@router.get("/models/{model_id}/uncertainty")
def uncertainty(model_id: int, db: Session = Depends(get_db), _=Depends(require("ml_inference:view"))):
    m = db.get(MlModel, model_id)
    if m is None:
        raise HTTPException(404, "Modelo no encontrado")
    run = db.get(MlRun, m.run_id)
    t = load_json(f"{run.artifact_dir}/preds.json")["test"]
    rel = reliability(t["y"], t["p"])
    cov = m.uncertainty.get("coverage_test", {})
    met = m.metrics.get("test", {})
    fig = I.fig("reliability", "lines", "Diagrama de fiabilidad (calibración) en Prueba",
                {"series": [{"name": m.name, "x": rel["mean_predicted"], "y": rel["observed"], "points": True, "sizes": rel["n"]}],
                 "xlabel": "Probabilidad media predicha", "ylabel": "Frecuencia observada", "diagonal": True, "xlim": [0, 1], "ylim": [0, 1.02]},
                f"Prueba, n = {met.get('n')}; Brier {I.n(met.get('brier'), 3)}; ECE {I.n(rel['ece'], 3)}; calibración {m.calibration_method}.",
                I.calibration_text(m.name, rel["ece"], met.get("brier")))
    cinterp = I.interp([f"La cobertura nominal es {I.pct(cov.get('nominal'), 0)}; en Prueba el conjunto conforme contiene la clase verdadera en "
                        f"{I.pct(cov.get('empirical_set'))} de los {I.n(cov.get('n'))} casos"
                        f" ({'cumple' if cov.get('meets_nominal') else 'NO cumple'} la cobertura declarada)."],
                       [f"{I.pct(cov.get('share_ambiguous'))} de los casos de Prueba quedan ambiguos (conjunto con ambas clases)."
                        if cov.get("share_ambiguous") else "",
                        "Predicción conforme dividida: la garantía es marginal (promedio), no por caso individual."])
    return {"coverage": cov, "reliability": fig, "conformal_interpretation": cinterp, "ece": rel["ece"],
            "q": m.uncertainty.get("q"), "alpha": m.uncertainty.get("alpha"), "n_cal": m.uncertainty.get("n_cal")}
