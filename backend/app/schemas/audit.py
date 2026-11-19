from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel

from app.schemas.common import ORM


class AuditEventOut(ORM):
    id: int
    ts: datetime
    user_id: int | None
    username: str | None
    event_type: str
    module: str | None
    entity: str | None
    entity_id: str | None
    description: str
    ip: str | None
    user_agent: str | None
    details: dict[str, Any]


class ModuleSessionOut(ORM):
    id: int
    user_id: int
    username: str
    module: str
    entered_at: datetime
    exited_at: datetime | None
    duration_seconds: int | None
    ip: str | None
    exit_reason: str | None


class ModuleEnterIn(BaseModel):
    module: str


class ModuleEnterOut(BaseModel):
    session_id: int


class ModuleExitIn(BaseModel):
    session_id: int
    reason: str | None = None


class ByModule(BaseModel):
    module: str
    visits: int
    total_seconds: int


class ByUser(BaseModel):
    username: str
    visits: int
    total_seconds: int
    last_seen: datetime | None


class ByEventType(BaseModel):
    event_type: str
    count: int


class AuditSummary(BaseModel):
    by_module: list[ByModule]
    by_user: list[ByUser]
    by_event_type: list[ByEventType]
