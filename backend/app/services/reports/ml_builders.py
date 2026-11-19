"""Reportes del Laboratorio ML (Fase 5). Usan el modelo común y los 3 renderizadores; cada tabla y figura lleva
título autosuficiente, nota (n, definiciones) y «Cómo leerlo / qué significa» generado a partir de los datos reales."""
from __future__ import annotations

from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.ml import dataset_service as DS
from app.ml import interpret as I
from app.ml import models as M
from app.ml.analysis import training_analysis
from app.ml.groups import GROUP_KEYS
from app.models import (MlDataset, MlDatasetVersion, MlFoldResult, MlJob, MlModel, MlPrediction, MlRun)
from app.services.reports.builders import ReportDef
from app.services.reports.model import Chart, Kpi, ReportData, Table


def to_chart(f: dict) -> Chart:
    ip = f.get("interpretation", {})
    return Chart(title=f["title"], kind=f["kind"], labels=[], series={}, spec={"kind": f["kind"], "title": f["title"], "data": f["data"]},
                 note=f.get("note", ""), meaning=ip.get("meaning", []), caution=ip.get("caution", []))


def to_table(t: dict) -> Table:
    ip = t.get("interpretation", {})
    cols = [c["key"] for c in t["columns"]]
    return Table(title=t["title"], columns=[c["label"] for c in t["columns"]],
                 rows=[[_cell(r.get(k)) for k in cols] for r in t["rows"]], decimals=3, note=t.get("note", ""),
                 meaning=ip.get("meaning", []), caution=ip.get("caution", []))


def _cell(v):
    if isinstance(v, (list, tuple)):
        return "[" + "; ".join(I.n(x, 3) if isinstance(x, float) else str(x) for x in v) + "]"
    if isinstance(v, dict):
        return ", ".join(f"{k}={x}" for k, x in v.items())
    return v


def _blocks(items: list[dict]) -> list:
    return [to_table(i) if i["kind"] == "table" else to_chart(i) for i in items]


def _by_id(items: list[dict]) -> dict:
    return {i["id"]: i for i in items}


def _kv_table(id_: str, title: str, rows: list[tuple[str, object]], note: str, meaning: list[str], caution: list[str]) -> dict:
    return I.table(id_, title, [("k", "Campo"), ("v", "Valor")], [{"k": k, "v": v} for k, v in rows], note, I.interp(meaning, caution))


def _need(params: dict, key: str) -> int:
    try:
        return int(params[key])
    except (KeyError, TypeError, ValueError):
        raise HTTPException(422, f"Falta el parámetro «{key}» para este reporte")


def _data(code, name, pf, pt, summary, kpis, blocks) -> ReportData:
    return ReportData(code=code, name=name, category="ml", period_from=pf, period_to=pt, summary=summary, kpis=kpis, blocks=blocks)


# ---------------------------------------------------------------------------------------------------------- dataset
def ml_dataset(db: Session, pf: datetime, pt: datetime, params: dict) -> ReportData:
    vid = _need(params, "dataset_version_id")
    v = db.get(MlDatasetVersion, vid)
    if v is None:
        raise HTTPException(404, "Versión de dataset no encontrada")
    ds = db.get(MlDataset, v.dataset_id)
    s = DS.summary(ds, v)
    val = DS.validation(ds, v)
    meta = v.meta
    ch = val["keys"][meta["group_key"]]
    meta_tbl = _kv_table("meta", "Metadatos del dataset y de la versión", [
        ("Nombre", meta["name"]), ("Versión", f"v{v.version} (hash {v.content_hash[:10]})"), ("Procedencia", meta["provenance"]),
        ("Licencia / atribución", meta["license"]), ("Unidad de análisis", "ventana host-tiempo" if meta["unit"] == "window" else "flujo"),
        ("Tamaño de ventana (min)", meta["window_minutes"] if meta["unit"] == "window" else "n/a"),
        ("Clave de agrupación", GROUP_KEYS[meta["group_key"]] + (f" (bloques de {meta['time_block_seconds']:g} s)" if meta["group_key"] == "time_block" else "")),
        ("Notas", meta.get("notes") or "—"), ("Duplicados de carga descartados", ds.n_duplicates_dropped)],
        f"Dataset #{ds.id}, creado por {ds.created_by}; {s['n_rows']} flujos en la instantánea (SHA-256 {ds.snapshot_sha256[:12]}).",
        [f"Se usan {I.n(s['n_labeled'])} {'ventanas' if meta['unit'] == 'window' else 'flujos'} con etiqueta conocida; {I.n(s['n_excluded'])} flujos Background/sin etiqueta se excluyen."],
        ["Un solo escenario de CTU-13: no se puede extrapolar a otras redes."])
    fi = _by_id(s["figures"])
    ti = _by_id(s["tables"])
    krows = []
    for k, r in val["keys"].items():
        cs = r.get("class_stats", {})
        krows.append({"key": r["label"], "viable": "Sí" if r.get("viable") else "No", "gb": cs.get("Botnet", {}).get("groups", "n/d"),
                      "gn": cs.get("Normal", {}).get("groups", "n/d"), "problem": (r["blocking"][0] if r.get("blocking") else "—")})
    valtbl = I.table("val_keys", "Validación de grupos (anti-fuga) por clave de agrupación",
                     [("key", "Clave"), ("viable", "Viable para 5×3"), ("gb", "Grupos Botnet"), ("gn", "Grupos Normal"), ("problem", "Problema principal")],
                     krows, f"n = {val['n_rows']} filas etiquetadas ({val['n_hosts_botnet']} hosts Botnet, {val['n_hosts_normal']} hosts Normal); semilla {val['seed']}.",
                     val["interpretation_global"])
    items = [meta_tbl, fi["classes"], ti["raw_labels"], fi.get("proto"), fi.get("state"), fi.get("ports"), fi.get("duration"),
             fi.get("bytes"), fi.get("nconn"), fi["timeseries"], ti["missing_outliers"], ti["class_comparison"], fi["correlation"],
             valtbl, val.get("partition_table")]
    items = [i for i in items if i]
    kp = [Kpi("Flujos etiquetados", I.n(s["n_labeled"])), Kpi("Botnet", I.n(s["n_botnet"])), Kpi("Normal", I.n(s["n_normal"])),
          Kpi("Excluidos (Background)", I.n(s["n_excluded"])), Kpi("Hosts Botnet", I.n(val["n_hosts_botnet"])),
          Kpi("Agrupación viable", "Sí" if ch.get("viable") else "NO")]
    summ = (f"Dataset «{meta['name']}» v{v.version}: {I.n(s['n_labeled'])} elementos etiquetados ({I.pct(s['n_botnet'] / max(s['n_labeled'], 1))} Botnet). "
            + (f"La agrupación «{GROUP_KEYS[meta['group_key']]}» es viable para 5×3 pliegues." if ch.get("viable")
               else f"La agrupación «{GROUP_KEYS[meta['group_key']]}» es INVIABLE: {ch['blocking'][0] if ch.get('blocking') else ''}"))
    return _data("ml_dataset", "ML · Dataset y validación de grupos", pf, pt, summ, kp, _blocks(items))


# ---------------------------------------------------------------------------------------------------------- training
def _job_runs(db: Session, job_id: int) -> tuple[MlJob, list[dict]]:
    j = db.get(MlJob, job_id)
    if j is None or j.kind != "train":
        raise HTTPException(404, "Trabajo de entrenamiento no encontrado")
    from app.api.routers.ml_training import run_dict

    runs = [run_dict(db, r) for r in db.execute(select(MlRun).where(MlRun.job_id == j.id, MlRun.status == "succeeded").order_by(MlRun.id)).scalars()]
    if not runs:
        raise HTTPException(409, "El trabajo no tiene ejecuciones terminadas")
    return j, runs


def ml_training(db: Session, pf: datetime, pt: datetime, params: dict) -> ReportData:
    j, runs = _job_runs(db, _need(params, "job_id"))
    a = training_analysis(j.params, (j.progress or {}).get("partition"), runs)
    c0 = runs[0]["config"]
    proto = _kv_table("protocol", "Protocolo de entrenamiento y reproducibilidad", [
        ("Validación cruzada", f"anidada {c0['n_outer']} pliegues externos × {c0['n_inner']} internos (StratifiedGroupKFold)"),
        ("Búsqueda", f"Optuna, muestreador {c0.get('sampler', 'tpe').upper()}, poda {c0.get('pruner', 'median')}, {c0['n_trials']} trials por pliegue"),
        ("Métrica objetivo", c0["metric"]), ("Agrupación", GROUP_KEYS.get(c0["group_key"], c0["group_key"])), ("Semilla", j.seed),
        ("Partición", "Desarrollo 70 % / Validación 15 % / Prueba 15 %, por grupos y estratificada"),
        ("Versiones de librerías", ", ".join(f"{k} {v}" for k, v in (j.libs or {}).items() if k in ("python", "scikit-learn", "optuna", "shap", "xgboost", "numpy", "pandas"))),
        ("Inicio / fin", f"{j.started_at:%Y-%m-%d %H:%M:%S} / {j.finished_at:%Y-%m-%d %H:%M:%S} UTC" if j.started_at and j.finished_at else "n/d"),
        ("Duración por modelo (s)", ", ".join(f"{M.MODEL_ES[r['model_type']]}: {r['duration_s']:.0f}" for r in runs if r['duration_s']))],
        f"Trabajo #{j.id} lanzado por {j.created_by}; ejecuciones: {len(runs)}.",
        [f"Cada modelo se evaluó con {c0['n_outer']} pliegues externos independientes; outer_val nunca participa en la búsqueda."],
        ["Validación por pliegues = una observación por pliegue; con n pequeño los IC son amplios."])
    items = [proto] + a["tables"][:1] + a["figures"] + a["tables"][1:]
    best = max((r for r in runs if r["model_type"] != "dummy"), key=lambda r: r["summary"]["cv"]["pr_auc"]["mean"] or 0, default=None)
    summ = (f"Entrenamiento anidado {c0['n_outer']}×{c0['n_inner']} de {len(runs)} modelos. "
            + (f"El mejor en PR-AUC externo es {M.MODEL_ES[best['model_type']]} ({I.n(best['summary']['cv']['pr_auc']['mean'], 3)} ± "
               f"{I.n(best['summary']['cv']['pr_auc']['std'], 3)})." if best else ""))
    kp = [Kpi("Modelos", str(len(runs))), Kpi("Pliegues externos", str(c0["n_outer"])), Kpi("Trials por pliegue", str(c0["n_trials"])),
          Kpi("Semilla", str(j.seed)), Kpi("Agrupación", GROUP_KEYS.get(c0["group_key"], c0["group_key"]))]
    return _data("ml_training", "ML · Entrenamiento y validación cruzada anidada", pf, pt, summ, kp, _blocks(items))


# ---------------------------------------------------------------------------------------------------------- evaluation
def ml_evaluation(db: Session, pf: datetime, pt: datetime, params: dict) -> ReportData:
    j, runs = _job_runs(db, _need(params, "job_id"))
    run_ids = [r["run_id"] for r in runs]
    res = None
    for e in db.execute(select(MlJob).where(MlJob.kind == "evaluate", MlJob.status == "succeeded").order_by(MlJob.id.desc())).scalars():
        if sorted(e.params.get("run_ids", [])) == sorted(run_ids) and e.result:
            res = e.result
            break
    if res is None:
        from app.ml.evaluation import compute_evaluation

        res = compute_evaluation(run_ids)
    items = [res["tables"][0], res["tables"][2]] + [f for f in res["figures"]] + [t for t in res["tables"] if t["id"] in ("stat_wilcoxon", "stat_mcnemar", "stat_bootstrap", "baselines", "metrics_folds")]
    # matriz de confusión en Prueba del mejor modelo
    from app.api.routers.ml_evaluation import confusion

    best = max((r for r in runs if r["model_type"] != "dummy"), key=lambda r: r["summary"]["cv"]["pr_auc"]["mean"] or 0, default=runs[0])
    cf = confusion(best["run_id"], None, db, None)
    items = items[:2] + cf["figures"] + items[2:]
    kp = [Kpi("Modelos comparados", str(len(runs))), Kpi("Pliegues externos", str(res["n_folds"])),
          Kpi("Casos en Prueba", I.n(res["test_n"])), Kpi("Prevalencia Botnet", I.pct(res["prevalence"])),
          Kpi("Mejor modelo (PR-AUC CV)", M.MODEL_ES[best["model_type"]])]
    summ = (f"Comparación de {len(runs)} modelos con el mismo protocolo y partición. En validación externa {M.MODEL_ES[best['model_type']]} "
            f"obtiene PR-AUC {I.n(best['summary']['cv']['pr_auc']['mean'], 3)}; en Prueba {I.n(best['test_metrics'].get('pr_auc'), 3)}. "
            f"Con {res['n_folds']} pliegues la potencia de las pruebas estadísticas es baja.")
    return _data("ml_evaluation", "ML · Evaluación y comparación de modelos", pf, pt, summ, kp, _blocks(items))


# ---------------------------------------------------------------------------------------------------------- explainability
def ml_explainability(db: Session, pf: datetime, pt: datetime, params: dict) -> ReportData:
    mid = _need(params, "model_id")
    m = db.get(MlModel, mid)
    if m is None:
        raise HTTPException(404, "Modelo no encontrado")
    res = None
    for j in db.execute(select(MlJob).where(MlJob.kind == "explain", MlJob.status == "succeeded").order_by(MlJob.id.desc())).scalars():
        if j.params.get("model_id") == mid and j.result:
            res = j.result
            break
    if res is None:
        raise HTTPException(409, "Este modelo aún no tiene explicabilidad: ejecútela en el módulo Explicabilidad")
    items = res["figures"][:2] + res["figures"][2:3] + [t for t in res["tables"] if t["id"] == "shap_vs_perm"] + res["figures"][3:] + \
        [t for t in res["tables"] if t["id"] == "explain_stability"]
    seen, ordered = set(), []
    for i in items:
        if i["id"] not in seen:
            seen.add(i["id"])
            ordered.append(i)
    top = res["shap_importance"][:3]
    summ = (f"Explicabilidad de «{m.name}»: variables más influyentes según SHAP: " + ", ".join(I.lab(t["feature"]) for t in top) + ". "
            f"Estabilidad entre pliegues: Kendall W = {I.n(res['kendall_w'])}.")
    kp = [Kpi("Modelo", m.name), Kpi("Variable principal", I.lab(top[0]["feature"]) if top else "n/d"),
          Kpi("Kendall W entre pliegues", I.n(res["kendall_w"])), Kpi("τ medio", I.n(res["mean_tau"])), Kpi("Espacio SHAP", res["space"])]
    return _data("ml_explainability", "ML · Explicabilidad del modelo", pf, pt, summ, kp, _blocks(ordered))


# ---------------------------------------------------------------------------------------------------------- inference
def ml_inference(db: Session, pf: datetime, pt: datetime, params: dict) -> ReportData:
    q = select(MlPrediction).where(MlPrediction.ts >= pf, MlPrediction.ts <= pt)
    if params.get("model_id"):
        q = q.where(MlPrediction.model_id == int(params["model_id"]))
    preds = list(db.execute(q.order_by(MlPrediction.ts.desc()).limit(2000)).scalars())
    sev_order = ["critical", "high", "medium", "low", "info"]
    sev_es = {"critical": "Crítica", "high": "Alta", "medium": "Media", "low": "Baja", "info": "Info"}
    counts = {s: sum(1 for p in preds if p.severity == s) for s in sev_order}
    n = len(preds)
    bots = sum(1 for p in preds if p.predicted_class == "Botnet")
    bins = [0, 0.1, 0.3, 0.5, 0.7, 0.9, 1.0001]
    hist = [sum(1 for p in preds if bins[i] <= p.probability < bins[i + 1]) for i in range(6)]
    ood = sum(1 for p in preds if (p.detail or {}).get("ood", {}).get("is_ood"))
    f_sev = I.fig("sev", "bars", "Predicciones por severidad", {"labels": [sev_es[s] for s in sev_order],
                  "series": [{"name": "Predicciones", "values": [counts[s] for s in sev_order]}], "ylabel": "Predicciones"},
                  f"n = {n} predicciones entre {pf:%Y-%m-%d} y {pt:%Y-%m-%d}.",
                  I.interp([f"{I.n(counts['critical'] + counts['high'])} de {I.n(n)} predicciones ({I.pct((counts['critical'] + counts['high']) / max(n, 1), 0)}) son de severidad alta o crítica."
                            if n else "No hay predicciones en el período."], ["La severidad combina probabilidad, incertidumbre, detector determinista y criticidad del activo."]))
    f_hist = I.fig("probhist", "bars", "Distribución de la probabilidad calibrada de Botnet",
                   {"labels": ["0–0,1", "0,1–0,3", "0,3–0,5", "0,5–0,7", "0,7–0,9", "0,9–1"], "series": [{"name": "Predicciones", "values": hist}],
                    "ylabel": "Predicciones", "xlabel": "Probabilidad"}, f"n = {n} predicciones.",
                   I.interp([f"{I.n(bots)} de {I.n(n)} predicciones se clasifican como Botnet al umbral del modelo." if n else "Sin datos."],
                            ["Las predicciones del período dependen de lo que el usuario eligió consultar: no representan el tráfico total."]))
    rows = [{"id": p.id, "ts": p.ts.strftime("%Y-%m-%d %H:%M:%S"), "kind": p.input_kind, "ref": p.input_ref, "prob": p.probability,
             "interval": [p.interval_low, p.interval_high], "klass": p.predicted_class, "sev": sev_es.get(p.severity, p.severity),
             "user": p.username, "narr": p.narrative_source} for p in preds]
    tbl = I.table("preds", "Predicciones del período", [("id", "ID"), ("ts", "Fecha (UTC)"), ("kind", "Entrada"), ("ref", "Referencia"),
                  ("prob", "Prob. calibrada"), ("interval", "Intervalo conforme"), ("klass", "Clase"), ("sev", "Severidad"),
                  ("user", "Usuario"), ("narr", "Narración")], rows, f"n = {n} predicciones (máx. 2000); probabilidades calibradas en Validación.",
                  I.interp([f"{I.n(ood)} predicciones marcaron variables fuera de distribución." if n else ""],
                           ["Revise manualmente las predicciones con aviso fuera de distribución o conjunto ambiguo."]))
    summ = f"Se registraron {n} predicciones en el período: {bots} Botnet; {counts['critical']} críticas y {counts['high']} altas."
    kp = [Kpi("Predicciones", str(n)), Kpi("Botnet", str(bots)), Kpi("Críticas", str(counts["critical"])),
          Kpi("Altas", str(counts["high"])), Kpi("Fuera de distribución", str(ood))]
    return _data("ml_inference", "ML · Predicciones del período", pf, pt, summ, kp, _blocks([f_sev, f_hist, tbl]))


# ---------------------------------------------------------------------------------------------------------- model card
def ml_model_card(db: Session, pf: datetime, pt: datetime, params: dict) -> ReportData:
    mid = _need(params, "model_id")
    m = db.get(MlModel, mid)
    if m is None:
        raise HTTPException(404, "Modelo no encontrado")
    run = db.get(MlRun, m.run_id)
    v = db.get(MlDatasetVersion, m.dataset_version_id)
    ds = db.get(MlDataset, v.dataset_id)
    j = db.get(MlJob, run.job_id)
    meta = v.meta
    t, cv = m.metrics["test"], m.metrics["cv"]
    cov = m.uncertainty.get("coverage_test", {})
    unit_es = "ventana host-tiempo" if m.unit == "window" else "flujo"
    s = DS.summary(ds, v)
    val = DS.validation(ds, v)
    fn100, fp100 = (1 - (t.get("recall") or 0)) * 100, (1 - (t.get("precision") or 0)) * 100
    data_tbl = _kv_table("card_data", "Datos de entrenamiento", [
        ("Dataset", f"{meta['name']} v{v.version}"), ("Procedencia", meta["provenance"]), ("Licencia / atribución", meta["license"]),
        ("Unidad", unit_es), ("Etiquetas", f"{I.n(s['n_botnet'])} Botnet / {I.n(s['n_normal'])} Normal; {I.n(s['n_excluded'])} excluidos (Background)"),
        ("Hosts con Botnet", val["n_hosts_botnet"]), ("Agrupación", GROUP_KEYS[meta["group_key"]]),
        ("Variables", f"versión {m.feature_spec_version}; sin IP, identificadores, marca de tiempo ni etiqueta")],
        f"Versión de dataset #{v.id}; SHA-256 de la instantánea {ds.snapshot_sha256[:12]}.",
        [f"El modelo se entrenó solo con {I.n(s['n_labeled'])} {unit_es}s de un escenario."], ["Un solo escenario CTU-13: validar antes de usar en otra red."])
    use_tbl = _kv_table("card_use", "Uso previsto", [
        ("Tarea", f"Clasificar cada {unit_es} como Botnet o Normal (probabilidad calibrada + clase al umbral {m.threshold:.3f})"),
        ("Usuarios", "Analistas de seguridad de una PYME; apoyo a la decisión, no decisión automática"),
        ("Integración", "Enriquece hallazgos del pipeline si se activa en Detección" + (" (modelo ACTIVO)" if m.is_active else "")),
        ("Fuera de alcance", "Tráfico cifrado sin metadatos de flujo, otras familias de malware no vistas, redes con perfil distinto")],
        "Descripción generada a partir de la configuración del modelo.", [f"El modelo opera sobre {unit_es}s; no examina contenido de paquetes."], [])
    perf = _kv_table("card_perf", "Rendimiento", [
        ("Modelo", f"{M.MODEL_ES[m.model_type]} — hiperparámetros: {run.final_params}"),
        ("PR-AUC CV externa (media ± desv.; IC 95 % t)", f"{I.n(cv['pr_auc']['mean'], 3)} ± {I.n(cv['pr_auc']['std'], 3)} [{I.n(cv['pr_auc']['ci_t'][0], 3)}; {I.n(cv['pr_auc']['ci_t'][1], 3)}]"),
        ("Prueba: PR-AUC / ROC-AUC", f"{I.n(t['pr_auc'], 3)} / {I.n(t['roc_auc'], 3)}"),
        ("Prueba: precisión / exhaustividad / F1 / MCC", f"{I.n(t['precision'], 3)} / {I.n(t['recall'], 3)} / {I.n(t['f1'], 3)} / {I.n(t['mcc'], 3)}"),
        ("Prueba: matriz", f"VP {t['tp']}, FP {t['fp']}, FN {t['fn']}, VN {t['tn']} (n = {t['n']})"),
        ("Calibración", f"{m.calibration_method} sobre Validación; Brier en Prueba {I.n(t['brier'], 3)}"),
        ("Incertidumbre", f"conforme dividida, cobertura nominal {I.pct(cov.get('nominal'), 0)}, empírica en Prueba {I.pct(cov.get('empirical_set'))}")],
        f"Prueba se usó una sola vez (n = {t['n']}, {t['n_pos']} Botnet).",
        [f"Al umbral {m.threshold:.3f}, {I.n(round(fn100))} de cada 100 flujos de botnet pasarían sin alerta y {I.n(round(fp100))} de cada 100 alertas serían falsas."],
        ["Pocos grupos en Prueba: cifras orientativas."])
    lim = []
    if val["n_hosts_botnet"] <= 5:
        lim.append(f"Solo {val['n_hosts_botnet']} hosts generaron tráfico Botnet: no se pudo validar por host; la agrupación usada ({GROUP_KEYS[meta['group_key']]}) es menos exigente y generaliza peor a hosts nuevos.")
    lim.append(f"Los datos provienen de un único escenario de {I.n(s['n_rows'])} flujos y {I.n(meta.get('span_minutes', 0), 1)} minutos de captura.")
    if cov and not cov.get("meets_nominal"):
        lim.append("La cobertura conforme observada en Prueba no alcanza la nominal.")
    lim.append(f"Con {run.config.get('n_outer', 5) if getattr(run, 'config', None) else 5} pliegues externos los intervalos de confianza son amplios y las pruebas entre modelos tienen baja potencia.")
    risk_tbl = _kv_table("card_risk", "Limitaciones y riesgos", [(f"Limitación {i + 1}", x) for i, x in enumerate(lim)] + [
        ("Riesgo: falsos negativos", f"{I.n(round(fn100))} de cada 100 botnets pasan sin alerta en Prueba"),
        ("Riesgo: falsas alarmas", f"{I.n(round(fp100))} de cada 100 alertas son falsas en Prueba"),
        ("Riesgo: deriva", "El tráfico real cambia con el tiempo; revise la calibración y reentrene periódicamente"),
        ("Reproducibilidad", f"semilla {j.seed}; SHA-256 del modelo {m.sha256[:16]}; librerías {', '.join(f'{k} {x}' for k, x in (j.libs or {}).items() if k in ('scikit-learn', 'optuna', 'xgboost', 'shap'))}")],
        "Generado a partir de los metadatos del dataset y las métricas reales.", lim[:2], [])
    summ = (f"Ficha del modelo «{m.name}»: PR-AUC en Prueba {I.n(t['pr_auc'], 3)}, F1 {I.n(t['f1'], 3)}; "
            f"{I.n(round(fn100))} de cada 100 botnets pasarían sin alerta. {lim[0]}")
    kp = [Kpi("Modelo", M.MODEL_ES[m.model_type]), Kpi("PR-AUC (Prueba)", I.n(t["pr_auc"], 3)), Kpi("F1 (Prueba)", I.n(t["f1"], 3)),
          Kpi("Umbral", I.n(m.threshold, 3)), Kpi("Activo en el pipeline", "Sí" if m.is_active else "No")]
    items = [data_tbl, use_tbl, perf]
    try:  # diagrama de fiabilidad en Prueba (figura a 600 DPI, como en el resto de reportes)
        from app.ml.metrics import reliability
        from app.ml.store import load_json

        pt_ = load_json(f"{run.artifact_dir}/preds.json")["test"]
        rel = reliability(pt_["y"], pt_["p"])
        items.append(I.fig("card_reliability", "lines", "Diagrama de fiabilidad (calibración) en Prueba",
                           {"series": [{"name": m.name, "x": rel["mean_predicted"], "y": rel["observed"], "points": True,
                                        "sizes": rel["n"]}],
                            "xlabel": "Probabilidad media predicha", "ylabel": "Frecuencia observada", "diagonal": True,
                            "xlim": [0, 1], "ylim": [0, 1.02]},
                           f"Prueba, n = {t['n']}; Brier {I.n(t.get('brier'), 3)}; ECE {I.n(rel['ece'], 3)}; calibración {m.calibration_method}.",
                           I.calibration_text(m.name, rel["ece"], t.get("brier"))))
    except Exception:  # la ficha sigue siendo válida sin la figura
        pass
    items.append(risk_tbl)
    return _data("ml_model_card", "ML · Ficha del modelo", pf, pt, summ, kp, _blocks(items))


ML_REPORTS = [
    ReportDef("ml_dataset", "ML · Dataset y validación de grupos", "Estadística descriptiva del dataset y validación anti-fuga de grupos.",
              "ml", ml_dataset, ("ml_data:view",), ("dataset_version_id",)),
    ReportDef("ml_training", "ML · Entrenamiento", "Protocolo, validación cruzada anidada e hiperparámetros.",
              "ml", ml_training, ("ml_training:view",), ("job_id",)),
    ReportDef("ml_evaluation", "ML · Evaluación", "Métricas con IC, matrices, curvas y pruebas estadísticas entre modelos.",
              "ml", ml_evaluation, ("ml_evaluation:view",), ("job_id",)),
    ReportDef("ml_explainability", "ML · Explicabilidad", "SHAP, permutación, mapas de calor, dependencia parcial, oclusión y estabilidad.",
              "ml", ml_explainability, ("ml_explain:view",), ("model_id",)),
    ReportDef("ml_inference", "ML · Predicciones del período", "Predicciones individuales registradas en el período.",
              "ml", ml_inference, ("ml_inference:view",), ()),
    ReportDef("ml_model_card", "ML · Ficha del modelo", "Datos, uso previsto, métricas, limitaciones y riesgos.",
              "ml", ml_model_card, ("ml_evaluation:view", "ml_inference:view"), ("model_id",)),
]
