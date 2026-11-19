from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.common import (ORM, AlertChannel, FindingStatus, FindingType, LlmVerdict, Severity,
                                SourceFormat)


class UserRef(BaseModel):
    id: int
    full_name: str


class CommentOut(ORM):
    id: int
    author: str
    body: str
    created_at: datetime


class FindingOut(ORM):
    id: int
    created_at: datetime
    first_seen: datetime
    last_seen: datetime
    occurrences: int
    finding_type: FindingType
    severity: Severity
    score: float
    status: FindingStatus
    title: str
    src_ip: str | None
    dst_ip: str | None
    dst_port: int | None
    proto: str | None
    window_start: datetime | None
    window_end: datetime | None
    evidence: dict[str, Any]
    llm_verdict: LlmVerdict | None
    llm_confidence: float | None
    is_noise: bool
    llm_explanation: str
    llm_recommendation: str
    llm_model: str | None
    assigned_to: UserRef | None


class FindingDetail(FindingOut):
    comments: list[CommentOut] = []


class FindingPatch(BaseModel):
    status: FindingStatus | None = None
    severity: Severity | None = None
    assigned_to_id: int | None = None
    is_noise: bool | None = None


class CommentIn(BaseModel):
    body: str = Field(min_length=1, max_length=4000)


class AlertOut(ORM):
    id: int
    created_at: datetime
    finding_id: int | None
    rule_id: int | None
    severity: Severity
    title: str
    message: str
    channel: AlertChannel
    delivered: bool
    acknowledged_at: datetime | None
    acknowledged_by: str | None
    # solo informativos para el despachador (n8n)
    webhook_url: str | None = None
    email_to: str | None = None


class AlertRuleIn(BaseModel):
    name: str = Field(min_length=2, max_length=128)
    enabled: bool = True
    min_severity: Severity = "high"
    finding_types: list[FindingType] = []
    channels: list[AlertChannel] = ["in_app"]
    webhook_url: str | None = None
    email_to: str | None = None
    include_noise: bool = False


class AlertRuleOut(AlertRuleIn, ORM):
    id: int


class SourceIn(BaseModel):
    name: str = Field(min_length=2, max_length=128)
    format: SourceFormat
    description: str = ""
    enabled: bool = True


class SourceOut(SourceIn, ORM):
    id: int
    last_ingest_at: datetime | None = None
    log_count: int = 0


class AssetIn(BaseModel):
    ip: str
    hostname: str = ""
    owner: str = ""
    asset_type: str = "workstation"
    criticality: str = Field("medium", pattern="^(low|medium|high|critical)$")
    expected_ports: list[int] = []
    notes: str = ""


class AssetOut(AssetIn, ORM):
    id: int


class ListEntryIn(BaseModel):
    list_type: str = Field(pattern="^(allow|deny)$")
    kind: str = Field(pattern="^(ip|cidr|port|domain)$")
    value: str = Field(min_length=1, max_length=255)
    note: str = ""


class ListEntryOut(ListEntryIn, ORM):
    id: int
    created_at: datetime


class FirewallLogOut(ORM):
    id: int
    ts: datetime
    source_id: int | None
    source_name: str | None = None
    log_type: str
    action: str
    proto: str | None
    src_ip: str
    src_port: int | None
    dst_ip: str
    dst_port: int | None
    direction: str
    bytes_out: int
    bytes_in: int
    packets: int | None
    duration: float | None
    signature: str | None
    signature_id: int | None
    category: str | None
    ids_severity: int | None
    label: str | None
    raw: dict[str, Any]


class IngestRunOut(ORM):
    id: int
    started_at: datetime
    finished_at: datetime | None
    status: str
    trigger: str
    source_id: int | None
    source_name: str | None = None
    filename: str | None
    lines_read: int
    logs_inserted: int
    parse_errors: int
    findings_created: int
    findings_noise: int
    error: str | None


class IngestRunIn(BaseModel):
    source_id: int | None = None


class DatasetIn(BaseModel):
    rebase_time: bool = True
    max_rows: int | None = Field(None, ge=1, le=20_000_000)


class DetectIn(BaseModel):
    window_hours: int | None = Field(None, ge=1, le=24 * 30)


class DetectOut(BaseModel):
    findings_created: int
    findings_updated: int
    findings_noise: int
    duration_ms: int


class IngestStatus(BaseModel):
    last_run: IngestRunOut | None
    dataset_available: bool
    dataset_loaded: bool
    pending_files: int
