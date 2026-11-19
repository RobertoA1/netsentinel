"""Genera los fixtures de prueba (formato real, contenido propio). Ejecutar una vez: python make_fixtures.py"""
import json
import random
from datetime import datetime, timedelta
from pathlib import Path

HERE = Path(__file__).parent
random.seed(13)
BASE = datetime(2011, 8, 10, 9, 0, 0)
HEADER = "StartTime,Dur,Proto,SrcAddr,Sport,Dir,DstAddr,Dport,State,sTos,dTos,TotPkts,TotBytes,SrcBytes,Label"


def row(t, dur, proto, src, sport, dst, dport, state, pk, tot, srcb, label):
    return (f"{t.strftime('%Y/%m/%d %H:%M:%S.%f')},{dur:.6f},{proto},{src},{sport},   ->,{dst},{dport},"
            f"{state},0,0,{pk},{tot},{srcb},{label}")


lines = [HEADER]
# 1) Beaconing: 48 conexiones cada 60 s (+-1 s) con tamaño casi constante, host infectado -> C2 puerto 443
t = BASE
for i in range(48):
    t = BASE + timedelta(seconds=60 * i + random.uniform(-1, 1))
    lines.append(row(t, 0.4, "tcp", "147.32.84.165", 1025 + i, "185.44.12.9", 443, "S_RA", 8, 620 + random.randint(-5, 5),
                     310, "flow=From-Botnet-V42-TCP-CC#6-Plain-HTTP-Encrypted-Data"))
# 2) Tráfico normal irregular: 3 equipos navegando a muchos destinos (intervalos aleatorios)
hosts = ["147.32.84.10", "147.32.84.11", "147.32.84.12"]
dests = [f"93.184.{i}.{j}" for i in range(1, 4) for j in range(1, 6)]
t = BASE
for i in range(160):
    t += timedelta(seconds=random.expovariate(1 / 20))
    lines.append(row(t, random.random(), "tcp", random.choice(hosts), random.randint(2000, 60000),
                     random.choice(dests), random.choice(["80", "443", "443", "53"]), "SF", random.randint(4, 40),
                     random.randint(400, 40000), random.randint(100, 5000), "flow=Background-Established-cmpgw-CVUT"))
# 3) Exfiltración: un host sube ~120 MB a un destino en pocas conexiones largas
for i in range(6):
    t = BASE + timedelta(minutes=10 * i + 3)
    lines.append(row(t, 120.0, "tcp", "147.32.84.77", 40000 + i, "203.0.113.50", 8443, "SF", 90000,
                     21_000_000, 20_500_000, "flow=From-Botnet-V42-TCP-Attempt"))
# 4) Puerto inusual (4444) hacia un solo destino, 12 conexiones
for i in range(12):
    t = BASE + timedelta(minutes=5 * i, seconds=random.randint(0, 100))
    lines.append(row(t, 1.5, "tcp", "147.32.84.88", 50000 + i, "198.51.100.7", "4444", "SF", 12, 5000, 2500, "flow=From-Botnet-V42-TCP-Attempt"))
# 5) Casos de borde: puerto hex, puerto vacío, ARP, línea malformada
lines.append(row(BASE + timedelta(minutes=1), 0.1, "udp", "147.32.84.10", "0x0303", "224.0.0.251", "5353", "INT", 2, 200, 200, "flow=Background-UDP-Established"))
lines.append(row(BASE + timedelta(minutes=2), 0.0, "icmp", "147.32.84.10", "", "8.8.8.8", "", "ECO", 2, 196, 98, "flow=Background"))
lines.append("2011/08/10 09:03:00.000000,0.0,arp,00:1b:21:aa:bb:cc,,  who,00:1b:21:dd:ee:ff,,RQ,0,0,1,60,60,flow=Background")
lines.append("esto-no-es-una-fila-valida")
lines.append("2011/08/10 09:04:00.000000,0.1,tcp,999.1.1.1,80,->,8.8.8.8,80,SF,0,0,1,100,50,flow=Bad-IP")
(HERE / "ctu13_sample.binetflow").write_text("\n".join(lines) + "\n")

# OPNsense filterlog (BSD syslog + RFC5424, IPv4 e IPv6, TCP/UDP/ICMP, líneas basura)
op = [
    "Nov 11 10:00:01 fw.local filterlog[4242]: 5,,,1000000103,igb1,match,pass,out,4,0x0,,64,1234,0,DF,6,tcp,60,192.168.1.10,93.184.216.34,51234,443,0,S,1234567,,64240,,mss",
    "Nov 11 10:00:02 fw.local filterlog[4242]: 7,,,1000000105,igb0,match,block,in,4,0x0,,52,4321,0,none,17,udp,76,203.0.113.9,192.168.1.10,53122,1900,56",
    "Nov 11 10:00:03 fw.local filterlog[4242]: 9,,,1000000110,igb1,match,pass,out,6,0x00,0x12345,64,UDP,17,64,fd00::10,2606:4700::1111,50000,53,24",
    "<134>1 2026-11-11T10:00:04+00:00 fw.local filterlog 4242 - [meta sequenceId=\"9\"] 11,,,1000000111,igb1,match,pass,out,4,0x0,,64,0,0,none,1,icmp,84,192.168.1.10,1.1.1.1,request,1234,1",
    "Nov 11 10:00:05 fw.local dhcpd[100]: DHCPACK on 192.168.1.20 to aa:bb:cc:dd:ee:ff",
    "Nov 11 10:00:06 fw.local filterlog[4242]: basura,truncada",
    "Nov 11 10:00:07 fw.local filterlog[4242]: 5,,,1,igb1,match,pass,out,4,0x0,,64,1,0,none,6,tcp,60,no-es-ip,8.8.8.8,1,2,0",
]
(HERE / "opnsense_filterlog.log").write_text("\n".join(op) + "\n")

# Suricata EVE
ev = [
    {"timestamp": "2026-11-11T10:00:01.123456+0000", "event_type": "alert", "src_ip": "192.168.1.30", "src_port": 49822,
     "dest_ip": "45.9.148.10", "dest_port": 80, "proto": "TCP", "alert": {"action": "allowed", "signature_id": 2024897,
     "signature": "ET MALWARE Possible Beacon Activity", "category": "A Network Trojan was detected", "severity": 1},
     "flow": {"bytes_toserver": 512, "bytes_toclient": 1024}, "http": {"hostname": "evil.example"}},
    {"timestamp": "2026-11-11T10:00:02.000000+0000", "event_type": "flow", "src_ip": "192.168.1.10", "src_port": 40000,
     "dest_ip": "93.184.216.34", "dest_port": 443, "proto": "TCP",
     "flow": {"pkts_toserver": 10, "pkts_toclient": 12, "bytes_toserver": 1200, "bytes_toclient": 5400, "age": 3, "state": "closed"}},
    {"timestamp": "2026-11-11T10:00:03.000000+0000", "event_type": "dns", "src_ip": "192.168.1.10", "dest_ip": "8.8.8.8"},
]
txt = "\n".join(json.dumps(e) for e in ev) + "\n{esto no es json\n" + json.dumps({"timestamp": "mal", "event_type": "alert", "src_ip": "1.1.1.1", "dest_ip": "2.2.2.2", "alert": {"signature": "x"}}) + "\n"
(HERE / "suricata_eve.json").write_text(txt)
print("fixtures generados")
