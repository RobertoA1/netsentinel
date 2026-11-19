from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.base import utcnow
from app.models import ReportHistory
from app.services.reports.builders import REPORTS, ReportDef
from app.services.reports.model import ReportData, ReportMeta
from app.services.reports.render_docx import render_docx
from app.services.reports.render_pdf import render_pdf
from app.services.reports.render_xlsx import render_xlsx

RENDERERS = {"pdf": (render_pdf, "application/pdf"),
             "docx": (render_docx, "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
             "xlsx": (render_xlsx, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}


def generate(db: Session, rdef: ReportDef, fmt: str, pf: datetime, pt: datetime, generated_by: str,
             generated_by_id: int | None, params: dict | None = None) -> tuple[bytes, str, str, ReportHistory]:
    data: ReportData = rdef.builder(db, pf, pt, params or {}) if (rdef.params or rdef.category == "ml") else rdef.builder(db, pf, pt)
    meta = ReportMeta(generated_by=generated_by, generated_at=utcnow())
    render, mime = RENDERERS[fmt]
    content = render(data, meta)
    fname = f"netsentinel_{rdef.code}_{pf:%Y%m%d}_{pt:%Y%m%d}.{fmt}"
    path = None
    try:
        d = Path(get_settings().reports_dir)
        d.mkdir(parents=True, exist_ok=True)
        stamp = meta.generated_at.strftime("%Y%m%dT%H%M%S")
        path = d / f"{stamp}_{re.sub(r'[^A-Za-z0-9_.-]', '_', fname)}"
        path.write_bytes(content)
    except OSError:
        path = None  # el historial se guarda igual; el archivo se sirve en la respuesta
    h = ReportHistory(report_code=rdef.code, report_name=rdef.name, format=fmt, date_from=pf, date_to=pt,
                      generated_by=generated_by, generated_by_id=generated_by_id, generated_at=meta.generated_at,
                      size_bytes=len(content), file_path=str(path) if path else None)
    db.add(h)
    db.commit()
    return content, mime, fname, h
