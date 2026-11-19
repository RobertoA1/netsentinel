"""Funciones SQL portables (PostgreSQL en producción; SQLite solo para pruebas unitarias)."""
from __future__ import annotations

from sqlalchemy.ext.compiler import compiles
from sqlalchemy.sql.expression import FunctionElement

from app.db.base import UTCDateTime


class epoch_bucket(FunctionElement):
    """Trunca un timestamp al múltiplo de `secs` segundos (UTC)."""

    type = UTCDateTime()
    inherit_cache = False
    name = "epoch_bucket"

    def __init__(self, col, secs: int):
        self.secs = int(secs)
        super().__init__(col)


@compiles(epoch_bucket, "postgresql")
def _pg_bucket(el, compiler, **kw):
    col = compiler.process(list(el.clauses)[0], **kw)
    return f"to_timestamp(floor(extract(epoch from {col}) / {el.secs}) * {el.secs})"


@compiles(epoch_bucket, "sqlite")
def _sqlite_bucket(el, compiler, **kw):
    col = compiler.process(list(el.clauses)[0], **kw)
    return f"datetime((CAST(strftime('%s', {col}) AS INTEGER) / {el.secs}) * {el.secs}, 'unixepoch')"


class bucket_index(FunctionElement):
    """Índice (entero) del cubo de `secs` segundos hacia atrás desde `ref_epoch`."""

    inherit_cache = False
    name = "bucket_index"

    def __init__(self, ref_epoch: int, col, secs: int):
        self.ref_epoch, self.secs = int(ref_epoch), int(secs)
        super().__init__(col)


@compiles(bucket_index, "postgresql")
def _pg_idx(el, compiler, **kw):
    col = compiler.process(list(el.clauses)[0], **kw)
    return f"floor(({el.ref_epoch} - extract(epoch from {col})) / {el.secs})"


@compiles(bucket_index, "sqlite")
def _sqlite_idx(el, compiler, **kw):
    col = compiler.process(list(el.clauses)[0], **kw)
    return f"(({el.ref_epoch} - CAST(strftime('%s', {col}) AS INTEGER)) / {el.secs})"
