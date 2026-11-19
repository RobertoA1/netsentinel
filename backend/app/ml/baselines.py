"""Detectores deterministas de NetSentinel evaluados contra las etiquetas del dataset ML."""
from __future__ import annotations

from datetime import datetime, timezone

import numpy as np
import pandas as pd

from app.services.detectors.beaconing import detect_beaconing, group_from_series
from app.services.detectors.common import DetectionConfig
from app.core.ports import DEFAULT_COMMON_PORTS


def _dt(x: float) -> datetime:
    return datetime.fromtimestamp(float(x), tz=timezone.utc)


def default_cfg() -> DetectionConfig:
    from app.schemas.settings import DetectionSettings

    return DetectionConfig.from_dict(DetectionSettings().model_dump())


def flagged_flows(flows: pd.DataFrame, cfg: DetectionConfig | None = None) -> np.ndarray:
    """Máscara booleana (alineada con `flows`): True si el flujo pertenece a un grupo marcado por beaconing
    (origen, destino, puerto, protocolo con intervalos regulares) o usa un puerto destino inusual (fuera de la lista
    de puertos comunes configurada y con >= umbral de conexiones del mismo origen)."""
    cfg = cfg or default_cfg()
    d = flows.reset_index(drop=True)
    flag = np.zeros(len(d), dtype=bool)
    tmin, tmax = float(d["ts"].min()), float(d["ts"].max())
    ws, we = _dt(tmin), _dt(tmax + 1)
    # Beaconing por grupo
    key = ["src_ip", "dst_ip", "dst_port", "proto"]
    for k, g in d.groupby(key, dropna=False, sort=False):
        if len(g) < cfg.beacon_min_connections:
            continue
        stamps = [_dt(x) for x in g["ts"].astype(float)]
        grp = group_from_series(str(k[0]), str(k[1]), None if pd.isna(k[2]) else int(k[2]), k[3], stamps,
                                pd.to_numeric(g["bytes_out"], errors="coerce").fillna(0).tolist())
        if detect_beaconing([grp], cfg, ws, we):
            flag[g.index.values] = True
    # Puertos inusuales
    common = set(cfg.common_ports) or set(DEFAULT_COMMON_PORTS)
    dp = pd.to_numeric(d["dst_port"], errors="coerce")
    unusual = dp.notna() & ~dp.isin(list(common))
    cnt = d[unusual].groupby(["src_ip", "dst_port"]).size()
    keys = set(cnt[cnt >= cfg.unusual_port_min_connections].index)
    for i in np.where(unusual.values)[0]:
        if (d.at[i, "src_ip"], d.at[i, "dst_port"]) in keys:
            flag[i] = True
    return flag


def flagged_for_prepared(all_flows: pd.DataFrame, aux: pd.DataFrame, unit: str, window_minutes: float | None) -> np.ndarray:
    """Predicción binaria de los detectores alineada con las filas de `Prepared` (flujos o ventanas)."""
    mask = flagged_flows(all_flows)
    if unit == "flow":
        return mask[aux["_row"].values.astype(int)]
    w = max(1, int(round(float(window_minutes or 1) * 60)))
    d = all_flows.reset_index(drop=True)
    ws = (np.floor(d["ts"].astype(float) / w) * w)
    hit = set(zip(d.loc[mask, "src_ip"], ws[mask]))
    return np.array([(s, t) in hit for s, t in zip(aux["_src_ip"], aux["_t"].astype(float))])
