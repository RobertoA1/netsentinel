"""Claves de agrupación (anti-fuga), partición Desarrollo/Validación/Prueba por grupos estratificada,
generación de pliegues anidados y validador de viabilidad."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedGroupKFold

GROUP_KEYS = {
    "src_ip": "Host origen",
    "src_dst": "Par origen-destino",
    "time_block": "Bloque temporal",
}
KEY_STRICTNESS = ["src_ip", "src_dst", "time_block"]  # de más a menos exigente para generalizar a hosts nuevos
PART_NAMES = ["dev", "val", "test"]
PART_ES = {"dev": "Desarrollo", "val": "Validación", "test": "Prueba"}
FRACS = (0.70, 0.15, 0.15)
MIN_ROWS_PER_PARTITION_CLASS = 30
MIN_FOLD_POSITIVES = 10
MIN_GROUPS_PER_PARTITION_CLASS = 3
BLOCK_OPTIONS_S = [5, 10, 15, 30, 60, 120, 300, 600, 1800, 3600]


def group_ids(aux: pd.DataFrame, group_key: str, unit: str, block_seconds: float = 10.0) -> np.ndarray:
    """Identificador de grupo por fila (cadena). `aux` trae _src_ip, _dst_ip, _t."""
    if group_key == "src_ip":
        return aux["_src_ip"].astype(str).values
    if group_key == "src_dst":
        if unit == "window":
            raise ValueError("El par origen-destino no aplica a ventanas host-tiempo (una ventana agrega varios destinos)")
        return (aux["_src_ip"].astype(str) + ">" + aux["_dst_ip"].astype(str)).values
    if group_key == "time_block":
        b = max(1.0, float(block_seconds))
        t0 = float(np.nanmin(aux["_t"].values))
        return np.floor((aux["_t"].values - t0) / b).astype(int).astype(str)
    raise ValueError(f"Clave de agrupación desconocida: {group_key}")


def _loss(cur: np.ndarray, target: np.ndarray, totals: np.ndarray, cnt: np.ndarray) -> float:
    """Desvío relativo de las filas por (partición, clase) respecto al objetivo + castigo por clase sin grupos."""
    l = float((((cur - target) / np.maximum(totals, 1.0)) ** 2).sum())
    miss = np.maximum(0.0, MIN_GROUPS_PER_PARTITION_CLASS - cnt) * (target > 0)
    return l + 0.3 * float(miss.sum())


def partition_groups(y: np.ndarray, groups: np.ndarray, seed: int = 42, fracs=FRACS, n_starts: int = 60) -> np.ndarray:
    """Asigna cada GRUPO a Desarrollo(0)/Validación(1)/Prueba(2) estratificando por clase.
    Voraz con reinicios aleatorios + mejora local (mover/intercambiar grupos); gana la menor pérdida
    (desvío de las filas por clase respecto a 70/15/15). Determinista dada la semilla."""
    rng = np.random.default_rng(seed)
    df = pd.DataFrame({"y": y.astype(int), "g": groups})
    tab = df.groupby(["g", "y"]).size().unstack(fill_value=0)
    for c in (0, 1):
        if c not in tab:
            tab[c] = 0
    tab = tab[[0, 1]]
    gnames = list(tab.index)
    N = tab.values.astype(float)  # [grupo, clase]
    totals = N.sum(0)
    target = np.outer(np.array(fracs), totals)
    G = len(gnames)

    def evaluate(assign: np.ndarray):
        cur = np.zeros((3, 2))
        cnt = np.zeros((3, 2))
        for p in range(3):
            m = assign == p
            cur[p] = N[m].sum(0)
            cnt[p] = (N[m] > 0).sum(0)
        return _loss(cur, target, totals, cnt), cur, cnt

    best_assign, best_loss = None, np.inf
    for s in range(n_starts):
        order = np.argsort(-(N[:, 1] * 1e6 + N[:, 0] + rng.random(G) * (0 if s == 0 else N.max() * (0.5 + s / n_starts))))
        assign = np.zeros(G, dtype=int)
        cur = np.zeros((3, 2))
        cnt = np.zeros((3, 2))
        for gi in order:
            n = N[gi]
            costs = []
            for p in range(3):
                after = cur.copy()
                after[p] += n
                c2 = cnt.copy()
                c2[p] += (n > 0)
                costs.append(_loss(after, target, totals, c2))
            p = int(np.argmin(costs))
            assign[gi] = p
            cur[p] += n
            cnt[p] += (n > 0)
        # mejora local incremental: mover un grupo a otra partición si baja la pérdida
        cur = np.zeros((3, 2))
        cnt = np.zeros((3, 2))
        for p in range(3):
            m = assign == p
            cur[p], cnt[p] = N[m].sum(0), (N[m] > 0).sum(0)
        loss = _loss(cur, target, totals, cnt)
        for _ in range(4):
            improved = False
            for gi in rng.permutation(G):
                p0 = assign[gi]
                n, nz = N[gi], (N[gi] > 0)
                for p in range(3):
                    if p == p0:
                        continue
                    c2, k2 = cur.copy(), cnt.copy()
                    c2[p0] -= n
                    k2[p0] -= nz
                    c2[p] += n
                    k2[p] += nz
                    l2 = _loss(c2, target, totals, k2)
                    if l2 < loss - 1e-12:
                        cur, cnt, loss, improved = c2, k2, l2, True
                        assign[gi] = p
                        p0 = p
                        n = N[gi]
            if not improved:
                break
        if loss < best_loss:
            best_assign, best_loss = assign.copy(), loss
    lookup = {g: int(best_assign[i]) for i, g in enumerate(gnames)}
    return np.array([lookup[g] for g in groups])


@dataclass
class FoldSpec:
    outer_train: np.ndarray  # índices (relativos a Desarrollo)
    outer_val: np.ndarray
    inner: list[tuple[np.ndarray, np.ndarray]]


def nested_folds(y: np.ndarray, groups: np.ndarray, n_outer: int = 5, n_inner: int = 3, seed: int = 42) -> list[FoldSpec]:
    """StratifiedGroupKFold externo (n_outer) e interno (n_inner) sobre Desarrollo, con semilla fija."""
    outer = StratifiedGroupKFold(n_splits=n_outer, shuffle=True, random_state=seed)
    folds: list[FoldSpec] = []
    idx = np.arange(len(y))
    for k, (tr, va) in enumerate(outer.split(idx, y, groups)):
        inner = StratifiedGroupKFold(n_splits=n_inner, shuffle=True, random_state=seed + 1 + k)
        inn = [(tr[a], tr[b]) for a, b in inner.split(tr, y[tr], groups[tr])]
        folds.append(FoldSpec(tr, va, inn))
    return folds


def check_folds(y: np.ndarray, folds: list[FoldSpec]) -> list[str]:
    """Problemas: pliegues con una sola clase en validación o entrenamiento."""
    problems = []
    for k, f in enumerate(folds):
        for name, ix in (("validación externa", f.outer_val), ("entrenamiento externo", f.outer_train)):
            if len(np.unique(y[ix])) < 2:
                problems.append(f"Pliegue externo {k + 1}: {name} con una sola clase")
        for j, (a, b) in enumerate(f.inner):
            for name, ix in (("validación interna", b), ("entrenamiento interno", a)):
                if len(np.unique(y[ix])) < 2:
                    problems.append(f"Pliegue {k + 1}.{j + 1}: {name} con una sola clase")
    return problems


def _class_group_stats(y: np.ndarray, groups: np.ndarray) -> dict:
    df = pd.DataFrame({"y": y.astype(int), "g": groups})
    out = {}
    for c, name in ((1, "Botnet"), (0, "Normal")):
        sub = df[df.y == c]
        sizes = sub.groupby("g").size()
        out[name] = {"rows": int(len(sub)), "groups": int(len(sizes)),
                     "size_min": int(sizes.min()) if len(sizes) else 0,
                     "size_median": float(sizes.median()) if len(sizes) else 0.0,
                     "size_p90": float(sizes.quantile(0.9)) if len(sizes) else 0.0,
                     "size_max": int(sizes.max()) if len(sizes) else 0,
                     "top_group_share": float(sizes.max() / sizes.sum()) if len(sizes) else 0.0}
    mixed = df.groupby("g")["y"].nunique()
    out["mixed_groups"] = int((mixed > 1).sum())
    out["total_groups"] = int(df["g"].nunique())
    return out


def validate_key(X: pd.DataFrame, y: np.ndarray, aux: pd.DataFrame, group_key: str, unit: str,
                 block_seconds: float, seed: int = 42, n_outer: int = 5, n_inner: int = 3) -> dict:
    """Valida UNA clave de agrupación: simula la partición y los pliegues anidados y reporta todo."""
    res: dict = {"group_key": group_key, "label": GROUP_KEYS[group_key], "viable": False, "blocking": [], "warnings": []}
    try:
        groups = group_ids(aux, group_key, unit, block_seconds)
    except ValueError as e:
        res["blocking"].append(str(e))
        res["applicable"] = False
        return res
    res["applicable"] = True
    stats = _class_group_stats(y, groups)
    res["class_stats"] = stats
    nb, nn = stats["Botnet"]["groups"], stats["Normal"]["groups"]
    need = int(np.ceil(n_outer / 0.70))  # grupos mínimos por clase para que Desarrollo alimente 5 pliegues
    res["min_groups_needed_per_class"] = need
    res["outer_inner_requirement"] = f"{n_outer} pliegues externos x {n_inner} internos"
    if min(nb, nn) < need:
        res["blocking"].append(
            f"Hay {nb} grupo(s) de Botnet y {nn} de Normal; se necesitan al menos {need} de cada clase "
            f"(5 pliegues externos sobre el 70 % de Desarrollo, y 3 internos dentro de cada uno).")
    part = partition_groups(y, groups, seed)
    tab = {}
    for p, pn in enumerate(PART_NAMES):
        m = part == p
        tab[pn] = {"Botnet": {"rows": int((y[m] == 1).sum()), "groups": int(len(set(groups[m & (y == 1)])))},
                   "Normal": {"rows": int((y[m] == 0).sum()), "groups": int(len(set(groups[m & (y == 0)])))}}
    res["partition"] = tab
    for pn in PART_NAMES:
        for c in ("Botnet", "Normal"):
            if tab[pn][c]["groups"] == 0:
                res["blocking"].append(f"La partición {PART_ES[pn]} se queda sin grupos de {c}.")
    for pn in ("val", "test"):
        for c in ("Botnet", "Normal"):
            if 0 < tab[pn][c]["groups"] < MIN_GROUPS_PER_PARTITION_CLASS:
                res["blocking"].append(
                    f"La partición {PART_ES[pn]} tiene solo {tab[pn][c]['groups']} grupo(s) de {c} "
                    f"(mínimo {MIN_GROUPS_PER_PARTITION_CLASS}): la métrica dependería de muy pocos grupos.")
            if 0 < tab[pn][c]["rows"] < MIN_ROWS_PER_PARTITION_CLASS:
                res["blocking"].append(
                    f"La partición {PART_ES[pn]} solo tiene {tab[pn][c]['rows']} filas de {c} "
                    f"(mínimo {MIN_ROWS_PER_PARTITION_CLASS} para estimar métricas); los grupos son demasiado grandes "
                    "o muy pocos para repartirlos 70/15/15.")
    dev_share = {c: tab["dev"][c]["rows"] / max(sum(tab[p][c]["rows"] for p in PART_NAMES), 1) for c in ("Botnet", "Normal")}
    res["dev_share"] = dev_share
    for c, sh in dev_share.items():
        if sh < 0.5:
            res["blocking"].append(f"Desarrollo recibe solo {sh * 100:.0f} % de los flujos de {c} (objetivo 70 %): "
                                   "hay grupos gigantes que no se pueden repartir.")
    # grupos repartidos entre particiones (debe ser 0 por construcción)
    gp = pd.DataFrame({"g": groups, "p": part}).groupby("g")["p"].nunique()
    res["groups_split_across_partitions"] = int((gp > 1).sum())
    # fuga residual por OTRAS claves (host, destino) entre particiones
    leak = {}
    for name, col in (("hosts_origen", "_src_ip"), ("destinos", "_dst_ip")):
        if col in aux and aux[col].astype(str).str.len().gt(0).any():
            s = pd.DataFrame({"k": aux[col].astype(str).values, "p": part, "y": y})
            shared = s.groupby("k")["p"].nunique()
            leak[name] = int((shared > 1).sum())
            pos = s[s.y == 1].groupby("k")["p"].nunique()
            leak[name + "_botnet"] = int((pos > 1).sum())
    res["shared_keys_across_partitions"] = leak
    # duplicados exactos de variables entre particiones
    feat_cols = [c for c in X.columns if not c.startswith("_") and c != "y"]
    try:
        h = pd.util.hash_pandas_object(X[feat_cols].round(6), index=False)
        dd = pd.DataFrame({"h": h.values, "p": part}).groupby("h")["p"].nunique()
        res["duplicate_vectors_across_partitions"] = int((dd > 1).sum())
        res["duplicate_vectors_rows_share"] = float(
            pd.Series(h.values).map(dd).gt(1).mean()) if len(h) else 0.0
    except Exception:  # pragma: no cover
        res["duplicate_vectors_across_partitions"] = None
    prev = float(y.mean()) if len(y) else 0.0
    res["prevalence"] = prev
    res["imbalance_ratio"] = float((1 - prev) / prev) if prev > 0 else None
    # simulación de pliegues anidados sobre Desarrollo
    dev = part == 0
    if not res["blocking"]:
        try:
            folds = nested_folds(y[dev], groups[dev], n_outer, n_inner, seed)
            prob = check_folds(y[dev], folds)
            if prob:
                res["blocking"] += prob[:6]
            else:
                small = [k + 1 for k, f in enumerate(folds)
                         if int((y[dev][f.outer_val] == 1).sum()) < MIN_FOLD_POSITIVES]
                if small:
                    res["blocking"].append("Los pliegues externos " + ", ".join(map(str, small))
                                           + f" tienen menos de {MIN_FOLD_POSITIVES} flujos Botnet en validación.")
                res["fold_sizes"] = [{"outer_train": int(len(f.outer_train)), "outer_val": int(len(f.outer_val)),
                                      "val_botnet": int((y[dev][f.outer_val] == 1).sum())} for f in folds]
        except ValueError as e:
            res["blocking"].append("No se pueden construir los pliegues anidados: " + str(e))
    if stats["Botnet"]["top_group_share"] > 0.5:
        res["warnings"].append(
            f"Un solo grupo concentra {stats['Botnet']['top_group_share'] * 100:.0f} % de los flujos Botnet: "
            "los pliegues serán desiguales.")
    if stats["mixed_groups"] > 0 and group_key == "time_block":
        res["warnings"].append("Cada bloque temporal mezcla clases; la validación por bloques es menos exigente que "
                               "la validación por host.")
    if group_key == "src_dst":
        res["warnings"].append("Un mismo host aparece en varias particiones con destinos distintos: es una validación "
                               "MENOS exigente que por host y generaliza peor a hosts nuevos.")
    if group_key == "time_block":
        res["warnings"].append("Bloques contiguos en el tiempo son parecidos entre sí (autocorrelación): la "
                               "estimación puede ser optimista y no mide la generalización a hosts nuevos.")
    res["viable"] = not res["blocking"]
    return res


def validate_all(X: pd.DataFrame, y: np.ndarray, aux: pd.DataFrame, unit: str, block_seconds: float,
                 chosen: str, seed: int = 42) -> dict:
    """Valida la clave elegida y las alternativas; recomienda la más exigente de las viables.
    Para el bloque temporal prueba varios tamaños y recomienda el MAYOR viable (menos autocorrelación)."""
    per_key = {k: validate_key(X, y, aux, k, unit, block_seconds, seed) for k in KEY_STRICTNESS}
    options = []
    span = float(aux["_t"].max() - aux["_t"].min()) if len(aux) else 0.0
    for b in BLOCK_OPTIONS_S:
        if b > max(span, 1.0):
            continue
        r = validate_key(X, y, aux, "time_block", unit, b, seed)
        cs = r.get("class_stats", {})
        options.append({"seconds": b, "viable": bool(r.get("viable")),
                        "groups_botnet": cs.get("Botnet", {}).get("groups"),
                        "groups_normal": cs.get("Normal", {}).get("groups"),
                        "problem": (r["blocking"][0] if r.get("blocking") else None)})
    viable_blocks = [o["seconds"] for o in options if o["viable"]]
    rec_block = max(viable_blocks) if viable_blocks else None
    viable_keys = [k for k in ("src_ip", "src_dst") if per_key[k].get("viable")]
    if viable_keys:
        recommended = viable_keys[0]
    elif rec_block is not None:
        recommended = "time_block"
    else:
        recommended = None
    return {"chosen": chosen, "recommended": recommended, "recommended_block_seconds": rec_block,
            "keys": per_key, "time_block_options": options, "seed": seed,
            "n_rows": int(len(y)), "n_botnet": int((y == 1).sum()), "n_normal": int((y == 0).sum()),
            "n_hosts_botnet": int(aux.loc[y == 1, "_src_ip"].nunique()),
            "n_hosts_normal": int(aux.loc[y == 0, "_src_ip"].nunique()), "unit": unit,
            "block_seconds": block_seconds, "span_seconds": span}
