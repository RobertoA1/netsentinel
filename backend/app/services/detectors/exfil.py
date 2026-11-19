"""Detectores de exfiltración y de anomalía de top talkers."""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime
from typing import Iterable, Sequence

from app.services.detectors.common import (Candidate, DetectionConfig, clamp, mean_stdev, severity_from_score,
                                           zscore)

MIN_BASELINE_BUCKETS = 3


@dataclass
class HostVolume:
    src_ip: str
    bytes_out: int
    bytes_in: int
    connections: int
    first_ts: datetime
    last_ts: datetime
    top_destinations: list[dict] = field(default_factory=list)


def baseline_stats(observed: Sequence[float], total_buckets: int) -> tuple[float, float, int]:
    """Media/desv. del histórico rellenando con ceros los buckets sin datos. Devuelve (media, desv, nº con datos)."""
    n_obs = len(observed)
    vals = list(observed) + [0.0] * max(0, total_buckets - n_obs)
    m, s = mean_stdev(vals)
    return m, s, n_obs


def detect_exfiltration(hosts: Iterable[HostVolume], baselines: dict[str, tuple[float, float, int]],
                        cfg: DetectionConfig, window_start: datetime, window_end: datetime) -> list[Candidate]:
    out: list[Candidate] = []
    for h in hosts:
        if h.bytes_out < cfg.exfil_min_bytes:
            continue
        ratio = h.bytes_out / max(h.bytes_in, 1)
        mean, stdev, n_obs = baselines.get(h.src_ip, (0.0, 0.0, 0))
        has_baseline = n_obs >= MIN_BASELINE_BUCKETS
        z = zscore(h.bytes_out, mean, stdev) if has_baseline else None
        if has_baseline:
            if z < cfg.exfil_zscore:
                continue
        elif ratio < 3:  # sin histórico: exigir asimetría salida/entrada clara
            continue
        vol = clamp(math.log2(h.bytes_out / max(cfg.exfil_min_bytes, 1)) / 4)
        rat = clamp(ratio / 20)
        zs = clamp((z or 0) / (2 * cfg.exfil_zscore)) if z is not None else 0.0
        if z is not None:
            score = 30 + 70 * (0.35 * zs + 0.4 * vol + 0.25 * rat)
        else:
            score = 30 + 70 * (0.6 * vol + 0.4 * rat)
        score = round(min(100.0, score), 1)
        gb = h.bytes_out / 1e9
        out.append(Candidate(
            finding_type="exfiltration", severity=severity_from_score(score), score=score,
            title=f"Posible exfiltración: {h.src_ip} envió {h.bytes_out / 1e6:.1f} MB al exterior"
                  + (f" (z={z:.1f})" if z is not None else ""),
            src_ip=h.src_ip, dst_ip=(h.top_destinations[0]["ip"] if h.top_destinations else None), dst_port=None,
            proto=None, window_start=window_start, window_end=window_end, first_seen=h.first_ts,
            last_seen=h.last_ts,
            evidence={"bytes_out": h.bytes_out, "baseline_mean": round(mean, 1), "baseline_stdev": round(stdev, 1),
                      "zscore": None if z is None else round(z, 2), "ratio_out_in": round(min(ratio, 1e6), 2),
                      "top_destinations": h.top_destinations[:5], "baseline_available": has_baseline,
                      "gb_out": round(gb, 3)},
            dedup_key=f"exfiltration|{h.src_ip}",
        ))
    return sorted(out, key=lambda c: -c.score)


@dataclass
class TalkerStats:
    src_ip: str
    connections: int
    unique_destinations: int
    first_ts: datetime
    last_ts: datetime


def detect_talker_anomalies(
    talkers: Sequence[TalkerStats],
    conn_baselines: dict[str, tuple[float, float, int]],
    dest_baselines: dict[str, tuple[float, float, int]],
    cfg: DetectionConfig, window_start: datetime, window_end: datetime,
) -> list[Candidate]:
    """Anomalía de nº de conexiones o destinos únicos frente a la base propia (o frente a los pares)."""
    n = len(talkers)
    sums = {m: (sum(getattr(t, m) for t in talkers), sum(getattr(t, m) ** 2 for t in talkers))
            for m in ("connections", "unique_destinations")}

    def peers(t: TalkerStats, metric: str) -> tuple[float, float]:
        """Media/desv. de los DEMÁS hosts (leave-one-out: un valor extremo no se enmascara a sí mismo)."""
        v = getattr(t, metric)
        m = n - 1
        s1, s2 = sums[metric][0] - v, sums[metric][1] - v * v
        mean = s1 / m
        return mean, max(0.0, s2 / m - mean * mean) ** 0.5
    out: list[Candidate] = []
    for t in talkers:
        best: tuple[float, str, float, float, str] | None = None
        for metric, value, base, peer, floor in (
            ("connections", t.connections, conn_baselines.get(t.src_ip), "connections", cfg.talker_min_connections),
            ("unique_destinations", t.unique_destinations, dest_baselines.get(t.src_ip), "unique_destinations",
             cfg.talker_min_destinations),
        ):
            if value < floor:
                continue
            if base and base[2] >= MIN_BASELINE_BUCKETS:
                mean, stdev, src = base[0], base[1], "history"
            elif n >= 5:
                mean, stdev = peers(t, peer)
                src = "peers"
            else:
                continue
            z = zscore(value, mean, stdev)
            if z >= cfg.exfil_zscore and (best is None or z > best[0]):
                best = (z, metric, mean, float(value), src)
        if best is None:
            continue
        z, metric, mean, value, src = best
        score = round(min(100.0, 40 + 60 * clamp((z - cfg.exfil_zscore) / (3 * cfg.exfil_zscore))), 1)
        out.append(Candidate(
            finding_type="talker_anomaly", severity=severity_from_score(min(score, 80)), score=score,
            title=f"Actividad anómala de {t.src_ip}: {int(value)} {'conexiones' if metric == 'connections' else 'destinos únicos'}"
                  f" (z={z:.1f})",
            src_ip=t.src_ip, dst_ip=None, dst_port=None, proto=None, window_start=window_start,
            window_end=window_end, first_seen=t.first_ts, last_seen=t.last_ts,
            evidence={"metric": metric, "value": int(value), "baseline_mean": round(mean, 1),
                      "zscore": round(z, 2), "unique_destinations": t.unique_destinations, "baseline_source": src},
            dedup_key=f"talker_anomaly|{t.src_ip}|{metric}",
        ))
    return sorted(out, key=lambda c: -c.score)
