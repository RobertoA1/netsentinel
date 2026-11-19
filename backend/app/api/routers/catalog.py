from __future__ import annotations

import ipaddress

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.deps import AuditCtx, audited, require
from app.core.pagination import PageParams, page_params, paginate
from app.db.session import get_db
from app.models import Asset, FirewallLog, ListEntry, Source
from app.schemas.common import Page
from app.schemas.findings import (AssetIn, AssetOut, ListEntryIn, ListEntryOut, SourceIn, SourceOut)

router = APIRouter(tags=["catalogs"])


# ---- fuentes -------------------------------------------------------------

def _src_out(db: Session, s: Source) -> SourceOut:
    n = db.execute(select(func.count()).select_from(FirewallLog).where(FirewallLog.source_id == s.id)).scalar_one()
    o = SourceOut.model_validate(s)
    o.log_count = n
    return o


@router.get("/sources", response_model=list[SourceOut])
def list_sources(db: Session = Depends(get_db), _=Depends(require("sources:view", "ingestion:view"))):
    return [_src_out(db, s) for s in db.execute(select(Source).order_by(Source.id)).scalars()]


@router.post("/sources", response_model=SourceOut, status_code=201)
def create_source(body: SourceIn, db: Session = Depends(get_db), _=Depends(require("sources:create")),
                  audit: AuditCtx = Depends(audited("create", "sources", "source"))):
    if db.execute(select(Source).where(Source.name == body.name)).first():
        raise HTTPException(409, "Ya existe una fuente con ese nombre")
    s = Source(**body.model_dump())
    db.add(s)
    db.commit()
    audit.set(s.id, f"Fuente creada: {s.name}")
    return _src_out(db, s)


def _src(db: Session, sid: int) -> Source:
    s = db.get(Source, sid)
    if s is None:
        raise HTTPException(404, "Fuente no encontrada")
    return s


@router.get("/sources/{sid}", response_model=SourceOut)
def get_source(sid: int, db: Session = Depends(get_db), _=Depends(require("sources:view", "ingestion:view"))):
    return _src_out(db, _src(db, sid))


@router.put("/sources/{sid}", response_model=SourceOut)
def update_source(sid: int, body: SourceIn, db: Session = Depends(get_db), _=Depends(require("sources:update")),
                  audit: AuditCtx = Depends(audited("update", "sources", "source"))):
    s = _src(db, sid)
    if db.execute(select(Source).where(Source.name == body.name, Source.id != sid)).first():
        raise HTTPException(409, "Ya existe una fuente con ese nombre")
    for k, v in body.model_dump().items():
        setattr(s, k, v)
    db.commit()
    audit.set(s.id, f"Fuente actualizada: {s.name}")
    return _src_out(db, s)


@router.delete("/sources/{sid}", status_code=204)
def delete_source(sid: int, db: Session = Depends(get_db), _=Depends(require("sources:delete")),
                  audit: AuditCtx = Depends(audited("delete", "sources", "source"))):
    s = _src(db, sid)
    name = s.name
    db.delete(s)  # los logs conservan su registro (source_id queda en NULL)
    db.commit()
    audit.set(sid, f"Fuente eliminada: {name}")
    return Response(status_code=204)


# ---- activos -------------------------------------------------------------

def _check_asset(b: AssetIn) -> None:
    try:
        ipaddress.ip_address(b.ip.strip())
    except ValueError:
        raise HTTPException(422, "IP inválida")
    if any(not 0 < p < 65536 for p in b.expected_ports):
        raise HTTPException(422, "Puertos esperados fuera de rango")


@router.get("/assets", response_model=Page[AssetOut])
def list_assets(q: str | None = None, pp: PageParams = Depends(page_params), db: Session = Depends(get_db),
                _=Depends(require("assets:view"))):
    stmt = select(Asset)
    if q:
        like = f"%{q.lower()}%"
        stmt = stmt.where(or_(Asset.ip.like(f"{q}%"), func.lower(Asset.hostname).like(like),
                              func.lower(Asset.owner).like(like)))
    return paginate(db, stmt, pp, {"id": Asset.id, "ip": Asset.ip, "hostname": Asset.hostname,
                                   "criticality": Asset.criticality}, "ip")


@router.post("/assets", response_model=AssetOut, status_code=201)
def create_asset(body: AssetIn, db: Session = Depends(get_db), _=Depends(require("assets:create")),
                 audit: AuditCtx = Depends(audited("create", "assets", "asset"))):
    _check_asset(body)
    ip = str(ipaddress.ip_address(body.ip.strip()))
    if db.execute(select(Asset).where(Asset.ip == ip)).first():
        raise HTTPException(409, "Ya existe un activo con esa IP")
    a = Asset(**{**body.model_dump(), "ip": ip})
    db.add(a)
    db.commit()
    audit.set(a.id, f"Activo creado: {a.ip}")
    return a


def _asset(db: Session, aid: int) -> Asset:
    a = db.get(Asset, aid)
    if a is None:
        raise HTTPException(404, "Activo no encontrado")
    return a


@router.get("/assets/{aid}", response_model=AssetOut)
def get_asset(aid: int, db: Session = Depends(get_db), _=Depends(require("assets:view"))):
    return _asset(db, aid)


@router.put("/assets/{aid}", response_model=AssetOut)
def update_asset(aid: int, body: AssetIn, db: Session = Depends(get_db), _=Depends(require("assets:update")),
                 audit: AuditCtx = Depends(audited("update", "assets", "asset"))):
    _check_asset(body)
    a = _asset(db, aid)
    ip = str(ipaddress.ip_address(body.ip.strip()))
    if db.execute(select(Asset).where(Asset.ip == ip, Asset.id != aid)).first():
        raise HTTPException(409, "Ya existe un activo con esa IP")
    for k, v in {**body.model_dump(), "ip": ip}.items():
        setattr(a, k, v)
    db.commit()
    audit.set(a.id, f"Activo actualizado: {a.ip}")
    return a


@router.delete("/assets/{aid}", status_code=204)
def delete_asset(aid: int, db: Session = Depends(get_db), _=Depends(require("assets:delete")),
                 audit: AuditCtx = Depends(audited("delete", "assets", "asset"))):
    a = _asset(db, aid)
    ip = a.ip
    db.delete(a)
    db.commit()
    audit.set(aid, f"Activo eliminado: {ip}")
    return Response(status_code=204)


# ---- listas allow/deny ----------------------------------------------------

def _validate_entry(b: ListEntryIn) -> str:
    v = b.value.strip()
    try:
        if b.kind == "ip":
            return str(ipaddress.ip_address(v))
        if b.kind == "cidr":
            return str(ipaddress.ip_network(v, strict=False))
        if b.kind == "port":
            if not 0 < int(v) < 65536:
                raise ValueError
            return str(int(v))
    except ValueError:
        raise HTTPException(422, f"Valor inválido para el tipo '{b.kind}'")
    return v.lower()


@router.get("/lists", response_model=Page[ListEntryOut])
def list_entries(list_type: str | None = None, kind: str | None = None, q: str | None = None,
                 pp: PageParams = Depends(page_params), db: Session = Depends(get_db),
                 _=Depends(require("lists:view"))):
    stmt = select(ListEntry)
    if list_type:
        stmt = stmt.where(ListEntry.list_type == list_type)
    if kind:
        stmt = stmt.where(ListEntry.kind == kind)
    if q:
        stmt = stmt.where(or_(ListEntry.value.like(f"%{q.lower()}%"), func.lower(ListEntry.note).like(f"%{q.lower()}%")))
    return paginate(db, stmt, pp, {"id": ListEntry.id, "created_at": ListEntry.created_at,
                                   "value": ListEntry.value, "kind": ListEntry.kind}, "-created_at")


@router.post("/lists", response_model=ListEntryOut, status_code=201)
def create_entry(body: ListEntryIn, db: Session = Depends(get_db), _=Depends(require("lists:create")),
                 audit: AuditCtx = Depends(audited("create", "lists", "list_entry"))):
    value = _validate_entry(body)
    if db.execute(select(ListEntry).where(ListEntry.list_type == body.list_type, ListEntry.kind == body.kind,
                                          ListEntry.value == value)).first():
        raise HTTPException(409, "La entrada ya existe en la lista")
    e = ListEntry(list_type=body.list_type, kind=body.kind, value=value, note=body.note)
    db.add(e)
    db.commit()
    audit.set(e.id, f"Entrada {e.list_type} agregada: {e.kind} {e.value}")
    return e


@router.delete("/lists/{eid}", status_code=204)
def delete_entry(eid: int, db: Session = Depends(get_db), _=Depends(require("lists:delete")),
                 audit: AuditCtx = Depends(audited("delete", "lists", "list_entry"))):
    e = db.get(ListEntry, eid)
    if e is None:
        raise HTTPException(404, "Entrada no encontrada")
    desc = f"Entrada {e.list_type} eliminada: {e.kind} {e.value}"
    db.delete(e)
    db.commit()
    audit.set(eid, desc)
    return Response(status_code=204)
