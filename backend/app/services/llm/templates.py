"""Explicación y recomendación deterministas (plantillas en español) cuando el LLM no está disponible."""
from __future__ import annotations

from typing import Any


def _fmt_bytes(n: float) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(n) < 1024 or unit == "TB":
            return f"{n:.1f} {unit}" if unit != "B" else f"{int(n)} B"
        n /= 1024
    return f"{n:.1f} TB"


def template_analysis(finding_type: str, evidence: dict[str, Any], src_ip: str | None, dst_ip: str | None,
                      dst_port: int | None, in_denylist: bool = False) -> tuple[str, str]:
    src, dst = src_ip or "un equipo interno", dst_ip or "destinos externos"
    extra = " Además, el destino figura en su lista de bloqueo." if in_denylist else ""
    if finding_type == "beaconing":
        e = evidence
        expl = (f"El equipo {src} se conectó {e.get('connections')} veces a {dst}"
                f"{f':{dst_port}' if dst_port else ''} con un intervalo casi constante de unos "
                f"{float(e.get('mean_interval_s', 0)):.0f} segundos (variación {float(e.get('cv', 0)) * 100:.0f}%). "
                "Esa regularidad es típica de software automático que \"llama a casa\", como malware o "
                f"servicios de control remoto.{extra}")
        rec = (f"Identifique qué proceso de {src} genera este tráfico. Si no es un servicio conocido, aísle el "
               f"equipo de la red, bloquee {dst} en el firewall y ejecute un análisis antimalware.")
    elif finding_type == "exfiltration":
        e = evidence
        z = e.get("zscore")
        zt = f" y es {z:.1f} desviaciones por encima de su comportamiento habitual" if z is not None else ""
        tops = ", ".join(d["ip"] for d in (e.get("top_destinations") or [])[:3]) or "varios destinos"
        expl = (f"El equipo {src} envió {_fmt_bytes(e.get('bytes_out', 0))} hacia el exterior{zt}. "
                f"Envía mucho más de lo que recibe (relación {e.get('ratio_out_in')}:1). "
                f"Los destinos principales son: {tops}.{extra}")
        rec = ("Confirme con el responsable del equipo si hubo una copia de seguridad o carga legítima. "
               "Si no, revise qué datos salieron, bloquee los destinos y cambie las credenciales del usuario.")
    elif finding_type == "unusual_port":
        e = evidence
        expl = (f"Se detectaron {e.get('connections')} conexiones salientes al puerto {e.get('port')} "
                f"({e.get('service')}), que no está entre los puertos habituales de la red ni en el historial. "
                f"Origen principal: {src}. Puede ser una aplicación nueva o un canal no autorizado.{extra}")
        rec = (f"Verifique si la aplicación que usa el puerto {e.get('port')} es legítima. Si no lo es, "
               "bloquee ese puerto en el firewall y revise el equipo de origen.")
    elif finding_type == "ids_alert":
        e = evidence
        expl = (f"El sistema de detección de intrusos registró {e.get('count')} eventos de la firma "
                f"\"{e.get('signature')}\" (categoría {e.get('category') or 'sin categoría'}), "
                f"desde {e.get('distinct_sources')} origen(es).{extra}")
        rec = ("Revise el equipo afectado, confirme si el evento es un falso positivo de la firma y, si es real, "
               "bloquee el origen y actualice el sistema.")
    elif finding_type == "talker_anomaly":
        e = evidence
        what = "conexiones" if e.get("metric") == "connections" else "destinos distintos"
        expl = (f"El equipo {src} generó {e.get('value')} {what}, muy por encima de lo habitual "
                f"(promedio {e.get('baseline_mean')}, z={e.get('zscore')}). Esto puede indicar un escaneo de red, "
                f"malware propagándose o un software mal configurado.{extra}")
        rec = (f"Revise qué está ejecutando {src}. Si no hay una explicación legítima, desconéctelo de la red "
               "y analícelo.")
    else:
        expl, rec = "Se detectó actividad sospechosa en el tráfico de red.", "Revise el hallazgo con el equipo de TI."
    return expl, rec
