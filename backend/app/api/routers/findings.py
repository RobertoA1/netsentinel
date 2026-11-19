from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from app.core.deps import AuditCtx, audited, require
from app.core.pagination import PageParams, page_params, paginate
from app.core.timerange import TimeRange, list_range
from app.db.base import utcnow
from app.db.session import get_db
from app.models import Finding, FindingComment, FirewallLog as L, User
from app.schemas.common import Page
from app.schemas.findings import CommentIn, FindingDetail, FindingOut, FindingPatch, FirewallLogOut
from app.services import pipeline
from app.services.alerts.service import evaluate_alerts
from app.api.routers.logs import log_out

router = APIRouter(prefix="/findings", tags=["findings"])

SORT = {"id": Finding.id, "created_at": Finding.created_at, "last_seen": Finding.last_seen,
        "first_seen": Finding.first_seen, "score": Finding.score, "severity": Finding.severity,
        "status": Finding.status, "finding_type": Finding.finding_type, "occurrences": Finding.occurrences}


def finding_out(f: Finding, detail: bool = False):
    data = {c.name: getattr(f, c.name) for c in Finding.__table__.columns}
    data["assigned_to"] = ({"id": f.assigned_to.id, "full_name": f.assigned_to.full_name or f.assigned_to.username}
                           if f.assigned_to else None)
    if detail:
        data["comments"] = list(f.comments)
        return FindingDetail.model_validate(data)
    return FindingOut.model_validate(data)


def _get(db: Session, fid: int) -> Finding:
    f = db.execute(select(Finding).where(Finding.id == fid)).unique().scalar_one_or_none()
    if f is None:
        raise HTTPException(404, "Hallazgo no encontrado")
    return f


@router.get("", response_model=Page[FindingOut])
def list_findings(finding_type: str | None = None, severity: str | None = None, status: str | None = None,
                  is_noise: bool | None = None, src_ip: str | None = None, dst_ip: str | None = None,
                  assigned_to_id: int | None = None, q: str | None = None, tr: TimeRange = Depends(list_range),
                  pp: PageParams = Depends(page_params), db: Session = Depends(get_db),
                  _=Depends(require("findings:view"))):
    stmt = select(Finding)
    if tr.start:
        stmt = stmt.where(Finding.last_seen >= tr.start)
    stmt = stmt.where(Finding.first_seen <= tr.end)
    for k, v in (("finding_type", finding_type), ("severity", severity), ("status", status),
                 ("is_noise", is_noise), ("src_ip", src_ip), ("dst_ip", dst_ip),
                 ("assigned_to_id", assigned_to_id)):
        if v is not None:
            stmt = stmt.where(getattr(Finding, k) == v)
    if q:
        like = f"%{q.lower()}%"
        stmt = stmt.where(or_(func.lower(Finding.title).like(like), Finding.src_ip.like(f"{q}%"),
                              Finding.dst_ip.like(f"{q}%"), func.lower(Finding.llm_explanation).like(like)))
    page = paginate(db, stmt, pp, SORT, "-last_seen")
    page["items"] = [finding_out(f) for f in page["items"]]
    return page


@router.get("/{fid}", response_model=FindingDetail)
def get_finding(fid: int, db: Session = Depends(get_db), _=Depends(require("findings:view"))):
    return finding_out(_get(db, fid), detail=True)


@router.patch("/{fid}", response_model=FindingDetail)
def patch_finding(fid: int, body: FindingPatch, db: Session = Depends(get_db), p=Depends(require("findings:update")),
                  audit: AuditCtx = Depends(audited("update", "findings", "finding"))):
    f = _get(db, fid)
    data = body.model_dump(exclude_unset=True)
    changes: dict = {}
    if "assigned_to_id" in data and data["assigned_to_id"] is not None and db.get(User, data["assigned_to_id"]) is None:
        raise HTTPException(422, "El usuario asignado no existe")
    was_noise = f.is_noise
    for k, v in data.items():
        old = getattr(f, k)
        if old != v:
            changes[k] = {"from": old, "to": v}
            setattr(f, k, v)
    if "status" in changes:
        now = utcnow()
        if f.status != "new" and f.acknowledged_at is None:
            f.acknowledged_at = now
        if f.status in ("closed", "false_positive"):
            f.resolved_at = now
        elif f.resolved_at is not None:
            f.resolved_at = None
    db.flush()
    if was_noise and not f.is_noise:
        evaluate_alerts(db, f)
    db.commit()
    db.expire_all()
    audit.set(f.id, f"Hallazgo #{f.id} actualizado", {"changes": changes})
    return finding_out(_get(db, fid), detail=True)


@router.post("/{fid}/comments", response_model=FindingDetail, status_code=201)
def add_comment(fid: int, body: CommentIn, db: Session = Depends(get_db), p=Depends(require("findings:update")),
                audit: AuditCtx = Depends(audited("create", "findings", "finding_comment"))):
    f = _get(db, fid)
    db.add(FindingComment(finding_id=f.id, author_id=p.user_id, author=p.display_name, body=body.body.strip()))
    db.commit()
    db.expire(f)
    audit.set(f.id, f"Comentario agregado al hallazgo #{f.id}")
    return finding_out(_get(db, fid), detail=True)


@router.post("/{fid}/reanalyze", response_model=FindingDetail)
def reanalyze(fid: int, db: Session = Depends(get_db), _=Depends(require("findings:update")),
              audit: AuditCtx = Depends(audited("execute", "findings", "finding"))):
    f = _get(db, fid)
    pipeline.reanalyze_finding(db, f)
    audit.set(f.id, f"Reanálisis LLM del hallazgo #{f.id}", {"llm_verdict": f.llm_verdict})
    return finding_out(_get(db, fid), detail=True)


@router.get("/{fid}/related-logs", response_model=Page[FirewallLogOut])
def related_logs(fid: int, pp: PageParams = Depends(page_params), db: Session = Depends(get_db),
                 _=Depends(require("findings:view", "logs:view"))):
    f = _get(db, fid)
    stmt = select(L)
    if f.window_start:
        stmt = stmt.where(L.ts >= f.window_start)
    if f.window_end:
        stmt = stmt.where(L.ts <= f.window_end)
    if f.finding_type == "ids_alert":
        stmt = stmt.where(L.log_type == "ids", L.signature == f.evidence.get("signature"))
    elif f.finding_type == "unusual_port":
        stmt = stmt.where(L.dst_port == f.dst_port, L.direction == "outbound")
        if f.proto:
            stmt = stmt.where(L.proto == f.proto)
    else:
        if f.src_ip:
            stmt = stmt.where(L.src_ip == f.src_ip)
        if f.finding_type == "beaconing":
            stmt = stmt.where(L.dst_ip == f.dst_ip, L.dst_port == f.dst_port)
    from app.api.routers.logs import SORT as LSORT
    page = paginate(db, stmt, pp, LSORT, "-ts")
    page["items"] = log_out(db, page["items"])
    return page
