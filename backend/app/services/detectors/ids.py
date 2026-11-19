"""Agrupación de alertas IDS por firma y severidad."""
from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

from app.services.detectors.common import Candidate, clamp

# En Suricata, severity 1 = más grave.
IDS_SEVERITY = {1: "high", 2: "medium", 3: "low"}
IDS_BASE_SCORE = {1: 70.0, 2: 50.0, 3: 30.0}


@dataclass
class IdsGroup:
    signature: str
    signature_id: int | None
    category: str | None
    ids_severity: int | None
    count: int
    distinct_sources: int
    top_src: str | None
    top_dst: str | None
    top_port: int | None
    first_ts: datetime
    last_ts: datetime


def detect_ids_alerts(groups: Iterable[IdsGroup], window_start: datetime, window_end: datetime) -> list[Candidate]:
    out: list[Candidate] = []
    for g in groups:
        sev_n = g.ids_severity if g.ids_severity in IDS_SEVERITY else None
        base = IDS_BASE_SCORE.get(sev_n, 15.0)
        score = round(min(100.0, base + 20 * clamp(math.log10(g.count) / 3) + 5 * clamp(g.distinct_sources / 10)), 1)
        severity = IDS_SEVERITY.get(sev_n, "info")
        if score >= 90 and severity == "high":
            severity = "critical"
        key = g.signature_id if g.signature_id is not None else g.signature[:80]
        out.append(Candidate(
            finding_type="ids_alert", severity=severity, score=score,
            title=f"Alerta IDS: {g.signature} ({g.count} eventos)",
            src_ip=g.top_src if g.distinct_sources == 1 else g.top_src, dst_ip=g.top_dst, dst_port=g.top_port,
            proto=None, window_start=window_start, window_end=window_end, first_seen=g.first_ts,
            last_seen=g.last_ts,
            evidence={"signature": g.signature, "signature_id": g.signature_id, "category": g.category,
                      "ids_severity": g.ids_severity, "count": g.count, "distinct_sources": g.distinct_sources},
            dedup_key=f"ids_alert|{key}|{g.ids_severity}",
            context={"hostnames": []},
        ))
    return sorted(out, key=lambda c: -c.score)
