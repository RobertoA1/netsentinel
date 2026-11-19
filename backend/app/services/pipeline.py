"""Orquestación de detección: SQL -> detectores puros -> listas -> upsert -> LLM -> alertas."""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.ports import service_name
from app.db.base import utcnow
from app.models import Asset, Finding, ListEntry
from app.schemas.settings import LLMSettings
from app.services import settings_service
from app.services.alerts.service import evaluate_alerts
from app.services.detectors import queries
from app.services.detectors.beaconing import detect_beaconing
from app.services.detectors.common import Candidate, DetectionConfig, bump, sev_rank
from app.services.detectors.exfil import detect_exfiltration, detect_talker_anomalies
from app.services.detectors.ids import detect_ids_alerts
from app.services.detectors.lists import ListMatcher
from app.services.detectors.ports import detect_unusual_ports
from app.services.llm.chain import LLMAnalyzer, compute_is_noise
from app.services.llm.templates import template_analysis

log = logging.getLogger("netsentinel.pipeline")
CRIT_BUMP = {"critical"}


@dataclass
class DetectionResult:
    findings_created: int = 0
    findings_updated: int = 0
    findings_noise: int = 0
    duration_ms: int = 0
    llm_used: int = 0
    new_ids: list[int] = field(default_factory=list)


def load_matcher(db: Session) -> ListMatcher:
    rows = db.execute(select(ListEntry.list_type, ListEntry.kind, ListEntry.value)).all()
    return ListMatcher([(r[0], r[1], r[2]) for r in rows])


def run_candidates(db: Session, cfg: DetectionConfig, ws: datetime, we: datetime) -> list[Candidate]:
    """Ejecuta los 5 detectores y devuelve candidatos tras aplicar allow/deny y criticidad del activo."""
    assets = {a.ip: a for a in db.execute(select(Asset)).scalars()}
    expected = {ip: {int(p) for p in (a.expected_ports or [])} for ip, a in assets.items()}
    cands: list[Candidate] = []

    groups = queries.beacon_groups(db, ws, we, cfg)
    beacons = detect_beaconing(groups, cfg, ws, we)
    by_key = {(g.src_ip, g.dst_ip, g.dst_port, g.proto): g for g in groups}
    for c in beacons[:100]:
        g = by_key[(c.src_ip, c.dst_ip, c.dst_port, c.proto)]
        c.evidence["intervals_sample"] = queries.interval_sample(db, g, ws, we)
    cands += beacons

    cands += detect_unusual_ports(queries.port_groups(db, ws, we, cfg), cfg, expected,
                                  queries.baseline_ports(db, ws), ws, we)

    hosts = queries.host_volumes(db, ws, we, cfg.exfil_min_bytes)
    base = queries.bucket_baselines(db, ws, cfg.detection_window_hours, "bytes_out", [h.src_ip for h in hosts])
    cands += detect_exfiltration(hosts, base, cfg, ws, we)

    cands += detect_ids_alerts(queries.ids_groups(db, ws, we), ws, we)

    talkers = queries.talker_stats(db, ws, we)
    cand_hosts = [t.src_ip for t in talkers if t.connections >= cfg.talker_min_connections
                  or t.unique_destinations >= cfg.talker_min_destinations]
    cands += detect_talker_anomalies(
        talkers, queries.bucket_baselines(db, ws, cfg.detection_window_hours, "connections", cand_hosts),
        queries.bucket_baselines(db, ws, cfg.detection_window_hours, "destinations", cand_hosts), cfg, ws, we)

    matcher = load_matcher(db)
    final: list[Candidate] = []
    for c in cands:
        a = assets.get(c.src_ip or "")
        if a is not None:
            c.context["asset"] = {"hostname": a.hostname, "type": a.asset_type, "criticality": a.criticality,
                                  "owner": a.owner, "expected_ports": sorted(expected.get(a.ip, []))}
            if a.criticality in CRIT_BUMP and c.finding_type in ("beaconing", "exfiltration"):
                c.severity = bump(c.severity, 1)
        r = matcher.apply(c)
        if r is not None:
            final.append(r)
    return final


def llm_context(f_type: str, title: str, severity: str, score: float, evidence: dict, src_ip, dst_ip, dst_port,
                proto, context: dict, window_hours: float) -> dict:
    return {
        "tipo_hallazgo": f_type, "titulo": title, "severidad_inicial": severity, "puntaje_0_100": score,
        "ventana_horas": round(window_hours, 1),
        "origen_ip": src_ip, "destino_ip": dst_ip, "puerto_destino": dst_port, "protocolo": proto,
        "servicio_del_puerto": service_name(dst_port) if dst_port else None,
        "evidencia_calculada": evidence,
        "activo_origen": context.get("asset"),
        "destino_en_lista_de_bloqueo": bool(context.get("in_denylist")),
    }


def apply_analysis(f: Finding, analyzer: LLMAnalyzer | None, ctx: dict, in_denylist: bool,
                   llm_settings: LLMSettings, use_llm: bool) -> bool:
    """Rellena veredicto/explicación/recomendación (LLM si responde, plantilla si no). True si usó LLM."""
    verdict = analyzer.analyze(ctx) if (use_llm and analyzer is not None) else None
    if verdict is None:
        f.llm_verdict, f.llm_confidence, f.llm_model = None, None, None
        f.is_noise = False
        f.llm_explanation, f.llm_recommendation = template_analysis(
            f.finding_type, f.evidence, f.src_ip, f.dst_ip, f.dst_port, in_denylist)
        return False
    f.llm_verdict, f.llm_confidence, f.llm_model = verdict.verdict, verdict.confidence, llm_settings.model
    f.llm_explanation, f.llm_recommendation = verdict.explanation, verdict.recommendation
    f.is_noise = compute_is_noise(verdict.verdict, verdict.confidence, llm_settings.noise_confidence_threshold)
    if verdict.severity_adjustment and not f.is_noise:
        f.severity = bump(f.severity, verdict.severity_adjustment)
    return True


def upsert_and_analyze(db: Session, cands: list[Candidate], window_hours: float, analyzer: LLMAnalyzer | None,
                       llm_settings: LLMSettings, result: DetectionResult) -> None:
    now = utcnow()
    keys = [c.dedup_key for c in cands]
    existing: dict[str, Finding] = {}
    if keys:
        rows = db.execute(select(Finding).where(Finding.dedup_key.in_(keys), Finding.status != "closed")
                          .order_by(Finding.id)).unique().scalars()
        for f in rows:
            existing[f.dedup_key] = f  # el más reciente gana

    new_pairs: list[tuple[Finding, Candidate]] = []
    to_alert: list[Finding] = []
    for c in cands:
        f = existing.get(c.dedup_key)
        if f is None:
            f = Finding(
                created_at=now, first_seen=c.first_seen, last_seen=c.last_seen, occurrences=1,
                dedup_key=c.dedup_key, finding_type=c.finding_type, severity=c.severity, score=c.score,
                status="new", title=c.title[:512], src_ip=c.src_ip, dst_ip=c.dst_ip, dst_port=c.dst_port,
                proto=c.proto, window_start=c.window_start, window_end=c.window_end, evidence=c.evidence)
            db.add(f)
            new_pairs.append((f, c))
        else:
            old_sev = f.severity
            if c.last_seen > f.last_seen:
                f.occurrences += 1
                f.last_seen = c.last_seen
            f.first_seen = min(f.first_seen, c.first_seen)
            f.score, f.evidence, f.title = c.score, c.evidence, c.title[:512]
            f.window_start, f.window_end = c.window_start, c.window_end
            if sev_rank(c.severity) > sev_rank(f.severity):
                f.severity = c.severity
            result.findings_updated += 1
            if sev_rank(f.severity) > sev_rank(old_sev) and not f.is_noise and f.status not in ("false_positive",):
                to_alert.append(f)
    db.flush()

    if new_pairs:  # ML opcional (apagado por defecto): añade evidence["ml"], que el LLM recibe como contexto
        from app.services.ml_inference import enrich_findings

        enrich_findings(db, [f for f, _ in new_pairs])

    new_pairs.sort(key=lambda p: -p[0].score)
    limit = llm_settings.max_findings_per_run
    for i, (f, c) in enumerate(new_pairs):
        ctx = llm_context(f.finding_type, f.title, f.severity, f.score, f.evidence, f.src_ip, f.dst_ip, f.dst_port,
                          f.proto, c.context, window_hours)
        used = apply_analysis(f, analyzer, ctx, bool(c.context.get("in_denylist")), llm_settings, i < limit)
        result.llm_used += int(used)
        result.findings_created += 1
        if f.is_noise:
            result.findings_noise += 1
        else:
            to_alert.append(f)
        result.new_ids.append(f.id)
    db.flush()
    for f in to_alert:
        evaluate_alerts(db, f)
    db.commit()


def run_detection(db: Session, window_hours: int | None = None, analyzer: LLMAnalyzer | None = None,
                  now: datetime | None = None) -> DetectionResult:
    t0 = time.monotonic()
    res = DetectionResult()
    cfg = DetectionConfig.from_dict(settings_service.get_setting(db, "detection").model_dump())
    llm_settings: LLMSettings = settings_service.get_setting(db, "llm")
    hours = window_hours or cfg.detection_window_hours
    cfg.detection_window_hours = hours
    last = queries.latest_log_ts(db)
    if last is None:
        res.duration_ms = int((time.monotonic() - t0) * 1000)
        return res
    we = last + timedelta(seconds=1)  # ventana anclada al último registro (sirve con datos históricos)
    ws = we - timedelta(hours=hours)
    cands = run_candidates(db, cfg, ws, we)
    if analyzer is None:
        analyzer = LLMAnalyzer(llm_settings)
    upsert_and_analyze(db, cands, hours, analyzer, llm_settings, res)
    res.duration_ms = int((time.monotonic() - t0) * 1000)
    log.info("Detección: +%d, ~%d, ruido %d, LLM %d", res.findings_created, res.findings_updated,
             res.findings_noise, res.llm_used)
    return res


def reanalyze_finding(db: Session, f: Finding, analyzer: LLMAnalyzer | None = None) -> Finding:
    llm_settings: LLMSettings = settings_service.get_setting(db, "llm")
    analyzer = analyzer or LLMAnalyzer(llm_settings)
    assets = {a.ip: a for a in db.execute(select(Asset).where(Asset.ip == (f.src_ip or ""))).scalars()}
    a = assets.get(f.src_ip or "")
    matcher = load_matcher(db)
    ctx_extra: dict = {"in_denylist": matcher.ip_in("deny", f.dst_ip) or matcher.ip_in("deny", f.src_ip)}
    if a:
        ctx_extra["asset"] = {"hostname": a.hostname, "type": a.asset_type, "criticality": a.criticality,
                              "owner": a.owner, "expected_ports": a.expected_ports}
    hours = ((f.window_end - f.window_start).total_seconds() / 3600) if f.window_start and f.window_end else 24
    ctx = llm_context(f.finding_type, f.title, f.severity, f.score, f.evidence, f.src_ip, f.dst_ip, f.dst_port,
                      f.proto, ctx_extra, hours)
    was_noise = f.is_noise
    apply_analysis(f, analyzer, ctx, bool(ctx_extra["in_denylist"]), llm_settings, True)
    db.flush()
    if was_noise and not f.is_noise:
        evaluate_alerts(db, f)
    db.commit()
    return f
