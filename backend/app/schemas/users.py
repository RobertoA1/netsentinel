from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.schemas.common import ORM

PASSWORD_MIN = 8


def _check_email(v: str) -> str:
    v = v.strip()
    if "@" not in v or " " in v or len(v) < 3:
        raise ValueError("Correo electrónico inválido")
    return v


class RoleRef(ORM):
    id: int
    name: str
    description: str = ""


class ProfileOut(ORM):
    job_title: str = ""
    department: str = ""
    phone: str = ""
    avatar_color: str = "#3b82f6"
    theme: str = "system"
    language: str = "es"
    timezone: str = "America/Lima"


class ProfileIn(BaseModel):
    job_title: str | None = None
    department: str | None = None
    phone: str | None = None
    avatar_color: str | None = None
    theme: str | None = Field(None, pattern="^(light|dark|system)$")
    language: str | None = None
    timezone: str | None = None


class UserOut(ORM):
    id: int
    username: str
    email: str
    full_name: str
    is_active: bool
    must_change_password: bool
    last_login_at: datetime | None
    role: RoleRef
    profile: ProfileOut
    created_at: datetime


class UserMe(ORM):
    id: int
    username: str
    email: str
    full_name: str
    is_active: bool
    must_change_password: bool
    last_login_at: datetime | None
    role: RoleRef
    profile: ProfileOut
    permissions: list[str]


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=64, pattern=r"^[A-Za-z0-9_.\-]+$")
    email: str
    full_name: str = ""
    password: str = Field(min_length=PASSWORD_MIN, max_length=128)
    role_id: int
    is_active: bool = True
    profile: ProfileIn | None = None

    _e = field_validator("email")(_check_email)


class UserUpdate(BaseModel):
    email: str | None = None
    full_name: str | None = None
    role_id: int | None = None
    is_active: bool | None = None
    profile: ProfileIn | None = None

    @field_validator("email")
    @classmethod
    def _v(cls, v):
        return _check_email(v) if v is not None else v


class ResetPassword(BaseModel):
    new_password: str = Field(min_length=PASSWORD_MIN, max_length=128)


class RoleOut(ORM):
    id: int
    name: str
    description: str
    is_system: bool
    permissions: list[str]
    user_count: int = 0


class RoleIn(BaseModel):
    name: str = Field(min_length=2, max_length=64)
    description: str = ""
    permissions: list[str] = []


class LoginIn(BaseModel):
    username: str
    password: str


class LoginOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserMe


class RefreshIn(BaseModel):
    refresh_token: str


class RefreshOut(BaseModel):
    access_token: str
    refresh_token: str


class MeUpdate(ProfileIn):
    full_name: str | None = None
    email: str | None = None

    @field_validator("email")
    @classmethod
    def _v(cls, v):
        return _check_email(v) if v is not None else v


class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(min_length=PASSWORD_MIN, max_length=128)
