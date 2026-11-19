from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.core.deps import AuditCtx, Principal, audited, require
from app.core.pagination import PageParams, page_params, paginate
from app.core.timerange import TimeRange, list_range
from app.db.base import utcnow
from app.db.session import get_db
from app.models import Alert, AlertRule
from app.schemas.common import Page
from app.schemas.findings import AlertOut, AlertRuleIn, AlertRuleOut

router = APIRouter(tags=["alerts"])
SORT = {"id": Alert.id, "created_at": Alert.created_at, "severity": Alert.severity}


@router.get("/alerts", response_model=Page[AlertOut])
def list_alerts(acknowledged: bool | None = None, severity: str | None = None, channel: str = "in_app",
                tr: TimeRange = Depends(list_range), pp: PageParams = Depends(page_params),
                db: Session = Depends(get_db), _=Depends(require("alerts:view"))):
    """Por defecto solo las alertas in_app (las webhook/email son el despacho de la misma alerta)."""
    stmt = select(Alert)
    if channel != "all":
        stmt = stmt.where(Alert.channel == channel)
    if tr.start:
        stmt = stmt.where(Alert.created_at >= tr.start)
    stmt = stmt.where(Alert.created_at <= tr.end)
    if acknowledged is True:
        stmt = stmt.where(Alert.acknowledged_at.is_not(None))
    elif acknowledged is False:
        stmt = stmt.where(Alert.acknowledged_at.is_(None))
    if severity:
        stmt = stmt.where(Alert.severity == severity)
    return paginate(db, stmt, pp, SORT, "-created_at")


@router.get("/alerts/unread-count")
def unread_count(db: Session = Depends(get_db), _=Depends(require("alerts:view"))):
    n = db.execute(select(func.count()).select_from(Alert).where(
        Alert.channel == "in_app", Alert.acknowledged_at.is_(None))).scalar_one()
    return {"count": n}


@router.get("/alerts/pending-dispatch", response_model=list[AlertOut])
def pending_dispatch(limit: int = 100, db: Session = Depends(get_db), _=Depends(require("alerts:view", api_key=True))):
    return list(db.execute(select(Alert).where(Alert.channel != "in_app", Alert.delivered.is_(False))
                           .order_by(Alert.id).limit(min(limit, 500))).scalars().unique())


@router.post("/alerts/ack-all")
def ack_all(db: Session = Depends(get_db), p: Principal = Depends(require("alerts:update")),
            audit: AuditCtx = Depends(audited("update", "alerts", "alert"))):
    res = db.execute(update(Alert).where(Alert.channel == "in_app", Alert.acknowledged_at.is_(None))
                     .values(acknowledged_at=utcnow(), acknowledged_by_id=p.user_id))
    db.commit()
    audit.set(None, f"Alertas reconocidas en bloque ({res.rowcount})", {"count": res.rowcount})
    return {"acknowledged": res.rowcount}


@router.post("/alerts/{aid}/ack", response_model=AlertOut)
def ack(aid: int, db: Session = Depends(get_db), p: Principal = Depends(require("alerts:update")),
        audit: AuditCtx = Depends(audited("update", "alerts", "alert"))):
    a = db.get(Alert, aid)
    if a is None:
        raise HTTPException(404, "Alerta no encontrada")
    if a.acknowledged_at is None:
        a.acknowledged_at, a.acknowledged_by_id = utcnow(), p.user_id
        db.commit()
        db.refresh(a)
    audit.set(aid, f"Alerta #{aid} reconocida")
    return a


@router.post("/alerts/{aid}/delivered", status_code=204)
def delivered(aid: int, db: Session = Depends(get_db), _=Depends(require("alerts:update", api_key=True))):
    a = db.get(Alert, aid)
    if a is None:
        raise HTTPException(404, "Alerta no encontrada")
    a.delivered, a.delivered_at = True, utcnow()
    db.commit()
    return Response(status_code=204)


# ---- reglas -------------------------------------------------------------

def _check_rule(r: AlertRuleIn) -> None:
    if r.webhook_url and not r.webhook_url.startswith(("http://", "https://")):
        raise HTTPException(422, "webhook_url debe comenzar con http:// o https://")
    if r.email_to and "@" not in r.email_to:
        raise HTTPException(422, "email_to no es un correo válido")


@router.get("/alert-rules", response_model=list[AlertRuleOut])
def list_rules(db: Session = Depends(get_db), _=Depends(require("alerts:view"))):
    return list(db.execute(select(AlertRule).order_by(AlertRule.id)).scalars())


@router.post("/alert-rules", response_model=AlertRuleOut, status_code=201)
def create_rule(body: AlertRuleIn, db: Session = Depends(get_db), _=Depends(require("alerts:create")),
                audit: AuditCtx = Depends(audited("create", "alerts", "alert_rule"))):
    _check_rule(body)
    r = AlertRule(**body.model_dump())
    db.add(r)
    db.commit()
    audit.set(r.id, f"Regla de alerta creada: {r.name}")
    return r


def _rule(db: Session, rid: int) -> AlertRule:
    r = db.get(AlertRule, rid)
    if r is None:
        raise HTTPException(404, "Regla no encontrada")
    return r


@router.get("/alert-rules/{rid}", response_model=AlertRuleOut)
def get_rule(rid: int, db: Session = Depends(get_db), _=Depends(require("alerts:view"))):
    return _rule(db, rid)


@router.put("/alert-rules/{rid}", response_model=AlertRuleOut)
def update_rule(rid: int, body: AlertRuleIn, db: Session = Depends(get_db), _=Depends(require("alerts:update")),
                audit: AuditCtx = Depends(audited("update", "alerts", "alert_rule"))):
    _check_rule(body)
    r = _rule(db, rid)
    for k, v in body.model_dump().items():
        setattr(r, k, v)
    db.commit()
    audit.set(r.id, f"Regla de alerta actualizada: {r.name}")
    return r


@router.delete("/alert-rules/{rid}", status_code=204)
def delete_rule(rid: int, db: Session = Depends(get_db), _=Depends(require("alerts:delete")),
                audit: AuditCtx = Depends(audited("delete", "alerts", "alert_rule"))):
    r = _rule(db, rid)
    name = r.name
    db.delete(r)
    db.commit()
    audit.set(rid, f"Regla de alerta eliminada: {name}")
    return Response(status_code=204)
