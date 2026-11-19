from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.deps import authenticated, Principal, require
from app.core.pagination import PageParams, page_params, paginate
from app.core.permissions import MODULE_CODES
from app.core.timerange import TimeRange, list_range
from app.db.session import get_db
from app.models import AuditEvent, ModuleSession
from app.schemas.audit import (AuditEventOut, AuditSummary, ByEventType, ByModule, ByUser, ModuleEnterIn,
                               ModuleEnterOut, ModuleExitIn, ModuleSessionOut)
from app.schemas.common import Page
from app.services.audit import service as svc

router = APIRouter(prefix="/audit", tags=["audit"])
EXIT_REASONS = {"navigation", "logout", "timeout", "close"}


@router.post("/module-enter", response_model=ModuleEnterOut)
def module_enter(body: ModuleEnterIn, request: Request, p: Principal = Depends(authenticated),
                 db: Session = Depends(get_db)):
    if p.user is None:
        raise HTTPException(403, "Requiere un usuario autenticado")
    if body.module not in MODULE_CODES and body.module not in ("settings", "profile", "home"):
        raise HTTPException(422, "Módulo desconocido")
    s = svc.enter_module(db, p.user.id, p.user.username, body.module, request)
    return ModuleEnterOut(session_id=s.id)


@router.post("/module-exit", status_code=204)
def module_exit(body: ModuleExitIn, request: Request, p: Principal = Depends(authenticated),
                db: Session = Depends(get_db)):
    if p.user is None:
        raise HTTPException(403, "Requiere un usuario autenticado")
    reason = body.reason if body.reason in EXIT_REASONS else "navigation"
    if not svc.exit_module(db, p.user.id, p.user.username, body.session_id, reason, request):
        raise HTTPException(404, "Sesión de módulo no encontrada")
    return Response(status_code=204)


def _time_filter(stmt, col, tr: TimeRange):
    if tr.start:
        stmt = stmt.where(col >= tr.start)
    return stmt.where(col <= tr.end)


@router.get("/events", response_model=Page[AuditEventOut])
def events(user_id: int | None = None, event_type: str | None = None, module: str | None = None,
           q: str | None = None, tr: TimeRange = Depends(list_range), pp: PageParams = Depends(page_params),
           db: Session = Depends(get_db), _=Depends(require("audit:view"))):
    stmt = _time_filter(select(AuditEvent), AuditEvent.ts, tr)
    if user_id is not None:
        stmt = stmt.where(AuditEvent.user_id == user_id)
    if event_type:
        stmt = stmt.where(AuditEvent.event_type == event_type)
    if module:
        stmt = stmt.where(AuditEvent.module == module)
    if q:
        like = f"%{q.lower()}%"
        stmt = stmt.where(or_(func.lower(AuditEvent.description).like(like),
                              func.lower(func.coalesce(AuditEvent.username, "")).like(like),
                              func.lower(func.coalesce(AuditEvent.entity, "")).like(like)))
    return paginate(db, stmt, pp, {"id": AuditEvent.id, "ts": AuditEvent.ts, "username": AuditEvent.username,
                                   "event_type": AuditEvent.event_type, "module": AuditEvent.module}, "-ts")


@router.get("/module-sessions", response_model=Page[ModuleSessionOut])
def module_sessions(user_id: int | None = None, module: str | None = None, tr: TimeRange = Depends(list_range),
                    pp: PageParams = Depends(page_params), db: Session = Depends(get_db),
                    _=Depends(require("audit:view"))):
    svc.close_stale_sessions(db)
    stmt = _time_filter(select(ModuleSession), ModuleSession.entered_at, tr)
    if user_id is not None:
        stmt = stmt.where(ModuleSession.user_id == user_id)
    if module:
        stmt = stmt.where(ModuleSession.module == module)
    return paginate(db, stmt, pp, {"id": ModuleSession.id, "entered_at": ModuleSession.entered_at,
                                   "username": ModuleSession.username, "module": ModuleSession.module,
                                   "duration_seconds": ModuleSession.duration_seconds}, "-entered_at")


@router.get("/summary", response_model=AuditSummary)
def summary(tr: TimeRange = Depends(list_range), db: Session = Depends(get_db), _=Depends(require("audit:view"))):
    svc.close_stale_sessions(db)
    ms = _time_filter(select(ModuleSession.module, func.count(), func.coalesce(func.sum(ModuleSession.duration_seconds), 0))
                      .group_by(ModuleSession.module), ModuleSession.entered_at, tr)
    by_module = [ByModule(module=m, visits=v, total_seconds=int(t)) for m, v, t in db.execute(
        ms.order_by(func.count().desc())).all()]
    us = _time_filter(select(ModuleSession.username, func.count(), func.coalesce(func.sum(ModuleSession.duration_seconds), 0),
                             func.max(ModuleSession.entered_at)).group_by(ModuleSession.username),
                      ModuleSession.entered_at, tr)
    by_user = [ByUser(username=u, visits=v, total_seconds=int(t), last_seen=ls) for u, v, t, ls in db.execute(
        us.order_by(func.count().desc())).all()]
    es = _time_filter(select(AuditEvent.event_type, func.count()).group_by(AuditEvent.event_type), AuditEvent.ts, tr)
    by_type = [ByEventType(event_type=t, count=c) for t, c in db.execute(es.order_by(func.count().desc())).all()]
    return AuditSummary(by_module=by_module, by_user=by_user, by_event_type=by_type)
