"""Tipos y utilidades comunes de los detectores (módulo puro, sin base de datos)."""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Iterable

SEVERITIES = ["info", "low", "medium", "high", "critical"]


def sev_rank(s: str) -> int:
    return SEVERITIES.index(s)


def bump(severity: str, steps: int) -> str:
    return SEVERITIES[max(0, min(len(SEVERITIES) - 1, sev_rank(severity) + steps))]


def severity_from_score(score: float) -> str:
    if score >= 85:
        return "critical"
    if score >= 70:
        return "high"
    if score >= 50:
        return "medium"
    if score >= 30:
        return "low"
    return "info"


def mean_stdev(values: Iterable[float]) -> tuple[float, float]:
    vals = list(values)
    if not vals:
        return 0.0, 0.0
    m = sum(vals) / len(vals)
    var = sum((v - m) ** 2 for v in vals) / len(vals)
    return m, math.sqrt(var)


def zscore(value: float, mean: float, stdev: float) -> float:
    """z-score con piso en la desviación para evitar divisiones por ~0."""
    eff = max(stdev, abs(mean) * 0.1, 1.0)
    return (value - mean) / eff


def clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


@dataclass
class DetectionConfig:
    beacon_min_connections: int = 10
    beacon_max_cv: float = 0.25
    beacon_min_score: float = 60.0
    exfil_zscore: float = 3.0
    exfil_min_bytes: int = 52428800
    common_ports: set[int] = field(default_factory=set)
    unusual_port_min_connections: int = 3
    internal_cidrs: list[str] = field(default_factory=list)
    detection_window_hours: int = 24
    talker_min_connections: int = 200
    talker_min_destinations: int = 25

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "DetectionConfig":
        return cls(
            beacon_min_connections=int(d["beacon_min_connections"]), beacon_max_cv=float(d["beacon_max_cv"]),
            beacon_min_score=float(d["beacon_min_score"]), exfil_zscore=float(d["exfil_zscore"]),
            exfil_min_bytes=int(d["exfil_min_bytes"]), common_ports=set(d["common_ports"]),
            unusual_port_min_connections=int(d["unusual_port_min_connections"]),
            internal_cidrs=list(d["internal_cidrs"]), detection_window_hours=int(d["detection_window_hours"]),
        )


@dataclass
class Candidate:
    finding_type: str
    severity: str
    score: float
    title: str
    src_ip: str | None
    dst_ip: str | None
    dst_port: int | None
    proto: str | None
    window_start: datetime
    window_end: datetime
    first_seen: datetime
    last_seen: datetime
    evidence: dict[str, Any]
    dedup_key: str
    context: dict[str, Any] = field(default_factory=dict)
