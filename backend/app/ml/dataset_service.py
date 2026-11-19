"""Fase 1 — Datos: registro de datasets ML, versionado inmutable, estadística descriptiva y validación de grupos."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats as sps
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.base import utcnow
from app.ml import data as D
from app.ml import groups as G
from app.ml import interpret as I
from app.ml import prepare as P
from app.ml.features import FEATURE_LABELS_ES, feature_columns, feature_spec
from app.ml.store import dump_json, load_json
from app.models import MlDataset, MlDatasetVersion, Source


class DatasetError(ValueError):
    pass


@lru_cache(maxsize=3)
def _flows_cached(path: str, sha: str) -> pd.DataFrame:
    return D.load_snapshot(path, sha)


def flows_of(ds: MlDataset) -> pd.DataFrame:
    return _flows_cached(ds.snapshot_path, ds.snapshot_sha256)


def _new_dataset(db: Session, name: str, df: pd.DataFrame, dup: int, origin: str, source_id: int | None, meta_kw: dict,
                 user: str) -> tuple[MlDataset, MlDatasetVersion]:
    if df.empty:
        raise DatasetError("El origen no contiene flujos")
    if db.execute(select(MlDataset.id).where(MlDataset.name == name)).first():
        raise DatasetError("Ya existe un dataset ML con ese nombre")
    labs = df["label_raw"].dropna()
    if labs.empty:
        raise DatasetError("El origen no tiene etiquetas (columna Label): no sirve para aprendizaje supervisado")
    ds = MlDataset(name=name, origin=origin, source_id=source_id, snapshot_path="", snapshot_sha256="", n_rows=len(df),
                   n_duplicates_dropped=dup, created_by=user)
    db.add(ds)
    db.flush()
    ds.snapshot_path, ds.snapshot_sha256 = D.save_snapshot(df, ds.id)
    meta = P.validate_meta(P.default_meta(name, df, **meta_kw))
    # la agrupación por defecto es la RECOMENDADA por el validador (si hay una viable)
    if not meta_kw.get("group_key"):
        meta = _auto_group(df, meta)
    v = MlDatasetVersion(dataset_id=ds.id, version=1, meta=meta, content_hash=P.meta_hash(meta, ds.snapshot_sha256),
                         change_note="Versión inicial", created_by=user)
    db.add(v)
    db.commit()
    return ds, v


def _auto_group(df: pd.DataFrame, meta: dict) -> dict:
    ff = P.feature_frame(df, meta)
    ff = ff[ff["y"].notna()].reset_index(drop=True)
    if len(ff) < 20 or ff["y"].nunique() < 2:
        return meta
    cols = feature_columns(meta["unit"])
    g = G.validate_all(ff[cols], ff["y"].astype(int).values, ff[[c for c in ff.columns if c.startswith("_")]],
                       meta["unit"], meta["time_block_seconds"], meta["group_key"])
    if g["recommended"]:
        meta["group_key"] = g["recommended"]
        if g["recommended"] == "time_block" and g["recommended_block_seconds"]:
            meta["time_block_seconds"] = float(g["recommended_block_seconds"])
    return meta


def create_from_source(db: Session, name: str, source_id: int, user: str, **meta_kw) -> tuple[MlDataset, MlDatasetVersion]:
    src = db.get(Source, source_id)
    if src is None:
        raise DatasetError("Fuente inexistente")
    if src.format != "ctu13_binetflow":
        raise DatasetError("Solo las fuentes con formato ctu13_binetflow tienen etiquetas de verdad conocida")
    df, dup = D.frame_from_source(db, source_id)
    return _new_dataset(db, name, df, dup, "source", source_id, {"description": f"Fuente «{src.name}» (#{src.id})", **meta_kw}, user)


def create_from_upload(db: Session, name: str, content: bytes, filename: str, user: str, cidrs: list[str],
                       **meta_kw) -> tuple[MlDataset, MlDatasetVersion]:
    try:
        df, info = D.frame_from_file(content, filename, cidrs)
    except ValueError as e:
        raise DatasetError(str(e)) from e
    kw = {"description": f"Archivo subido: {Path(filename).name} ({info['lines']} líneas, {info['parse_errors']} con error)",
          **meta_kw}
    return _new_dataset(db, name, df, info["duplicates_dropped"], "upload", None, kw, user)


EDITABLE = ("name", "description", "provenance", "license", "label_map", "unit", "window_minutes", "group_key",
            "time_block_seconds", "notes")


def update_meta(db: Session, ds: MlDataset, changes: dict, note: str, user: str) -> MlDatasetVersion:
    """Cada cambio crea una versión nueva (las anteriores son inmutables: un entrenamiento referencia una de ellas)."""
    cur = db.execute(select(MlDatasetVersion).where(MlDatasetVersion.dataset_id == ds.id,
                                                    MlDatasetVersion.version == ds.current_version)).scalar_one()
    meta = dict(cur.meta)
    for k in EDITABLE:
        if k in changes and changes[k] is not None:
            meta[k] = changes[k]
    meta = P.validate_meta(meta)
    if meta["name"] != ds.name:
        if db.execute(select(MlDataset.id).where(MlDataset.name == meta["name"], MlDataset.id != ds.id)).first():
            raise DatasetError("Ya existe un dataset con ese nombre")
        ds.name = meta["name"]
    h = P.meta_hash(meta, ds.snapshot_sha256)
    if meta == cur.meta:
        raise DatasetError("No hay cambios que guardar")
    v = MlDatasetVersion(dataset_id=ds.id, version=cur.version + 1, meta=meta, content_hash=h,
                         change_note=(note or "Edición de metadatos")[:500], created_by=user)
    db.add(v)
    ds.current_version = v.version
    db.commit()
    return v


# ------------------------------------------------------------------------------ estadística descriptiva
def _cache(ds: MlDataset, version: int, kind: str) -> Path:
    return Path(ds.snapshot_path).parent / f"v{version}_{kind}.json"


def summary(ds: MlDataset, v: MlDatasetVersion, refresh: bool = False) -> dict:
    cp = _cache(ds, v.version, "summary")
    if cp.exists() and not refresh:
        return load_json(cp)
    meta = v.meta
    flows = flows_of(ds)
    d = D.labelled_frame(flows, meta["label_map"])
    n_excl = int(d["y_flow"].isna().sum())
    ff = P.feature_frame(flows, meta, True)
    ff = ff[ff["y"].notna()].reset_index(drop=True)
    y = ff["y"].astype(int).values
    cols = feature_columns(meta["unit"])
    X = ff[cols]
    unit_es = "ventanas host-tiempo" if meta["unit"] == "window" else "flujos"
    nb, nn = int((y == 1).sum()), int((y == 0).sum())
    figs, tables = [], []
    note_n = f"n = {nb + nn} {unit_es} etiquetados (Botnet {nb}, Normal {nn}); excluidos: {n_excl} flujos sin etiqueta conocida."
    # clases
    figs.append(I.fig("classes", "bars", "Distribución de clases", {"labels": ["Normal", "Botnet"],
                      "series": [{"name": unit_es.capitalize(), "values": [nn, nb]}], "ylabel": f"Nº de {unit_es}"},
                      note_n, I.class_distribution(nb, nn, n_excl, unit_es)))
    # etiquetas crudas
    rc = d["label_raw"].fillna("(sin etiqueta)").value_counts()
    rows = [{"label": k, "count": int(c), "klass": meta["label_map"].get(k, "excluded")} for k, c in rc.head(40).items()]
    tables.append(I.table("raw_labels", "Etiquetas originales y su clase asignada", [("label", "Etiqueta original"),
                          ("klass", "Clase"), ("count", "Flujos")], rows,
                          f"Total de {len(d)} flujos en la instantánea (duplicados de carga eliminados: {ds.n_duplicates_dropped}).",
                          I.interp([f"{n_excl} flujos ({I.pct(n_excl / max(len(d), 1))}) quedan excluidos por ser Background u otras etiquetas sin verdad conocida."],
                                   ["El mapeo es editable en los metadatos; cada cambio crea una versión nueva."])))
    flow = d[d["y_flow"].notna()].copy()
    flow["klass"] = np.where(flow["y_flow"] == 1, "Botnet", "Normal")

    def grouped_bar(id_, title, series_by, labels, note, ip, log=False):
        figs.append(I.fig(id_, "bars", title, {"labels": [str(x) for x in labels],
                          "series": [{"name": c, "values": [int(series_by[c].get(l, 0)) for l in labels]} for c in ("Normal", "Botnet")],
                          "ylabel": "Flujos", "log": log}, note, ip))

    for col, lab_, topn in (("proto", "Protocolos por clase", 6), ("state", "Estados de conexión por clase", 10)):
        ct = flow.groupby([col, "klass"]).size().unstack(fill_value=0)
        for c in ("Normal", "Botnet"):
            if c not in ct:
                ct[c] = 0
        top = (ct.sum(1).sort_values(ascending=False).head(topn)).index.tolist()
        sb = {c: ct[c].to_dict() for c in ("Normal", "Botnet")}
        topk = top[0] if top else ""
        grouped_bar(col, lab_, sb, top, f"{note_n} Se muestran las {len(top)} categorías más frecuentes (escala log).",
                    I.interp([f"{topk} es la categoría más frecuente: {I.n(int(ct.loc[topk].sum()))} flujos "
                              f"(Botnet {I.n(int(ct.loc[topk, 'Botnet']))}, Normal {I.n(int(ct.loc[topk, 'Normal']))})."] if top else [],
                             ["Escala logarítmica: barras pequeñas pueden ser órdenes de magnitud menores."]), log=True)
    port = pd.to_numeric(flow["dst_port"], errors="coerce").dropna().astype(int)
    pc = flow.loc[port.index].assign(p=port).groupby(["p", "klass"]).size().unstack(fill_value=0)
    for c in ("Normal", "Botnet"):
        if c not in pc:
            pc[c] = 0
    top = pc.sum(1).sort_values(ascending=False).head(12).index.tolist()
    if top:
        grouped_bar("ports", "Puertos destino más frecuentes por clase", {c: pc[c].to_dict() for c in ("Normal", "Botnet")}, top,
                    note_n + " Solo flujos con puerto (TCP/UDP).",
                    I.interp([f"El puerto {top[0]} concentra {I.n(int(pc.loc[top[0]].sum()))} flujos; "
                              f"el {I.pct(pc.loc[top[0], 'Botnet'] / max(pc.loc[top[0]].sum(), 1), 0)} son Botnet."],
                             ["Un puerto muy asociado a una clase puede ser una pista específica de este escenario."]), log=True)
    # histogramas log de duración y bytes
    def log_hist(id_, title, series, klass, xlabel):
        s = pd.to_numeric(pd.Series(np.asarray(series)), errors="coerce")
        kl = np.asarray(klass)
        lv = np.log10(s.clip(lower=0) + 1)
        edges = np.linspace(0, max(float(lv.max()), 1), 13)
        labels = [f"{10 ** edges[i]:.3g}–{10 ** edges[i + 1]:.3g}" for i in range(12)]
        vals = {}
        for c in ("Normal", "Botnet"):
            h, _ = np.histogram(lv[kl == c].dropna(), bins=edges)
            vals[c] = [int(x) for x in h]
        med = {c: float(s[kl == c].median()) for c in ("Normal", "Botnet")}
        figs.append(I.fig(id_, "bars", title, {"labels": labels, "series": [{"name": c, "values": vals[c]} for c in ("Normal", "Botnet")],
                          "ylabel": unit_es.capitalize(), "xlabel": xlabel, "log": True}, note_n + " Eje X en escala log10 (1 + valor).",
                          I.interp([f"La mediana de {xlabel.lower()} es {I.n(med['Botnet'], 1)} en Botnet y {I.n(med['Normal'], 1)} en Normal."],
                                   ["Distribuciones con cola larga: la media no representa al caso típico."])))
    if meta["unit"] == "flow":
        log_hist("duration", "Duración del flujo por clase (escala log)", flow["duration"], flow["klass"], "Duración (s)")
        log_hist("bytes", "Bytes totales por clase (escala log)", flow["bytes_out"].fillna(0) + flow["bytes_in"].fillna(0),
                 flow["klass"], "Bytes totales")
    else:
        klass_w = np.where(y == 1, "Botnet", "Normal")
        log_hist("bytes", "Bytes salientes por ventana y clase (escala log)", X["bytes_out_sum"], klass_w, "Bytes salientes por ventana")
        log_hist("nconn", "Conexiones por ventana y clase (escala log)", X["n_conn"], klass_w, "Conexiones por ventana")
    # serie temporal por clase
    t = pd.to_numeric(flow["ts"], errors="coerce")
    t0, t1 = float(t.min()), float(t.max())
    nb_bins = 40
    edges = np.linspace(t0, t1 + 1e-6, nb_bins + 1)
    ser = []
    for c in ("Normal", "Botnet"):
        h, _ = np.histogram(t[flow["klass"] == c], bins=edges)
        ser.append({"name": c, "x": [round((edges[i] - t0) / 60, 2) for i in range(nb_bins)], "y": [int(x) for x in h]})
    peak = max(ser[1]["y"]) if ser[1]["y"] else 0
    first_b = next((s for s, v in zip(ser[1]["x"], ser[1]["y"]) if v > 0), None)
    figs.append(I.fig("timeseries", "lines", "Flujos por intervalo de tiempo y clase",
                      {"series": ser, "xlabel": "Minutos desde el primer flujo", "ylabel": "Flujos por intervalo"},
                      f"{nb_bins} intervalos de {I.n((t1 - t0) / nb_bins, 1)} s sobre {I.n((t1 - t0) / 60, 1)} min de captura; solo flujos etiquetados.",
                      I.interp([f"El tráfico Botnet empieza al minuto {I.n(first_b, 1)} y alcanza {I.n(peak)} flujos en un intervalo."
                                if first_b is not None else "No hay tráfico Botnet."],
                               ["La captura es corta: la separación temporal entre clases puede confundirse con la separación por grupos de tiempo."])))
    # faltantes y atípicos
    mrows, krows = [], []
    for c in cols:
        s = X[c]
        if c in ("proto", "state", "dir", "direction", "dst_port_class", "src_port_class"):
            mrows.append({"feature": FEATURE_LABELS_ES.get(c, c), "missing_pct": float(s.isna().mean() * 100), "outlier_pct": 0.0})
            continue
        v = pd.to_numeric(s, errors="coerce")
        q1, q3 = v.quantile(0.25), v.quantile(0.75)
        iqr = q3 - q1
        out = float(((v < q1 - 1.5 * iqr) | (v > q3 + 1.5 * iqr)).mean() * 100) if iqr > 0 else 0.0
        mrows.append({"feature": FEATURE_LABELS_ES.get(c, c), "missing_pct": float(v.isna().mean() * 100), "outlier_pct": out})
        a, b = v[y == 0].dropna(), v[y == 1].dropna()
        ks = float(sps.ks_2samp(a, b).statistic) if len(a) > 1 and len(b) > 1 else None
        krows.append({"feature": c, "label": FEATURE_LABELS_ES.get(c, c), "ks": ks, "median_normal": float(a.median()) if len(a) else None,
                      "median_botnet": float(b.median()) if len(b) else None})
    tables.append(I.table("missing_outliers", "Valores faltantes y atípicos por variable",
                          [("feature", "Variable"), ("missing_pct", "Faltantes (%)"), ("outlier_pct", "Atípicos IQR (%)")],
                          [{**r, "feature": r["feature"]} for r in mrows], note_n + " Atípico = fuera de [Q1 − 1,5·IQR, Q3 + 1,5·IQR].",
                          I.missing_outliers([{"feature": cols[i], **r} for i, r in enumerate(mrows)])))
    tables.append(I.table("class_comparison", "Comparación de distribuciones por clase (KS y medianas)",
                          [("label", "Variable"), ("ks", "KS"), ("median_normal", "Mediana Normal"), ("median_botnet", "Mediana Botnet")],
                          sorted(krows, key=lambda r: -(r["ks"] or 0)), note_n + " KS = distancia máxima entre las distribuciones acumuladas (0 = iguales, 1 = disjuntas).",
                          I.ks_table([{"feature": r["feature"], "ks": r["ks"] or 0} for r in krows])))
    # correlaciones
    num = [c for c in cols if c in X and X[c].dtype != object and not str(X[c].dtype).startswith("str") and c not in ("proto", "state", "dir", "direction", "dst_port_class", "src_port_class")]
    cm = X[num].apply(pd.to_numeric, errors="coerce").corr(method="spearman")
    sel = (cm.abs().sum().sort_values(ascending=False).head(14)).index.tolist()
    pairs = []
    for i, a in enumerate(num):
        for b in num[i + 1:]:
            r_ = cm.loc[a, b]
            if r_ == r_:
                pairs.append({"a": a, "b": b, "rho": float(r_)})
    pairs.sort(key=lambda p: -abs(p["rho"]))
    figs.append(I.fig("correlation", "heatmap", "Correlación de Spearman entre variables",
                      {"rows": [FEATURE_LABELS_ES.get(c, c) for c in sel], "cols": [FEATURE_LABELS_ES.get(c, c) for c in sel],
                       "values": [[None if cm.loc[a, b] != cm.loc[a, b] else round(float(cm.loc[a, b]), 3) for b in sel] for a in sel],
                       "vlabel": "ρ de Spearman", "scale": "div", "vmin": -1, "vmax": 1, "annotate": False},
                      f"Variables numéricas más correlacionadas (14 de {len(num)}); n = {len(X)} {unit_es}.", I.correlation(pairs, len(num))))
    out = {"n_rows": len(d), "n_labeled": nb + nn, "n_botnet": nb, "n_normal": nn, "n_excluded": n_excl, "unit": meta["unit"],
           "figures": figs, "tables": tables, "feature_spec": feature_spec(meta["unit"], meta["window_minutes"])}
    dump_json(cp, out)
    return out


def validation(ds: MlDataset, v: MlDatasetVersion, refresh: bool = False) -> dict:
    cp = _cache(ds, v.version, "validation")
    if cp.exists() and not refresh:
        return load_json(cp)
    meta = v.meta
    flows = flows_of(ds)
    ff = P.feature_frame(flows, meta, True)
    ff = ff[ff["y"].notna()].reset_index(drop=True)
    if ff["y"].nunique() < 2:
        raise DatasetError("Tras aplicar el mapeo de etiquetas solo queda una clase")
    cols = feature_columns(meta["unit"])
    g = G.validate_all(ff[cols], ff["y"].astype(int).values, ff[[c for c in ff.columns if c.startswith("_")]],
                       meta["unit"], meta["time_block_seconds"], meta["group_key"])
    chosen = g["keys"][meta["group_key"]]
    g["interpretation"] = I.validation(chosen)
    g["interpretation_global"] = I.validation_global(g)
    pt = chosen.get("partition")
    if pt:
        g["partition_table"] = I.table(
            "partition", "Clase × partición (filas y grupos)",
            [("partition", "Partición"), ("rows_botnet", "Filas Botnet"), ("rows_normal", "Filas Normal"),
             ("groups_botnet", "Grupos Botnet"), ("groups_normal", "Grupos Normal")],
            [{"partition": G.PART_ES[k], "rows_botnet": pt[k]["Botnet"]["rows"], "rows_normal": pt[k]["Normal"]["rows"],
              "groups_botnet": pt[k]["Botnet"]["groups"], "groups_normal": pt[k]["Normal"]["groups"]} for k in G.PART_NAMES],
            f"Partición 70/15/15 por grupos «{chosen['label']}», estratificada por clase, semilla 42. n = {g['n_rows']} filas.",
            I.partition({"rows": [{"partition": G.PART_ES[k], "rows_botnet": pt[k]["Botnet"]["rows"], "rows_normal": pt[k]["Normal"]["rows"],
                                   "groups_botnet": pt[k]["Botnet"]["groups"], "groups_normal": pt[k]["Normal"]["groups"]} for k in G.PART_NAMES]}))
    dump_json(cp, g)
    return g
