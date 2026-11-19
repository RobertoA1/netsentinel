"""Definición VERSIONADA de variables (flujo y ventana host-tiempo) y su cálculo.

Reglas anti-fuga: NO se usan IP, identificadores, marca de tiempo absoluta ni la etiqueta como variables.
`FORBIDDEN_FEATURES` se verifica en `assert_no_leakage`.
"""
from __future__ import annotations

import math
from typing import Iterable

import numpy as np
import pandas as pd

FEATURE_SPEC_VERSION = "1.0.0"

RAW_COLUMNS = ["ts", "src_ip", "dst_ip", "src_port", "dst_port", "proto", "state", "dir", "direction",
               "bytes_out", "bytes_in", "packets", "duration", "label_raw"]

FORBIDDEN_FEATURES = {"src_ip", "dst_ip", "ts", "ts_epoch", "id", "label", "label_raw", "y", "class", "group",
                      "window_start", "src_mac", "dst_mac"}

# ---- flujo ------------------------------------------------------------------------------------------------
FLOW_NUMERIC = ["duration", "bytes_out", "bytes_in", "bytes_total", "packets", "bytes_per_packet", "ratio_out",
                "bytes_per_s", "pkts_per_s", "dst_port"]
FLOW_CATEGORICAL = ["proto", "state", "dir", "direction", "dst_port_class", "src_port_class"]
FLOW_LOG_COLS = ["duration", "bytes_out", "bytes_in", "bytes_total", "packets", "bytes_per_packet", "bytes_per_s",
                 "pkts_per_s"]

# ---- ventana host-tiempo ----------------------------------------------------------------------------------
WINDOW_NUMERIC = ["n_conn", "n_dst", "n_dport", "entropy_dport", "entropy_dst", "bytes_out_sum", "bytes_in_sum",
                  "pkts_sum", "bytes_out_mean", "pkts_mean", "ratio_out", "prop_tcp", "prop_udp", "prop_icmp",
                  "prop_other", "prop_state_est", "prop_state_attempt", "prop_state_reset", "mean_gap_s",
                  "std_gap_s", "cv_gap", "beacon_best_cv", "beacon_top_n"]
WINDOW_CATEGORICAL: list[str] = []
WINDOW_LOG_COLS = ["n_conn", "n_dst", "n_dport", "bytes_out_sum", "bytes_in_sum", "pkts_sum", "bytes_out_mean",
                   "pkts_mean", "mean_gap_s", "std_gap_s"]

FEATURE_LABELS_ES = {
    "duration": "Duración (s)", "bytes_out": "Bytes enviados", "bytes_in": "Bytes recibidos",
    "bytes_total": "Bytes totales", "packets": "Paquetes", "bytes_per_packet": "Bytes por paquete",
    "ratio_out": "Proporción de bytes salientes", "bytes_per_s": "Bytes por segundo",
    "pkts_per_s": "Paquetes por segundo", "dst_port": "Puerto destino", "proto": "Protocolo",
    "state": "Estado de la conexión", "dir": "Sentido del flujo", "direction": "Dirección de red",
    "dst_port_class": "Clase de puerto destino", "src_port_class": "Clase de puerto origen",
    "n_conn": "Nº de conexiones", "n_dst": "Destinos únicos", "n_dport": "Puertos destino únicos",
    "entropy_dport": "Entropía de puertos", "entropy_dst": "Entropía de destinos",
    "bytes_out_sum": "Bytes salientes totales", "bytes_in_sum": "Bytes entrantes totales",
    "pkts_sum": "Paquetes totales", "bytes_out_mean": "Bytes salientes medios", "pkts_mean": "Paquetes medios",
    "prop_tcp": "Proporción TCP", "prop_udp": "Proporción UDP", "prop_icmp": "Proporción ICMP",
    "prop_other": "Proporción otros protocolos", "prop_state_est": "Proporción de conexiones establecidas",
    "prop_state_attempt": "Proporción de intentos sin respuesta", "prop_state_reset": "Proporción de reinicios (RST)",
    "mean_gap_s": "Intervalo medio (s)", "std_gap_s": "Desviación del intervalo (s)",
    "cv_gap": "Coef. de variación del intervalo", "beacon_best_cv": "Mejor CV por destino (beaconing)",
    "beacon_top_n": "Conexiones del destino más regular",
}

FEATURE_GROUPS = {
    "flow": {"Volumen": ["bytes_out", "bytes_in", "bytes_total", "packets", "bytes_per_packet", "ratio_out"],
             "Ritmo": ["duration", "bytes_per_s", "pkts_per_s"],
             "Puertos": ["dst_port", "dst_port_class", "src_port_class"],
             "Protocolo y estado": ["proto", "state", "dir", "direction"]},
    "window": {"Volumen": ["bytes_out_sum", "bytes_in_sum", "pkts_sum", "bytes_out_mean", "pkts_mean", "ratio_out"],
               "Diversidad": ["n_conn", "n_dst", "n_dport", "entropy_dport", "entropy_dst"],
               "Protocolo y estado": ["prop_tcp", "prop_udp", "prop_icmp", "prop_other", "prop_state_est",
                                      "prop_state_attempt", "prop_state_reset"],
               "Regularidad": ["mean_gap_s", "std_gap_s", "cv_gap", "beacon_best_cv", "beacon_top_n"]},
}


def feature_spec(unit: str, window_minutes: float | None = None) -> dict:
    """Definición de variables que se guarda junto a cada modelo (versionada)."""
    if unit == "window":
        num, cat, log = WINDOW_NUMERIC, WINDOW_CATEGORICAL, WINDOW_LOG_COLS
    else:
        num, cat, log = FLOW_NUMERIC, FLOW_CATEGORICAL, FLOW_LOG_COLS
    return {"version": FEATURE_SPEC_VERSION, "unit": unit, "window_minutes": window_minutes if unit == "window" else None,
            "numeric": list(num), "categorical": list(cat), "log1p": list(log),
            "groups": FEATURE_GROUPS["window" if unit == "window" else "flow"],
            "excluded_by_design": sorted(FORBIDDEN_FEATURES),
            "notes": "Sin IP, identificadores, marca de tiempo absoluta ni etiqueta (fuga de información)."}


def feature_columns(unit: str) -> list[str]:
    return (WINDOW_NUMERIC + WINDOW_CATEGORICAL) if unit == "window" else (FLOW_NUMERIC + FLOW_CATEGORICAL)


def assert_no_leakage(columns: Iterable[str]) -> None:
    bad = sorted(set(columns) & FORBIDDEN_FEATURES)
    if bad:
        raise ValueError("Variables prohibidas por fuga de información: " + ", ".join(bad))


def _port_class(s: pd.Series) -> pd.Series:
    v = pd.to_numeric(s, errors="coerce")
    out = pd.Series("none", index=s.index, dtype="object")
    out[(v >= 0) & (v < 1024)] = "well_known"
    out[(v >= 1024) & (v < 49152)] = "registered"
    out[v >= 49152] = "dynamic"
    return out


def flow_features(df: pd.DataFrame) -> pd.DataFrame:
    """Variables por flujo. Índice conservado. No incluye IP ni tiempo."""
    out = pd.DataFrame(index=df.index)
    dur = pd.to_numeric(df["duration"], errors="coerce")
    bo = pd.to_numeric(df["bytes_out"], errors="coerce").fillna(0).astype(float)
    bi = pd.to_numeric(df["bytes_in"], errors="coerce").fillna(0).astype(float)
    pk = pd.to_numeric(df["packets"], errors="coerce")
    tot = bo + bi
    out["duration"] = dur
    out["bytes_out"], out["bytes_in"], out["bytes_total"] = bo, bi, tot
    out["packets"] = pk
    out["bytes_per_packet"] = tot / pk.where(pk > 0)
    out["ratio_out"] = bo / tot.where(tot > 0)
    d = dur.clip(lower=1e-3)
    out["bytes_per_s"] = tot / d
    out["pkts_per_s"] = pk / d
    out["dst_port"] = pd.to_numeric(df["dst_port"], errors="coerce")
    out["proto"] = df["proto"].fillna("unk").astype(str).str.lower()
    out["state"] = df["state"].fillna("unk").astype(str).replace("", "unk")
    out["dir"] = df["dir"].fillna("unk").astype(str).str.strip().replace("", "unk")
    out["direction"] = df["direction"].fillna("unk").astype(str)
    out["dst_port_class"] = _port_class(df["dst_port"])
    out["src_port_class"] = _port_class(df["src_port"])
    return out[FLOW_NUMERIC + FLOW_CATEGORICAL]


def _entropy(values: pd.Series) -> float:
    c = values.value_counts(normalize=True)
    return float(-(c * np.log2(c)).sum()) if len(c) else 0.0


def _state_family(state: pd.Series, proto: pd.Series) -> pd.DataFrame:
    st = state.fillna("").astype(str)
    tcp = proto.eq("tcp")
    reset = st.str.contains("R", regex=False) & tcp
    est = st.str.contains("PA", regex=False) | st.str.contains("FA", regex=False)
    attempt = tcp & ~est & (st.str.endswith("_") | st.str.match(r"^S_R?A?$"))
    return pd.DataFrame({"est": est & tcp, "attempt": attempt, "reset": reset})


def window_features(df: pd.DataFrame, window_minutes: int, only_labeled: bool = False) -> pd.DataFrame:
    """Agregados por (src_ip, ventana de N minutos). Devuelve columnas de ventana + src_ip, win_start (epoch s)
    y, si existe `y_flow` (1 botnet, 0 normal, NaN excluido), la etiqueta de la ventana `y`
    (1 si hay algún flujo botnet; 0 si solo hay normales; NaN si no hay flujos etiquetados)."""
    w = max(1, int(round(float(window_minutes) * 60)))
    d = df.copy()
    d["_t"] = pd.to_numeric(d["ts"], errors="coerce").astype(float)
    d["win_start"] = (np.floor(d["_t"] / w) * w).astype(float)
    if only_labeled and "y_flow" in d:  # entrenamiento: las ventanas sin flujos etiquetados no tienen verdad conocida
        keep = d.groupby(["src_ip", "win_start"])["y_flow"].transform(lambda s: s.notna().any())
        d = d[keep.values]
    d["proto"] = d["proto"].fillna("").astype(str).str.lower()
    fam = _state_family(d["state"], d["proto"])
    d["_est"], d["_att"], d["_rst"] = fam["est"].values, fam["attempt"].values, fam["reset"].values
    d["_tcp"], d["_udp"] = d["proto"].eq("tcp"), d["proto"].eq("udp")
    d["_icmp"] = d["proto"].str.startswith("icmp")
    d["_bo"] = pd.to_numeric(d["bytes_out"], errors="coerce").fillna(0)
    d["_bi"] = pd.to_numeric(d["bytes_in"], errors="coerce").fillna(0)
    d["_pk"] = pd.to_numeric(d["packets"], errors="coerce").fillna(0)
    rows = []
    for (src, ws), g in d.groupby(["src_ip", "win_start"], sort=False):
        n = len(g)
        tg = np.sort(g["_t"].values)
        gaps = np.diff(tg)
        mg = float(gaps.mean()) if len(gaps) else np.nan
        sg = float(gaps.std()) if len(gaps) else np.nan
        cvg = (sg / mg) if (len(gaps) and mg and mg > 0) else np.nan
        best_cv, top_n = np.nan, 0
        for _, gg in g.groupby(["dst_ip", "dst_port", "proto"], sort=False, dropna=False):
            if len(gg) >= 5:
                gp = np.diff(np.sort(gg["_t"].values))
                if len(gp) and gp.mean() >= 1.0:
                    cv = float(gp.std() / gp.mean())
                    if np.isnan(best_cv) or cv < best_cv:
                        best_cv, top_n = cv, len(gg)
        bo, bi = float(g["_bo"].sum()), float(g["_bi"].sum())
        tcp, udp, icmp = float(g["_tcp"].mean()), float(g["_udp"].mean()), float(g["_icmp"].mean())
        rec = {"src_ip": src, "win_start": ws, "n_conn": n, "n_dst": g["dst_ip"].nunique(),
               "n_dport": g["dst_port"].nunique(), "entropy_dport": _entropy(g["dst_port"].astype(str)),
               "entropy_dst": _entropy(g["dst_ip"]), "bytes_out_sum": bo, "bytes_in_sum": bi,
               "pkts_sum": float(g["_pk"].sum()), "bytes_out_mean": bo / n, "pkts_mean": float(g["_pk"].mean()),
               "ratio_out": bo / (bo + bi) if (bo + bi) > 0 else np.nan, "prop_tcp": tcp, "prop_udp": udp,
               "prop_icmp": icmp, "prop_other": max(0.0, 1 - tcp - udp - icmp),
               "prop_state_est": float(g["_est"].mean()), "prop_state_attempt": float(g["_att"].mean()),
               "prop_state_reset": float(g["_rst"].mean()), "mean_gap_s": mg, "std_gap_s": sg, "cv_gap": cvg,
               "beacon_best_cv": best_cv, "beacon_top_n": top_n}
        if "y_flow" in g:
            yf = g["y_flow"].dropna()
            rec["y"] = np.nan if yf.empty else float(yf.max())
            rec["n_labeled"] = int(len(yf))
        rows.append(rec)
    out = pd.DataFrame(rows)
    return out


def build_feature_frame(flows: pd.DataFrame, unit: str, window_minutes: float | None,
                        only_labeled: bool = True) -> pd.DataFrame:
    """Devuelve un DataFrame con las variables del modelo + columnas auxiliares (`_`): src_ip, dst_ip, _t, y...
    Las columnas auxiliares NO son variables (se usan para grupos, partición y gráficos)."""
    if unit == "window":
        wf = window_features(flows, window_minutes or 5, only_labeled=only_labeled)
        aux = pd.DataFrame({"_src_ip": wf["src_ip"].values, "_t": wf["win_start"].values,
                            "_dst_ip": "", "_row": -1, "y": wf.get("y", pd.Series(np.nan, index=wf.index)).values})
        X = wf[WINDOW_NUMERIC].reset_index(drop=True)
        return pd.concat([X, aux.reset_index(drop=True)], axis=1)
    X = flow_features(flows).reset_index(drop=True)
    tt = pd.to_numeric(flows["ts"], errors="coerce")
    aux = pd.DataFrame({"_src_ip": flows["src_ip"].values, "_dst_ip": flows["dst_ip"].values,
                        "_t": tt.values, "_row": np.arange(len(flows)),
                        "y": flows["y_flow"].values if "y_flow" in flows else np.nan})
    return pd.concat([X, aux.reset_index(drop=True)], axis=1)


def numeric_summary(X: pd.DataFrame, cols: list[str]) -> dict:
    return {c: {"min": float(np.nanmin(X[c])) if X[c].notna().any() else None,
                "max": float(np.nanmax(X[c])) if X[c].notna().any() else None} for c in cols}


def safe_float(v) -> float | None:
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return None if (math.isnan(f) or math.isinf(f)) else f
