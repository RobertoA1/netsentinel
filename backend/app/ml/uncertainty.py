"""Incertidumbre: predicción conforme dividida (split conformal), fuera de distribución y su verificación."""
from __future__ import annotations

import numpy as np
import pandas as pd

from app.ml.features import feature_columns, FLOW_CATEGORICAL, WINDOW_CATEGORICAL

ALPHA = 0.10  # cobertura nominal 90 %


def fit_uncertainty(y_cal, p_cal, X_train: pd.DataFrame, unit: str, alpha: float = ALPHA) -> dict:
    """Cuantil conforme sobre Validación (puntaje de no conformidad |y - p| de la clase verdadera, método LAC) y
    rangos de percentiles 1-99 del entrenamiento para el aviso de fuera de distribución."""
    y = np.asarray(y_cal).astype(int)
    p = np.asarray(p_cal, float)
    score = np.where(y == 1, 1 - p, p)  # no conformidad: 1 - prob. asignada a la clase verdadera
    n = len(score)
    level = min(1.0, np.ceil((n + 1) * (1 - alpha)) / n)
    q = float(np.quantile(score, level, method="higher"))
    cat = WINDOW_CATEGORICAL if unit == "window" else FLOW_CATEGORICAL
    num = [c for c in feature_columns(unit) if c not in cat]
    ranges = {}
    for c in num:
        v = pd.to_numeric(X_train[c], errors="coerce").dropna()
        if len(v) > 10:
            ranges[c] = [float(v.quantile(0.01)), float(v.quantile(0.99)), float(v.min()), float(v.max())]
    cats = {c: sorted({str(v) for v in X_train[c].dropna().unique()})[:200] for c in cat}
    return {"alpha": alpha, "nominal_coverage": 1 - alpha, "q": q, "n_cal": int(n), "ranges": ranges, "categories": cats,
            "ood_fraction_threshold": 0.25}


def prediction_set(unc: dict, p: float) -> list[str]:
    q = unc["q"]
    s = []
    if 1 - p <= q:
        s.append("Botnet")
    if p <= q:
        s.append("Normal")
    return s


def prob_interval(unc: dict, p: float) -> tuple[float, float]:
    """Intervalo conforme de la probabilidad: p ± q recortado a [0, 1] (misma garantía de cobertura marginal que
    el conjunto de predicción: contiene la etiqueta observada con al menos 1 - alpha)."""
    q = unc["q"]
    return max(0.0, p - q), min(1.0, p + q)


def coverage_on_test(unc: dict, y_test, p_test) -> dict:
    y = np.asarray(y_test).astype(int)
    p = np.asarray(p_test, float)
    covered = np.array([("Botnet" if yy == 1 else "Normal") in prediction_set(unc, pp) for yy, pp in zip(y, p)])
    sizes = np.array([len(prediction_set(unc, pp)) for pp in p])
    lo_hi = [prob_interval(unc, pp) for pp in p]
    inside = np.array([lo <= yy <= hi for yy, (lo, hi) in zip(y, lo_hi)])
    out = {"nominal": unc["nominal_coverage"], "empirical_set": float(covered.mean()),
           "empirical_interval": float(inside.mean()), "n": int(len(y)),
           "share_ambiguous": float((sizes == 2).mean()), "share_empty": float((sizes == 0).mean()),
           "mean_interval_width": float(np.mean([hi - lo for lo, hi in lo_hi]))}
    for c, name in ((1, "Botnet"), (0, "Normal")):
        m = y == c
        out[f"coverage_{name.lower()}"] = float(covered[m].mean()) if m.any() else None
    out["meets_nominal"] = bool(out["empirical_set"] >= out["nominal"] - 0.02)
    return out


def ood_check(unc: dict, row: dict) -> dict:
    """Variables numéricas fuera del rango p1-p99 del entrenamiento (y categorías nunca vistas)."""
    flags = []
    n_num = 0
    for c, (lo, hi, mn, mx) in unc["ranges"].items():
        v = row.get(c)
        try:
            v = float(v)
        except (TypeError, ValueError):
            continue
        if v != v:
            continue
        n_num += 1
        if v < lo or v > hi:
            hard = v < mn or v > mx
            flags.append({"feature": c, "value": v, "p01": lo, "p99": hi, "beyond_training_range": bool(hard)})
    for c, cats in unc["categories"].items():
        v = row.get(c)
        if v is not None and str(v) not in cats:
            flags.append({"feature": c, "value": str(v), "unseen_category": True})
    frac = len(flags) / max(n_num + len(unc["categories"]), 1)
    return {"is_ood": bool(frac >= unc["ood_fraction_threshold"]), "fraction_out_of_range": frac,
            "flags": flags[:10], "n_out_of_range": len(flags)}
