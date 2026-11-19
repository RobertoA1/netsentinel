"""Detector de beaconing (comunicación periódica hacia un destino)."""
from __future__ import annotations

import ipaddress
import math
from dataclasses import dataclass, field
from datetime import datetime
from typing import Iterable

from app.services.detectors.common import (Candidate, DetectionConfig, clamp, mean_stdev, severity_from_score)

PERIODIC_BY_DESIGN = {53, 123}  # DNS/NTP son periódicos por naturaleza: se penaliza el puntaje
MIN_MEAN_INTERVAL_S = 1.0


def _is_group_destination(ip: str) -> bool:
    """Multicast, broadcast y link-local: anuncios periódicos de la propia red (IGMP, mDNS, SSDP), no C&C."""
    try:
        a = ipaddress.ip_address(ip)
    except ValueError:
        return False
    return a.is_multicast or a.is_link_local or a.is_unspecified or ip.endswith(".255")


@dataclass
class BeaconGroup:
    src_ip: str
    dst_ip: str
    dst_port: int | None
    proto: str | None
    connections: int
    mean_interval_s: float
    stdev_interval_s: float
    mean_bytes: float
    stdev_bytes: float
    first_ts: datetime
    last_ts: datetime
    intervals_sample: list[float] = field(default_factory=list)


def group_from_series(src_ip: str, dst_ip: str, dst_port: int | None, proto: str | None,
                      timestamps: list[datetime], sizes: list[float]) -> BeaconGroup:
    """Construye las estadísticas a partir de series (útil para pruebas y fallback sin SQL)."""
    ts = sorted(timestamps)
    gaps = [(b - a).total_seconds() for a, b in zip(ts, ts[1:])]
    mi, si = mean_stdev(gaps)
    mb, sb = mean_stdev(sizes)
    return BeaconGroup(src_ip, dst_ip, dst_port, proto, len(ts), mi, si, mb, sb, ts[0], ts[-1],
                       [round(g, 2) for g in gaps[:12]])


def score_beaconing(g: BeaconGroup, cfg: DetectionConfig) -> tuple[float, dict] | None:
    if g.connections < cfg.beacon_min_connections or g.mean_interval_s < MIN_MEAN_INTERVAL_S:
        return None
    cv = g.stdev_interval_s / g.mean_interval_s
    if cv > cfg.beacon_max_cv:
        return None
    bytes_cv = (g.stdev_bytes / g.mean_bytes) if g.mean_bytes > 0 else 0.0
    duration_s = max((g.last_ts - g.first_ts).total_seconds(), 0.0)
    regularity = 1 - 0.6 * (cv / cfg.beacon_max_cv)
    size_reg = 1 - min(bytes_cv, 1.0)
    count_f = clamp(0.5 + 0.5 * math.log10(g.connections / cfg.beacon_min_connections))
    dur_f = clamp(duration_s / 3600 / 2)
    score = 100 * (0.5 * regularity + 0.2 * size_reg + 0.2 * count_f + 0.1 * dur_f)
    if g.dst_port in PERIODIC_BY_DESIGN:
        score *= 0.7
    evidence = {
        "connections": g.connections, "mean_interval_s": round(g.mean_interval_s, 3),
        "stdev_interval_s": round(g.stdev_interval_s, 3), "cv": round(cv, 4),
        "mean_bytes": round(g.mean_bytes, 1), "bytes_cv": round(bytes_cv, 4),
        "duration_h": round(duration_s / 3600, 3), "intervals_sample": list(g.intervals_sample),
    }
    return round(min(100.0, score), 1), evidence


def detect_beaconing(groups: Iterable[BeaconGroup], cfg: DetectionConfig, window_start: datetime,
                     window_end: datetime) -> list[Candidate]:
    out: list[Candidate] = []
    for g in groups:
        if _is_group_destination(g.dst_ip):
            continue
        res = score_beaconing(g, cfg)
        if res is None:
            continue
        score, ev = res
        if score < cfg.beacon_min_score:
            continue
        port = g.dst_port
        out.append(Candidate(
            finding_type="beaconing", severity=severity_from_score(score), score=score,
            title=f"Beaconing regular hacia {g.dst_ip}:{port if port is not None else '-'}"
                  f" ({g.connections} conexiones cada ~{ev['mean_interval_s']:.0f} s)",
            src_ip=g.src_ip, dst_ip=g.dst_ip, dst_port=port, proto=g.proto,
            window_start=window_start, window_end=window_end, first_seen=g.first_ts, last_seen=g.last_ts,
            evidence=ev, dedup_key=f"beaconing|{g.src_ip}|{g.dst_ip}|{port}|{g.proto}",
        ))
    return sorted(out, key=lambda c: -c.score)
