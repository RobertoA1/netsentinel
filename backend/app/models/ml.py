"""Modelos del Laboratorio ML: datasets versionados, trabajos, ejecuciones, pliegues, modelos y predicciones."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, BigPK, JSONType, UTCDateTime, utcnow


class MlDataset(Base):
    __tablename__ = "ml_datasets"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(128), unique=True)
    origin: Mapped[str] = mapped_column(String(16), default="source")  # source | upload
    source_id: Mapped[int | None] = mapped_column(ForeignKey("sources.id", ondelete="SET NULL"), nullable=True)
    snapshot_path: Mapped[str] = mapped_column(String(1024))
    snapshot_sha256: Mapped[str] = mapped_column(String(64))
    n_rows: Mapped[int] = mapped_column(Integer, default=0)
    n_duplicates_dropped: Mapped[int] = mapped_column(Integer, default=0)
    current_version: Mapped[int] = mapped_column(Integer, default=1)
    created_by: Mapped[str] = mapped_column(String(64), default="")
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)


class MlDatasetVersion(Base):
    """Versión INMUTABLE de los metadatos/configuración. Un entrenamiento referencia una de estas filas."""

    __tablename__ = "ml_dataset_versions"
    __table_args__ = (UniqueConstraint("dataset_id", "version", name="uq_ml_dsv"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("ml_datasets.id", ondelete="CASCADE"), index=True)
    version: Mapped[int] = mapped_column(Integer)
    meta: Mapped[dict] = mapped_column(JSONType, default=dict)
    content_hash: Mapped[str] = mapped_column(String(64))
    change_note: Mapped[str] = mapped_column(String(500), default="")
    created_by: Mapped[str] = mapped_column(String(64), default="")
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)


class MlJob(Base):
    __tablename__ = "ml_jobs"
    __table_args__ = (Index("ix_ml_jobs_status", "status"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    kind: Mapped[str] = mapped_column(String(16))  # train | evaluate | explain | optimize
    status: Mapped[str] = mapped_column(String(20), default="queued")
    name: Mapped[str] = mapped_column(String(160), default="")
    params: Mapped[dict] = mapped_column(JSONType, default=dict)
    progress: Mapped[dict] = mapped_column(JSONType, default=dict)
    result: Mapped[dict] = mapped_column(JSONType, default=dict)
    log: Mapped[str] = mapped_column(Text, default="")
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    seed: Mapped[int] = mapped_column(Integer, default=42)
    time_limit_s: Mapped[int] = mapped_column(Integer, default=7200)
    libs: Mapped[dict] = mapped_column(JSONType, default=dict)
    resources: Mapped[dict] = mapped_column(JSONType, default=dict)
    dataset_version_id: Mapped[int | None] = mapped_column(ForeignKey("ml_dataset_versions.id", ondelete="SET NULL"),
                                                           nullable=True)
    created_by: Mapped[str] = mapped_column(String(64), default="")
    created_by_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)
    started_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    heartbeat_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    pid: Mapped[int | None] = mapped_column(Integer, nullable=True)


class MlRun(Base):
    """Una ejecución = un modelo dentro de un trabajo de entrenamiento (todas comparten partición y pliegues)."""

    __tablename__ = "ml_runs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("ml_jobs.id", ondelete="CASCADE"), index=True)
    dataset_version_id: Mapped[int | None] = mapped_column(ForeignKey("ml_dataset_versions.id", ondelete="SET NULL"),
                                                           nullable=True, index=True)
    model_type: Mapped[str] = mapped_column(String(24))
    status: Mapped[str] = mapped_column(String(16), default="pending")
    config: Mapped[dict] = mapped_column(JSONType, default=dict)
    summary: Mapped[dict] = mapped_column(JSONType, default=dict)
    final_params: Mapped[dict] = mapped_column(JSONType, default=dict)
    val_metrics: Mapped[dict] = mapped_column(JSONType, default=dict)
    test_metrics: Mapped[dict] = mapped_column(JSONType, default=dict)
    artifact_dir: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    duration_s: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)


class MlFoldResult(Base):
    __tablename__ = "ml_fold_results"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("ml_runs.id", ondelete="CASCADE"), index=True)
    outer_fold: Mapped[int] = mapped_column(Integer)
    best_params: Mapped[dict] = mapped_column(JSONType, default=dict)
    inner_best_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    outer_metrics: Mapped[dict] = mapped_column(JSONType, default=dict)
    n_trials: Mapped[int] = mapped_column(Integer, default=0)
    n_pruned: Mapped[int] = mapped_column(Integer, default=0)
    duration_s: Mapped[float | None] = mapped_column(Float, nullable=True)
    curve: Mapped[list] = mapped_column(JSONType, default=list)
    sizes: Mapped[dict] = mapped_column(JSONType, default=dict)


class MlModel(Base):
    __tablename__ = "ml_models"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("ml_runs.id", ondelete="CASCADE"), unique=True)
    dataset_version_id: Mapped[int | None] = mapped_column(ForeignKey("ml_dataset_versions.id", ondelete="SET NULL"),
                                                           nullable=True)
    name: Mapped[str] = mapped_column(String(128))
    model_type: Mapped[str] = mapped_column(String(24))
    unit: Mapped[str] = mapped_column(String(16), default="flow")
    window_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    model_path: Mapped[str] = mapped_column(String(1024))
    sha256: Mapped[str] = mapped_column(String(64))
    threshold: Mapped[float] = mapped_column(Float, default=0.5)
    calibration_method: Mapped[str] = mapped_column(String(16), default="sigmoid")
    feature_spec_version: Mapped[str] = mapped_column(String(16), default="1.0.0")
    metrics: Mapped[dict] = mapped_column(JSONType, default=dict)
    uncertainty: Mapped[dict] = mapped_column(JSONType, default=dict)
    is_baseline: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    promoted_by: Mapped[str | None] = mapped_column(String(64), nullable=True)
    promoted_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)


class MlPrediction(Base):
    __tablename__ = "ml_predictions"
    __table_args__ = (Index("ix_ml_predictions_ts", "ts"),)
    id: Mapped[int] = mapped_column(BigPK, primary_key=True, autoincrement=True)
    ts: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)
    model_id: Mapped[int] = mapped_column(ForeignKey("ml_models.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    username: Mapped[str] = mapped_column(String(64), default="")
    input_kind: Mapped[str] = mapped_column(String(16))  # flow | window | finding | manual
    input_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    finding_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    features: Mapped[dict] = mapped_column(JSONType, default=dict)
    probability: Mapped[float] = mapped_column(Float)
    interval_low: Mapped[float | None] = mapped_column(Float, nullable=True)
    interval_high: Mapped[float | None] = mapped_column(Float, nullable=True)
    predicted_class: Mapped[str] = mapped_column(String(16))
    severity: Mapped[str] = mapped_column(String(12))
    detail: Mapped[dict] = mapped_column(JSONType, default=dict)  # severidad paso a paso, OOD, conjunto conforme, SHAP
    narrative: Mapped[str] = mapped_column(Text, default="")
    narrative_source: Mapped[str] = mapped_column(String(16), default="template")
