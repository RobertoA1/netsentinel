from __future__ import annotations

from datetime import datetime

from sqlalchemy import ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, BigPK, JSONType, UTCDateTime, utcnow


class AuditEvent(Base):
    """Bitácora de solo inserción (UPDATE bloqueado por trigger en PostgreSQL)."""

    __tablename__ = "audit_events"
    __table_args__ = (
        Index("ix_audit_events_ts", "ts"),
        Index("ix_audit_events_user_ts", "user_id", "ts"),
        Index("ix_audit_events_type", "event_type"),
    )
    id: Mapped[int] = mapped_column(BigPK, primary_key=True, autoincrement=True)
    ts: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)
    user_id: Mapped[int | None] = mapped_column(Integer, nullable=True)  # sin FK: la bitácora sobrevive al usuario
    username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    event_type: Mapped[str] = mapped_column(String(16))
    module: Mapped[str | None] = mapped_column(String(32), nullable=True)
    entity: Mapped[str | None] = mapped_column(String(64), nullable=True)
    entity_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    description: Mapped[str] = mapped_column(String(1000), default="")
    ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(512), nullable=True)
    details: Mapped[dict] = mapped_column(JSONType, default=dict)


class ModuleSession(Base):
    __tablename__ = "module_sessions"
    __table_args__ = (Index("ix_module_sessions_user_open", "user_id", "exited_at"),)
    id: Mapped[int] = mapped_column(BigPK, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    username: Mapped[str] = mapped_column(String(64))
    module: Mapped[str] = mapped_column(String(32))
    entered_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow, index=True)
    last_activity_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)
    exited_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(512), nullable=True)
    exit_reason: Mapped[str | None] = mapped_column(String(16), nullable=True)


class ReportHistory(Base):
    __tablename__ = "report_history"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    report_code: Mapped[str] = mapped_column(String(32))
    report_name: Mapped[str] = mapped_column(String(128))
    format: Mapped[str] = mapped_column(String(8))
    date_from: Mapped[datetime] = mapped_column(UTCDateTime)
    date_to: Mapped[datetime] = mapped_column(UTCDateTime)
    generated_by: Mapped[str] = mapped_column(String(255))
    generated_by_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    generated_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow, index=True)
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    file_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
