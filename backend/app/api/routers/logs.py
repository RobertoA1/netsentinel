from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from app.core.deps import require
from app.core.pagination import PageParams, page_params, paginate
from app.core.timerange import TimeRange, list_range
from app.db.session import get_db
from app.models import FirewallLog as L, Source
from app.schemas.common import Page
from app.schemas.findings import FirewallLogOut

router = APIRouter(prefix="/logs", tags=["logs"], dependencies=[Depends(require("logs:view"))])

SORT = {"id": L.id, "ts": L.ts, "src_ip": L.src_ip, "dst_ip": L.dst_ip, "dst_port": L.dst_port,
        "bytes_out": L.bytes_out, "bytes_in": L.bytes_in, "proto": L.proto, "action": L.action}


def log_out(db: Session, rows: list[L]) -> list[FirewallLogOut]:
    ids = {r.source_id for r in rows if r.source_id}
    names = {s.id: s.name for s in db.execute(select(Source).where(Source.id.in_(ids))).scalars()} if ids else {}
    out = []
    for r in rows:
        o = FirewallLogOut.model_validate(r)
        o.source_name = names.get(r.source_id)
        out.append(o)
    return out


def apply_log_filters(stmt, tr: TimeRange, **f):
    if tr.start:
        stmt = stmt.where(L.ts >= tr.start)
    stmt = stmt.where(L.ts <= tr.end)
    for k in ("src_ip", "dst_ip", "dst_port", "proto", "action", "log_type", "direction", "source_id"):
        if f.get(k) is not None:
            stmt = stmt.where(getattr(L, k) == f[k])
    q = f.get("q")
    if q:
        like = f"%{q.lower()}%"
        stmt = stmt.where(or_(L.src_ip.like(f"{q}%"), L.dst_ip.like(f"{q}%"),
                              func.lower(func.coalesce(L.signature, "")).like(like),
                              func.lower(func.coalesce(L.category, "")).like(like),
                              func.lower(func.coalesce(L.label, "")).like(like)))
    return stmt


@router.get("", response_model=Page[FirewallLogOut])
def list_logs(q: str | None = None, src_ip: str | None = None, dst_ip: str | None = None,
              dst_port: int | None = None, proto: str | None = None, action: str | None = None,
              log_type: str | None = None, direction: str | None = None, source_id: int | None = None,
              tr: TimeRange = Depends(list_range), pp: PageParams = Depends(page_params),
              db: Session = Depends(get_db)):
    stmt = apply_log_filters(select(L), tr, q=q, src_ip=src_ip, dst_ip=dst_ip, dst_port=dst_port,
                             proto=proto.lower() if proto else None, action=action, log_type=log_type,
                             direction=direction, source_id=source_id)
    page = paginate(db, stmt, pp, SORT, "-ts")
    page["items"] = log_out(db, page["items"])
    return page


@router.get("/{log_id}", response_model=FirewallLogOut)
def get_log(log_id: int, db: Session = Depends(get_db)):
    r = db.get(L, log_id)
    if r is None:
        raise HTTPException(404, "Registro no encontrado")
    return log_out(db, [r])[0]
