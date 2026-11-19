from __future__ import annotations

from typing import TypeVar

from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.base import utcnow
from app.models import AppSetting
from app.schemas.settings import DetectionSettings, LLMSettings, RetentionSettings

T = TypeVar("T", bound=BaseModel)

_MODELS = {"detection": DetectionSettings, "llm": LLMSettings, "retention": RetentionSettings}


def default_for(key: str) -> BaseModel:
    s = get_settings()
    if key == "llm":
        return LLMSettings(base_url=s.ollama_base_url, model=s.ollama_model,
                           max_findings_per_run=s.llm_max_findings_per_run)
    return _MODELS[key]()


def get_setting(db: Session, key: str):
    row = db.get(AppSetting, key)
    base = default_for(key)
    if row is None:
        return base
    merged = {**base.model_dump(), **(row.value or {})}
    return _MODELS[key].model_validate(merged)


def put_setting(db: Session, key: str, value: BaseModel, commit: bool = True):
    row = db.get(AppSetting, key)
    data = value.model_dump()
    if row is None:
        db.add(AppSetting(key=key, value=data, updated_at=utcnow()))
    else:
        row.value = data
        row.updated_at = utcnow()
    if commit:
        db.commit()
    return value


def ensure_defaults(db: Session) -> None:
    for key in _MODELS:
        if db.get(AppSetting, key) is None:
            put_setting(db, key, default_for(key), commit=False)
    db.commit()
