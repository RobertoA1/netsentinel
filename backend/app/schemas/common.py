from __future__ import annotations

from datetime import datetime
from typing import Any, Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")

FindingType = Literal["beaconing", "unusual_port", "exfiltration", "ids_alert", "talker_anomaly"]
Severity = Literal["critical", "high", "medium", "low", "info"]
FindingStatus = Literal["new", "in_review", "confirmed", "false_positive", "closed"]
LlmVerdict = Literal["real", "noise", "uncertain"]
AlertChannel = Literal["in_app", "email", "webhook"]
ReportFormat = Literal["pdf", "docx", "xlsx"]
SourceFormat = Literal["opnsense_filterlog", "suricata_eve", "ctu13_binetflow"]


class ORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int


class Detail(BaseModel):
    detail: str
