from __future__ import annotations

import ipaddress

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import AuditCtx, audited, require
from app.db.session import get_db
from app.schemas.settings import DetectionSettings, LLMSettings, LLMTestOut, RetentionSettings
from app.services import settings_service
from app.services.llm.health import test_llm

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/detection", response_model=DetectionSettings)
def get_detection(db: Session = Depends(get_db), _=Depends(require("detection:view"))):
    return settings_service.get_setting(db, "detection")


@router.put("/detection", response_model=DetectionSettings)
def put_detection(body: DetectionSettings, db: Session = Depends(get_db), _=Depends(require("detection:update")),
                  audit: AuditCtx = Depends(audited("update", "detection", "settings_detection"))):
    for c in body.internal_cidrs:
        try:
            ipaddress.ip_network(c, strict=False)
        except ValueError:
            raise HTTPException(422, f"CIDR inválido: {c}")
    if any(not 0 < p < 65536 for p in body.common_ports):
        raise HTTPException(422, "Puertos comunes fuera de rango")
    settings_service.put_setting(db, "detection", body)
    audit.set("detection", "Configuración de detección actualizada", body.model_dump())
    return body


@router.get("/llm", response_model=LLMSettings)
def get_llm(db: Session = Depends(get_db), _=Depends(require("llm:view"))):
    return settings_service.get_setting(db, "llm")


@router.put("/llm", response_model=LLMSettings)
def put_llm(body: LLMSettings, db: Session = Depends(get_db), _=Depends(require("llm:update")),
            audit: AuditCtx = Depends(audited("update", "llm", "settings_llm"))):
    if not body.base_url.startswith(("http://", "https://")):
        raise HTTPException(422, "base_url debe comenzar con http:// o https://")
    settings_service.put_setting(db, "llm", body)
    audit.set("llm", "Configuración del LLM actualizada", body.model_dump())
    return body


@router.post("/llm/test", response_model=LLMTestOut)
def llm_test(db: Session = Depends(get_db), _=Depends(require("llm:execute", "llm:update")),
             audit: AuditCtx = Depends(audited("execute", "llm", "settings_llm"))):
    res = test_llm(settings_service.get_setting(db, "llm"))
    audit.set("llm", "Prueba de conexión con el LLM", {"ok": res["ok"]})
    return res


@router.get("/retention", response_model=RetentionSettings)
def get_retention(db: Session = Depends(get_db), _=Depends(require("detection:view"))):
    return settings_service.get_setting(db, "retention")


@router.put("/retention", response_model=RetentionSettings)
def put_retention(body: RetentionSettings, db: Session = Depends(get_db), _=Depends(require("detection:update")),
                  audit: AuditCtx = Depends(audited("update", "detection", "settings_retention"))):
    settings_service.put_setting(db, "retention", body)
    audit.set("retention", "Política de retención actualizada", body.model_dump())
    return body
