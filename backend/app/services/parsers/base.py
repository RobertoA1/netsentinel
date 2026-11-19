"""Infraestructura común de parsers y clasificación de dirección."""
from __future__ import annotations

import ipaddress
from datetime import datetime, timezone
from functools import lru_cache
from typing import Any, Iterable, Iterator


class ParseError(ValueError):
    """Línea malformada (se cuenta en parse_errors y se continúa)."""


class DirectionClassifier:
    """Calcula outbound/inbound/internal a partir de internal_cidrs."""

    def __init__(self, cidrs: Iterable[str]):
        self.nets = []
        for c in cidrs:
            try:
                self.nets.append(ipaddress.ip_network(c.strip(), strict=False))
            except ValueError:
                continue
        self._is_internal = lru_cache(maxsize=200_000)(self._internal)

    def _internal(self, ip: str) -> bool:
        try:
            a = ipaddress.ip_address(ip)
        except ValueError:
            return False
        return any(a.version == n.version and a in n for n in self.nets)

    def classify(self, src_ip: str, dst_ip: str) -> str:
        s, d = self._is_internal(src_ip), self._is_internal(dst_ip)
        if s and d:
            return "internal"
        if s:
            return "outbound"
        if d:
            return "inbound"
        # Ninguna IP pertenece a las redes internas configuradas: se trata como tráfico que
        # atraviesa el perímetro hacia fuera (típico de flujos capturados en el borde).
        return "outbound"


def valid_ip(value: str) -> str:
    try:
        return str(ipaddress.ip_address(value.strip()))
    except ValueError as e:
        raise ParseError(f"IP inválida: {value!r}") from e


def to_int(value: Any) -> int | None:
    if value is None:
        return None
    s = str(value).strip()
    if s == "" or s.lower() in ("none", "null", "nan"):
        return None
    try:
        if s.lower().startswith("0x"):
            return int(s, 16)
        return int(float(s))
    except ValueError as e:
        raise ParseError(f"Entero inválido: {value!r}") from e


def to_port(value: Any) -> int | None:
    p = to_int(value)
    if p is None:
        return None
    if not 0 <= p <= 65535:
        raise ParseError(f"Puerto fuera de rango: {p}")
    return p


def to_float(value: Any) -> float | None:
    if value is None or str(value).strip() == "":
        return None
    try:
        return float(value)
    except ValueError as e:
        raise ParseError(f"Número inválido: {value!r}") from e


def make_log(**kw: Any) -> dict:
    base = {
        "log_type": "flow", "action": "pass", "proto": None, "src_port": None, "dst_port": None,
        "bytes_out": 0, "bytes_in": 0, "packets": None, "duration": None, "signature": None,
        "signature_id": None, "category": None, "ids_severity": None, "label": None, "raw": {},
    }
    base.update(kw)
    return base


class LineParser:
    """Interfaz: parse_line devuelve dict (log), None (línea ignorada) o lanza ParseError."""

    name = ""

    def parse_line(self, line: str) -> dict | None:  # pragma: no cover - interfaz
        raise NotImplementedError


class ParseStats:
    def __init__(self) -> None:
        self.lines_read = 0
        self.parse_errors = 0
        self.ignored = 0
        self.error_samples: list[str] = []


def parse_stream(parser: LineParser, lines: Iterable[str], stats: ParseStats) -> Iterator[dict]:
    for line in lines:
        line = line.rstrip("\r\n")
        if not line.strip():
            continue
        stats.lines_read += 1
        try:
            rec = parser.parse_line(line)
        except ParseError as e:
            stats.parse_errors += 1
            if len(stats.error_samples) < 5:
                stats.error_samples.append(f"{e}: {line[:120]}")
            continue
        except Exception as e:  # cualquier fallo inesperado de una línea no aborta la ingesta
            stats.parse_errors += 1
            if len(stats.error_samples) < 5:
                stats.error_samples.append(f"{type(e).__name__}: {line[:120]}")
            continue
        if rec is None:
            stats.ignored += 1
            continue
        yield rec


def utc(dt: datetime) -> datetime:
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)
