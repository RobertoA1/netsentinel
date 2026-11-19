"""Métricas de clasificación binaria, agregación entre pliegues con IC 95 % (t de Student y bootstrap)."""
from __future__ import annotations

import math

import numpy as np
from scipy import stats
from sklearn.metrics import (average_precision_score, brier_score_loss, confusion_matrix, matthews_corrcoef,
                             precision_recall_curve, roc_auc_score, roc_curve)

METRIC_NAMES = ["precision", "recall", "f1", "specificity", "balanced_accuracy", "accuracy", "mcc", "roc_auc",
                "pr_auc", "brier"]
METRIC_ES = {"precision": "Precisión", "recall": "Exhaustividad", "f1": "F1", "specificity": "Especificidad",
             "balanced_accuracy": "Exactitud balanceada", "accuracy": "Exactitud", "mcc": "MCC",
             "roc_auc": "ROC-AUC", "pr_auc": "PR-AUC", "brier": "Brier"}
OBJECTIVES = ["pr_auc", "f1", "mcc", "roc_auc"]


def _f(x) -> float | None:
    x = float(x)
    return None if (math.isnan(x) or math.isinf(x)) else x


def confusion(y, p, thr: float) -> dict:
    pred = (np.asarray(p) >= thr).astype(int)
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
    return {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)}


def compute_metrics(y, p, thr: float = 0.5) -> dict:
    y = np.asarray(y).astype(int)
    p = np.asarray(p, dtype=float)
    c = confusion(y, p, thr)
    tp, fp, fn, tn = c["tp"], c["fp"], c["fn"], c["tn"]
    prec = tp / (tp + fp) if (tp + fp) else float("nan")
    rec = tp / (tp + fn) if (tp + fn) else float("nan")
    spec = tn / (tn + fp) if (tn + fp) else float("nan")
    f1 = 2 * prec * rec / (prec + rec) if (prec == prec and rec == rec and (prec + rec) > 0) else (
        0.0 if (tp + fp + fn) else float("nan"))
    two = len(np.unique(y)) == 2
    pred = (p >= thr).astype(int)
    out = {"precision": prec, "recall": rec, "f1": f1, "specificity": spec,
           "balanced_accuracy": (rec + spec) / 2 if (rec == rec and spec == spec) else float("nan"),
           "accuracy": (tp + tn) / max(len(y), 1),
           "mcc": float(matthews_corrcoef(y, pred)) if two else float("nan"),
           "roc_auc": float(roc_auc_score(y, p)) if two else float("nan"),
           "pr_auc": float(average_precision_score(y, p)) if two else float("nan"),
           "brier": float(brier_score_loss(y, np.clip(p, 0, 1)))}
    res = {k: _f(v) for k, v in out.items()}
    res.update(c)
    res["n"] = int(len(y))
    res["n_pos"] = int(y.sum())
    res["threshold"] = float(thr)
    return res


def metric_value(y, p, name: str, thr: float = 0.5) -> float:
    """Valor de la métrica objetivo (mayor es mejor) usado por Optuna; NaN -> 0."""
    y = np.asarray(y)
    if len(np.unique(y)) < 2:
        return 0.0
    if name == "pr_auc":
        return float(average_precision_score(y, p))
    if name == "roc_auc":
        return float(roc_auc_score(y, p))
    pred = (np.asarray(p) >= thr).astype(int)
    if name == "mcc":
        return float(matthews_corrcoef(y, pred))
    if name == "f1":
        tp = int(((pred == 1) & (y == 1)).sum())
        fp = int(((pred == 1) & (y == 0)).sum())
        fn = int(((pred == 0) & (y == 1)).sum())
        return 2 * tp / max(2 * tp + fp + fn, 1)
    raise ValueError(f"Métrica objetivo no soportada: {name}")


def best_threshold(y, p, objective: str = "f1") -> tuple[float, float]:
    """Umbral que maximiza F1 (o MCC) sobre Validación. Devuelve (umbral, valor)."""
    y = np.asarray(y).astype(int)
    p = np.asarray(p, dtype=float)
    cands = np.unique(np.concatenate([np.quantile(p, np.linspace(0, 1, 201)), [0.5]]))
    best, bv = 0.5, -2.0
    for t in cands:
        v = metric_value(y, p, "mcc" if objective == "mcc" else "f1", float(t))
        if v > bv + 1e-12 or (abs(v - bv) <= 1e-12 and abs(t - 0.5) < abs(best - 0.5)):
            best, bv = float(t), v
    return best, bv


def curves(y, p, max_points: int = 200) -> dict:
    y = np.asarray(y).astype(int)
    p = np.asarray(p, dtype=float)
    fpr, tpr, _ = roc_curve(y, p)
    pr, rc, _ = precision_recall_curve(y, p)
    return {"roc": {"fpr": _thin(fpr, max_points), "tpr": _thin(tpr, max_points)},
            "pr": {"recall": _thin(rc, max_points), "precision": _thin(pr, max_points)},
            "prevalence": float(y.mean())}


def _thin(a, n):
    a = np.asarray(a, dtype=float)
    if len(a) <= n:
        return [round(float(x), 5) for x in a]
    idx = np.unique(np.linspace(0, len(a) - 1, n).astype(int))
    return [round(float(x), 5) for x in a[idx]]


def roc_band(fold_y, fold_p, grid=None) -> dict:
    """Media y desviación de la TPR en una malla común de FPR (banda de variabilidad entre pliegues)."""
    grid = np.linspace(0, 1, 101) if grid is None else grid
    tprs = []
    for y, p in zip(fold_y, fold_p):
        fpr, tpr, _ = roc_curve(y, p)
        tprs.append(np.interp(grid, fpr, tpr))
    t = np.array(tprs)
    return {"x": grid.round(4).tolist(), "mean": t.mean(0).round(5).tolist(),
            "lo": np.clip(t.mean(0) - t.std(0, ddof=1) if len(t) > 1 else t.mean(0), 0, 1).round(5).tolist(),
            "hi": np.clip(t.mean(0) + t.std(0, ddof=1) if len(t) > 1 else t.mean(0), 0, 1).round(5).tolist()}


def pr_band(fold_y, fold_p, grid=None) -> dict:
    grid = np.linspace(0, 1, 101) if grid is None else grid
    ps = []
    for y, p in zip(fold_y, fold_p):
        pr, rc, _ = precision_recall_curve(y, p)
        o = np.argsort(rc)
        ps.append(np.interp(grid, rc[o], pr[o]))
    t = np.array(ps)
    sd = t.std(0, ddof=1) if len(t) > 1 else np.zeros_like(t[0])
    return {"x": grid.round(4).tolist(), "mean": t.mean(0).round(5).tolist(),
            "lo": np.clip(t.mean(0) - sd, 0, 1).round(5).tolist(), "hi": np.clip(t.mean(0) + sd, 0, 1).round(5).tolist()}


def reliability(y, p, n_bins: int = 10) -> dict:
    y = np.asarray(y).astype(int)
    p = np.asarray(p, dtype=float)
    edges = np.linspace(0, 1, n_bins + 1)
    idx = np.clip(np.digitize(p, edges[1:-1]), 0, n_bins - 1)
    xs, ys, ns = [], [], []
    for b in range(n_bins):
        m = idx == b
        if m.sum() > 0:
            xs.append(float(p[m].mean()))
            ys.append(float(y[m].mean()))
            ns.append(int(m.sum()))
    ece = float(sum(n * abs(x - yv) for x, yv, n in zip(xs, ys, ns)) / max(sum(ns), 1))
    return {"mean_predicted": [round(x, 4) for x in xs], "observed": [round(v, 4) for v in ys], "n": ns,
            "ece": ece}


def aggregate(values, seed: int = 42, n_boot: int = 10000) -> dict:
    """Una observación por pliegue externo -> media, desviación, IC 95 % t de Student (n-1 g.l.) y bootstrap."""
    v = np.array([x for x in values if x is not None and not (isinstance(x, float) and math.isnan(x))], dtype=float)
    n = len(v)
    if n == 0:
        return {"n": 0, "mean": None, "std": None, "ci_t": [None, None], "ci_boot": [None, None], "values": []}
    mean = float(v.mean())
    sd = float(v.std(ddof=1)) if n > 1 else 0.0
    if n > 1 and sd > 0:
        h = stats.t.ppf(0.975, n - 1) * sd / math.sqrt(n)
        ci_t = [mean - h, mean + h]
        # las métricas acotadas no pueden salirse de su rango observable: se recorta el IC t (aproximación normal)
        if v.min() >= -1e-9:
            ci_t[0] = max(ci_t[0], 0.0)
        if v.max() <= 1 + 1e-9:
            ci_t[1] = min(ci_t[1], 1.0)
    else:
        ci_t = [mean, mean]
    rng = np.random.default_rng(seed)
    bm = rng.choice(v, size=(n_boot, n), replace=True).mean(1)
    ci_b = [float(np.percentile(bm, 2.5)), float(np.percentile(bm, 97.5))]
    return {"n": n, "mean": mean, "std": sd, "ci_t": [float(c) for c in ci_t], "ci_boot": ci_b,
            "values": [float(x) for x in v]}


def aggregate_metrics(fold_metrics: list[dict], names=METRIC_NAMES, seed: int = 42) -> dict:
    return {m: aggregate([fm.get(m) for fm in fold_metrics], seed) for m in names}
