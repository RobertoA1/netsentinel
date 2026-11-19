"""Pruebas estadísticas entre modelos: Friedman, Wilcoxon + Holm, McNemar, bootstrap pareado por grupos,
tamaños de efecto (diferencia media, d de Cohen pareada, delta de Cliff)."""
from __future__ import annotations

import itertools
import math

import numpy as np
from scipy import stats

from app.ml.metrics import metric_value


def holm(pvals: list[float]) -> list[float]:
    """Corrección de Holm-Bonferroni (p ajustados, monótonos, tope 1)."""
    m = len(pvals)
    order = np.argsort(pvals)
    adj = np.empty(m)
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, (m - rank) * pvals[i])
        adj[i] = min(1.0, running)
    return adj.tolist()


def wilcoxon_min_p(n: int) -> float:
    """p mínimo alcanzable de Wilcoxon exacto bilateral con n pares sin empates ni ceros."""
    return 2.0 / (2 ** n)


def friedman(table: dict[str, list[float]]) -> dict:
    """table: modelo -> valores por pliegue (mismo orden). Necesita >= 3 modelos."""
    names = list(table)
    if len(names) < 3:
        return {"applicable": False, "reason": "Friedman requiere al menos 3 modelos"}
    arr = [np.asarray(table[k], dtype=float) for k in names]
    n = len(arr[0])
    try:
        stat, p = stats.friedmanchisquare(*arr)
    except ValueError as e:
        return {"applicable": False, "reason": str(e)}
    ranks = stats.rankdata(-np.vstack(arr), axis=0)  # 1 = mejor
    return {"applicable": True, "statistic": float(stat), "p_value": float(p), "n_folds": n, "k_models": len(names),
            "mean_ranks": {k: float(r) for k, r in zip(names, ranks.mean(1))}}


def cliffs_delta(a, b) -> float:
    a, b = np.asarray(a, float), np.asarray(b, float)
    gt = sum((x > y) for x in a for y in b)
    lt = sum((x < y) for x in a for y in b)
    return float((gt - lt) / (len(a) * len(b)))


def cohen_dz(a, b) -> float | None:
    d = np.asarray(a, float) - np.asarray(b, float)
    sd = d.std(ddof=1) if len(d) > 1 else 0.0
    return float(d.mean() / sd) if sd > 0 else None


def pairwise_wilcoxon(table: dict[str, list[float]]) -> list[dict]:
    names = list(table)
    rows = []
    for a, b in itertools.combinations(names, 2):
        x, y = np.asarray(table[a], float), np.asarray(table[b], float)
        d = x - y
        if np.allclose(d, 0):
            p, w = 1.0, 0.0
        else:
            try:
                r = stats.wilcoxon(x, y, method="exact", alternative="two-sided")
                p, w = float(r.pvalue), float(r.statistic)
            except ValueError:
                p, w = 1.0, 0.0
        rows.append({"a": a, "b": b, "mean_diff": float(d.mean()), "cohen_dz": cohen_dz(x, y),
                     "cliffs_delta": cliffs_delta(x, y), "statistic": w, "p_value": p, "n_folds": len(x),
                     "min_attainable_p": wilcoxon_min_p(len(x))})
    adj = holm([r["p_value"] for r in rows]) if rows else []
    for r, pa in zip(rows, adj):
        r["p_holm"] = pa
        r["significant_005"] = bool(pa < 0.05)
    return rows


def mcnemar(y, pred_a, pred_b) -> dict:
    """McNemar exacto (binomial) sobre predicciones emparejadas. b: A acierta y B falla; c: A falla y B acierta."""
    y, a, b_ = np.asarray(y), np.asarray(pred_a), np.asarray(pred_b)
    ca, cb = a == y, b_ == y
    b = int((ca & ~cb).sum())
    c = int((~ca & cb).sum())
    n = b + c
    p = 1.0 if n == 0 else float(stats.binomtest(min(b, c), n, 0.5).pvalue)
    return {"b_a_right_b_wrong": b, "c_a_wrong_b_right": c, "discordant": n, "p_value": p}


def paired_bootstrap_diff(y, p_a, p_b, groups, metric: str = "pr_auc", n_boot: int = 1000, seed: int = 42) -> dict:
    """IC 95 % de la diferencia (A - B) de una métrica remuestreando GRUPOS con reemplazo (emparejado)."""
    y, p_a, p_b, groups = np.asarray(y), np.asarray(p_a), np.asarray(p_b), np.asarray(groups)
    ug, inv = np.unique(groups, return_inverse=True)
    members = [np.where(inv == i)[0] for i in range(len(ug))]
    rng = np.random.default_rng(seed)
    base = metric_value(y, p_a, metric) - metric_value(y, p_b, metric)
    diffs = []
    for _ in range(n_boot):
        pick = rng.integers(0, len(ug), len(ug))
        idx = np.concatenate([members[i] for i in pick])
        if len(np.unique(y[idx])) < 2:
            continue
        diffs.append(metric_value(y[idx], p_a[idx], metric) - metric_value(y[idx], p_b[idx], metric))
    d = np.array(diffs)
    if len(d) == 0:
        return {"metric": metric, "diff": float(base), "ci": [None, None], "n_boot": 0}
    return {"metric": metric, "diff": float(base), "ci": [float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))],
            "n_boot": int(len(d)), "ci_excludes_zero": bool(np.percentile(d, 2.5) > 0 or np.percentile(d, 97.5) < 0)}


def kendalls_w(rank_matrix: np.ndarray) -> float:
    """Concordancia de Kendall W entre m evaluadores (filas) que ordenan n objetos (columnas)."""
    m, n = rank_matrix.shape
    if m < 2 or n < 2:
        return float("nan")
    s = ((rank_matrix.sum(0) - rank_matrix.sum(0).mean()) ** 2).sum()
    return float(12 * s / (m ** 2 * (n ** 3 - n)))


def mean_pairwise_kendall_tau(imp: np.ndarray) -> float:
    taus = []
    for i, j in itertools.combinations(range(imp.shape[0]), 2):
        t = stats.kendalltau(imp[i], imp[j]).statistic
        if t == t:
            taus.append(t)
    return float(np.mean(taus)) if taus else float("nan")


def fmt_p(p: float | None) -> str:
    if p is None or (isinstance(p, float) and math.isnan(p)):
        return "n/d"
    return "<0,001" if p < 0.001 else f"{p:.3f}".replace(".", ",")
