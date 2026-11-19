from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.deps import AuditCtx, audited, require
from app.core.pagination import PageParams, page_params, paginate
from app.core.permissions import permissions_catalog, valid_permission
from app.core.security import hash_password
from app.db.session import get_db
from app.models import Role, User, UserProfile
from app.schemas.common import Page
from app.schemas.users import ResetPassword, RoleIn, RoleOut, UserCreate, UserOut, UserUpdate

router = APIRouter(tags=["users"])


@router.get("/users", response_model=Page[UserOut])
def list_users(q: str | None = None, role_id: int | None = None, is_active: bool | None = None,
               pp: PageParams = Depends(page_params), db: Session = Depends(get_db),
               _=Depends(require("users:view"))):
    stmt = select(User)
    if q:
        like = f"%{q.lower()}%"
        stmt = stmt.where(or_(func.lower(User.username).like(like), func.lower(User.email).like(like),
                              func.lower(User.full_name).like(like)))
    if role_id is not None:
        stmt = stmt.where(User.role_id == role_id)
    if is_active is not None:
        stmt = stmt.where(User.is_active == is_active)
    return paginate(db, stmt, pp, {"id": User.id, "username": User.username, "full_name": User.full_name,
                                   "created_at": User.created_at, "last_login_at": User.last_login_at}, "username")


@router.post("/users", response_model=UserOut, status_code=201)
def create_user(body: UserCreate, db: Session = Depends(get_db), _=Depends(require("users:create")),
                audit: AuditCtx = Depends(audited("create", "users", "user"))):
    if db.get(Role, body.role_id) is None:
        raise HTTPException(422, "El rol indicado no existe")
    if db.execute(select(User).where(or_(User.username == body.username, User.email == body.email))).first():
        raise HTTPException(409, "Ya existe un usuario con ese nombre o correo")
    u = User(username=body.username, email=body.email, full_name=body.full_name,
             password_hash=hash_password(body.password), role_id=body.role_id, is_active=body.is_active,
             must_change_password=True)
    prof = body.profile.model_dump(exclude_none=True) if body.profile else {}
    u.profile = UserProfile(**prof)
    db.add(u)
    db.commit()
    db.refresh(u)
    audit.set(u.id, f"Usuario creado: {u.username}", {"role_id": body.role_id})
    return u


def _get_user(db: Session, uid: int) -> User:
    u = db.execute(select(User).where(User.id == uid)).unique().scalar_one_or_none()
    if u is None:
        raise HTTPException(404, "Usuario no encontrado")
    return u


@router.get("/users/{uid}", response_model=UserOut)
def get_user(uid: int, db: Session = Depends(get_db), _=Depends(require("users:view"))):
    return _get_user(db, uid)


@router.put("/users/{uid}", response_model=UserOut)
def update_user(uid: int, body: UserUpdate, db: Session = Depends(get_db), p=Depends(require("users:update")),
                audit: AuditCtx = Depends(audited("update", "users", "user"))):
    u = _get_user(db, uid)
    data = body.model_dump(exclude_unset=True)
    if "role_id" in data and data["role_id"] is not None and db.get(Role, data["role_id"]) is None:
        raise HTTPException(422, "El rol indicado no existe")
    if u.id == p.user_id and (data.get("is_active") is False):
        raise HTTPException(400, "No puede desactivar su propia cuenta")
    if u.role.name == "admin" and (data.get("is_active") is False or
                                   (data.get("role_id") not in (None, u.role_id))):
        others = db.execute(select(func.count()).select_from(User).join(Role).where(
            Role.name == "admin", User.is_active.is_(True), User.id != u.id)).scalar_one()
        if others == 0:
            raise HTTPException(400, "Debe existir al menos un administrador activo")
    if data.get("email") and data["email"] != u.email:
        if db.execute(select(User).where(User.email == data["email"], User.id != u.id)).first():
            raise HTTPException(409, "Ya existe un usuario con ese correo")
        u.email = data["email"]
    for k in ("full_name", "role_id", "is_active"):
        if data.get(k) is not None:
            setattr(u, k, data[k])
    if data.get("is_active"):
        u.failed_attempts, u.locked_until = 0, None
    for k, v in (data.get("profile") or {}).items():
        if v is not None:
            setattr(u.profile, k, v)
    db.commit()
    db.expire_all()
    u = _get_user(db, uid)
    audit.set(u.id, f"Usuario actualizado: {u.username}", {"fields": sorted(data.keys())})
    return u


@router.delete("/users/{uid}", status_code=204)
def delete_user(uid: int, db: Session = Depends(get_db), p=Depends(require("users:delete")),
                audit: AuditCtx = Depends(audited("delete", "users", "user"))):
    u = _get_user(db, uid)
    if u.id == p.user_id:
        raise HTTPException(400, "No puede eliminar su propia cuenta")
    if u.role.name == "admin":
        others = db.execute(select(func.count()).select_from(User).join(Role).where(
            Role.name == "admin", User.id != u.id)).scalar_one()
        if others == 0:
            raise HTTPException(400, "No se puede eliminar al último administrador")
    name = u.username
    db.delete(u)
    db.commit()
    audit.set(uid, f"Usuario eliminado: {name}")
    return Response(status_code=204)


@router.post("/users/{uid}/reset-password", status_code=204)
def reset_password(uid: int, body: ResetPassword, db: Session = Depends(get_db),
                   _=Depends(require("users:update")),
                   audit: AuditCtx = Depends(audited("update", "users", "user_password"))):
    u = _get_user(db, uid)
    u.password_hash = hash_password(body.new_password)
    u.must_change_password = True
    u.failed_attempts, u.locked_until = 0, None
    db.commit()
    audit.set(u.id, f"Contraseña restablecida para {u.username}")
    return Response(status_code=204)


# ---- roles ---------------------------------------------------------------

def _role_out(db: Session, r: Role) -> RoleOut:
    n = db.execute(select(func.count()).select_from(User).where(User.role_id == r.id)).scalar_one()
    return RoleOut(id=r.id, name=r.name, description=r.description, is_system=r.is_system,
                   permissions=r.permissions, user_count=n)


def _check_perms(perms: list[str]) -> None:
    bad = [p for p in perms if not valid_permission(p)]
    if bad:
        raise HTTPException(422, "Permisos desconocidos: " + ", ".join(bad))


@router.get("/roles", response_model=list[RoleOut])
def list_roles(db: Session = Depends(get_db), _=Depends(require("roles:view", "users:view"))):
    return [_role_out(db, r) for r in db.execute(select(Role).order_by(Role.id)).scalars()]


@router.post("/roles", response_model=RoleOut, status_code=201)
def create_role(body: RoleIn, db: Session = Depends(get_db), _=Depends(require("roles:create")),
                audit: AuditCtx = Depends(audited("create", "roles", "role"))):
    _check_perms(body.permissions)
    if db.execute(select(Role).where(Role.name == body.name)).first():
        raise HTTPException(409, "Ya existe un rol con ese nombre")
    r = Role(name=body.name, description=body.description, is_system=False)
    r.set_permissions(body.permissions)
    db.add(r)
    db.commit()
    audit.set(r.id, f"Rol creado: {r.name}", {"permissions": sorted(body.permissions)})
    return _role_out(db, r)


def _get_role(db: Session, rid: int) -> Role:
    r = db.get(Role, rid)
    if r is None:
        raise HTTPException(404, "Rol no encontrado")
    return r


@router.get("/roles/{rid}", response_model=RoleOut)
def get_role(rid: int, db: Session = Depends(get_db), _=Depends(require("roles:view", "users:view"))):
    return _role_out(db, _get_role(db, rid))


@router.put("/roles/{rid}", response_model=RoleOut)
def update_role(rid: int, body: RoleIn, db: Session = Depends(get_db), _=Depends(require("roles:update")),
                audit: AuditCtx = Depends(audited("update", "roles", "role"))):
    r = _get_role(db, rid)
    _check_perms(body.permissions)
    if r.name == "admin":
        raise HTTPException(400, "El rol admin no se puede modificar")
    if body.name != r.name and db.execute(select(Role).where(Role.name == body.name)).first():
        raise HTTPException(409, "Ya existe un rol con ese nombre")
    if r.is_system and body.name != r.name:
        raise HTTPException(400, "No se puede renombrar un rol del sistema")
    r.name, r.description = body.name, body.description
    r.set_permissions(body.permissions)
    db.commit()
    audit.set(r.id, f"Rol actualizado: {r.name}", {"permissions": sorted(body.permissions)})
    return _role_out(db, r)


@router.delete("/roles/{rid}", status_code=204)
def delete_role(rid: int, db: Session = Depends(get_db), _=Depends(require("roles:delete")),
                audit: AuditCtx = Depends(audited("delete", "roles", "role"))):
    r = _get_role(db, rid)
    if r.name == "admin":
        raise HTTPException(400, "El rol admin no se puede borrar")
    if r.is_system:
        raise HTTPException(400, "Los roles del sistema no se pueden borrar")
    if db.execute(select(func.count()).select_from(User).where(User.role_id == rid)).scalar_one():
        raise HTTPException(409, "El rol tiene usuarios asignados")
    name = r.name
    db.delete(r)
    db.commit()
    audit.set(rid, f"Rol eliminado: {name}")
    return Response(status_code=204)


@router.get("/permissions")
def permissions(_=Depends(require("roles:view", "users:view"))):
    return permissions_catalog()
