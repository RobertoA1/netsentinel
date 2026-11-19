"""Modelo de datos común de los reportes (los renderizadores lo convierten a pdf/docx/xlsx)."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

SYSTEM_NAME = "NetSentinel"
MAX_TABLE_ROWS_DOC = 300  # filas máximas en PDF/Word (Excel lleva todas)


@dataclass
class Kpi:
    label: str
    value: str


@dataclass
class Table:
    title: str
    columns: list[str]
    rows: list[list[Any]]
    total_rows: int | None = None  # si las filas fueron recortadas por el builder
    decimals: int | None = None  # decimales de los números (reportes ML: 3)
    note: str = ""  # definiciones, n y unidades (reportes ML)
    meaning: list[str] = field(default_factory=list)  # «Cómo leerlo / qué significa»
    caution: list[str] = field(default_factory=list)  # «Precaución»


@dataclass
class Chart:
    title: str
    kind: str  # bar | hbar | line | pie
    labels: list[str]
    series: dict[str, list[float]]
    ylabel: str = ""
    spec: dict | None = None  # especificación de figura ML (se dibuja con ml.figures)
    note: str = ""
    meaning: list[str] = field(default_factory=list)
    caution: list[str] = field(default_factory=list)


@dataclass
class ReportData:
    code: str
    name: str
    category: str
    period_from: datetime
    period_to: datetime
    summary: str
    kpis: list[Kpi] = field(default_factory=list)
    tables: list[Table] = field(default_factory=list)
    charts: list[Chart] = field(default_factory=list)
    blocks: list[Any] = field(default_factory=list)  # si no está vacío: figuras y tablas en este orden


@dataclass
class ReportMeta:
    generated_by: str
    generated_at: datetime
