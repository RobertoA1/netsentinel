"""Detectores puros: sin base de datos."""
import random
from datetime import datetime, timedelta, timezone

from app.core.ports import DEFAULT_COMMON_PORTS
from app.services.detectors.beaconing import detect_beaconing, group_from_series
from app.services.detectors.common import DetectionConfig, mean_stdev
from app.services.detectors.exfil import (HostVolume, TalkerStats, baseline_stats, detect_exfiltration,
                                          detect_talker_anomalies)
from app.services.detectors.ids import IdsGroup, detect_ids_alerts
from app.services.detectors.lists import ListMatcher
from app.services.detectors.ports import PortGroup, detect_unusual_ports

T0 = datetime(2026, 11, 11, 0, 0, tzinfo=timezone.utc)
WS, WE = T0, T0 + timedelta(hours=24)


def cfg(**kw):
    base = dict(common_ports=set(DEFAULT_COMMON_PORTS), internal_cidrs=["10.0.0.0/8"])
    base.update(kw)
    return DetectionConfig(**base)


def test_beaconing_regular_positive():
    rnd = random.Random(1)
    ts = [T0 + timedelta(seconds=60 * i + rnd.uniform(-1, 1)) for i in range(50)]
    g = group_from_series("10.0.0.5", "185.1.2.3", 443, "tcp", ts, [600 + rnd.randint(-4, 4) for _ in ts])
    out = detect_beaconing([g], cfg(), WS, WE)
    assert len(out) == 1
    c = out[0]
    assert c.finding_type == "beaconing" and c.score >= 80 and c.severity in ("high", "critical")
    ev = c.evidence
    assert ev["connections"] == 50 and 55 < ev["mean_interval_s"] < 65 and ev["cv"] < 0.05
    assert set(ev) >= {"stdev_interval_s", "mean_bytes", "bytes_cv", "duration_h", "intervals_sample"}
    assert c.dedup_key == "beaconing|10.0.0.5|185.1.2.3|443|tcp"


def test_beaconing_irregular_negative():
    rnd = random.Random(2)
    t, ts = T0, []
    for _ in range(80):
        t += timedelta(seconds=rnd.expovariate(1 / 45))   # intervalos exponenciales: CV ~ 1
        ts.append(t)
    g = group_from_series("10.0.0.5", "93.184.1.1", 443, "tcp", ts, [rnd.randint(100, 90000) for _ in ts])
    assert detect_beaconing([g], cfg(), WS, WE) == []


def test_beaconing_requires_min_connections():
    ts = [T0 + timedelta(seconds=60 * i) for i in range(5)]
    g = group_from_series("a", "b", 443, "tcp", ts, [100] * 5)
    assert detect_beaconing([g], cfg(), WS, WE) == []


def test_exfiltration_with_baseline_and_ratio():
    h = HostVolume("10.0.0.7", 800_000_000, 5_000_000, 40, T0, WE, [{"ip": "203.0.113.5", "bytes": 700_000_000}])
    base = {"10.0.0.7": baseline_stats([20e6, 25e6, 18e6, 22e6, 30e6], 14)}
    out = detect_exfiltration([h], base, cfg(), WS, WE)
    assert len(out) == 1
    ev = out[0].evidence
    assert ev["zscore"] > 3 and ev["ratio_out_in"] == 160.0 and ev["top_destinations"][0]["ip"] == "203.0.113.5"
    assert out[0].severity in ("high", "critical")
    assert set(ev) >= {"bytes_out", "baseline_mean", "baseline_stdev"}


def test_exfiltration_below_threshold_or_normal_for_host():
    small = HostVolume("10.0.0.8", 10_000_000, 1, 5, T0, WE)
    assert detect_exfiltration([small], {}, cfg(), WS, WE) == []
    # el host siempre sube mucho: no es anómalo frente a su historial
    big = HostVolume("10.0.0.9", 900_000_000, 1_000, 5, T0, WE)
    base = {"10.0.0.9": baseline_stats([850e6, 900e6, 880e6, 910e6, 870e6] * 3, 14)}
    assert detect_exfiltration([big], base, cfg(), WS, WE) == []


def test_exfiltration_without_baseline_needs_asymmetry():
    sym = HostVolume("10.0.0.10", 200_000_000, 190_000_000, 5, T0, WE)
    asym = HostVolume("10.0.0.11", 200_000_000, 1_000_000, 5, T0, WE)
    out = detect_exfiltration([sym, asym], {}, cfg(), WS, WE)
    assert [c.src_ip for c in out] == ["10.0.0.11"] and out[0].evidence["zscore"] is None


def test_unusual_port_detected_and_filters():
    groups = [
        PortGroup("10.0.0.5", 4444, "tcp", 30, 5000, 1, "198.51.100.7", T0, WE),
        PortGroup("10.0.0.5", 443, "tcp", 500, 9999, 20, "1.1.1.1", T0, WE),       # común
        PortGroup("10.0.0.6", 8123, "tcp", 40, 100, 1, "5.5.5.5", T0, WE),          # esperado en el activo
        PortGroup("10.0.0.7", 9999, "tcp", 40, 100, 1, "6.6.6.6", T0, WE),          # en la línea base
        PortGroup("10.0.0.8", 7777, "tcp", 2, 100, 1, "7.7.7.7", T0, WE),           # pocas conexiones
    ]
    out = detect_unusual_ports(groups, cfg(), {"10.0.0.6": {8123}}, {9999}, WS, WE)
    assert [c.dst_port for c in out] == [4444]
    ev = out[0].evidence
    assert ev["port"] == 4444 and ev["service"] == "Metasploit/backdoor" and ev["in_baseline"] is False
    assert ev["connections"] == 30 and ev["distinct_sources"] == 1 and "first_seen" in ev


def test_ids_grouping_severity():
    g = IdsGroup("ET MALWARE X", 1, "Trojan", 1, 120, 3, "10.0.0.5", "1.2.3.4", 80, T0, WE)
    low = IdsGroup("ET INFO Y", 2, "Info", 3, 4, 1, "10.0.0.5", "1.2.3.4", 80, T0, WE)
    out = detect_ids_alerts([low, g], WS, WE)
    assert out[0].severity == "high" and out[1].severity == "low"
    assert out[0].evidence["count"] == 120 and out[0].evidence["signature_id"] == 1


def test_talker_anomaly_vs_history_and_peers():
    t = TalkerStats("10.0.0.5", 5000, 400, T0, WE)
    base = {"10.0.0.5": baseline_stats([100, 120, 90, 110], 14)}
    out = detect_talker_anomalies([t], base, {}, cfg(), WS, WE)
    assert len(out) == 1 and out[0].evidence["metric"] in ("connections", "unique_destinations")
    peers = [TalkerStats(f"10.0.1.{i}", 300 + i, 10, T0, WE) for i in range(8)] + [TalkerStats("10.0.9.9", 9000, 10, T0, WE)]
    out = detect_talker_anomalies(peers, {}, {}, cfg(), WS, WE)
    assert [c.src_ip for c in out] == ["10.0.9.9"] and out[0].evidence["baseline_source"] == "peers"


def test_lists_allow_suppresses_deny_elevates():
    rnd = random.Random(3)
    ts = [T0 + timedelta(seconds=60 * i + rnd.uniform(-1, 1)) for i in range(30)]
    c = detect_beaconing([group_from_series("10.0.0.5", "185.1.2.3", 443, "tcp", ts, [500] * 30)], cfg(), WS, WE)[0]
    assert ListMatcher([("allow", "cidr", "185.1.2.0/24")]).apply(c) is None
    assert ListMatcher([("allow", "ip", "10.0.0.5")]).apply(c) is None
    before = c.severity
    c2 = detect_beaconing([group_from_series("10.0.0.5", "185.1.2.3", 443, "tcp", ts, [500] * 30)], cfg(), WS, WE)[0]
    c2 = ListMatcher([("deny", "ip", "185.1.2.3")]).apply(c2)
    assert c2.evidence["denylist_match"] is True and c2.score > c.score
    assert ListMatcher([("allow", "port", "80")]).apply(c) is c


def test_mean_stdev():
    m, s = mean_stdev([2, 4, 4, 4, 5, 5, 7, 9])
    assert m == 5 and s == 2
