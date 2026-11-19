from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app import __version__
from app.core.deps import AuditCtx, audited, require_admin_or_key
from app.db.session import get_db
from app.services import maintenance, settings_service
from app.services.llm.health import ollama_reachable

router = APIRouter(tags=["system"])


@router.get("/health")
def health(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False
    llm_ok = False
    if db_ok:
        try:
            llm_ok = ollama_reachable(settings_service.get_setting(db, "llm"))
        except Exception:
            llm_ok = False
    return {"status": "ok" if db_ok else "degraded", "db": db_ok, "llm": llm_ok, "version": __version__}


@router.post("/maintenance/purge")
def purge(db: Session = Depends(get_db), _=Depends(require_admin_or_key()),
          audit: AuditCtx = Depends(audited("execute", "audit", "maintenance"))):
    res = maintenance.purge(db)
    audit.set(None, "Purga de retención ejecutada", res)
    return res
