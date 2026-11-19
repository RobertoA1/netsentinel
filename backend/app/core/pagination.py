from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from fastapi import Query
from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session


@dataclass
class PageParams:
    page: int
    page_size: int
    sort: str | None


def page_params(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=500),
    sort: str | None = Query(None, description="Campo; prefijo '-' para descendente"),
) -> PageParams:
    return PageParams(page, page_size, sort)


def paginate(db: Session, stmt: Select, pp: PageParams, sort_fields: dict[str, Any], default_sort: str,
             scalars: bool = True) -> dict:
    """Aplica orden y paginación. `sort_fields` mapea nombre público -> columna."""
    sort = pp.sort or default_sort
    desc = sort.startswith("-")
    key = sort.lstrip("-+")
    col = sort_fields.get(key)
    if col is None:
        dkey = default_sort.lstrip("-+")
        col = sort_fields[dkey]
        desc = default_sort.startswith("-")
    total = db.execute(select(func.count()).select_from(stmt.order_by(None).subquery())).scalar_one()
    ordered = stmt.order_by(col.desc() if desc else col.asc())
    # desempate estable
    first_col = next(iter(sort_fields.values()))
    if first_col is not col:
        ordered = ordered.order_by(first_col.desc() if desc else first_col.asc())
    ordered = ordered.limit(pp.page_size).offset((pp.page - 1) * pp.page_size)
    res = db.execute(ordered)
    items = list(res.scalars().unique()) if scalars else list(res.all())
    return {"items": items, "total": total, "page": pp.page, "page_size": pp.page_size}
