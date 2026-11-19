"""Laboratorio ML: datasets versionados, trabajos, ejecuciones, pliegues, modelos y predicciones.

No modifica 0001. Crea solo las tablas ML (checkfirst) y, en PostgreSQL, el esquema `optuna`
donde Optuna guarda sus estudios (almacenamiento RDB) sin mezclar tablas con las de la aplicación.

Revision ID: 0002
Revises: 0001
"""
from alembic import op

import app.models  # noqa: F401
from app.db.base import Base

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

ML_TABLES = ["ml_datasets", "ml_dataset_versions", "ml_jobs", "ml_runs", "ml_fold_results", "ml_models",
             "ml_predictions"]


def upgrade() -> None:
    bind = op.get_bind()
    tables = [Base.metadata.tables[t] for t in ML_TABLES]
    Base.metadata.create_all(bind=bind, tables=tables, checkfirst=True)
    if bind.dialect.name == "postgresql":
        op.execute("CREATE SCHEMA IF NOT EXISTS optuna")


def downgrade() -> None:
    bind = op.get_bind()
    tables = [Base.metadata.tables[t] for t in reversed(ML_TABLES)]
    Base.metadata.drop_all(bind=bind, tables=tables, checkfirst=True)
    if bind.dialect.name == "postgresql":
        op.execute("DROP SCHEMA IF EXISTS optuna CASCADE")
