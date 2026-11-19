"""Agregaciones SQL (SQLAlchemy Core) que alimentan los detectores puros."""
from __future__ import annotations

import math
from datetime import datetime, timedelta

from sqlalchemy import Float, and_, cast, func, select
from sqlalchemy.orm import Session

from app.db.sqlfuncs import bucket_index
from app.models import FirewallLog as L
from app.services.detectors.beaconing import BeaconGroup
from app.services.detectors.common import DetectionConfig
from app.services.detectors.exfil import HostVolume, TalkerStats, baseline_stats
from app.services.detectors.ids import IdsGroup
from app.services.detectors.ports import PortGroup

BASELINE_DAYS = 14
MAX_BEACON_GROUPS = 400


def _epoch(col):
    return func.extract("epoch", col)


def _std(mean_sq: float, mean: float) -> float:
    return math.sqrt(max(0.0, float(mean_sq) - float(mean) ** 2))


def _flows(ws: datetime, we: datetime):
    """Tráfico saliente de firewall/flujos (excluye alertas IDS) dentro de la ventana."""
    return and_(L.ts >= ws, L.ts < we, L.direction == "outbound", L.log_type != "ids")


def latest_log_ts(db: Session) -> datetime | None:
    return db.execute(select(func.max(L.ts))).scalar()


def beacon_groups(db: Session, ws: datetime, we: datetime, cfg: DetectionConfig) -> list[BeaconGroup]:
    keys = [L.src_ip, L.dst_ip, L.dst_port, L.proto]
    gap = (_epoch(L.ts) - func.lag(_epoch(L.ts)).over(partition_by=keys, order_by=L.ts)).label("gap")
    x = select(*keys, L.ts.label("ts"), cast(L.bytes_out, Float).label("b"), gap).where(_flows(ws, we)).subquery()
    g = cast(x.c.gap, Float)
    stmt = (select(x.c.src_ip, x.c.dst_ip, x.c.dst_port, x.c.proto, func.count().label("n"),
                   func.avg(g), func.avg(g * g), func.avg(x.c.b), func.avg(x.c.b * x.c.b),
                   func.min(x.c.ts), func.max(x.c.ts))
            .group_by(x.c.src_ip, x.c.dst_ip, x.c.dst_port, x.c.proto)
            .having(func.count() >= cfg.beacon_min_connections)
            .order_by(func.count().desc()).limit(MAX_BEACON_GROUPS))
    out = []
    for r in db.execute(stmt).all():
        mg, mg2, mb, mb2 = (float(v or 0) for v in (r[5], r[6], r[7], r[8]))
        out.append(BeaconGroup(r[0], r[1], r[2], r[3], int(r[4]), mg, _std(mg2, mg), mb, _std(mb2, mb), r[9], r[10]))
    return out


def interval_sample(db: Session, g: BeaconGroup, ws: datetime, we: datetime, n: int = 12) -> list[float]:
    stmt = (select(L.ts).where(_flows(ws, we), L.src_ip == g.src_ip, L.dst_ip == g.dst_ip,
                               L.dst_port.is_not_distinct_from(g.dst_port), L.proto.is_not_distinct_from(g.proto))
            .order_by(L.ts).limit(n + 1))
    ts = [r[0] for r in db.execute(stmt).all()]
    return [round((b - a).total_seconds(), 2) for a, b in zip(ts, ts[1:])]


def port_groups(db: Session, ws: datetime, we: datetime, cfg: DetectionConfig) -> list[PortGroup]:
    stmt = (select(L.src_ip, L.dst_port, L.proto, func.count(), func.coalesce(func.sum(L.bytes_out + L.bytes_in), 0),
                   func.count(func.distinct(L.dst_ip)), func.min(L.dst_ip), func.min(L.ts), func.max(L.ts))
            .where(_flows(ws, we), L.dst_port.is_not(None), L.proto.in_(["tcp", "udp"]),
                   L.dst_port.not_in(sorted(cfg.common_ports)) if cfg.common_ports else True)
            .group_by(L.src_ip, L.dst_port, L.proto)
            .having(func.count() >= cfg.unusual_port_min_connections)
            .order_by(func.count().desc()).limit(3000))
    return [PortGroup(r[0], int(r[1]), r[2], int(r[3]), int(r[4]), int(r[5]), r[6], r[7], r[8])
            for r in db.execute(stmt).all()]


def baseline_ports(db: Session, ws: datetime) -> set[int]:
    stmt = select(L.dst_port).distinct().where(L.ts >= ws - timedelta(days=BASELINE_DAYS), L.ts < ws,
                                               L.direction == "outbound", L.dst_port.is_not(None))
    return {int(r[0]) for r in db.execute(stmt).all()}


def host_volumes(db: Session, ws: datetime, we: datetime, min_bytes: int) -> list[HostVolume]:
    bo = func.sum(L.bytes_out)
    stmt = (select(L.src_ip, bo, func.sum(L.bytes_in), func.count(), func.min(L.ts), func.max(L.ts))
            .where(_flows(ws, we)).group_by(L.src_ip).having(bo >= min_bytes).order_by(bo.desc()).limit(200))
    hosts = [HostVolume(r[0], int(r[1]), int(r[2] or 0), int(r[3]), r[4], r[5]) for r in db.execute(stmt).all()]
    for h in hosts:
        b = func.sum(L.bytes_out)
        tops = db.execute(select(L.dst_ip, b).where(_flows(ws, we), L.src_ip == h.src_ip)
                          .group_by(L.dst_ip).order_by(b.desc()).limit(5)).all()
        h.top_destinations = [{"ip": t[0], "bytes": int(t[1])} for t in tops]
    return hosts


def bucket_baselines(db: Session, ws: datetime, window_hours: int, metric: str,
                     hosts: list[str]) -> dict[str, tuple[float, float, int]]:
    """Histórico por host en cubos del tamaño de la ventana. metric: bytes_out|connections|destinations."""
    if not hosts:
        return {}
    val = {"bytes_out": func.sum(L.bytes_out), "connections": func.count(),
           "destinations": func.count(func.distinct(L.dst_ip))}[metric]
    bucket_s = window_hours * 3600
    b = bucket_index(int(ws.timestamp()), L.ts, bucket_s).label("b")
    stmt = (select(L.src_ip, b, val).where(L.ts >= ws - timedelta(days=BASELINE_DAYS), L.ts < ws,
                                           L.direction == "outbound", L.log_type != "ids", L.src_ip.in_(hosts))
            .group_by(L.src_ip, b))
    per: dict[str, list[float]] = {}
    for r in db.execute(stmt).all():
        per.setdefault(r[0], []).append(float(r[2]))
    total = max(1, int(BASELINE_DAYS * 24 / window_hours))
    return {h: baseline_stats(per.get(h, []), total) for h in hosts}


def talker_stats(db: Session, ws: datetime, we: datetime, limit: int = 2000) -> list[TalkerStats]:
    stmt = (select(L.src_ip, func.count(), func.count(func.distinct(L.dst_ip)), func.min(L.ts), func.max(L.ts))
            .where(_flows(ws, we)).group_by(L.src_ip).order_by(func.count().desc()).limit(limit))
    return [TalkerStats(r[0], int(r[1]), int(r[2]), r[3], r[4]) for r in db.execute(stmt).all()]


def ids_groups(db: Session, ws: datetime, we: datetime) -> list[IdsGroup]:
    stmt = (select(L.signature, L.signature_id, L.category, L.ids_severity, func.count(),
                   func.count(func.distinct(L.src_ip)), func.min(L.src_ip), func.min(L.dst_ip), func.min(L.dst_port),
                   func.min(L.ts), func.max(L.ts))
            .where(L.ts >= ws, L.ts < we, L.log_type == "ids", L.signature.is_not(None))
            .group_by(L.signature, L.signature_id, L.category, L.ids_severity)
            .order_by(func.count().desc()).limit(200))
    return [IdsGroup(r[0], r[1], r[2], r[3], int(r[4]), int(r[5]), r[6], r[7], r[8], r[9], r[10])
            for r in db.execute(stmt).all()]
