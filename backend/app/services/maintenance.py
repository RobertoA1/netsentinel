"""Purga de datos según la política de retención."""
from __future__ import annotations

from datetime import timedelta

from sqlalchemy import delete, select, text
from sqlalchemy.orm import Session

from app.db.base import utcnow
from app.models import Alert, AuditEvent, Finding, FirewallLog, IngestRun, ModuleSession
from app.services import settings_service


def purge(db: Session) -> dict:
    ret = settings_service.get_setting(db, "retention")
    now = utcnow()
    out: dict[str, int] = {}
    if db.get_bind().dialect.name == "postgresql":
        # El trigger de la bitácora bloquea DELETE salvo en esta transacción de purga autorizada.
        db.execute(text("SET LOCAL netsentinel.audit_purge = 'on'"))
    out["logs_deleted"] = db.execute(delete(FirewallLog).where(FirewallLog.ts < now - timedelta(days=ret.logs_days))).rowcount
    old_findings = delete(Finding).where(Finding.last_seen < now - timedelta(days=ret.findings_days))
    # alertas de hallazgos purgados (en SQLite no hay cascada garantizada)
    db.execute(delete(Alert).where(Alert.finding_id.in_(
        select(Finding.id).where(Finding.last_seen < now - timedelta(days=ret.findings_days)))))
    out["findings_deleted"] = db.execute(old_findings).rowcount
    cutoff = now - timedelta(days=ret.audit_days)
    out["audit_events_deleted"] = db.execute(delete(AuditEvent).where(AuditEvent.ts < cutoff)).rowcount
    out["module_sessions_deleted"] = db.execute(delete(ModuleSession).where(
        ModuleSession.entered_at < cutoff, ModuleSession.exited_at.is_not(None))).rowcount
    out["ingest_runs_deleted"] = db.execute(delete(IngestRun).where(
        IngestRun.started_at < now - timedelta(days=ret.logs_days))).rowcount
    db.commit()
    return out
