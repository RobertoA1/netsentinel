from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import Integer, and_, case, cast, func, literal_column, select
from sqlalchemy.orm import Session

from app.api.routers.findings import finding_out
from app.core.deps import require
from app.core.ports import service_name
from app.core.timerange import TimeRange, dashboard_range
from app.db.session import get_db
from app.db.sqlfuncs import epoch_bucket
from app.models import Alert, Asset, Finding, FirewallLog as L, IngestRun
from app.schemas.findings import FindingOut
from app.services import settings_service
from app.services.pipeline import load_matcher

router = APIRouter(prefix="/dashboard", tags=["dashboard"], dependencies=[Depends(require("dashboard:view"))])

OPEN_STATUSES = ("new", "in_review", "confirmed")


def _bucket_seconds(tr: TimeRange, bucket: str) -> int:
    if bucket == "5m":
        return 300
    if bucket == "1h":
        return 3600
    if bucket == "1d":
        return 86400
    span = tr.span.total_seconds()
    if span <= 6 * 3600:
        return 300
    if span <= 3 * 86400:
        return 3600
    return 86400


def _bucket_expr(col, secs: int):
    return epoch_bucket(col, secs)


def _log_range(tr: TimeRange):
    conds = [L.ts <= tr.end]
    if tr.start:
        conds.append(L.ts >= tr.start)
    return and_(*conds)


def _delta(cur: float, prev: float) -> float:
    if prev == 0:
        return 0.0 if cur == 0 else 100.0
    return round((cur - prev) / prev * 100, 1)


def _period_stats(db: Session, tr: TimeRange) -> dict:
    r = db.execute(select(
        func.count(), func.coalesce(func.sum(L.bytes_out), 0), func.coalesce(func.sum(L.bytes_in), 0),
        func.count(func.distinct(L.src_ip)), func.count(func.distinct(L.dst_ip)),
        func.count().filter(L.action == "block")).where(_log_range(tr))).one()
    fcond = [Finding.last_seen <= tr.end]
    if tr.start:
        fcond.append(Finding.last_seen >= tr.start)
    f = db.execute(select(
        func.count().filter(and_(Finding.is_noise.is_(False), Finding.status.in_(OPEN_STATUSES))),
        func.count().filter(and_(Finding.is_noise.is_(False), Finding.status.in_(OPEN_STATUSES),
                                 Finding.severity == "critical")),
        func.count().filter(Finding.is_noise.is_(True)), func.count()).where(and_(*fcond))).one()
    return {"total_logs": r[0], "total_bytes_out": int(r[1]), "total_bytes_in": int(r[2]), "unique_sources": r[3],
            "unique_destinations": r[4], "blocked_connections": r[5], "open_findings": f[0],
            "critical_findings": f[1], "noise_filtered": f[2], "findings_total": f[3]}


@router.get("/summary")
def summary(tr: TimeRange = Depends(dashboard_range), db: Session = Depends(get_db)):
    cur = _period_stats(db, tr)
    prev = _period_stats(db, tr.previous())
    ac = [Alert.channel == "in_app", Alert.acknowledged_at.is_(None)]
    unack = db.execute(select(func.count()).select_from(Alert).where(*ac)).scalar_one()
    last = db.execute(select(func.max(IngestRun.finished_at)).where(IngestRun.status == "success")).scalar()
    out = {k: cur[k] for k in ("total_logs", "total_bytes_out", "total_bytes_in", "unique_sources",
                               "unique_destinations", "blocked_connections", "open_findings", "critical_findings",
                               "noise_filtered")}
    out["noise_ratio"] = round(cur["noise_filtered"] / cur["findings_total"], 4) if cur["findings_total"] else 0.0
    out["alerts_unacknowledged"] = unack
    out["last_ingest_at"] = last
    out["deltas"] = {k: _delta(cur[k], prev[k]) for k in (
        "total_logs", "total_bytes_out", "total_bytes_in", "blocked_connections", "open_findings",
        "critical_findings")}
    return out


@router.get("/traffic-timeseries")
def traffic_timeseries(bucket: Literal["auto", "5m", "1h", "1d"] = "auto", tr: TimeRange = Depends(dashboard_range),
                       db: Session = Depends(get_db)):
    b = _bucket_expr(L.ts, _bucket_seconds(tr, bucket)).label("b")
    rows = db.execute(select(b, func.coalesce(func.sum(L.bytes_out), 0), func.coalesce(func.sum(L.bytes_in), 0),
                             func.count(), func.count().filter(L.action == "block"))
                      .where(_log_range(tr)).group_by(b).order_by(b)).all()
    return [{"ts": r[0], "bytes_out": int(r[1]), "bytes_in": int(r[2]), "connections": r[3], "blocked": r[4]}
            for r in rows]


@router.get("/top-talkers")
def top_talkers(metric: Literal["bytes", "connections", "destinations"] = "bytes", limit: int = Query(10, ge=1, le=100),
                direction: Literal["outbound", "inbound", "internal", "all"] = "outbound",
                tr: TimeRange = Depends(dashboard_range), db: Session = Depends(get_db)):
    bo = func.coalesce(func.sum(L.bytes_out), 0).label("bo")
    bi = func.coalesce(func.sum(L.bytes_in), 0).label("bi")
    n = func.count().label("n")
    d = func.count(func.distinct(L.dst_ip)).label("d")
    order = {"bytes": bo, "connections": n, "destinations": d}[metric]
    stmt = select(L.src_ip, bo, bi, n, d).where(_log_range(tr))
    if direction != "all":
        stmt = stmt.where(L.direction == direction)
    rows = db.execute(stmt.group_by(L.src_ip).order_by(order.desc(), L.src_ip).limit(limit)).all()
    ips = [r[0] for r in rows]
    names = {a.ip: a.hostname for a in db.execute(select(Asset).where(Asset.ip.in_(ips))).scalars()} if ips else {}
    fcnt = {}
    if ips:
        fq = select(Finding.src_ip, func.count()).where(Finding.src_ip.in_(ips), Finding.is_noise.is_(False),
                                                         Finding.last_seen <= tr.end)
        if tr.start:
            fq = fq.where(Finding.last_seen >= tr.start)
        fcnt = dict(db.execute(fq.group_by(Finding.src_ip)).all())
    return [{"ip": r[0], "hostname": names.get(r[0]) or None, "bytes_out": int(r[1]), "bytes_in": int(r[2]),
             "connections": r[3], "unique_destinations": r[4], "findings": fcnt.get(r[0], 0)} for r in rows]


@router.get("/top-destinations")
def top_destinations(limit: int = Query(10, ge=1, le=100), tr: TimeRange = Depends(dashboard_range),
                     db: Session = Depends(get_db)):
    b = func.coalesce(func.sum(L.bytes_out), 0).label("b")
    rows = db.execute(select(L.dst_ip, b, func.count(), func.count(func.distinct(L.src_ip)))
                      .where(_log_range(tr), L.direction == "outbound").group_by(L.dst_ip)
                      .order_by(b.desc(), L.dst_ip).limit(limit)).all()
    m = load_matcher(db)
    return [{"ip": r[0], "bytes": int(r[1]), "connections": r[2], "unique_sources": r[3],
             "in_denylist": m.ip_in("deny", r[0])} for r in rows]


@router.get("/top-ports")
def top_ports(limit: int = Query(10, ge=1, le=100), tr: TimeRange = Depends(dashboard_range),
              db: Session = Depends(get_db)):
    n = func.count().label("n")
    rows = db.execute(select(L.dst_port, L.proto, n, func.coalesce(func.sum(L.bytes_out + L.bytes_in), 0))
                      .where(_log_range(tr), L.dst_port.is_not(None)).group_by(L.dst_port, L.proto)
                      .order_by(n.desc(), L.dst_port).limit(limit)).all()
    common = set(settings_service.get_setting(db, "detection").common_ports)
    return [{"port": r[0], "proto": r[1], "service": service_name(r[0]), "connections": r[2], "bytes": int(r[3]),
             "unusual": r[0] not in common} for r in rows]


def _finding_range(tr: TimeRange):
    conds = [Finding.first_seen <= tr.end]
    if tr.start:
        conds.append(Finding.last_seen >= tr.start)
    return and_(*conds)


@router.get("/findings-by-severity")
def findings_by_severity(tr: TimeRange = Depends(dashboard_range), db: Session = Depends(get_db)):
    rows = dict(db.execute(select(Finding.severity, func.count()).where(_finding_range(tr), Finding.is_noise.is_(False))
                           .group_by(Finding.severity)).all())
    return [{"severity": s, "count": rows.get(s, 0)} for s in ("critical", "high", "medium", "low", "info")]


@router.get("/findings-by-type")
def findings_by_type(tr: TimeRange = Depends(dashboard_range), db: Session = Depends(get_db)):
    rows = db.execute(select(Finding.finding_type, func.count().filter(Finding.is_noise.is_(False)),
                             func.count().filter(Finding.is_noise.is_(True))).where(_finding_range(tr))
                      .group_by(Finding.finding_type)).all()
    got = {r[0]: (r[1], r[2]) for r in rows}
    return [{"finding_type": t, "count": got.get(t, (0, 0))[0], "noise": got.get(t, (0, 0))[1]}
            for t in ("beaconing", "unusual_port", "exfiltration", "ids_alert", "talker_anomaly")]


@router.get("/findings-timeseries")
def findings_timeseries(bucket: Literal["auto", "5m", "1h", "1d"] = "auto", tr: TimeRange = Depends(dashboard_range),
                        db: Session = Depends(get_db)):
    b = _bucket_expr(Finding.first_seen, _bucket_seconds(tr, bucket)).label("b")
    rows = db.execute(select(b, func.count().filter(Finding.is_noise.is_(False)),
                             func.count().filter(Finding.is_noise.is_(True)))
                      .where(_finding_range(tr)).group_by(b).order_by(b)).all()
    return [{"ts": r[0], "real": r[1], "noise": r[2]} for r in rows]


@router.get("/flows")
def flows(limit: int = Query(30, ge=1, le=200), tr: TimeRange = Depends(dashboard_range),
          db: Session = Depends(get_db)):
    b = func.coalesce(func.sum(L.bytes_out + L.bytes_in), 0).label("b")
    rows = db.execute(select(L.src_ip, L.dst_ip, L.dst_port, b, func.count()).where(_log_range(tr))
                      .group_by(L.src_ip, L.dst_ip, L.dst_port).order_by(b.desc()).limit(limit)).all()
    return [{"src_ip": r[0], "dst_ip": r[1], "dst_port": r[2], "bytes": int(r[3]), "connections": r[4]}
            for r in rows]


@router.get("/recent-findings", response_model=list[FindingOut])
def recent_findings(limit: int = Query(8, ge=1, le=50), tr: TimeRange = Depends(dashboard_range),
                    db: Session = Depends(get_db)):
    rows = db.execute(select(Finding).where(_finding_range(tr), Finding.is_noise.is_(False))
                      .order_by(Finding.last_seen.desc(), Finding.id.desc()).limit(limit)).unique().scalars().all()
    return rows
