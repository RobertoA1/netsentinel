"""Parser de EVE JSON de Suricata (event_type alert y flow)."""
from __future__ import annotations

import json
from datetime import datetime

from app.services.parsers.base import (LineParser, ParseError, make_log, to_int, to_port, utc, valid_ip)


def _ts(s: str) -> datetime:
    if not isinstance(s, str):
        raise ParseError("timestamp ausente")
    try:
        return utc(datetime.fromisoformat(s))
    except ValueError:
        pass
    try:  # offsets sin dos puntos (+0000) en versiones antiguas
        return utc(datetime.strptime(s, "%Y-%m-%dT%H:%M:%S.%f%z"))
    except ValueError as e:
        raise ParseError(f"timestamp inválido: {s!r}") from e


class SuricataEveParser(LineParser):
    name = "suricata_eve"

    def parse_line(self, line: str) -> dict | None:
        try:
            ev = json.loads(line)
        except json.JSONDecodeError as e:
            raise ParseError("JSON inválido") from e
        if not isinstance(ev, dict):
            raise ParseError("El evento EVE no es un objeto")
        et = ev.get("event_type")
        if et not in ("alert", "flow"):
            return None
        if not ev.get("src_ip") or not ev.get("dest_ip"):
            raise ParseError("Faltan src_ip/dest_ip")
        common = dict(
            ts=_ts(ev.get("timestamp")), proto=str(ev.get("proto", "")).lower() or None,
            src_ip=valid_ip(ev["src_ip"]), src_port=to_port(ev.get("src_port")), dst_ip=valid_ip(ev["dest_ip"]),
            dst_port=to_port(ev.get("dest_port")),
        )
        if et == "alert":
            a = ev.get("alert") or {}
            if not a.get("signature"):
                raise ParseError("alert sin signature")
            fl = ev.get("flow") or {}
            return make_log(
                **common, log_type="ids", action="block" if a.get("action") == "blocked" else "alert",
                bytes_out=to_int(fl.get("bytes_toserver")) or 0, bytes_in=to_int(fl.get("bytes_toclient")) or 0,
                signature=str(a["signature"])[:512], signature_id=to_int(a.get("signature_id")),
                category=(str(a["category"])[:255] if a.get("category") else None),
                ids_severity=to_int(a.get("severity")),
                raw={"app_proto": ev.get("app_proto"), "in_iface": ev.get("in_iface"),
                     "http_host": (ev.get("http") or {}).get("hostname"),
                     "tls_sni": (ev.get("tls") or {}).get("sni")},
            )
        fl = ev.get("flow")
        if not isinstance(fl, dict):
            raise ParseError("flow sin objeto flow")
        pk = (to_int(fl.get("pkts_toserver")) or 0) + (to_int(fl.get("pkts_toclient")) or 0)
        age = fl.get("age")
        return make_log(
            **common, log_type="flow", action="pass",
            bytes_out=to_int(fl.get("bytes_toserver")) or 0, bytes_in=to_int(fl.get("bytes_toclient")) or 0,
            packets=pk or None, duration=float(age) if age is not None else None,
            raw={"state": fl.get("state"), "reason": fl.get("reason"), "app_proto": ev.get("app_proto")},
        )
