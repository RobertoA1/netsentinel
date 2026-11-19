"""Servicios conocidos por puerto y puertos comunes por defecto."""

SERVICES: dict[int, str] = {
    20: "FTP-data", 21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP", 53: "DNS", 67: "DHCP", 68: "DHCP",
    69: "TFTP", 80: "HTTP", 110: "POP3", 123: "NTP", 135: "MS-RPC", 137: "NetBIOS", 138: "NetBIOS",
    139: "NetBIOS", 143: "IMAP", 161: "SNMP", 162: "SNMP-trap", 389: "LDAP", 443: "HTTPS", 445: "SMB",
    465: "SMTPS", 514: "Syslog", 587: "SMTP-submission", 636: "LDAPS", 853: "DNS-over-TLS",
    993: "IMAPS", 995: "POP3S", 1080: "SOCKS", 1433: "MSSQL", 1521: "Oracle", 1723: "PPTP",
    1900: "SSDP", 3306: "MySQL", 3389: "RDP", 4444: "Metasploit/backdoor", 5060: "SIP",
    5353: "mDNS", 5432: "PostgreSQL", 5900: "VNC", 6667: "IRC", 6697: "IRC-TLS", 8080: "HTTP-alt",
    8443: "HTTPS-alt", 9001: "Tor/alt", 9050: "Tor-SOCKS", 27017: "MongoDB",
}

DEFAULT_COMMON_PORTS = [
    21, 22, 25, 53, 67, 68, 80, 110, 123, 137, 138, 143, 161, 389, 443, 465, 514, 587,
    636, 853, 993, 995, 5353, 8080, 8443,
]


def service_name(port: int | None) -> str:
    if port is None:
        return "desconocido"
    return SERVICES.get(port, "desconocido")
