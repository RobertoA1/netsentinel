from datetime import datetime, timezone

import pytest

from app.services.parsers import DirectionClassifier, ParseStats, get_parser, parse_stream
from app.services.parsers.base import ParseError
from app.services.parsers.ctu13 import Ctu13Parser
from app.services.parsers.opnsense import OpnsenseFilterlogParser
from app.services.parsers.suricata import SuricataEveParser
from helpers import FIXTURES

NOW = datetime(2026, 11, 11, 12, 0, tzinfo=timezone.utc)


def run(fmt, path):
    st = ParseStats()
    rows = list(parse_stream(get_parser(fmt), path.read_text().splitlines(), st))
    return rows, st


def test_opnsense_ipv4_tcp():
    p = OpnsenseFilterlogParser(now=NOW)
    r = p.parse_line("Nov 11 10:00:01 fw filterlog[42]: 5,,,1000000103,igb1,match,pass,out,4,0x0,,64,1234,0,DF,6,tcp,60,"
                     "192.168.1.10,93.184.216.34,51234,443,0,S,1,,64240,,mss")
    assert (r["src_ip"], r["dst_ip"], r["src_port"], r["dst_port"], r["proto"], r["action"]) == \
           ("192.168.1.10", "93.184.216.34", 51234, 443, "tcp", "pass")
    assert r["ts"] == datetime(2026, 11, 11, 10, 0, 1, tzinfo=timezone.utc) and r["log_type"] == "firewall"
    assert r["bytes_out"] == 60


def test_opnsense_ipv6_udp_block_and_icmp_5424():
    p = OpnsenseFilterlogParser(now=NOW)
    r = p.parse_line("Nov 11 10:00:03 fw filterlog[4]: 9,,,1000000110,igb1,match,block,out,6,0x00,0x12345,64,UDP,17,64,"
                     "fd00::10,2606:4700::1111,50000,53,24")
    assert r["proto"] == "udp" and r["action"] == "block" and r["dst_ip"] == "2606:4700::1111" and r["dst_port"] == 53
    r = p.parse_line('<134>1 2026-11-11T10:00:04+00:00 fw filterlog 4242 - [meta sequenceId="9"] 11,,,1,igb1,match,pass,'
                     'out,4,0x0,,64,0,0,none,1,icmp,84,192.168.1.10,1.1.1.1,request,1,1')
    assert r["proto"] == "icmp" and r["dst_port"] is None and r["ts"].hour == 10


def test_opnsense_file_tolerates_garbage():
    rows, st = run("opnsense_filterlog", FIXTURES / "opnsense_filterlog.log")
    assert len(rows) == 4
    assert st.parse_errors == 2          # basura truncada + IP inválida
    assert st.ignored == 1               # línea dhcpd
    assert st.lines_read == 7


def test_opnsense_errors():
    p = OpnsenseFilterlogParser(now=NOW)
    with pytest.raises(ParseError):
        p.parse_line("Nov 11 10:00:06 fw filterlog[1]: a,b")


def test_suricata_alert_and_flow():
    rows, st = run("suricata_eve", FIXTURES / "suricata_eve.json")
    assert len(rows) == 2 and st.parse_errors == 2 and st.ignored == 1
    a, f = rows
    assert a["log_type"] == "ids" and a["signature_id"] == 2024897 and a["ids_severity"] == 1
    assert a["category"].startswith("A Network Trojan") and a["bytes_out"] == 512 and a["proto"] == "tcp"
    assert f["log_type"] == "flow" and f["bytes_out"] == 1200 and f["bytes_in"] == 5400
    assert f["packets"] == 22 and f["duration"] == 3.0 and a["ts"].tzinfo is not None


def test_ctu13_parser_fields():
    p = Ctu13Parser()
    p.parse_line("StartTime,Dur,Proto,SrcAddr,Sport,Dir,DstAddr,Dport,State,sTos,dTos,TotPkts,TotBytes,SrcBytes,Label")
    r = p.parse_line("2011/08/10 09:46:53.047277,3550.182373,tcp,147.32.84.165,0x0303,   ->,185.1.2.3,443,S_RA,0,0,12,"
                     "1500,400,flow=From-Botnet-V42-TCP-CC#6")
    assert r["bytes_out"] == 400 and r["bytes_in"] == 1100 and r["src_port"] == 0x303 and r["dst_port"] == 443
    assert r["label"] == "flow=From-Botnet-V42-TCP-CC#6" and r["duration"] == pytest.approx(3550.182373)
    assert r["packets"] == 12 and r["ts"] == datetime(2011, 8, 10, 9, 46, 53, 47277, tzinfo=timezone.utc)
    e = p.parse_line("2011/08/10 09:46:53.1,0.1,icmp,1.2.3.4,,  ->,8.8.8.8,,ECO,0,0,2,196,98,flow=x")
    assert e["src_port"] is None and e["dst_port"] is None and e["proto"] == "icmp"


def test_ctu13_file():
    rows, st = run("ctu13_binetflow", FIXTURES / "ctu13_sample.binetflow")
    assert len(rows) == 48 + 160 + 6 + 12 + 2
    assert st.parse_errors == 2 and st.ignored == 2          # basura + IP inválida; ignoradas: cabecera y ARP
    assert any(r["src_port"] == 0x303 for r in rows)


def test_direction_classifier():
    c = DirectionClassifier(["10.0.0.0/8", "192.168.0.0/16"])
    assert c.classify("10.0.0.5", "8.8.8.8") == "outbound"
    assert c.classify("8.8.8.8", "10.0.0.5") == "inbound"
    assert c.classify("10.0.0.5", "192.168.1.1") == "internal"
