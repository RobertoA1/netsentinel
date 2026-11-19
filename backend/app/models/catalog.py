from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, JSONType, UTCDateTime, utcnow


class Source(Base):
    __tablename__ = "sources"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(128), unique=True)
    format: Mapped[str] = mapped_column(String(32))
    description: Mapped[str] = mapped_column(String(255), default="")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    last_ingest_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)


class Asset(Base):
    __tablename__ = "assets"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ip: Mapped[str] = mapped_column(String(45), unique=True, index=True)
    hostname: Mapped[str] = mapped_column(String(255), default="")
    owner: Mapped[str] = mapped_column(String(255), default="")
    asset_type: Mapped[str] = mapped_column(String(64), default="workstation")
    criticality: Mapped[str] = mapped_column(String(16), default="medium")
    expected_ports: Mapped[list] = mapped_column(JSONType, default=list)
    notes: Mapped[str] = mapped_column(Text, default="")


class ListEntry(Base):
    __tablename__ = "list_entries"
    __table_args__ = (UniqueConstraint("list_type", "kind", "value", name="uq_list_entry"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    list_type: Mapped[str] = mapped_column(String(8))
    kind: Mapped[str] = mapped_column(String(8))
    value: Mapped[str] = mapped_column(String(255))
    note: Mapped[str] = mapped_column(String(255), default="")
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)
