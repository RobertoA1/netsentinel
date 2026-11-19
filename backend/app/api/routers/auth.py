from __future__ import annotations

from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_strict_settings
from app.core.deps import get_current_user_lenient
from app.core.security import create_token, decode_token, hash_password, verify_password
from app.db.base import utcnow
from app.db.session import get_db
from app.models import User, UserProfile
from app.schemas.users import (LoginIn, LoginOut, MeUpdate, PasswordChange, RefreshIn, RefreshOut, UserMe)
from app.services.audit import service as audit_svc

router = APIRouter(prefix="/auth", tags=["auth"])


def _me(user: User) -> UserMe:
    return UserMe.model_validate({
        "id": user.id, "username": user.username, "email": user.email, "full_name": user.full_name,
        "is_active": user.is_active, "must_change_password": user.must_change_password,
        "last_login_at": user.last_login_at, "role": user.role, "profile": user.profile,
        "permissions": user.permissions})


@router.post("/login", response_model=LoginOut)
def login(body: LoginIn, request: Request, db: Session = Depends(get_db)):
    s = get_strict_settings()
    user = db.execute(select(User).where(User.username == body.username.strip())).unique().scalar_one_or_none()
    now = utcnow()
    if user is not None and user.locked_until and user.locked_until > now:
        mins = int((user.locked_until - now).total_seconds() // 60) + 1
        audit_svc.record_event(db, "login_failed", request=request, user_id=user.id, username=user.username,
                               module="auth", description="Intento de acceso con la cuenta bloqueada",
                               details={"reason": "locked"})
        raise HTTPException(403, f"Cuenta bloqueada por intentos fallidos. Intente de nuevo en {mins} minuto(s)")
    if user is None or not user.is_active or not verify_password(body.password, user.password_hash):
        reason = "unknown_user" if user is None else ("inactive" if not user.is_active else "bad_password")
        msg = "Usuario o contraseña incorrectos"
        if user is not None and user.is_active and reason == "bad_password":
            user.failed_attempts += 1
            if user.failed_attempts >= s.max_failed_logins:
                user.locked_until = now + timedelta(minutes=s.lockout_minutes)
                user.failed_attempts = 0
                msg = f"Cuenta bloqueada por {s.lockout_minutes} minutos tras {s.max_failed_logins} intentos fallidos"
            db.commit()
        audit_svc.record_event(db, "login_failed", request=request, user_id=user.id if user else None,
                               username=user.username if user else body.username[:64], module="auth",
                               description="Inicio de sesión fallido", details={"reason": reason})
        raise HTTPException(403 if "bloqueada" in msg else 401, msg)
    user.failed_attempts = 0
    user.locked_until = None
    user.last_login_at = now
    db.commit()
    audit_svc.record_event(db, "login", request=request, user_id=user.id, username=user.username, module="auth",
                           description="Inicio de sesión")
    return LoginOut(access_token=create_token(user.id, "access"), refresh_token=create_token(user.id, "refresh"),
                    user=_me(user))


@router.post("/refresh", response_model=RefreshOut)
def refresh(body: RefreshIn, db: Session = Depends(get_db)):
    uid = decode_token(body.refresh_token, "refresh")
    user = db.get(User, uid) if uid else None
    if user is None or not user.is_active:
        raise HTTPException(401, "Refresh token inválido o expirado")
    return RefreshOut(access_token=create_token(user.id, "access"), refresh_token=create_token(user.id, "refresh"))


@router.post("/logout", status_code=204)
def logout(request: Request, user: User = Depends(get_current_user_lenient), db: Session = Depends(get_db)):
    audit_svc.close_open_sessions(db, user.id, "logout", request, user.username)
    audit_svc.record_event(db, "logout", request=request, user_id=user.id, username=user.username, module="auth",
                           description="Cierre de sesión")
    return Response(status_code=204)


@router.get("/me", response_model=UserMe)
def me(user: User = Depends(get_current_user_lenient)):
    return _me(user)


@router.put("/me/profile", response_model=UserMe)
def update_profile(body: MeUpdate, request: Request, user: User = Depends(get_current_user_lenient),
                   db: Session = Depends(get_db)):
    data = body.model_dump(exclude_unset=True)
    if "email" in data and data["email"] != user.email:
        if db.execute(select(User).where(User.email == data["email"], User.id != user.id)).first():
            raise HTTPException(409, "Ya existe un usuario con ese correo")
        user.email = data["email"]
    if data.get("full_name") is not None:
        user.full_name = data["full_name"]
    if user.profile is None:
        user.profile = UserProfile()
    for k in ("job_title", "department", "phone", "avatar_color", "theme", "language", "timezone"):
        if data.get(k) is not None:
            setattr(user.profile, k, data[k])
    db.commit()
    audit_svc.record_event(db, "update", request=request, user_id=user.id, username=user.username, module="auth",
                           entity="profile", entity_id=user.id, description="Actualización del perfil propio",
                           details={"fields": sorted(data.keys())})
    return _me(user)


@router.post("/me/password", status_code=204)
def change_password(body: PasswordChange, request: Request, user: User = Depends(get_current_user_lenient),
                    db: Session = Depends(get_db)):
    if not verify_password(body.current_password, user.password_hash):
        raise HTTPException(400, "La contraseña actual es incorrecta")
    if body.new_password == body.current_password:
        raise HTTPException(400, "La nueva contraseña debe ser distinta de la actual")
    user.password_hash = hash_password(body.new_password)
    user.must_change_password = False
    db.commit()
    audit_svc.record_event(db, "update", request=request, user_id=user.id, username=user.username, module="auth",
                           entity="password", entity_id=user.id, description="Cambio de contraseña propio")
    return Response(status_code=204)
