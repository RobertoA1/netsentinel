"""Esquema inicial de NetSentinel.

Las tablas se crean desde los metadatos de los modelos (fuente única de verdad del esquema en esta
versión inicial); después se añaden los objetos específicos de PostgreSQL: el trigger que hace la
bitácora de solo inserción.

Revision ID: 0001
Revises:
"""
from alembic import op

import app.models  # noqa: F401
from app.db.base import Base

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

AUDIT_GUARD = """
CREATE OR REPLACE FUNCTION audit_events_guard() RETURNS trigger AS $$
BEGIN
  IF TG_OP = 'UPDATE' THEN
    RAISE EXCEPTION 'La bitácora de auditoría es de solo inserción (UPDATE no permitido)';
  END IF;
  IF TG_OP = 'DELETE' AND COALESCE(current_setting('netsentinel.audit_purge', true), 'off') <> 'on' THEN
    RAISE EXCEPTION 'La bitácora de auditoría solo se purga mediante la política de retención';
  END IF;
  RETURN OLD;
END;
$$ LANGUAGE plpgsql;
"""


def upgrade() -> None:
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)
    if bind.dialect.name == "postgresql":
        op.execute(AUDIT_GUARD)
        op.execute("CREATE TRIGGER audit_events_no_update BEFORE UPDATE ON audit_events "
                   "FOR EACH ROW EXECUTE FUNCTION audit_events_guard()")
        op.execute("CREATE TRIGGER audit_events_no_delete BEFORE DELETE ON audit_events "
                   "FOR EACH ROW EXECUTE FUNCTION audit_events_guard()")


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("DROP TRIGGER IF EXISTS audit_events_no_delete ON audit_events")
        op.execute("DROP TRIGGER IF EXISTS audit_events_no_update ON audit_events")
        op.execute("DROP FUNCTION IF EXISTS audit_events_guard()")
    Base.metadata.drop_all(bind=bind)
