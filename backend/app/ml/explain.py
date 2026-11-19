"""Explicabilidad tabular: SHAP (global/local), permutación, mapas de calor, dependencia parcial/ICE y oclusión."""
from __future__ import annotations

import warnings
from typing import Callable

import numpy as np
import pandas as pd
from sklearn.inspection import permutation_importance
from sklearn.pipeline import Pipeline

from app.ml import models as M
from app.ml.features import FEATURE_GROUPS, FLOW_CATEGORICAL, WINDOW_CATEGORICAL, feature_columns
from app.ml.metrics import metric_value

warnings.filterwarnings("ignore", category=UserWarning, module="shap")


def cat_cols(unit: str) -> list[str]:
    return WINDOW_CATEGORICAL if unit == "window" else FLOW_CATEGORICAL


def transformed_to_original(pipe: Pipeline, unit: str) -> tuple[list[str], list[str]]:
    names = list(pipe.named_steps["pre"].get_feature_names_out())
    orig = feature_columns(unit)
    cats = sorted(cat_cols(unit), key=len, reverse=True)
    mapping = []
    for nme in names:
        if nme in orig:
            mapping.append(nme)
            continue
        m = next((c for c in cats if nme.startswith(c + "_")), None)
        mapping.append(m or nme)
    return names, mapping


class ShapExplainer:
    """Envuelve el explicador adecuado: Lineal (LR), Tree (RF, XGBoost) o Permutation (HGB)."""

    def __init__(self, pipe: Pipeline, model_type: str, unit: str, background: pd.DataFrame):
        self.pipe, self.model_type, self.unit = pipe, model_type, unit
        self.names, self.mapping = transformed_to_original(pipe, unit)
        self.orig = feature_columns(unit)
        pre, self.clf = pipe.named_steps["pre"], pipe.named_steps["clf"]
        bg = pre.transform(background.head(100))
        import shap

        if model_type == "logreg":
            self.exp = shap.LinearExplainer(self.clf, bg)
            self.space = "log-odds"
        elif model_type in ("random_forest", "xgboost"):
            self.exp = shap.TreeExplainer(self.clf)
            self.space = "probabilidad" if model_type == "random_forest" else "log-odds"
        elif model_type == "hist_gb":
            f = lambda Z: self.clf.predict_proba(pd.DataFrame(Z, columns=self.names))[:, 1]  # noqa: E731
            self.exp = shap.explainers.Permutation(f, shap.maskers.Independent(bg.values, max_samples=60))
            self.space = "probabilidad"
        else:
            self.exp = None
            self.space = "n/a"
        self.base = 0.0

    def values_transformed(self, X: pd.DataFrame) -> np.ndarray:
        Z = self.pipe.named_steps["pre"].transform(X)
        if self.exp is None:
            return np.zeros(Z.shape)
        if self.model_type == "hist_gb":
            ex = self.exp(Z.values, max_evals=2 * Z.shape[1] + 1, silent=True)
            self.base = float(np.mean(ex.base_values))
            return np.asarray(ex.values)
        if self.model_type == "logreg":
            v = self.exp.shap_values(Z)
            self.base = float(np.ravel(self.exp.expected_value)[0])
            return np.asarray(v)
        v = self.exp.shap_values(np.asarray(Z, dtype=float), check_additivity=False)
        ev = np.ravel(self.exp.expected_value)
        v = np.asarray(v)
        if v.ndim == 3:  # (n, f, clases) -> clase positiva
            v = v[:, :, 1]
            self.base = float(ev[1] if len(ev) > 1 else ev[0])
        else:
            self.base = float(ev[0])
        return v

    def values(self, X: pd.DataFrame) -> np.ndarray:
        """Contribuciones agregadas a las variables ORIGINALES (suma de las columnas one-hot)."""
        V = self.values_transformed(X)
        out = np.zeros((V.shape[0], len(self.orig)))
        idx = {c: i for i, c in enumerate(self.orig)}
        for j, m in enumerate(self.mapping):
            if m in idx:
                out[:, idx[m]] += V[:, j]
        return out


def stratified_sample(y: np.ndarray, n: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    pos, neg = np.where(y == 1)[0], np.where(y == 0)[0]
    k = n // 2
    a = rng.choice(pos, min(k, len(pos)), replace=False) if len(pos) else np.array([], int)
    b = rng.choice(neg, min(n - len(a), len(neg)), replace=False) if len(neg) else np.array([], int)
    return np.sort(np.concatenate([a, b]))


def global_shap(ex: ShapExplainer, X: pd.DataFrame, y: np.ndarray, seed: int, n: int = 500, top: int = 12) -> dict:
    idx = stratified_sample(y, n, seed)
    Xs = X.iloc[idx]
    V = ex.values(Xs)
    mean_abs = np.abs(V).mean(0)
    order = np.argsort(-mean_abs)
    importance = [{"feature": ex.orig[i], "value": float(mean_abs[i])} for i in order]
    swarm = []
    rng = np.random.default_rng(seed)
    for i in order[:top]:
        col = ex.orig[i]
        if col in cat_cols(ex.unit):
            codes = pd.factorize(Xs[col].astype(str))[0].astype(float)
            c = codes / max(codes.max(), 1)
        else:
            c = pd.to_numeric(Xs[col], errors="coerce").rank(pct=True).fillna(0.5).values
        sel = rng.choice(len(Xs), min(150, len(Xs)), replace=False)
        swarm.append({"feature": col, "points": [{"x": round(float(V[s, i]), 5), "c": round(float(c[s]), 3)} for s in sel]})
    return {"importance": importance, "swarm": swarm, "space": ex.space, "n": int(len(Xs)), "base": ex.base,
            "values": V, "index": idx}


def permutation_val(pipe: Pipeline, X: pd.DataFrame, y: np.ndarray, seed: int, metric: str = "average_precision",
                    n_repeats: int = 5, max_rows: int = 2000) -> list[dict]:
    if len(X) > max_rows:
        idx = stratified_sample(y, max_rows, seed)
        X, y = X.iloc[idx], y[idx]
    r = permutation_importance(pipe, X, y, scoring=metric, n_repeats=n_repeats, random_state=seed, n_jobs=1)
    order = np.argsort(-r.importances_mean)
    return [{"feature": X.columns[i], "value": float(r.importances_mean[i]), "std": float(r.importances_std[i])}
            for i in order]


def rank_discrepancy(shap_imp: list[dict], perm_imp: list[dict], gap: int = 5) -> list[dict]:
    rs = {d["feature"]: i + 1 for i, d in enumerate(shap_imp)}
    rp = {d["feature"]: i + 1 for i, d in enumerate(perm_imp)}
    rows = []
    for f in rs:
        a, b = rs[f], rp.get(f, len(rs))
        rows.append({"feature": f, "rank_shap": a, "rank_perm": b, "diff": abs(a - b), "flag": abs(a - b) >= gap})
    return sorted(rows, key=lambda r: -r["diff"])


def time_bins(t: np.ndarray, n_bins: int = 20) -> tuple[np.ndarray, np.ndarray]:
    lo, hi = float(np.nanmin(t)), float(np.nanmax(t))
    edges = np.linspace(lo, hi + 1e-6, n_bins + 1)
    return np.digitize(t, edges[1:-1]), edges


def host_time_heatmap(p: np.ndarray, aux: pd.DataFrame, n_bins: int = 16, top_hosts: int = 14) -> dict:
    b, edges = time_bins(aux["_t"].values, n_bins)
    df = pd.DataFrame({"h": aux["_src_ip"].values, "b": b, "p": p})
    risk = df.groupby("h")["p"].agg(["max", "count"])
    hosts = risk.sort_values(["max", "count"], ascending=False).head(top_hosts).index.tolist()
    mat = df[df.h.isin(hosts)].pivot_table(index="h", columns="b", values="p", aggfunc="mean").reindex(
        index=hosts, columns=range(n_bins))
    cnt = df[df.h.isin(hosts)].pivot_table(index="h", columns="b", values="p", aggfunc="count").reindex(
        index=hosts, columns=range(n_bins)).fillna(0)
    t0 = edges[0]
    cols = [f"+{(edges[i] - t0) / 60:.1f} min" for i in range(n_bins)]
    return {"rows": hosts, "cols": cols, "values": [[None if np.isnan(v) else round(float(v), 4) for v in r]
                                                    for r in mat.values], "counts": cnt.astype(int).values.tolist(),
            "vlabel": "Probabilidad media de Botnet", "scale": "seq", "vmin": 0, "vmax": 1}


def feature_time_heatmap(V: np.ndarray, orig: list[str], t: np.ndarray, n_bins: int = 16, top: int = 8) -> dict:
    b, edges = time_bins(t, n_bins)
    order = np.argsort(-np.abs(V).mean(0))[:top]
    rows = [orig[i] for i in order]
    mat = np.full((len(order), n_bins), np.nan)
    for k in range(n_bins):
        m = b == k
        if m.sum() > 0:
            mat[:, k] = V[m][:, order].mean(0)
    t0 = edges[0]
    lim = float(np.nanmax(np.abs(mat))) if np.isfinite(mat).any() else 1.0
    return {"rows": rows, "cols": [f"+{(edges[i] - t0) / 60:.1f} min" for i in range(n_bins)],
            "values": [[None if np.isnan(v) else round(float(v), 4) for v in r] for r in mat],
            "vlabel": "Contribución media (SHAP)", "scale": "div", "vmin": -lim, "vmax": lim}


def pdp_ice(predict: Callable[[pd.DataFrame], np.ndarray], X: pd.DataFrame, features: list[str], unit: str,
            n_grid: int = 20, n_rows: int = 200, n_ice: int = 25, seed: int = 42) -> list[dict]:
    rng = np.random.default_rng(seed)
    sub = X.iloc[rng.choice(len(X), min(n_rows, len(X)), replace=False)].reset_index(drop=True)
    out = []
    for f in features:
        if f in cat_cols(unit):
            continue
        v = pd.to_numeric(X[f], errors="coerce").dropna()
        if v.nunique() < 3:
            continue
        grid = np.unique(np.quantile(v, np.linspace(0.02, 0.98, n_grid)))
        P = np.zeros((len(sub), len(grid)))
        for j, gv in enumerate(grid):
            d = sub.copy()
            d[f] = gv
            P[:, j] = predict(d)
        ice_idx = rng.choice(len(sub), min(n_ice, len(sub)), replace=False)
        out.append({"feature": f, "grid": [round(float(g), 6) for g in grid],
                    "pdp": [round(float(x), 5) for x in P.mean(0)],
                    "ice": [[round(float(x), 4) for x in P[i]] for i in ice_idx]})
    return out


def normal_reference(X: pd.DataFrame, y: np.ndarray, unit: str) -> dict:
    """Valores de referencia para enmascarar: mediana (numéricas) / moda (categóricas) de la clase NORMAL."""
    nn = X[y == 0]
    ref = {}
    for c in X.columns:
        if c in cat_cols(unit):
            m = nn[c].mode()
            ref[c] = m.iloc[0] if len(m) else X[c].mode().iloc[0]
        else:
            ref[c] = float(pd.to_numeric(nn[c], errors="coerce").median())
    return ref


def occlusion(predict: Callable[[pd.DataFrame], np.ndarray], Xpos: pd.DataFrame, ref: dict, unit: str) -> dict:
    base = predict(Xpos)
    feats = []
    for c in Xpos.columns:
        d = Xpos.copy()
        d[c] = ref[c]
        feats.append({"feature": c, "drop": float((base - predict(d)).mean())})
    feats.sort(key=lambda r: -r["drop"])
    groups = []
    for gname, cols in FEATURE_GROUPS["window" if unit == "window" else "flow"].items():
        d = Xpos.copy()
        for c in cols:
            if c in d:
                d[c] = ref[c]
        groups.append({"group": gname, "features": cols, "drop": float((base - predict(d)).mean())})
    groups.sort(key=lambda r: -r["drop"])
    return {"features": feats, "groups": groups, "n": int(len(Xpos)), "mean_prob": float(base.mean())}


def fold_importances(pipes_vals: list[np.ndarray]) -> dict:
    """pipes_vals: por pliegue, vector de importancia (|SHAP| medio) alineado a las variables originales."""
    from app.ml.stats_tests import kendalls_w, mean_pairwise_kendall_tau
    from scipy import stats as sps

    imp = np.array(pipes_vals)  # [k, f]
    ranks = np.vstack([sps.rankdata(-r) for r in imp])
    share = imp / np.maximum(imp.sum(1, keepdims=True), 1e-12)
    return {"kendall_w": kendalls_w(ranks), "mean_tau": mean_pairwise_kendall_tau(imp), "share": share, "ranks": ranks}
