"""Autenticación, RBAC y auditoría como dependencias de FastAPI."""
from __future__ import annotations

import hmac
from dataclasses import dataclass, field
from typing import Any, Callable, Iterator

from fastapi import Depends, Header, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_strict_settings
from app.core.security import decode_token
from app.db.session import get_db, new_session
from app.models import User
from app.services.audit import service as audit_svc


@dataclass
class Principal:
    user: User | None
    is_api_key: bool = False
    permissions: set[str] = field(default_factory=set)

    @property
    def username(self) -> str:
        return self.user.username if self.user else "n8n"

    @property
    def user_id(self) -> int | None:
        return self.user.id if self.user else None

    @property
    def display_name(self) -> str:
        if self.user:
            return self.user.full_name or self.user.username
        return "n8n (API key)"

    def can(self, perm: str) -> bool:
        return self.is_api_key or perm in self.permissions


def _bearer(authorization: str | None) -> str | None:
    if authorization and authorization.lower().startswith("bearer "):
        return authorization[7:].strip()
    return None


def _resolve(request: Request, db: Session, authorization: str | None, x_api_key: str | None,
             enforce_pwd_change: bool) -> Principal:
    token = _bearer(authorization)
    if token:
        uid = decode_token(token, "access")
        if uid is None:
            raise HTTPException(401, "Sesión expirada o token inválido")
        user = db.execute(select(User).where(User.id == uid)).unique().scalar_one_or_none()
        if user is None or not user.is_active:
            raise HTTPException(401, "Usuario inexistente o inactivo")
        if enforce_pwd_change and user.must_change_password:
            raise HTTPException(403, "Debe cambiar su contraseña antes de continuar")
        audit_svc.close_stale_sessions(db, user.id)
        audit_svc.touch_activity(db, user.id)
        return Principal(user=user, permissions=set(user.permissions))
    if x_api_key:
        key = get_strict_settings().n8n_api_key
        if key and hmac.compare_digest(x_api_key.encode(), key.encode()):
            return Principal(user=None, is_api_key=True)
        raise HTTPException(401, "API key inválida")
    raise HTTPException(401, "No autenticado")


def get_principal(request: Request, db: Session = Depends(get_db),
                  authorization: str | None = Header(None), x_api_key: str | None = Header(None)) -> Principal:
    p = _resolve(request, db, authorization, x_api_key, enforce_pwd_change=True)
    request.state.principal = p
    return p


def get_principal_lenient(request: Request, db: Session = Depends(get_db),
                          authorization: str | None = Header(None),
                          x_api_key: str | None = Header(None)) -> Principal:
    """Como get_principal pero permite usuarios con must_change_password (cambio de clave, /me, logout)."""
    p = _resolve(request, db, authorization, x_api_key, enforce_pwd_change=False)
    request.state.principal = p
    return p


def get_current_user(p: Principal = Depends(get_principal)) -> User:
    if p.user is None:
        raise HTTPException(403, "Esta ruta requiere un usuario autenticado")
    return p.user


def get_current_user_lenient(p: Principal = Depends(get_principal_lenient)) -> User:
    if p.user is None:
        raise HTTPException(403, "Esta ruta requiere un usuario autenticado")
    return p.user


def authenticated(p: Principal = Depends(get_principal)) -> Principal:
    return p


def require(*perms: str, api_key: bool = False) -> Callable[..., Principal]:
    """Exige AL MENOS UNO de los permisos `modulo:accion`. `api_key=True` admite X-API-Key (n8n)."""

    def dep(p: Principal = Depends(get_principal)) -> Principal:
        if p.is_api_key:
            if api_key:
                return p
            raise HTTPException(403, "La API key no tiene acceso a este recurso")
        if not any(x in p.permissions for x in perms):
            raise HTTPException(403, "No tiene permiso para esta acción (" + " o ".join(perms) + ")")
        return p

    return dep


def require_admin_or_key() -> Callable[..., Principal]:
    def dep(p: Principal = Depends(get_principal)) -> Principal:
        if p.is_api_key or (p.user and p.user.role and p.user.role.name == "admin"):
            return p
        raise HTTPException(403, "Solo un administrador o la API key pueden ejecutar esta acción")

    return dep


class AuditCtx:
    """El handler llama `audit.set(entity_id, descripción, detalles)`; el evento se registra al terminar bien."""

    def __init__(self, request: Request, principal: Principal, event_type: str, module: str, entity: str | None):
        self.request, self.principal = request, principal
        self.event_type, self.module, self.entity = event_type, module, entity
        self.entity_id: Any = None
        self.description: str | None = None
        self.details: dict = {}
        self.skip = False

    def set(self, entity_id: Any = None, description: str | None = None, details: dict | None = None,
            event_type: str | None = None) -> None:
        if entity_id is not None:
            self.entity_id = entity_id
        if description:
            self.description = description
        if details:
            self.details.update(details)
        if event_type:
            self.event_type = event_type

    def flush(self) -> None:
        if self.skip:
            return
        db = new_session()
        try:
            default = f"{self.event_type} en {self.entity or self.module}"
            audit_svc.record_event(
                db, self.event_type, request=self.request, user_id=self.principal.user_id,
                username=self.principal.username, module=self.module, entity=self.entity,
                entity_id=self.entity_id, description=self.description or default, details=self.details)
        finally:
            db.close()


def audited(event_type: str, module: str, entity: str | None = None) -> Callable[..., Iterator[AuditCtx]]:
    """Dependencia de auditoría: registra el evento solo si el handler termina sin error."""

    def dep(request: Request, p: Principal = Depends(get_principal)) -> Iterator[AuditCtx]:
        ctx = AuditCtx(request, p, event_type, module, entity or module)
        yield ctx
        ctx.flush()

    return dep
