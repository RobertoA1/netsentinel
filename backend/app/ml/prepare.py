"""Construye los datos de modelado (variables, etiquetas, grupos, partición) a partir de una versión de dataset."""
from __future__ import annotations

import hashlib
import json

import numpy as np
import pandas as pd

from app.ml import data as D
from app.ml.features import assert_no_leakage, build_feature_frame, feature_columns, feature_spec
from app.ml.groups import group_ids, partition_groups
from app.ml.nested import Prepared

DEFAULT_PROVENANCE = ("CTU-13, escenario 11 (CTU-Malware-Capture-Botnet-52, botnet Rbot). Stratosphere Laboratory, "
                      "CTU University (Praga). https://www.stratosphereips.org/datasets-ctu13")
DEFAULT_LICENSE = ("Uso libre citando: García, S., Grill, M., Stiborek, J., Zunino, A. An empirical comparison of "
                   "botnet detection methods. Computers & Security 45 (2014) 100-123.")
UNITS = ("flow", "window")


def default_meta(name: str, df: pd.DataFrame, **kw) -> dict:
    span_min = float((df["ts"].max() - df["ts"].min()) / 60.0) if len(df) else 0.0
    win = 5 if span_min >= 120 else 0.25
    meta = {"name": name, "description": "", "provenance": DEFAULT_PROVENANCE, "license": DEFAULT_LICENSE,
            "label_map": D.default_label_map(df["label_raw"].dropna().unique()), "unit": "flow",
            "window_minutes": win, "group_key": "time_block", "time_block_seconds": 10.0, "notes": "",
            "span_minutes": round(span_min, 2)}
    meta.update({k: v for k, v in kw.items() if v is not None})
    return meta


def validate_meta(meta: dict) -> dict:
    m = dict(meta)
    if m.get("unit") not in UNITS:
        raise ValueError("La unidad de análisis debe ser 'flow' o 'window'")
    w = float(m.get("window_minutes") or 1)
    if not 0.25 <= w <= 240:
        raise ValueError("El tamaño de ventana debe estar entre 0,25 y 240 minutos")
    m["window_minutes"] = w
    tb = float(m.get("time_block_seconds") or 10.0)
    if not 1 <= tb <= 86400:
        raise ValueError("El bloque temporal debe estar entre 1 segundo y 24 horas")
    m["time_block_seconds"] = tb
    if m.get("group_key") not in ("src_ip", "src_dst", "time_block"):
        raise ValueError("Clave de agrupación inválida (src_ip, src_dst o time_block)")
    if m["unit"] == "window" and m["group_key"] == "src_dst":
        raise ValueError("El par origen-destino no aplica a ventanas host-tiempo")
    lm = m.get("label_map") or {}
    if not isinstance(lm, dict) or any(v not in ("Botnet", "Normal", D.EXCLUDED) for v in lm.values()):
        raise ValueError("El mapeo de etiquetas solo admite Botnet, Normal o excluded")
    if "Botnet" not in lm.values() or "Normal" not in lm.values():
        raise ValueError("El mapeo debe asignar al menos una etiqueta a Botnet y otra a Normal")
    for k in ("name", "description", "provenance", "license", "notes"):
        m[k] = str(m.get(k, ""))[:4000]
    if not m["name"].strip():
        raise ValueError("El nombre es obligatorio")
    return m


def meta_hash(meta: dict, snapshot_sha: str) -> str:
    keys = ("label_map", "unit", "window_minutes", "group_key", "time_block_seconds")
    blob = json.dumps({k: meta.get(k) for k in keys}, sort_keys=True) + snapshot_sha
    return hashlib.sha256(blob.encode()).hexdigest()


def feature_frame(flows: pd.DataFrame, meta: dict, only_labeled: bool = True) -> pd.DataFrame:
    d = D.labelled_frame(flows, meta["label_map"])
    return build_feature_frame(d, meta["unit"], meta["window_minutes"], only_labeled=only_labeled)


def prepare(flows: pd.DataFrame, meta: dict, seed: int = 42) -> Prepared:
    ff = feature_frame(flows, meta, True)
    ff = ff[ff["y"].notna()].reset_index(drop=True)
    cols = feature_columns(meta["unit"])
    assert_no_leakage(cols)
    aux = ff[[c for c in ff.columns if c.startswith("_")]].copy()
    y = ff["y"].astype(int).values
    groups = group_ids(aux, meta["group_key"], meta["unit"], meta["time_block_seconds"])
    part = partition_groups(y, groups, seed)
    return Prepared(X=ff[cols].copy(), y=y, aux=aux, groups=groups, part=part, unit=meta["unit"],
                    window_minutes=meta["window_minutes"] if meta["unit"] == "window" else None)


def partition_table(prep: Prepared) -> dict:
    rows = []
    names = ["Desarrollo", "Validación", "Prueba"]
    for p, nm in enumerate(names):
        m = prep.part == p
        rows.append({"partition": nm,
                     "rows_botnet": int((prep.y[m] == 1).sum()), "rows_normal": int((prep.y[m] == 0).sum()),
                     "groups_botnet": int(len(set(prep.groups[m & (prep.y == 1)]))),
                     "groups_normal": int(len(set(prep.groups[m & (prep.y == 0)]))), "rows": int(m.sum())})
    return {"rows": rows, "n": int(len(prep.y))}
