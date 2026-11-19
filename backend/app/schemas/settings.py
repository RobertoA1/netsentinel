from __future__ import annotations

from pydantic import BaseModel, Field

from app.core.ports import DEFAULT_COMMON_PORTS


class DetectionSettings(BaseModel):
    beacon_min_connections: int = Field(10, ge=3)
    beacon_max_cv: float = Field(0.25, gt=0, le=2)
    beacon_min_score: float = Field(60, ge=0, le=100)
    exfil_zscore: float = Field(3.0, gt=0)
    exfil_min_bytes: int = Field(52428800, ge=0)
    common_ports: list[int] = Field(default_factory=lambda: list(DEFAULT_COMMON_PORTS))
    unusual_port_min_connections: int = Field(3, ge=1)
    internal_cidrs: list[str] = Field(default_factory=lambda: ["10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"])
    detection_window_hours: int = Field(24, ge=1, le=720)


class LLMSettings(BaseModel):
    enabled: bool = True
    base_url: str = "http://ollama:11434"
    model: str = "llama3.2:3b"
    temperature: float = Field(0.1, ge=0, le=2)
    timeout_seconds: int = Field(60, ge=1, le=600)
    noise_confidence_threshold: float = Field(0.7, ge=0, le=1)
    max_findings_per_run: int = Field(30, ge=0, le=1000)


class RetentionSettings(BaseModel):
    logs_days: int = Field(90, ge=1)
    findings_days: int = Field(365, ge=1)
    audit_days: int = Field(730, ge=1)


class LLMTestOut(BaseModel):
    ok: bool
    model: str
    latency_ms: int
    message: str
