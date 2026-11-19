"""Parser de líneas syslog `filterlog` de OPNsense/pfSense (IPv4 e IPv6)."""
from __future__ import annotations

import re
from datetime import datetime, timezone

from app.services.parsers.base import (LineParser, ParseError, make_log, to_int, to_port, utc, valid_ip)

_MONTHS = {m: i for i, m in enumerate(
    ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], 1)}
_BSD_TS = re.compile(r"^(?:<\d+>)?\s*([A-Z][a-z]{2})\s+(\d{1,2})\s+(\d{2}):(\d{2}):(\d{2})")
_ISO_TS = re.compile(r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?)")
_FILTERLOG = re.compile(r"filterlog(?:\[\d+\])?:\s*(.*)$")
_FILTERLOG_5424 = re.compile(r"filterlog\s+\S+\s+\S+\s+(?:\[[^\]]*\]\s*|-\s*)*(.*)$")


def _parse_ts(prefix: str, now: datetime) -> datetime:
    m = _ISO_TS.search(prefix)
    if m:
        s = m.group(1)
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        try:
            return utc(datetime.fromisoformat(s))
        except ValueError:
            pass
    m = _BSD_TS.match(prefix)
    if m:
        mon, day, hh, mm, ss = m.groups()
        if mon in _MONTHS:
            try:
                dt = datetime(now.year, _MONTHS[mon], int(day), int(hh), int(mm), int(ss), tzinfo=timezone.utc)
            except ValueError as e:
                raise ParseError("Fecha syslog inválida") from e
            if dt > now.replace(microsecond=0) and (dt - now).days > 1:
                dt = dt.replace(year=now.year - 1)
            return dt
    raise ParseError("Sin marca de tiempo syslog reconocible")


class OpnsenseFilterlogParser(LineParser):
    name = "opnsense_filterlog"

    def __init__(self, now: datetime | None = None):
        self.now = now or datetime.now(timezone.utc)

    def parse_line(self, line: str) -> dict | None:
        idx = line.find("filterlog")
        if idx < 0:
            return None  # otra línea de syslog: se ignora
        m = _FILTERLOG.search(line)
        if m:
            csv = m.group(1)
        else:
            m = _FILTERLOG_5424.search(line)
            if not m:
                raise ParseError("No se encontró el cuerpo CSV de filterlog")
            csv = m.group(1)
        ts = _parse_ts(line[:idx], self.now)
        f = [x.strip() for x in csv.split(",")]
        if len(f) < 9:
            raise ParseError("Campos insuficientes en filterlog")
        action = f[6].lower()
        if action in ("block", "reject", "drop"):
            action = "block"
        elif action == "pass":
            action = "pass"
        else:
            raise ParseError(f"Acción desconocida: {action}")
        ipver = f[8]
        if ipver == "4":
            if len(f) < 20:
                raise ParseError("Línea IPv4 truncada")
            proto, length, src, dst, rest = f[16].lower(), f[17], f[18], f[19], f[20:]
        elif ipver == "6":
            if len(f) < 17:
                raise ParseError("Línea IPv6 truncada")
            proto, length, src, dst, rest = f[12].lower(), f[14], f[15], f[16], f[17:]
        else:
            raise ParseError(f"Versión IP desconocida: {ipver!r}")
        if proto.startswith("icmp") or proto == "ipv6-icmp":
            proto = "icmp"
        src, dst = valid_ip(src), valid_ip(dst)
        sport = dport = None
        if proto in ("tcp", "udp") and len(rest) >= 2:
            sport, dport = to_port(rest[0]), to_port(rest[1])
        size = to_int(length) or 0
        return make_log(
            ts=ts, log_type="firewall", action=action, proto=proto, src_ip=src, src_port=sport, dst_ip=dst,
            dst_port=dport, bytes_out=size, bytes_in=0, packets=1,
            raw={"rule": f[0], "interface": f[4], "reason": f[5], "dir": f[7], "ipver": ipver,
                 "tcp_flags": rest[3] if proto == "tcp" and len(rest) > 3 else None},
        )
