"""Bitácora de auditoría y sesiones de módulo."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import Request
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.base import utcnow
from app.models import AuditEvent, ModuleSession

EVENT_TYPES = {"login", "logout", "login_failed", "module_enter", "module_exit", "create", "update",
               "delete", "export", "execute"}


def client_ip(request: Request | None) -> str | None:
    if request is None:
        return None
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        return fwd.split(",")[0].strip()[:64]
    return request.client.host if request.client else None


def record_event(db: Session, event_type: str, *, request: Request | None = None, user_id: int | None = None,
                 username: str | None = None, module: str | None = None, entity: str | None = None,
                 entity_id: Any = None, description: str = "", details: dict | None = None,
                 commit: bool = True) -> AuditEvent:
    assert event_type in EVENT_TYPES, event_type
    ev = AuditEvent(
        ts=utcnow(), user_id=user_id, username=username, event_type=event_type, module=module, entity=entity,
        entity_id=None if entity_id is None else str(entity_id), description=description[:1000],
        ip=client_ip(request), user_agent=(request.headers.get("user-agent", "")[:512] if request else None),
        details=details or {},
    )
    db.add(ev)
    if commit:
        db.commit()
    return ev


# ---- sesiones de módulo -------------------------------------------------

def _close(s: ModuleSession, when: datetime, reason: str) -> None:
    s.exited_at = when
    s.exit_reason = reason
    s.duration_seconds = max(0, int((when - s.entered_at).total_seconds()))


def close_stale_sessions(db: Session, user_id: int | None = None) -> int:
    """Cierra como `timeout` las sesiones sin actividad en N minutos (cierre perezoso)."""
    limit = utcnow() - timedelta(minutes=get_settings().module_session_timeout_minutes)
    stmt = select(ModuleSession).where(ModuleSession.exited_at.is_(None), ModuleSession.last_activity_at < limit)
    if user_id is not None:
        stmt = stmt.where(ModuleSession.user_id == user_id)
    rows = db.execute(stmt).scalars().all()
    for s in rows:
        _close(s, s.last_activity_at, "timeout")
        db.add(AuditEvent(ts=s.last_activity_at, user_id=s.user_id, username=s.username, event_type="module_exit",
                          module=s.module, description=f"Salida del módulo {s.module} (timeout por inactividad)",
                          ip=s.ip, user_agent=s.user_agent,
                          details={"session_id": s.id, "reason": "timeout", "duration_seconds": s.duration_seconds}))
    if rows:
        db.commit()
    return len(rows)


def touch_activity(db: Session, user_id: int) -> None:
    """Marca actividad del usuario en su sesión de módulo abierta (máx. 1 UPDATE por minuto)."""
    now = utcnow()
    db.execute(
        update(ModuleSession)
        .where(ModuleSession.user_id == user_id, ModuleSession.exited_at.is_(None),
               ModuleSession.last_activity_at < now - timedelta(seconds=30))
        .values(last_activity_at=now)
    )
    db.commit()


def close_open_sessions(db: Session, user_id: int, reason: str, request: Request | None = None,
                        username: str | None = None) -> int:
    rows = db.execute(
        select(ModuleSession).where(ModuleSession.user_id == user_id, ModuleSession.exited_at.is_(None))
    ).scalars().all()
    now = utcnow()
    for s in rows:
        _close(s, now, reason)
        record_event(db, "module_exit", request=request, user_id=user_id, username=username or s.username,
                     module=s.module, description=f"Salida del módulo {s.module} ({reason})",
                     details={"session_id": s.id, "reason": reason, "duration_seconds": s.duration_seconds},
                     commit=False)
    db.commit()
    return len(rows)


def enter_module(db: Session, user_id: int, username: str, module: str, request: Request | None) -> ModuleSession:
    close_stale_sessions(db, user_id)
    close_open_sessions(db, user_id, "navigation", request, username)
    s = ModuleSession(user_id=user_id, username=username, module=module, entered_at=utcnow(),
                      last_activity_at=utcnow(), ip=client_ip(request),
                      user_agent=(request.headers.get("user-agent", "")[:512] if request else None))
    db.add(s)
    db.flush()
    record_event(db, "module_enter", request=request, user_id=user_id, username=username, module=module,
                 description=f"Entrada al módulo {module}", details={"session_id": s.id}, commit=False)
    db.commit()
    return s


def exit_module(db: Session, user_id: int, username: str, session_id: int, reason: str,
                request: Request | None) -> bool:
    s = db.get(ModuleSession, session_id)
    if s is None or s.user_id != user_id:
        return False
    if s.exited_at is None:
        _close(s, utcnow(), reason)
        record_event(db, "module_exit", request=request, user_id=user_id, username=username, module=s.module,
                     description=f"Salida del módulo {s.module} ({reason})",
                     details={"session_id": s.id, "reason": reason, "duration_seconds": s.duration_seconds},
                     commit=False)
        db.commit()
    return True
