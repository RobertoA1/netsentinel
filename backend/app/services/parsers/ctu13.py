"""Parser del dataset CTU-13 (binetflow). Se asume UTC en StartTime."""
from __future__ import annotations

from datetime import datetime, timezone

from app.services.parsers.base import (LineParser, ParseError, make_log, to_float, to_int, to_port, valid_ip)

DEFAULT_COLUMNS = ["StartTime", "Dur", "Proto", "SrcAddr", "Sport", "Dir", "DstAddr", "Dport", "State",
                   "sTos", "dTos", "TotPkts", "TotBytes", "SrcBytes", "Label"]
REQUIRED = {"StartTime", "Proto", "SrcAddr", "DstAddr", "TotBytes", "SrcBytes"}


def parse_start_time(s: str) -> datetime:
    s = s.strip()
    for fmt in ("%Y/%m/%d %H:%M:%S.%f", "%Y/%m/%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(s, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    raise ParseError(f"StartTime inválido: {s!r}")


class Ctu13Parser(LineParser):
    name = "ctu13_binetflow"

    def __init__(self) -> None:
        self.cols = {c: i for i, c in enumerate(DEFAULT_COLUMNS)}

    def parse_line(self, line: str) -> dict | None:
        parts = line.split(",")
        if parts[0].strip() == "StartTime":  # cabecera: define el orden de columnas
            cols = {c.strip(): i for i, c in enumerate(parts)}
            missing = REQUIRED - set(cols)
            if missing:
                raise ParseError("Cabecera binetflow sin columnas: " + ", ".join(sorted(missing)))
            self.cols = cols
            return None
        c = self.cols

        def get(name: str) -> str:
            i = c.get(name)
            return parts[i].strip() if i is not None and i < len(parts) else ""

        if len(parts) < max(c[k] for k in REQUIRED) + 1:
            raise ParseError("Fila con columnas insuficientes")
        proto = get("Proto").lower()
        if proto in ("arp", "rarp"):
            return None  # sin direcciones IP (MAC): no aplica
        src, dst = valid_ip(get("SrcAddr")), valid_ip(get("DstAddr"))
        total, srcb = to_int(get("TotBytes")) or 0, to_int(get("SrcBytes")) or 0
        if total < 0 or srcb < 0:
            raise ParseError("Bytes negativos")
        out = min(srcb, total)
        label = get("Label") or None
        state = get("State")
        return make_log(
            ts=parse_start_time(get("StartTime")), log_type="flow", action="pass", proto=proto or None,
            src_ip=src, src_port=to_port(get("Sport")), dst_ip=dst, dst_port=to_port(get("Dport")),
            bytes_out=out, bytes_in=total - out, packets=to_int(get("TotPkts")), duration=to_float(get("Dur")),
            label=label[:255] if label else None, raw={"state": state, "dir": get("Dir")},
        )


def quick_start_time(line: str) -> datetime | None:
    """Lectura barata del StartTime (para calcular el desplazamiento de rebase)."""
    first = line.split(",", 1)[0]
    if not first or first.strip() == "StartTime":
        return None
    try:
        return parse_start_time(first)
    except ParseError:
        return None
