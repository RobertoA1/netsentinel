from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Literal

from fastapi import Query

RANGES = {"1h": timedelta(hours=1), "24h": timedelta(hours=24), "7d": timedelta(days=7), "30d": timedelta(days=30)}


@dataclass
class TimeRange:
    start: datetime | None
    end: datetime

    @property
    def span(self) -> timedelta:
        return (self.end - self.start) if self.start else timedelta(hours=24)

    def previous(self) -> "TimeRange":
        s = self.start or (self.end - self.span)
        return TimeRange(s - self.span, s)


def _aware(d: datetime | None) -> datetime | None:
    if d is None:
        return None
    return d.replace(tzinfo=timezone.utc) if d.tzinfo is None else d.astimezone(timezone.utc)


def resolve_range(range_: str | None, date_from: datetime | None, date_to: datetime | None,
                  default: str | None) -> TimeRange:
    now = datetime.now(timezone.utc)
    date_from, date_to = _aware(date_from), _aware(date_to)
    if date_from or date_to:
        return TimeRange(date_from, date_to or now)
    key = range_ or default
    if key is None:
        return TimeRange(None, now)
    return TimeRange(now - RANGES[key], now)


def dashboard_range(
    range: Literal["1h", "24h", "7d", "30d"] | None = Query(None),
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
) -> TimeRange:
    return resolve_range(range, date_from, date_to, "24h")


def list_range(
    range: Literal["1h", "24h", "7d", "30d"] | None = Query(None),
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
) -> TimeRange:
    """Para listados: sin parámetros no se filtra por tiempo."""
    return resolve_range(range, date_from, date_to, None)
