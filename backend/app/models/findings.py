from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, JSONType, UTCDateTime, utcnow


class Finding(Base):
    __tablename__ = "traffic_findings"
    __table_args__ = (
        Index("ix_findings_last_seen", "last_seen"),
        Index("ix_findings_type_sev", "finding_type", "severity"),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)
    first_seen: Mapped[datetime] = mapped_column(UTCDateTime)
    last_seen: Mapped[datetime] = mapped_column(UTCDateTime)
    occurrences: Mapped[int] = mapped_column(Integer, default=1)
    dedup_key: Mapped[str] = mapped_column(String(255), index=True)
    finding_type: Mapped[str] = mapped_column(String(24))
    severity: Mapped[str] = mapped_column(String(12))
    score: Mapped[float] = mapped_column(Float, default=0)
    status: Mapped[str] = mapped_column(String(16), default="new")
    title: Mapped[str] = mapped_column(String(512))
    src_ip: Mapped[str | None] = mapped_column(String(45), nullable=True, index=True)
    dst_ip: Mapped[str | None] = mapped_column(String(45), nullable=True, index=True)
    dst_port: Mapped[int | None] = mapped_column(Integer, nullable=True)
    proto: Mapped[str | None] = mapped_column(String(16), nullable=True)
    window_start: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    window_end: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    evidence: Mapped[dict] = mapped_column(JSONType, default=dict)
    llm_verdict: Mapped[str | None] = mapped_column(String(12), nullable=True)
    llm_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_noise: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    llm_explanation: Mapped[str] = mapped_column(Text, default="")
    llm_recommendation: Mapped[str] = mapped_column(Text, default="")
    llm_model: Mapped[str | None] = mapped_column(String(64), nullable=True)
    assigned_to_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    acknowledged_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    assigned_to = relationship("User", lazy="joined", foreign_keys=[assigned_to_id])
    comments: Mapped[list["FindingComment"]] = relationship(
        cascade="all, delete-orphan", order_by="FindingComment.id", lazy="select"
    )


class FindingComment(Base):
    __tablename__ = "finding_comments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    finding_id: Mapped[int] = mapped_column(ForeignKey("traffic_findings.id", ondelete="CASCADE"), index=True)
    author_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    author: Mapped[str] = mapped_column(String(255), default="")
    body: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)


class AlertRule(Base):
    __tablename__ = "alert_rules"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(128))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    min_severity: Mapped[str] = mapped_column(String(12), default="high")
    finding_types: Mapped[list] = mapped_column(JSONType, default=list)
    channels: Mapped[list] = mapped_column(JSONType, default=list)
    webhook_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    email_to: Mapped[str | None] = mapped_column(String(255), nullable=True)
    include_noise: Mapped[bool] = mapped_column(Boolean, default=False)


class Alert(Base):
    __tablename__ = "alerts"
    __table_args__ = (Index("ix_alerts_created", "created_at"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)
    finding_id: Mapped[int | None] = mapped_column(ForeignKey("traffic_findings.id", ondelete="CASCADE"), nullable=True, index=True)
    rule_id: Mapped[int | None] = mapped_column(ForeignKey("alert_rules.id", ondelete="SET NULL"), nullable=True)
    severity: Mapped[str] = mapped_column(String(12))
    title: Mapped[str] = mapped_column(String(512))
    message: Mapped[str] = mapped_column(Text, default="")
    channel: Mapped[str] = mapped_column(String(16), default="in_app")
    delivered: Mapped[bool] = mapped_column(Boolean, default=False)
    delivered_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    webhook_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    email_to: Mapped[str | None] = mapped_column(String(255), nullable=True)
    acknowledged_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    acknowledged_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    acknowledged_by_user = relationship("User", lazy="joined", foreign_keys=[acknowledged_by_id])

    @property
    def acknowledged_by(self) -> str | None:
        u = self.acknowledged_by_user
        return (u.full_name or u.username) if u else None
