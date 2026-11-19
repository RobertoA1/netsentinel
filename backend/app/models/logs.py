from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, Float, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, BigPK, JSONType, UTCDateTime, utcnow


class FirewallLog(Base):
    __tablename__ = "firewall_logs"
    __table_args__ = (
        Index("ix_firewall_logs_ts", "ts"),
        Index("ix_firewall_logs_src_ip_ts", "src_ip", "ts"),
        Index("ix_firewall_logs_dst_ip", "dst_ip"),
        Index("ix_firewall_logs_dst_port", "dst_port"),
        Index("ix_firewall_logs_dir_ts", "direction", "ts"),
        Index("ix_firewall_logs_source_id", "source_id"),
    )
    id: Mapped[int] = mapped_column(BigPK, primary_key=True, autoincrement=True)
    ts: Mapped[datetime] = mapped_column(UTCDateTime)
    source_id: Mapped[int | None] = mapped_column(ForeignKey("sources.id", ondelete="SET NULL"), nullable=True)
    log_type: Mapped[str] = mapped_column(String(16), default="flow")
    action: Mapped[str] = mapped_column(String(8), default="pass")
    proto: Mapped[str | None] = mapped_column(String(16), nullable=True)
    src_ip: Mapped[str] = mapped_column(String(45))
    src_port: Mapped[int | None] = mapped_column(Integer, nullable=True)
    dst_ip: Mapped[str] = mapped_column(String(45))
    dst_port: Mapped[int | None] = mapped_column(Integer, nullable=True)
    direction: Mapped[str] = mapped_column(String(16), default="outbound")
    bytes_out: Mapped[int] = mapped_column(BigInteger, default=0)
    bytes_in: Mapped[int] = mapped_column(BigInteger, default=0)
    packets: Mapped[int | None] = mapped_column(Integer, nullable=True)
    duration: Mapped[float | None] = mapped_column(Float, nullable=True)
    signature: Mapped[str | None] = mapped_column(String(512), nullable=True)
    signature_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    category: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ids_severity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    label: Mapped[str | None] = mapped_column(String(255), nullable=True)
    raw: Mapped[dict] = mapped_column(JSONType, default=dict)


class IngestRun(Base):
    __tablename__ = "ingest_runs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    started_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow, index=True)
    finished_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="running")
    trigger: Mapped[str] = mapped_column(String(16), default="manual")
    source_id: Mapped[int | None] = mapped_column(ForeignKey("sources.id", ondelete="SET NULL"), nullable=True)
    filename: Mapped[str | None] = mapped_column(String(512), nullable=True)
    lines_read: Mapped[int] = mapped_column(Integer, default=0)
    logs_inserted: Mapped[int] = mapped_column(Integer, default=0)
    parse_errors: Mapped[int] = mapped_column(Integer, default=0)
    findings_created: Mapped[int] = mapped_column(Integer, default=0)
    findings_noise: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str | None] = mapped_column(String(2000), nullable=True)


class IngestedFile(Base):
    """Avance de lectura por archivo en INGEST_DIR (soporta archivos que crecen y rotación)."""

    __tablename__ = "ingested_files"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id", ondelete="CASCADE"), index=True)
    path: Mapped[str] = mapped_column(String(1024))
    offset: Mapped[int] = mapped_column(BigInteger, default=0)
    processed_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)


class AppSetting(Base):
    __tablename__ = "app_settings"
    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[dict] = mapped_column(JSONType, default=dict)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow, onupdate=utcnow)
