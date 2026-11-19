"""Detector de puertos destino inusuales."""
from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

from app.core.ports import service_name
from app.services.detectors.common import Candidate, DetectionConfig, clamp, severity_from_score

MAX_FINDINGS = 25


@dataclass
class PortGroup:
    src_ip: str
    dst_port: int
    proto: str | None
    connections: int
    bytes: int
    distinct_dsts: int
    sample_dst: str | None
    first_ts: datetime
    last_ts: datetime


def detect_unusual_ports(groups: Iterable[PortGroup], cfg: DetectionConfig, expected_ports: dict[str, set[int]],
                         baseline_ports: set[int], window_start: datetime, window_end: datetime) -> list[Candidate]:
    agg: dict[tuple[int, str | None], dict] = {}
    for g in groups:
        if g.dst_port in cfg.common_ports or g.dst_port in baseline_ports:
            continue
        if g.dst_port in expected_ports.get(g.src_ip, ()):
            continue
        a = agg.setdefault((g.dst_port, g.proto), {
            "conns": 0, "bytes": 0, "srcs": {}, "dsts": set(), "first": g.first_ts, "last": g.last_ts})
        a["conns"] += g.connections
        a["bytes"] += g.bytes
        a["srcs"][g.src_ip] = a["srcs"].get(g.src_ip, 0) + g.connections
        if g.sample_dst:
            a["dsts"].add(g.sample_dst)
        a["distinct_dsts"] = a.get("distinct_dsts", 0) + g.distinct_dsts
        a["first"], a["last"] = min(a["first"], g.first_ts), max(a["last"], g.last_ts)
    out: list[Candidate] = []
    for (port, proto), a in agg.items():
        if a["conns"] < cfg.unusual_port_min_connections:
            continue
        nsrc = len(a["srcs"])
        score = 35 + 25 * clamp(math.log10(a["conns"] / cfg.unusual_port_min_connections + 1) / 2) \
            + 20 * clamp(nsrc / 5) + 20 * clamp(math.log10(a["bytes"] / 1e6 + 1) / 2)
        score = round(min(100.0, score), 1)
        top_src = max(a["srcs"], key=a["srcs"].get)
        dst_ip = next(iter(a["dsts"])) if a["distinct_dsts"] == 1 and a["dsts"] else None
        svc = service_name(port)
        out.append(Candidate(
            finding_type="unusual_port", severity=severity_from_score(min(score, 75)), score=score,
            title=f"Tráfico saliente hacia puerto inusual {port}/{proto or '?'}"
                  f" ({a['conns']} conexiones, {nsrc} origen(es))",
            src_ip=top_src if nsrc == 1 else top_src, dst_ip=dst_ip, dst_port=port, proto=proto,
            window_start=window_start, window_end=window_end, first_seen=a["first"], last_seen=a["last"],
            evidence={"port": port, "service": svc, "connections": a["conns"], "bytes": a["bytes"],
                      "distinct_sources": nsrc, "in_baseline": False, "first_seen": a["first"].isoformat()},
            dedup_key=f"unusual_port|{proto}|{port}",
        ))
    out.sort(key=lambda c: -c.score)
    return out[:MAX_FINDINGS]
