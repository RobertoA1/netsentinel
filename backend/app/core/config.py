"""Configuración de la aplicación (variables de entorno)."""
from __future__ import annotations

from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class ConfigError(RuntimeError):
    """Configuración obligatoria ausente o inválida."""


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    database_url: str = "postgresql+psycopg://netsentinel:netsentinel@db:5432/netsentinel"
    jwt_secret: str = ""
    n8n_api_key: str = ""
    admin_username: str = "admin"
    admin_password: str = ""
    admin_email: str = "admin@netsentinel.local"
    ollama_base_url: str = "http://ollama:11434"
    ollama_model: str = "llama3.2:3b"
    ingest_dir: str = "/data/ingest"
    dataset_dir: str = "/data/dataset"
    reports_dir: str = "/data/reports"
    ml_dir: str = "/data/ml"
    ml_n_jobs: int = 4
    ml_worker_poll_seconds: float = 3.0
    ml_max_upload_mb: int = 100
    ml_job_time_limit_seconds: int = 7200
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    llm_max_findings_per_run: int = 30
    access_token_minutes: int = 30
    refresh_token_days: int = 7
    max_failed_logins: int = 5
    lockout_minutes: int = 15
    module_session_timeout_minutes: int = 30

    @field_validator("database_url")
    @classmethod
    def _normalize_db_url(cls, v: str) -> str:
        if v.startswith("postgres://"):
            v = "postgresql://" + v[len("postgres://"):]
        if v.startswith("postgresql://"):
            v = "postgresql+psycopg://" + v[len("postgresql://"):]
        return v

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    def require_secrets(self) -> None:
        missing = []
        if not self.jwt_secret:
            missing.append("JWT_SECRET")
        if not self.admin_password:
            missing.append("ADMIN_PASSWORD")
        if missing:
            raise ConfigError(
                "Configuración incompleta: falta definir la(s) variable(s) de entorno "
                + ", ".join(missing)
                + ". NetSentinel no arranca sin secretos explícitos."
            )


@lru_cache
def get_settings() -> Settings:
    return Settings()


def get_strict_settings() -> Settings:
    s = get_settings()
    s.require_secrets()
    return s
