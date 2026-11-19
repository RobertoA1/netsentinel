"""Listas allow/deny: allow suprime hallazgos, deny eleva severidad."""
from __future__ import annotations

import ipaddress
from typing import Iterable

from app.services.detectors.common import Candidate, bump, severity_from_score


class ListMatcher:
    def __init__(self, entries: Iterable[tuple[str, str, str]] = ()):
        """entries: (list_type, kind, value)."""
        self.ips: dict[str, set[str]] = {"allow": set(), "deny": set()}
        self.nets: dict[str, list] = {"allow": [], "deny": []}
        self.ports: dict[str, set[int]] = {"allow": set(), "deny": set()}
        self.domains: dict[str, set[str]] = {"allow": set(), "deny": set()}
        for lt, kind, value in entries:
            if lt not in self.ips:
                continue
            value = value.strip()
            try:
                if kind == "ip":
                    self.ips[lt].add(str(ipaddress.ip_address(value)))
                elif kind == "cidr":
                    self.nets[lt].append(ipaddress.ip_network(value, strict=False))
                elif kind == "port":
                    self.ports[lt].add(int(value))
                elif kind == "domain":
                    self.domains[lt].add(value.lower().lstrip("."))
            except ValueError:
                continue

    def ip_in(self, lt: str, ip: str | None) -> bool:
        if not ip:
            return False
        if ip in self.ips[lt]:
            return True
        try:
            a = ipaddress.ip_address(ip)
        except ValueError:
            return False
        return any(a.version == n.version and a in n for n in self.nets[lt])

    def port_in(self, lt: str, port: int | None) -> bool:
        return port is not None and port in self.ports[lt]

    def domain_in(self, lt: str, host: str | None) -> bool:
        if not host:
            return False
        h = host.lower().rstrip(".")
        return any(h == d or h.endswith("." + d) for d in self.domains[lt])

    def matches(self, lt: str, c: Candidate) -> bool:
        if self.ip_in(lt, c.src_ip) or self.ip_in(lt, c.dst_ip) or self.port_in(lt, c.dst_port):
            return True
        return any(self.domain_in(lt, h) for h in c.context.get("hostnames", []))

    def apply(self, c: Candidate) -> Candidate | None:
        """None si el hallazgo queda suprimido por allow; si coincide con deny sube de severidad."""
        if self.matches("allow", c):
            return None
        if self.matches("deny", c):
            c.score = min(100.0, c.score + 15)
            c.severity = bump(max_sev(c.severity, severity_from_score(c.score)), 1)
            c.evidence["denylist_match"] = True
            c.context["in_denylist"] = True
        return c


def max_sev(a: str, b: str) -> str:
    from app.services.detectors.common import sev_rank
    return a if sev_rank(a) >= sev_rank(b) else b
