"""Evaluación de reglas de alerta para hallazgos no-ruido."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.base import utcnow
from app.models import Alert, AlertRule, Finding
from app.services.detectors.common import sev_rank

SEV_ES = {"critical": "CRÍTICO", "high": "ALTO", "medium": "MEDIO", "low": "BAJO", "info": "INFO"}


def rule_matches(rule: AlertRule, f: Finding) -> bool:
    if not rule.enabled:
        return False
    if f.is_noise and not rule.include_noise:
        return False
    if sev_rank(f.severity) < sev_rank(rule.min_severity):
        return False
    types = rule.finding_types or []
    return not types or f.finding_type in types


def alert_message(f: Finding) -> str:
    parts = [f"[{SEV_ES.get(f.severity, f.severity)}] {f.title}."]
    if f.llm_explanation:
        parts.append(f.llm_explanation)
    if f.llm_recommendation:
        parts.append("Recomendación: " + f.llm_recommendation)
    return " ".join(parts)[:4000]


def evaluate_alerts(db: Session, f: Finding, rules: list[AlertRule] | None = None) -> list[Alert]:
    """Crea alertas (una por regla y canal). in_app queda entregada; webhook/email, pendientes para n8n.

    Idempotente: no repite la alerta para la misma (hallazgo, regla, canal, severidad).
    """
    if rules is None:
        rules = list(db.execute(select(AlertRule).where(AlertRule.enabled.is_(True))).scalars())
    existing = {(a.rule_id, a.channel, a.severity) for a in
                db.execute(select(Alert).where(Alert.finding_id == f.id)).scalars()}
    created: list[Alert] = []
    for rule in rules:
        if not rule_matches(rule, f):
            continue
        for ch in rule.channels or []:
            if (rule.id, ch, f.severity) in existing:
                continue
            a = Alert(
                finding_id=f.id, rule_id=rule.id, severity=f.severity, title=f.title[:512],
                message=alert_message(f), channel=ch, delivered=(ch == "in_app"),
                delivered_at=utcnow() if ch == "in_app" else None,
                webhook_url=rule.webhook_url if ch == "webhook" else None,
                email_to=rule.email_to if ch == "email" else None, created_at=utcnow(),
            )
            db.add(a)
            created.append(a)
    if created:
        db.flush()
    return created
