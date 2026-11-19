"""Un builder por código de reporte: produce el modelo común ReportData."""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Callable

from sqlalchemy import and_, case, func, select
from sqlalchemy.orm import Session

from app.core.ports import service_name
from app.db.sqlfuncs import epoch_bucket
from app.models import (Asset, AuditEvent, Finding, FirewallLog as L, IngestRun, ModuleSession)
from app.services import settings_service
from app.services.reports.model import Chart, Kpi, ReportData, Table
from app.services.reports.util import human_bytes, human_duration

SEV_ORDER = ["critical", "high", "medium", "low", "info"]
SEV_ES = {"critical": "Crítica", "high": "Alta", "medium": "Media", "low": "Baja", "info": "Info"}
TYPE_ES = {"beaconing": "Beaconing", "unusual_port": "Puerto inusual", "exfiltration": "Exfiltración",
           "ids_alert": "Alerta IDS", "talker_anomaly": "Anomalía de host"}
STATUS_ES = {"new": "Nuevo", "in_review": "En revisión", "confirmed": "Confirmado",
             "false_positive": "Falso positivo", "closed": "Cerrado"}
ROW_CAP = 2000


@dataclass
class ReportDef:
    code: str
    name: str
    description: str
    category: str
    builder: Callable[[Session, datetime, datetime], ReportData]
    requires: tuple[str, ...]  # permiso(s) de datos necesarios (cualquiera)
    params: tuple[str, ...] = ()  # parámetros de entidad requeridos (reportes ML): dataset_version_id | job_id | model_id


def _fq(pf, pt, extra=()):
    return and_(Finding.last_seen >= pf, Finding.first_seen <= pt, *extra)


def _findings(db: Session, pf, pt, *conds, limit: int = ROW_CAP) -> list[Finding]:
    return list(db.execute(select(Finding).where(_fq(pf, pt, conds)).order_by(Finding.score.desc(), Finding.id)
                           .limit(limit)).unique().scalars())


def _data(code, name, cat, pf, pt, summary, kpis=None, tables=None, charts=None) -> ReportData:
    return ReportData(code=code, name=name, category=cat, period_from=pf, period_to=pt, summary=summary,
                      kpis=kpis or [], tables=tables or [], charts=charts or [])


def _ftable(title: str, fs: list[Finding]) -> Table:
    return Table(title, ["ID", "Última vez", "Tipo", "Severidad", "Puntaje", "Estado", "Origen", "Destino", "Puerto",
                         "Ruido", "Veredicto IA", "Hallazgo", "Recomendación"],
                 [[f.id, f.last_seen, TYPE_ES.get(f.finding_type, f.finding_type), SEV_ES.get(f.severity, f.severity),
                   f.score, STATUS_ES.get(f.status, f.status), f.src_ip, f.dst_ip, f.dst_port,
                   "Sí" if f.is_noise else "No", f.llm_verdict or "sin IA", f.title, f.llm_recommendation]
                  for f in fs])


# ---- operacionales --------------------------------------------------------

def op_findings(db, pf, pt):
    fs = _findings(db, pf, pt)
    real = [f for f in fs if not f.is_noise]
    sev = Counter(f.severity for f in real)
    typ = Counter(f.finding_type for f in real)
    summary = (f"En el período se registraron {len(fs)} hallazgos, de los cuales {len(real)} son relevantes y "
               f"{len(fs) - len(real)} fueron descartados como ruido. "
               f"{sev.get('critical', 0)} críticos y {sev.get('high', 0)} altos requieren atención prioritaria.")
    return _data("op_findings", "Hallazgos del período", "operational", pf, pt, summary,
                 [Kpi("Hallazgos totales", str(len(fs))), Kpi("Relevantes", str(len(real))),
                  Kpi("Ruido filtrado", str(len(fs) - len(real))), Kpi("Críticos", str(sev.get("critical", 0))),
                  Kpi("Altos", str(sev.get("high", 0))), Kpi("Sin confirmar (nuevos)",
                                                              str(sum(1 for f in real if f.status == "new")))],
                 [_ftable("Hallazgos", fs)],
                 [Chart("Hallazgos por severidad", "bar", [SEV_ES[s] for s in SEV_ORDER],
                        {"Hallazgos": [sev.get(s, 0) for s in SEV_ORDER]}, "Cantidad"),
                  Chart("Hallazgos por tipo", "pie", [TYPE_ES.get(t, t) for t in typ], {"Hallazgos": list(typ.values())})])


def op_top_talkers(db, pf, pt):
    bo = func.coalesce(func.sum(L.bytes_out), 0)
    rows = db.execute(select(L.src_ip, bo, func.coalesce(func.sum(L.bytes_in), 0), func.count(),
                             func.count(func.distinct(L.dst_ip)))
                      .where(L.ts >= pf, L.ts <= pt, L.direction == "outbound").group_by(L.src_ip)
                      .order_by(bo.desc()).limit(50)).all()
    names = {a.ip: a.hostname for a in db.execute(select(Asset)).scalars()}
    fc = dict(db.execute(select(Finding.src_ip, func.count()).where(_fq(pf, pt, [Finding.is_noise.is_(False)]))
                         .group_by(Finding.src_ip)).all())
    total = sum(int(r[1]) for r in rows)
    top = rows[:10]
    summary = (f"Se listan los {len(rows)} equipos internos con más tráfico saliente. "
               + (f"El mayor emisor es {rows[0][0]} con {human_bytes(rows[0][1])}." if rows else "No hay tráfico saliente en el período."))
    return _data("op_top_talkers", "Principales equipos por tráfico (top talkers)", "operational", pf, pt, summary,
                 [Kpi("Equipos con tráfico saliente", str(len(rows))), Kpi("Bytes salientes (top 50)", human_bytes(total))],
                 [Table("Top talkers", ["IP", "Host", "Bytes salientes", "Bytes entrantes", "Conexiones",
                                        "Destinos únicos", "Hallazgos"],
                        [[r[0], names.get(r[0], ""), int(r[1]), int(r[2]), r[3], r[4], fc.get(r[0], 0)] for r in rows])],
                 [Chart("Top 10 por bytes salientes (MB)", "hbar", [r[0] for r in top],
                        {"MB": [round(int(r[1]) / 1e6, 2) for r in top]})])


def _type_report(db, pf, pt, code, name, ftype, summary_fn, chart_fn):
    fs = _findings(db, pf, pt, Finding.finding_type == ftype)
    real = [f for f in fs if not f.is_noise]
    return _data(code, name, "operational", pf, pt, summary_fn(fs, real),
                 [Kpi("Hallazgos", str(len(fs))), Kpi("Relevantes", str(len(real))),
                  Kpi("Ruido", str(len(fs) - len(real))),
                  Kpi("Puntaje máximo", f"{max((f.score for f in fs), default=0):.1f}")],
                 [], [chart_fn(fs)]), fs


def op_beaconing(db, pf, pt):
    d, fs = _type_report(db, pf, pt, "op_beaconing", "Beaconing detectado", "beaconing",
                         lambda fs, real: f"Se detectaron {len(fs)} patrones de comunicación periódica "
                         f"({len(real)} relevantes). Un coeficiente de variación bajo indica regularidad típica de malware.",
                         lambda fs: Chart("Puntaje de beaconing (top 10)", "hbar",
                                          [f"{f.src_ip}->{f.dst_ip}:{f.dst_port}" for f in fs[:10]],
                                          {"Puntaje": [f.score for f in fs[:10]]}))
    d.tables.append(Table("Beaconing", ["ID", "Origen", "Destino", "Puerto", "Conexiones", "Intervalo medio (s)",
                                        "CV", "Duración (h)", "Puntaje", "Severidad", "Ruido", "Explicación"],
                          [[f.id, f.src_ip, f.dst_ip, f.dst_port, f.evidence.get("connections"),
                            f.evidence.get("mean_interval_s"), f.evidence.get("cv"), f.evidence.get("duration_h"),
                            f.score, SEV_ES.get(f.severity), "Sí" if f.is_noise else "No", f.llm_explanation]
                           for f in fs]))
    return d


def op_unusual_ports(db, pf, pt):
    d, fs = _type_report(db, pf, pt, "op_unusual_ports", "Puertos inusuales", "unusual_port",
                         lambda fs, real: f"Se detectaron {len(fs)} puertos destino fuera de lo habitual "
                         f"({len(real)} relevantes).",
                         lambda fs: Chart("Conexiones por puerto inusual (top 10)", "bar",
                                          [str(f.evidence.get("port")) for f in fs[:10]],
                                          {"Conexiones": [f.evidence.get("connections", 0) for f in fs[:10]]}))
    d.tables.append(Table("Puertos inusuales", ["ID", "Puerto", "Proto", "Servicio", "Conexiones", "Bytes",
                                                "Orígenes", "Origen principal", "Puntaje", "Severidad", "Ruido"],
                          [[f.id, f.dst_port, f.proto, f.evidence.get("service"), f.evidence.get("connections"),
                            f.evidence.get("bytes"), f.evidence.get("distinct_sources"), f.src_ip, f.score,
                            SEV_ES.get(f.severity), "Sí" if f.is_noise else "No"] for f in fs]))
    return d


def op_ids_alerts(db, pf, pt):
    rows = db.execute(select(L.signature, L.category, L.ids_severity, func.count(), func.count(func.distinct(L.src_ip)),
                             func.min(L.ts), func.max(L.ts))
                      .where(L.ts >= pf, L.ts <= pt, L.log_type == "ids").group_by(L.signature, L.category, L.ids_severity)
                      .order_by(func.count().desc()).limit(ROW_CAP)).all()
    cat = Counter()
    for r in rows:
        cat[r[1] or "sin categoría"] += r[3]
    total = sum(r[3] for r in rows)
    topcat = cat.most_common(8)
    return _data("op_ids_alerts", "Alertas del IDS", "operational", pf, pt,
                 f"El IDS registró {total} eventos en {len(rows)} firmas distintas durante el período.",
                 [Kpi("Eventos IDS", str(total)), Kpi("Firmas distintas", str(len(rows)))],
                 [Table("Alertas IDS por firma", ["Firma", "Categoría", "Severidad IDS", "Eventos", "Orígenes",
                                                  "Primera vez", "Última vez"],
                        [list(r) for r in rows])],
                 [Chart("Eventos IDS por categoría", "bar", [c for c, _ in topcat],
                        {"Eventos": [n for _, n in topcat]}, "Eventos")])


def op_ingestion(db, pf, pt):
    runs = list(db.execute(select(IngestRun).where(IngestRun.started_at >= pf, IngestRun.started_at <= pt)
                           .order_by(IngestRun.id.desc()).limit(ROW_CAP)).scalars())
    ok = sum(1 for r in runs if r.status == "success")
    return _data("op_ingestion", "Estado de la ingesta", "operational", pf, pt,
                 f"Hubo {len(runs)} ejecuciones de ingesta ({ok} exitosas, {len(runs) - ok} con error o en curso). "
                 f"Se insertaron {sum(r.logs_inserted for r in runs):,} registros con {sum(r.parse_errors for r in runs):,} errores de parseo.",
                 [Kpi("Ejecuciones", str(len(runs))), Kpi("Exitosas", str(ok)),
                  Kpi("Registros insertados", f"{sum(r.logs_inserted for r in runs):,}"),
                  Kpi("Errores de parseo", f"{sum(r.parse_errors for r in runs):,}")],
                 [Table("Ejecuciones de ingesta", ["ID", "Inicio", "Fin", "Estado", "Origen", "Archivo", "Líneas",
                                                   "Insertados", "Errores parseo", "Hallazgos", "Ruido", "Error"],
                        [[r.id, r.started_at, r.finished_at, r.status, r.trigger, r.filename, r.lines_read,
                          r.logs_inserted, r.parse_errors, r.findings_created, r.findings_noise, r.error]
                         for r in runs])],
                 [Chart("Registros insertados por ejecución", "bar", [f"#{r.id}" for r in reversed(runs[:20])],
                        {"Insertados": [r.logs_inserted for r in reversed(runs[:20])]})])


def op_audit_log(db, pf, pt):
    evs = list(db.execute(select(AuditEvent).where(AuditEvent.ts >= pf, AuditEvent.ts <= pt)
                          .order_by(AuditEvent.id.desc()).limit(ROW_CAP)).scalars())
    by = dict(db.execute(select(AuditEvent.event_type, func.count()).where(AuditEvent.ts >= pf, AuditEvent.ts <= pt)
                         .group_by(AuditEvent.event_type)).all())
    total = sum(by.values())
    sessions = list(db.execute(select(ModuleSession).where(ModuleSession.entered_at >= pf, ModuleSession.entered_at <= pt)
                               .order_by(ModuleSession.id.desc()).limit(ROW_CAP)).scalars())
    return _data("op_audit_log", "Bitácora de auditoría", "operational", pf, pt,
                 f"La bitácora registra {total} eventos en el período, incluidos {by.get('login', 0)} inicios de sesión, "
                 f"{by.get('login_failed', 0)} intentos fallidos y {len(sessions)} sesiones de módulo.",
                 [Kpi("Eventos", str(total)), Kpi("Inicios de sesión", str(by.get("login", 0))),
                  Kpi("Intentos fallidos", str(by.get("login_failed", 0))), Kpi("Sesiones de módulo", str(len(sessions)))],
                 [Table("Eventos de auditoría", ["ID", "Fecha", "Usuario", "Evento", "Módulo", "Entidad", "ID entidad",
                                                 "Descripción", "IP"],
                        [[e.id, e.ts, e.username, e.event_type, e.module, e.entity, e.entity_id, e.description, e.ip]
                         for e in evs], total_rows=total),
                  Table("Sesiones de módulo", ["ID", "Usuario", "Módulo", "Entrada", "Salida", "Duración (s)", "IP",
                                               "Motivo de salida"],
                        [[s.id, s.username, s.module, s.entered_at, s.exited_at, s.duration_seconds, s.ip, s.exit_reason]
                         for s in sessions])],
                 [Chart("Eventos por tipo", "bar", list(by.keys()), {"Eventos": list(by.values())})])


# ---- gestión -----------------------------------------------------------------

def mg_executive_summary(db, pf, pt):
    st = db.execute(select(func.count(), func.coalesce(func.sum(L.bytes_out), 0), func.coalesce(func.sum(L.bytes_in), 0),
                           func.count(func.distinct(L.src_ip)), func.count().filter(L.action == "block"))
                    .where(L.ts >= pf, L.ts <= pt)).one()
    fs = _findings(db, pf, pt, limit=5000)
    real = [f for f in fs if not f.is_noise]
    sev = Counter(f.severity for f in real)
    typ = Counter(f.finding_type for f in real)
    top = sorted(real, key=lambda f: -f.score)[:10]
    ratio = (len(fs) - len(real)) / len(fs) * 100 if fs else 0
    risk = ("ALTO" if sev.get("critical") else "MEDIO" if sev.get("high") else "BAJO")
    summary = (f"Nivel de riesgo del período: {risk}. Se analizaron {st[0]:,} registros de red y se generaron "
               f"{len(fs)} hallazgos; {len(real)} son relevantes ({sev.get('critical', 0)} críticos, "
               f"{sev.get('high', 0)} altos) y el filtro de ruido descartó el {ratio:.0f}%. "
               + ("Se recomienda revisar de inmediato los hallazgos críticos listados." if sev.get("critical") else
                  "No hay hallazgos críticos abiertos; mantenga la revisión periódica de los altos."))
    return _data("mg_executive_summary", "Resumen ejecutivo", "management", pf, pt, summary,
                 [Kpi("Registros analizados", f"{st[0]:,}"), Kpi("Tráfico saliente", human_bytes(st[1])),
                  Kpi("Tráfico entrante", human_bytes(st[2])), Kpi("Orígenes únicos", str(st[3])),
                  Kpi("Conexiones bloqueadas", f"{st[4]:,}"), Kpi("Hallazgos relevantes", str(len(real))),
                  Kpi("Críticos / Altos", f"{sev.get('critical', 0)} / {sev.get('high', 0)}"),
                  Kpi("Ruido filtrado", f"{ratio:.0f}%")],
                 [_ftable("Principales hallazgos", top)],
                 [Chart("Hallazgos por severidad", "bar", [SEV_ES[s] for s in SEV_ORDER],
                        {"Hallazgos": [sev.get(s, 0) for s in SEV_ORDER]}, "Cantidad"),
                  Chart("Hallazgos por tipo", "pie", [TYPE_ES.get(t, t) for t in typ], {"Hallazgos": list(typ.values())})])


def _day(col):
    return epoch_bucket(col, 86400)


def mg_trends(db, pf, pt):
    traffic = db.execute(select(_day(L.ts).label("d"), func.coalesce(func.sum(L.bytes_out), 0),
                                func.coalesce(func.sum(L.bytes_in), 0), func.count())
                         .where(L.ts >= pf, L.ts <= pt).group_by("d").order_by("d")).all()
    fnd = db.execute(select(_day(Finding.first_seen).label("d"),
                            func.count().filter(Finding.is_noise.is_(False)), func.count().filter(Finding.is_noise.is_(True)))
                     .where(_fq(pf, pt)).group_by("d").order_by("d")).all()
    days = [r[0].strftime("%m-%d") for r in traffic]
    total_out = sum(int(r[1]) for r in traffic)
    first_half = sum(r[3] for r in traffic[: len(traffic) // 2])
    second_half = sum(r[3] for r in traffic[len(traffic) // 2:])
    trend = ("al alza" if second_half > first_half * 1.1 else "a la baja" if second_half < first_half * 0.9 else "estable")
    return _data("mg_trends", "Tendencias", "management", pf, pt,
                 f"El volumen de conexiones se mantiene {trend} entre la primera y la segunda mitad del período. "
                 f"Se transfirieron {human_bytes(total_out)} hacia el exterior en {len(traffic)} días con actividad.",
                 [Kpi("Días con actividad", str(len(traffic))), Kpi("Bytes salientes", human_bytes(total_out)),
                  Kpi("Hallazgos relevantes", str(sum(r[1] for r in fnd))), Kpi("Ruido", str(sum(r[2] for r in fnd)))],
                 [Table("Tráfico diario", ["Día", "Bytes salientes", "Bytes entrantes", "Conexiones"],
                        [[r[0].strftime("%Y-%m-%d"), int(r[1]), int(r[2]), r[3]] for r in traffic]),
                  Table("Hallazgos diarios", ["Día", "Relevantes", "Ruido"],
                        [[r[0].strftime("%Y-%m-%d"), r[1], r[2]] for r in fnd])],
                 [Chart("Tráfico diario (MB)", "line", days,
                        {"Salientes": [round(int(r[1]) / 1e6, 2) for r in traffic],
                         "Entrantes": [round(int(r[2]) / 1e6, 2) for r in traffic]}, "MB"),
                  Chart("Hallazgos diarios", "line", [r[0].strftime("%m-%d") for r in fnd],
                        {"Relevantes": [r[1] for r in fnd], "Ruido": [r[2] for r in fnd]}, "Hallazgos")])


def mg_response_metrics(db, pf, pt):
    fs = _findings(db, pf, pt, limit=20000)
    real = [f for f in fs if not f.is_noise]
    mtta = [(f.acknowledged_at - f.created_at).total_seconds() for f in real if f.acknowledged_at]
    mttr = [(f.resolved_at - f.created_at).total_seconds() for f in real if f.resolved_at]
    fp = sum(1 for f in real if f.status == "false_positive")
    reviewed = sum(1 for f in real if f.status in ("confirmed", "false_positive", "closed"))
    fp_rate = fp / reviewed * 100 if reviewed else 0
    noise = len(fs) - len(real)
    noise_rate = noise / len(fs) * 100 if fs else 0
    avg = lambda v: (sum(v) / len(v)) if v else None  # noqa: E731
    by_type = defaultdict(lambda: [0, 0.0, 0])
    for f in real:
        by_type[f.finding_type][0] += 1
        if f.resolved_at:
            by_type[f.finding_type][1] += (f.resolved_at - f.created_at).total_seconds()
            by_type[f.finding_type][2] += 1
    return _data("mg_response_metrics", "Métricas de respuesta", "management", pf, pt,
                 f"El tiempo medio de reconocimiento (MTTA) fue {human_duration(avg(mtta))} y el de resolución (MTTR) "
                 f"{human_duration(avg(mttr))}. La tasa de falsos positivos entre hallazgos revisados fue {fp_rate:.0f}% y el "
                 f"filtro de ruido descartó {noise} de {len(fs)} hallazgos ({noise_rate:.0f}%).",
                 [Kpi("MTTA", human_duration(avg(mtta))), Kpi("MTTR", human_duration(avg(mttr))),
                  Kpi("Tasa de falsos positivos", f"{fp_rate:.0f}%"), Kpi("Eficacia del filtro de ruido", f"{noise_rate:.0f}%"),
                  Kpi("Hallazgos revisados", str(reviewed)), Kpi("Pendientes (nuevos)", str(sum(1 for f in real if f.status == 'new')))],
                 [Table("Resolución por tipo", ["Tipo", "Hallazgos", "Resueltos", "MTTR promedio"],
                        [[TYPE_ES.get(t, t), v[0], v[2], human_duration(v[1] / v[2]) if v[2] else "n/d"]
                         for t, v in by_type.items()]),
                  Table("Estado de los hallazgos", ["Estado", "Cantidad"],
                        [[STATUS_ES[s], sum(1 for f in real if f.status == s)] for s in STATUS_ES])],
                 [Chart("Hallazgos por estado", "bar", list(STATUS_ES.values()),
                        {"Hallazgos": [sum(1 for f in real if f.status == s) for s in STATUS_ES]}),
                  Chart("Ruido vs relevantes", "pie", ["Relevantes", "Ruido"], {"Hallazgos": [len(real), noise]})])


def mg_user_activity(db, pf, pt):
    rows = db.execute(select(ModuleSession.username, ModuleSession.module, func.count(),
                             func.coalesce(func.sum(ModuleSession.duration_seconds), 0), func.max(ModuleSession.entered_at))
                      .where(ModuleSession.entered_at >= pf, ModuleSession.entered_at <= pt)
                      .group_by(ModuleSession.username, ModuleSession.module)
                      .order_by(func.sum(ModuleSession.duration_seconds).desc().nulls_last())).all()
    ev = dict(db.execute(select(AuditEvent.event_type, func.count()).where(AuditEvent.ts >= pf, AuditEvent.ts <= pt)
                         .group_by(AuditEvent.event_type)).all())
    per_user: dict[str, int] = defaultdict(int)
    for r in rows:
        per_user[r[0]] += int(r[3])
    return _data("mg_user_activity", "Actividad de usuarios", "management", pf, pt,
                 f"{len(per_user)} usuarios usaron el sistema en el período, con {sum(r[2] for r in rows)} visitas a módulos, "
                 f"{ev.get('login', 0)} inicios de sesión y {ev.get('login_failed', 0)} intentos fallidos.",
                 [Kpi("Usuarios activos", str(len(per_user))), Kpi("Visitas a módulos", str(sum(r[2] for r in rows))),
                  Kpi("Tiempo total", human_duration(sum(per_user.values()))), Kpi("Inicios de sesión", str(ev.get("login", 0))),
                  Kpi("Intentos fallidos", str(ev.get("login_failed", 0)))],
                 [Table("Actividad por usuario y módulo", ["Usuario", "Módulo", "Visitas", "Tiempo total (s)", "Última visita"],
                        [list(r) for r in rows])],
                 [Chart("Tiempo de uso por usuario (min)", "hbar", list(per_user.keys())[:10],
                        {"Minutos": [round(v / 60, 1) for v in list(per_user.values())[:10]]})])


SEV_WEIGHT = {"critical": 10, "high": 5, "medium": 2, "low": 1, "info": 0.2}
CRIT_MULT = {"critical": 2.0, "high": 1.5, "medium": 1.0, "low": 0.8}


def mg_risk_by_asset(db, pf, pt):
    fs = _findings(db, pf, pt, Finding.is_noise.is_(False), Finding.src_ip.is_not(None), limit=20000)
    assets = {a.ip: a for a in db.execute(select(Asset)).scalars()}
    agg: dict[str, dict] = defaultdict(lambda: {"n": 0, "risk": 0.0, "crit": 0, "max": 0.0})
    for f in fs:
        a = agg[f.src_ip]
        a["n"] += 1
        a["risk"] += SEV_WEIGHT.get(f.severity, 0) * (f.score / 100)
        a["crit"] += f.severity == "critical"
        a["max"] = max(a["max"], f.score)
    rows = []
    for ip, a in agg.items():
        asset = assets.get(ip)
        mult = CRIT_MULT.get(asset.criticality, 1.0) if asset else 1.0
        rows.append([ip, asset.hostname if asset else "", asset.criticality if asset else "sin registrar", a["n"],
                     a["crit"], round(a["max"], 1), round(a["risk"] * mult, 1)])
    rows.sort(key=lambda r: -r[6])
    top = rows[:10]
    return _data("mg_risk_by_asset", "Riesgo por activo", "management", pf, pt,
                 f"Se evaluó el riesgo de {len(rows)} equipos con hallazgos relevantes. El riesgo pondera severidad, puntaje y "
                 f"criticidad del activo. " + (f"El equipo de mayor riesgo es {rows[0][0]}." if rows else "No hay hallazgos en el período."),
                 [Kpi("Equipos con hallazgos", str(len(rows))), Kpi("Activos registrados", str(len(assets))),
                  Kpi("Riesgo máximo", str(rows[0][6] if rows else 0))],
                 [Table("Riesgo por activo", ["IP", "Host", "Criticidad", "Hallazgos", "Críticos", "Puntaje máx.",
                                              "Riesgo ponderado"], rows)],
                 [Chart("Top 10 equipos por riesgo ponderado", "hbar", [r[0] for r in top], {"Riesgo": [r[6] for r in top]})])


REPORTS: dict[str, ReportDef] = {r.code: r for r in [
    ReportDef("op_findings", "Hallazgos del período", "Listado de hallazgos con severidad, estado y veredicto de IA.",
              "operational", op_findings, ("findings:view",)),
    ReportDef("op_top_talkers", "Top talkers", "Equipos con mayor tráfico saliente y destinos únicos.",
              "operational", op_top_talkers, ("logs:view", "findings:view")),
    ReportDef("op_beaconing", "Beaconing", "Comunicaciones periódicas sospechosas (posible C2).",
              "operational", op_beaconing, ("findings:view",)),
    ReportDef("op_unusual_ports", "Puertos inusuales", "Tráfico saliente hacia puertos fuera de lo habitual.",
              "operational", op_unusual_ports, ("findings:view",)),
    ReportDef("op_ids_alerts", "Alertas IDS", "Alertas del IDS agrupadas por firma y categoría.",
              "operational", op_ids_alerts, ("logs:view", "findings:view")),
    ReportDef("op_ingestion", "Estado de la ingesta", "Ejecuciones de ingesta, volúmenes y errores de parseo.",
              "operational", op_ingestion, ("ingestion:view",)),
    ReportDef("op_audit_log", "Bitácora de auditoría", "Eventos de auditoría y sesiones de módulo.",
              "operational", op_audit_log, ("audit:view",)),
    ReportDef("mg_executive_summary", "Resumen ejecutivo", "Visión general de riesgo para la gerencia.",
              "management", mg_executive_summary, ("reports:view",)),
    ReportDef("mg_trends", "Tendencias", "Evolución diaria de tráfico y hallazgos.",
              "management", mg_trends, ("reports:view",)),
    ReportDef("mg_response_metrics", "Métricas de respuesta", "MTTA, MTTR, falsos positivos y eficacia del filtro de ruido.",
              "management", mg_response_metrics, ("reports:view",)),
    ReportDef("mg_user_activity", "Actividad de usuarios", "Uso del sistema por usuario y módulo.",
              "management", mg_user_activity, ("reports:view",)),
    ReportDef("mg_risk_by_asset", "Riesgo por activo", "Riesgo ponderado por equipo y criticidad.",
              "management", mg_risk_by_asset, ("reports:view",)),
]}


def _register_ml() -> None:
    from app.services.reports.ml_builders import ML_REPORTS

    for r in ML_REPORTS:
        REPORTS[r.code] = r


_register_ml()
