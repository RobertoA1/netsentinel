from __future__ import annotations

from datetime import datetime
from typing import Any

from app.services.reports.model import ReportData


def fmt_dt(d: datetime | None) -> str:
    return d.strftime("%Y-%m-%d %H:%M UTC") if d else ""


def period_text(data: ReportData) -> str:
    return f"{data.period_from.strftime('%Y-%m-%d %H:%M')} a {data.period_to.strftime('%Y-%m-%d %H:%M')} UTC"


def cell_text(v: Any, decimals: int | None = None) -> str:
    if v is None:
        return ""
    if isinstance(v, datetime):
        return v.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(v, float):
        return f"{v:,.{2 if decimals is None else decimals}f}"
    if isinstance(v, int) and not isinstance(v, bool):
        return f"{v:,}"
    return str(v)


def human_bytes(n: float) -> str:
    n = float(n or 0)
    for u in ("B", "KB", "MB", "GB", "TB"):
        if abs(n) < 1024 or u == "TB":
            return f"{int(n)} B" if u == "B" else f"{n:.1f} {u}"
        n /= 1024
    return str(n)


def human_duration(seconds: float | None) -> str:
    if seconds is None:
        return "n/d"
    s = int(seconds)
    h, rem = divmod(s, 3600)
    m, sec = divmod(rem, 60)
    return f"{h} h {m} min" if h else (f"{m} min {sec} s" if m else f"{sec} s")
