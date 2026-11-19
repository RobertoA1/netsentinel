from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import AuditCtx, Principal, audited, require
from app.core.pagination import PageParams, page_params, paginate
from app.db.session import get_db
from app.models import ReportHistory
from app.schemas.common import ORM, Page, ReportFormat
from app.services.reports import service
from app.services.reports.builders import REPORTS

router = APIRouter(prefix="/reports", tags=["reports"])


class ReportIn(BaseModel):
    report_code: str
    format: ReportFormat
    date_from: datetime
    date_to: datetime
    params: dict = {}  # reportes ML: dataset_version_id | job_id | model_id


class ReportHistoryOut(ORM):
    id: int
    report_code: str
    report_name: str
    format: str
    date_from: datetime
    date_to: datetime
    generated_by: str
    generated_at: datetime
    size_bytes: int


def _allowed(p: Principal, rdef) -> bool:
    return p.is_api_key or any(x in p.permissions for x in rdef.requires)


@router.get("/catalog")
def catalog(p: Principal = Depends(require("reports:view"))):
    """Solo los reportes cuyos datos puede consultar el usuario (gestión: cualquiera con reports:view)."""
    return [{"code": r.code, "name": r.name, "description": r.description, "category": r.category,
             "formats": ["pdf", "docx", "xlsx"], "params": list(r.params)} for r in REPORTS.values() if _allowed(p, r)]


@router.post("/generate")
def generate(body: ReportIn, db: Session = Depends(get_db), p: Principal = Depends(require("reports:export")),
             audit: AuditCtx = Depends(audited("export", "reports", "report"))):
    rdef = REPORTS.get(body.report_code)
    if rdef is None:
        raise HTTPException(404, "Código de reporte desconocido")
    if not _allowed(p, rdef):
        raise HTTPException(403, "No tiene permiso para los datos de este reporte")
    pf = body.date_from if body.date_from.tzinfo else body.date_from.replace(tzinfo=timezone.utc)
    pt = body.date_to if body.date_to.tzinfo else body.date_to.replace(tzinfo=timezone.utc)
    if pt == pt.replace(hour=0, minute=0, second=0, microsecond=0):
        pt = pt + timedelta(days=1) - timedelta(seconds=1)  # fecha sin hora: incluye todo el día
    if pt <= pf:
        raise HTTPException(422, "date_to debe ser posterior a date_from")
    if pt - pf > timedelta(days=400):
        raise HTTPException(422, "El período máximo es de 400 días")
    content, mime, fname, h = service.generate(db, rdef, body.format, pf, pt, p.display_name, p.user_id,
                                              {k: v for k, v in body.params.items() if k in ('dataset_version_id', 'job_id', 'model_id')})
    audit.set(h.id, f"Reporte generado: {rdef.name} ({body.format})",
              {"report_code": rdef.code, "format": body.format, "size_bytes": len(content),
               "date_from": pf.isoformat(), "date_to": pt.isoformat(), "params": body.params if rdef.category == "ml" else None})
    return Response(content=content, media_type=mime,
                    headers={"Content-Disposition": f'attachment; filename="{fname}"',
                             "Access-Control-Expose-Headers": "Content-Disposition"})


@router.get("/history", response_model=Page[ReportHistoryOut])
def history(pp: PageParams = Depends(page_params), db: Session = Depends(get_db), _=Depends(require("reports:view"))):
    return paginate(db, select(ReportHistory), pp, {"id": ReportHistory.id, "generated_at": ReportHistory.generated_at,
                                                    "report_code": ReportHistory.report_code}, "-generated_at")
