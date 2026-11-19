"""Inferencia ML sobre datos operativos (flujos, ventanas, hallazgos) y enriquecimiento del pipeline de detección."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from functools import lru_cache

import numpy as np
import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.base import utcnow
from app.ml import features as F
from app.ml import serve
from app.ml.store import load_model
from app.models import Asset, AppSetting, Finding, FirewallLog as L, MlModel, MlPrediction

log = logging.getLogger("netsentinel.ml.inference")
MAX_FLOWS_PER_INPUT = 400
PIPELINE_KEY = "ml_pipeline"


class InferenceError(ValueError):
    pass


@lru_cache(maxsize=3)
def _bundle(model_id: int, path: str, sha: str) -> dict:
    return load_model(path, sha)


def bundle_of(m: MlModel) -> dict:
    return _bundle(m.id, m.model_path, m.sha256)


def get_severity_config(db: Session) -> dict:
    row = db.get(AppSetting, "ml_severity")
    return serve.validate_severity_config(row.value if row else {})


def put_severity_config(db: Session, cfg: dict) -> dict:
    cfg = serve.validate_severity_config(cfg)
    row = db.get(AppSetting, "ml_severity")
    if row is None:
        db.add(AppSetting(key="ml_severity", value=cfg))
    else:
        row.value, row.updated_at = cfg, utcnow()
    db.commit()
    return cfg


def pipeline_enabled(db: Session) -> bool:
    row = db.get(AppSetting, PIPELINE_KEY)
    return bool(row and row.value.get("enabled"))


def set_pipeline_enabled(db: Session, enabled: bool) -> None:
    row = db.get(AppSetting, PIPELINE_KEY)
    if row is None:
        db.add(AppSetting(key=PIPELINE_KEY, value={"enabled": enabled}))
    else:
        row.value, row.updated_at = {"enabled": enabled}, utcnow()
    db.commit()


def active_model(db: Session) -> MlModel | None:
    return db.execute(select(MlModel).where(MlModel.is_active.is_(True))).scalar_one_or_none()


# ---------------------------------------------------------------------- filas desde la BD
def _logs_frame(logs: list[L]) -> pd.DataFrame:
    rows = [(l.ts.timestamp(), l.src_ip, l.dst_ip, l.src_port, l.dst_port, l.proto, (l.raw or {}).get("state"),
             (l.raw or {}).get("dir"), l.direction, l.bytes_out, l.bytes_in, l.packets, l.duration, l.label) for l in logs]
    return pd.DataFrame(rows, columns=F.RAW_COLUMNS)


def _window_row(logs: list[L], minutes: float) -> pd.DataFrame:
    df = _logs_frame(logs)
    wf = F.window_features(df, minutes)
    if wf.empty:
        raise InferenceError("No hay flujos del host en esa ventana")
    return wf.sort_values("win_start").iloc[[-1]][F.WINDOW_NUMERIC].reset_index(drop=True)


def rows_for(db: Session, m: MlModel, kind: str, ref: dict) -> tuple[pd.DataFrame, dict]:
    """Devuelve (X con 1+ filas para el modelo, contexto {src_ip, det_score, criticality, n_flows,...})."""
    ctx: dict = {}
    unit = m.unit
    cols = F.feature_columns(unit)
    if kind == "manual":
        vals = ref.get("values") or {}
        bad = [k for k in vals if k not in cols]
        if bad:
            raise InferenceError("Variables desconocidas: " + ", ".join(bad))
        row = {c: vals.get(c) for c in cols}
        for c in cols:
            if c not in F.FLOW_CATEGORICAL and c not in F.WINDOW_CATEGORICAL:
                row[c] = np.nan if row[c] is None else float(row[c])
            else:
                row[c] = "unk" if row[c] is None else str(row[c])
        return pd.DataFrame([row])[cols], ctx
    logs: list[L] = []
    minutes = m.window_minutes or 1
    if kind == "flow":
        lg = db.get(L, int(ref["log_id"]))
        if lg is None:
            raise InferenceError("Flujo inexistente")
        ctx["src_ip"] = lg.src_ip
        if unit == "flow":
            return F.flow_features(_logs_frame([lg]))[cols].reset_index(drop=True), ctx
        end = lg.ts + timedelta(seconds=1)
        logs = _host_logs(db, lg.src_ip, end - timedelta(minutes=minutes), end)
    elif kind == "window":
        src = str(ref["src_ip"])
        end = _parse_dt(ref.get("window_end")) or db.execute(select(L.ts).where(L.src_ip == src).order_by(L.ts.desc()).limit(1)).scalar()
        if end is None:
            raise InferenceError("El host no tiene flujos")
        end = end + timedelta(seconds=1)
        ctx["src_ip"] = src
        logs = _host_logs(db, src, end - timedelta(minutes=float(ref.get("minutes") or minutes)), end)
    elif kind == "finding":
        f = db.get(Finding, int(ref["finding_id"]))
        if f is None:
            raise InferenceError("Hallazgo inexistente")
        ctx.update({"src_ip": f.src_ip, "det_score": f.score, "finding_id": f.id})
        if unit == "flow":
            q = select(L).where(L.src_ip == f.src_ip)
            if f.dst_ip:
                q = q.where(L.dst_ip == f.dst_ip)
            if f.window_start:
                q = q.where(L.ts >= f.window_start, L.ts <= (f.window_end or f.last_seen))
            logs = list(db.execute(q.order_by(L.ts.desc()).limit(MAX_FLOWS_PER_INPUT)).scalars())
        else:
            end = f.last_seen + timedelta(seconds=1)
            logs = _host_logs(db, f.src_ip or "", end - timedelta(minutes=minutes), end)
    else:
        raise InferenceError("Tipo de entrada desconocido")
    if not logs:
        raise InferenceError("No hay flujos para esa entrada")
    a = db.execute(select(Asset).where(Asset.ip == ctx.get("src_ip", ""))).scalar_one_or_none()
    ctx["criticality"] = a.criticality if a else None
    ctx["n_flows"] = len(logs)
    if unit == "window":
        return _window_row(logs, minutes), ctx
    return F.flow_features(_logs_frame(logs))[cols].reset_index(drop=True), ctx


def _host_logs(db: Session, src: str, start: datetime, end: datetime) -> list[L]:
    return list(db.execute(select(L).where(L.src_ip == src, L.ts >= start, L.ts < end).order_by(L.ts)
                           .limit(20000)).scalars())


def _parse_dt(v) -> datetime | None:
    if not v:
        return None
    d = datetime.fromisoformat(str(v).replace("Z", "+00:00"))
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def predict(db: Session, m: MlModel, kind: str, ref: dict, user: str, user_id: int | None,
            persist: bool = True) -> dict:
    """Predicción completa: probabilidad calibrada, conforme, OOD, severidad paso a paso, SHAP y plantilla de narración."""
    if m.is_baseline:
        raise InferenceError("La línea base trivial no sirve para inferencia")
    bundle = bundle_of(m)
    X, ctx = rows_for(db, m, kind, ref)
    key = f"{m.id}:{m.sha256[:12]}"
    # varias filas (hallazgo/ventana con flujos): se puntúan todas sin SHAP y se explica la de mayor riesgo
    pre = serve.predict_rows(bundle, key, X, with_explanation=False)
    best = int(np.argmax([r["probability"] for r in pre]))
    rec = serve.predict_rows(bundle, key, X.iloc[[best]], with_explanation=True)[0]
    if len(pre) > 1:
        rec["n_scored"] = len(pre)
        rec["share_positive"] = float(np.mean([r["predicted_class"] == "Botnet" for r in pre]))
        rec["mean_probability"] = float(np.mean([r["probability"] for r in pre]))
    lo, hi = rec["interval"]
    sev, steps = serve.severity(rec["probability"], hi - lo, rec["ambiguous"], rec["ood"]["is_ood"], ctx.get("det_score"),
                                ctx.get("criticality"), get_severity_config(db))
    rec["severity"], rec["severity_steps"] = sev, steps
    rec["narrative"] = serve.template_narrative(rec, sev, m.unit, ctx.get("det_score"))
    rec["narrative_source"] = "template"
    rec["context"] = {k: v for k, v in ctx.items()}
    rec["features"] = {k: (None if pd.isna(v) else (float(v) if isinstance(v, (int, float, np.number)) else str(v)))
                       for k, v in X.iloc[best].to_dict().items()}
    if persist:
        pr = MlPrediction(model_id=m.id, user_id=user_id, username=user, input_kind=kind,
                          input_ref=str(ref.get("log_id") or ref.get("finding_id") or ref.get("src_ip") or "manual")[:128],
                          finding_id=ctx.get("finding_id"), features=rec["features"], probability=rec["probability"],
                          interval_low=lo, interval_high=hi, predicted_class=rec["predicted_class"], severity=sev,
                          detail={k: rec[k] for k in ("severity_steps", "ood", "prediction_set", "ambiguous", "threshold",
                                                       "contributions", "context", "n_scored", "share_positive") if k in rec},
                          narrative=rec["narrative"], narrative_source="template")
        db.add(pr)
        db.commit()
        rec["id"] = pr.id
    return rec


def narrative_for(db: Session, pr: MlPrediction, chat_model=None) -> tuple[str, str]:
    """Narración bajo demanda: LLM (LangChain/Ollama) con degradación a plantilla. El LLM recibe SOLO números ya calculados."""
    from app.schemas.settings import LLMSettings
    from app.services import settings_service
    from app.services.llm.chain import build_chat_model

    m = db.get(MlModel, pr.model_id)
    d = pr.detail or {}
    rec = {"probability": pr.probability, "interval": [pr.interval_low, pr.interval_high], "threshold": d.get("threshold", 0.5),
           "predicted_class": pr.predicted_class, "contributions": d.get("contributions"), "ood": d.get("ood", {"is_ood": False}),
           "ambiguous": d.get("ambiguous", False)}
    if chat_model is None:
        s: LLMSettings = settings_service.get_setting(db, "llm")
        if s.enabled:
            try:
                chat_model = build_chat_model(s)
                chat_model.format = ""  # texto libre, no JSON
            except Exception:
                chat_model = None
    text, src = serve.narrate(rec, pr.severity, d.get("severity_steps", []), m.unit if m else "flow",
                              (d.get("context") or {}).get("det_score"), chat_model)
    pr.narrative, pr.narrative_source = text, src
    db.commit()
    return text, src


# ---------------------------------------------------------------------- integración con el pipeline
def enrich_findings(db: Session, findings: list[Finding]) -> int:
    """Añade `evidence["ml"]` a cada hallazgo si hay modelo activo Y el ajuste de Detección está encendido.
    Nunca lanza: el sistema sigue funcionando igual si el ML falla."""
    try:
        if not pipeline_enabled(db):
            return 0
        m = active_model(db)
        if m is None:
            return 0
        n = 0
        for f in findings[:200]:
            try:
                rec = predict(db, m, "finding", {"finding_id": f.id}, "pipeline", None, persist=False)
            except InferenceError:
                continue
            c = rec.get("contributions") or {}
            ev = dict(f.evidence or {})
            ev["ml"] = {"ml_probability": round(rec["probability"], 4), "interval": [round(x, 4) for x in rec["interval"]],
                        "model": m.name, "model_id": m.id, "model_version": m.sha256[:10],
                        "predicted_class": rec["predicted_class"], "severity_ml": rec["severity"],
                        "top_factors": [{"variable": r["label"], "valor": r["value"], "shap": round(r["shap"], 4)}
                                        for r in (c.get("favor", [])[:3] + c.get("contra", [])[:2])],
                        "ood": rec["ood"]["is_ood"]}
            f.evidence = ev
            n += 1
        db.flush()
        return n
    except Exception:  # pragma: no cover
        log.exception("Enriquecimiento ML falló; se continúa sin ML")
        return 0
