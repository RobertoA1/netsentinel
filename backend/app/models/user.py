from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UTCDateTime, utcnow


class Role(Base):
    __tablename__ = "roles"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(64), unique=True)
    description: Mapped[str] = mapped_column(String(255), default="")
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)
    permission_rows: Mapped[list["RolePermission"]] = relationship(
        cascade="all, delete-orphan", lazy="selectin"
    )

    @property
    def permissions(self) -> list[str]:
        return sorted(p.code for p in self.permission_rows)

    def set_permissions(self, codes: list[str]) -> None:
        wanted = set(codes)
        self.permission_rows[:] = [p for p in self.permission_rows if p.code in wanted]
        have = {p.code for p in self.permission_rows}
        for c in sorted(wanted - have):
            self.permission_rows.append(RolePermission(code=c))


class RolePermission(Base):
    __tablename__ = "role_permissions"
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True)
    code: Mapped[str] = mapped_column(String(64), primary_key=True)


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    full_name: Mapped[str] = mapped_column(String(255), default="")
    password_hash: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    must_change_password: Mapped[bool] = mapped_column(Boolean, default=False)
    failed_attempts: Mapped[int] = mapped_column(Integer, default=0)
    locked_until: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    last_login_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"))
    role: Mapped[Role] = relationship(lazy="joined")
    profile: Mapped["UserProfile"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan", lazy="joined"
    )

    @property
    def permissions(self) -> list[str]:
        return self.role.permissions if self.role else []


class UserProfile(Base):
    __tablename__ = "user_profiles"
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    job_title: Mapped[str] = mapped_column(String(128), default="")
    department: Mapped[str] = mapped_column(String(128), default="")
    phone: Mapped[str] = mapped_column(String(64), default="")
    avatar_color: Mapped[str] = mapped_column(String(16), default="#3b82f6")
    theme: Mapped[str] = mapped_column(String(16), default="system")
    language: Mapped[str] = mapped_column(String(8), default="es")
    timezone: Mapped[str] = mapped_column(String(64), default="America/Lima")
    user: Mapped[User] = relationship(back_populates="profile")
