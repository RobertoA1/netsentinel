"""Fase 3 — Evaluación: métricas con IC, curvas, calibración, pruebas estadísticas y comparación con referencias."""
from __future__ import annotations

import numpy as np

from app.db.session import new_session
from app.ml import baselines
from app.ml import interpret as I
from app.ml import models as M
from app.ml import stats_tests as S
from app.ml.jobs import JobRunner
from app.ml.metrics import (METRIC_ES, METRIC_NAMES, compute_metrics, curves, pr_band, reliability, roc_band,
                            metric_value)
from app.ml.store import load_json
from app.models import MlFoldResult, MlModel, MlRun
from sqlalchemy import select

CV_TABLE_METRICS = ["precision", "recall", "f1", "specificity", "balanced_accuracy", "mcc", "roc_auc", "pr_auc", "brier"]


def load_runs(run_ids: list[int]) -> list[dict]:
    db = new_session()
    try:
        out = []
        for rid in run_ids:
            run = db.get(MlRun, rid)
            if run is None or run.status != "succeeded":
                raise ValueError(f"La ejecución {rid} no existe o no terminó")
            model = db.execute(select(MlModel).where(MlModel.run_id == rid)).scalar_one()
            folds = db.execute(select(MlFoldResult).where(MlFoldResult.run_id == rid)
                               .order_by(MlFoldResult.outer_fold)).scalars().all()
            preds = load_json(f"{run.artifact_dir}/preds.json")
            met = load_json(f"{run.artifact_dir}/metrics.json")
            out.append({"run_id": rid, "model_id": model.id, "name": model.name, "model_type": run.model_type,
                        "threshold": model.threshold, "config": run.config, "preds": preds, "metrics": met,
                        "folds": [{"outer": f.outer_fold, "best_params": f.best_params, "inner": f.inner_best_value,
                                   "metrics": f.outer_metrics, "curve": f.curve, "n_trials": f.n_trials,
                                   "n_pruned": f.n_pruned, "sizes": f.sizes, "duration_s": f.duration_s} for f in folds],
                        "dataset_version_id": run.dataset_version_id, "job_id": run.job_id})
        return out
    finally:
        db.close()


def model_es(r: dict) -> str:
    return M.MODEL_ES[r["model_type"]]


def build_evaluation(runs: list[dict], detectors_pred: np.ndarray | None, metric: str = "pr_auc") -> dict:
    metric_es = METRIC_ES.get(metric, metric)
    figs, tables = [], []
    n_folds = len(runs[0]["folds"])
    seed = runs[0]["config"].get("seed", 42)
    # ---- tabla de métricas CV (media, desv., IC t, IC bootstrap)
    rows = []
    for r in runs:
        cv = r["metrics"]["cv"]
        row = {"model": model_es(r), "model_type": r["model_type"], "run_id": r["run_id"], "model_id": r["model_id"]}
        for m in CV_TABLE_METRICS:
            a = cv[m]
            row[m] = a["mean"]
            row[m + "_std"] = a["std"]
            row[m + "_ci_t"] = a["ci_t"]
            row[m + "_ci_boot"] = a["ci_boot"]
            row[m + "_txt"] = ("n/d" if a["mean"] is None else
                               f"{I.n(a['mean'], 3)} ± {I.n(a['std'], 3)} [{I.n(a['ci_t'][0], 3)}; {I.n(a['ci_t'][1], 3)}]")
        rows.append(row)
    cols = [("model", "Modelo")] + [(m + "_txt", METRIC_ES[m]) for m in CV_TABLE_METRICS]
    tables.append(I.table("metrics_cv", "Métricas por modelo en validación cruzada externa (media ± desv. [IC 95 % t])", cols,
                          rows, f"n = {n_folds} pliegues externos (una observación por pliegue); umbral 0,5; IC t de Student con "
                                f"{n_folds - 1} g.l. Precisión..Brier definidas sobre flujos/ventanas de validación externa.",
                          I.metrics_table(rows, metric_es)))
    # ---- por pliegue
    frows = []
    for r in runs:
        for f in r["folds"]:
            frows.append({"model": model_es(r), "fold": f["outer"], **{m: f["metrics"].get(m) for m in CV_TABLE_METRICS},
                          "n": f["metrics"]["n"], "n_pos": f["metrics"]["n_pos"]})
    tables.append(I.table("metrics_folds", "Métricas por pliegue externo",
                          [("model", "Modelo"), ("fold", "Pliegue"), ("n", "n"), ("n_pos", "Botnet")]
                          + [(m, METRIC_ES[m]) for m in CV_TABLE_METRICS], frows,
                          "Cada fila es la evaluación única del modelo reentrenado en ese pliegue sobre outer_val.",
                          I.interp([f"Se listan {len(frows)} evaluaciones (modelos × pliegues)."],
                                   ["Pliegues con pocos flujos Botnet producen métricas muy variables."])))
    # ---- métricas en Prueba
    trows = []
    for r in runs:
        t = r["metrics"]["test"]
        trows.append({"model": model_es(r), "threshold": t["threshold"], **{m: t.get(m) for m in CV_TABLE_METRICS},
                      "tp": t["tp"], "fp": t["fp"], "fn": t["fn"], "tn": t["tn"], "n": t["n"]})
    tables.append(I.table("metrics_test", "Métricas en el conjunto de Prueba (evaluación única, umbral elegido en Validación)",
                          [("model", "Modelo"), ("threshold", "Umbral"), ("n", "n")] + [(m, METRIC_ES[m]) for m in CV_TABLE_METRICS],
                          trows, "Prueba se usó UNA sola vez; probabilidades calibradas en Validación; n y casos Botnet en la matriz.",
                          I.interp([f"{trows[-1]['model']} obtiene PR-AUC {I.n(trows[-1]['pr_auc'], 3)} y F1 {I.n(trows[-1]['f1'], 3)} en Prueba."
                                    if trows else ""],
                                   ["Un solo escenario y pocos grupos en Prueba: trate estas cifras como orientativas."])))
    # ---- dispersión entre pliegues (métrica objetivo)
    groups = [{"name": model_es(r), "values": [f["metrics"].get(metric) for f in r["folds"]]} for r in runs]
    figs.append(I.fig("dispersion", "dots", f"{metric_es} por pliegue externo", {"groups": groups, "ylabel": metric_es},
                      f"Cada punto es un pliegue externo (n = {n_folds}); la marca es la media.",
                      I.cv_dispersion(model_es(runs[-1]), runs[-1]["metrics"]["cv"][metric], metric_es)))
    # ---- ROC / PR con banda entre pliegues + calibración en Prueba
    roc_series, pr_series, cal_series = [], [], []
    for r in runs:
        fy = [np.array(f["y"]) for f in r["preds"]["folds"]]
        fp = [np.array(f["p"]) for f in r["preds"]["folds"]]
        if r["model_type"] != "dummy":
            b = roc_band(fy, fp)
            roc_series.append({"name": model_es(r), "x": b["x"], "y": b["mean"], "lo": b["lo"], "hi": b["hi"]})
            pb = pr_band(fy, fp)
            pr_series.append({"name": model_es(r), "x": pb["x"], "y": pb["mean"], "lo": pb["lo"], "hi": pb["hi"]})
        t = r["preds"]["test"]
        rel = reliability(t["y"], t["p"])
        if r["model_type"] != "dummy":
            cal_series.append({"name": model_es(r), "x": rel["mean_predicted"], "y": rel["observed"], "points": True,
                               "sizes": rel["n"]})
        r["_ece"] = rel["ece"]
    prev = float(np.mean(np.concatenate([np.array(f["y"]) for f in runs[0]["preds"]["folds"]])))
    best = max((r for r in runs if r["model_type"] != "dummy"), key=lambda r: r["metrics"]["cv"]["pr_auc"]["mean"] or 0,
               default=runs[0])
    bcv = best["metrics"]["cv"]
    figs.append(I.fig("roc", "lines", "Curva ROC (media ± desv. entre pliegues externos)",
                      {"series": roc_series, "xlabel": "Tasa de falsos positivos (1 − especificidad)",
                       "ylabel": "Exhaustividad (TPR)", "diagonal": True, "xlim": [0, 1], "ylim": [0, 1.02]},
                      "Banda = ± 1 desv. estándar entre pliegues; línea punteada = azar.",
                      I.roc_text(model_es(best), bcv["roc_auc"]["mean"], bcv["roc_auc"]["std"], n_folds)))
    figs.append(I.fig("pr", "lines", "Curva precisión-exhaustividad (media ± desv. entre pliegues externos)",
                      {"series": pr_series, "xlabel": "Exhaustividad", "ylabel": "Precisión",
                       "hlines": [{"y": prev, "label": f"Azar = prevalencia {I.n(prev, 3)}"}], "xlim": [0, 1],
                       "ylim": [0, 1.02]}, "Línea horizontal = prevalencia de Botnet (referencia de azar).",
                      I.pr_text(model_es(best), bcv["pr_auc"]["mean"], prev)))
    figs.append(I.fig("calibration", "lines", "Curva de calibración (diagrama de fiabilidad) en Prueba",
                      {"series": cal_series, "xlabel": "Probabilidad media predicha", "ylabel": "Frecuencia observada de Botnet",
                       "diagonal": True, "xlim": [0, 1], "ylim": [0, 1.02]},
                      "Diez intervalos de probabilidad; el tamaño del punto es proporcional al nº de casos. Diagonal = calibración perfecta.",
                      I.calibration_text(model_es(best), best["_ece"], best["metrics"]["test"]["brier"])))
    # ---- pruebas estadísticas
    tab = {model_es(r): [f["metrics"].get(metric) for f in r["folds"]] for r in runs}
    fr = S.friedman(tab)
    wil = S.pairwise_wilcoxon(tab)
    wrows = [{"a": w["a"], "b": w["b"], "mean_diff": w["mean_diff"], "cohen_dz": w["cohen_dz"],
              "cliffs_delta": w["cliffs_delta"], "p": w["p_value"], "p_holm": w["p_holm"],
              "sig": "Sí" if w["significant_005"] else "No"} for w in wil]
    ip = I.stat_tests(fr, wil, n_folds, metric_es)
    tables.append(I.table("stat_wilcoxon", f"Comparaciones por pares de {metric_es}: Wilcoxon exacto + Holm y tamaños de efecto",
                          [("a", "Modelo A"), ("b", "Modelo B"), ("mean_diff", "Dif. media (A−B)"),
                           ("cohen_dz", "d de Cohen pareada"), ("cliffs_delta", "Delta de Cliff"), ("p", "p"),
                           ("p_holm", "p Holm"), ("sig", "Signif. 5 %")], wrows,
                          f"n = {n_folds} pliegues pareados. Friedman: "
                          + (f"χ²={I.n(fr['statistic'])}, p={I.n(fr['p_value'], 3)}, {fr['k_models']} modelos."
                             if fr.get("applicable") else fr.get("reason", "")) +
                          f" p mínimo alcanzable (Wilcoxon bilateral, n={n_folds}): {I.n(2 / 2 ** n_folds, 4)}.", ip))
    # McNemar y bootstrap pareado en Prueba
    ty = np.array(runs[0]["preds"]["test"]["y"])
    tg = np.array(runs[0]["preds"]["test"]["groups"])
    pred = {model_es(r): (np.array(r["preds"]["test"]["p"]) >= r["threshold"]).astype(int) for r in runs}
    probs = {model_es(r): np.array(r["preds"]["test"]["p"]) for r in runs}
    mrows, brows = [], []
    names = list(pred)
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = names[i], names[j]
            mc = S.mcnemar(ty, pred[a], pred[b])
            mrows.append({"a": a, "b": b, "b_count": mc["b_a_right_b_wrong"], "c_count": mc["c_a_wrong_b_right"],
                          "p": mc["p_value"]})
            for mt in ("pr_auc", "roc_auc"):
                bb = S.paired_bootstrap_diff(ty, probs[a], probs[b], tg, mt, 1000, seed)
                brows.append({"a": a, "b": b, "metric": METRIC_ES[mt], "diff": bb["diff"],
                              "ci": f"[{I.n(bb['ci'][0], 3)}; {I.n(bb['ci'][1], 3)}]" if bb["ci"][0] is not None else "n/d",
                              "excludes0": "Sí" if bb.get("ci_excludes_zero") else "No"})
    n_test = int(len(ty))
    tables.append(I.table("stat_mcnemar", "McNemar exacto sobre predicciones emparejadas en Prueba",
                          [("a", "Modelo A"), ("b", "Modelo B"), ("b_count", "A acierta, B falla"),
                           ("c_count", "A falla, B acierta"), ("p", "p")], mrows,
                          f"n = {n_test} casos de Prueba; cada modelo a su umbral. Solo cuentan los casos discordantes.",
                          I.interp([f"{sum(1 for m in mrows if m['p'] < 0.05)} de {len(mrows)} pares difieren significativamente al 5 % (sin corrección múltiple)."
                                    if mrows else "Un solo modelo: no hay pares."],
                                   ["Se reportan también los resultados no significativos; sin corrección de Holm."])))
    tables.append(I.table("stat_bootstrap", "Diferencia de PR-AUC / ROC-AUC con IC 95 % por bootstrap emparejado (por grupos)",
                          [("a", "Modelo A"), ("b", "Modelo B"), ("metric", "Métrica"), ("diff", "Diferencia (A−B)"),
                           ("ci", "IC 95 %"), ("excludes0", "IC excluye 0")], brows,
                          f"1000 remuestreos de GRUPOS con reemplazo en Prueba (n = {n_test} casos, {len(set(tg.tolist()))} grupos).",
                          I.interp([f"{sum(1 for b in brows if b['excludes0'] == 'Sí')} de {len(brows)} diferencias tienen un IC que excluye el cero."
                                    if brows else "Sin pares."],
                                   ["Con pocos grupos en Prueba el IC es amplio; la diferencia observada puede ser azar."])))
    # ---- referencias: trivial y detectores deterministas (misma partición de Prueba)
    brow = []
    for r in runs:
        t = r["metrics"]["test"]
        brow.append({"kind": "dummy" if r["model_type"] == "dummy" else "model", "name": model_es(r),
                     "precision": t["precision"], "recall": t["recall"], "f1": t["f1"], "mcc": t["mcc"],
                     "balanced_accuracy": t["balanced_accuracy"], "pr_auc": t["pr_auc"]})
    if detectors_pred is not None:
        dm = compute_metrics(ty, detectors_pred.astype(float), 0.5)
        brow.append({"kind": "detectors", "name": "Detectores deterministas de NetSentinel", "precision": dm["precision"],
                     "recall": dm["recall"], "f1": dm["f1"], "mcc": dm["mcc"],
                     "balanced_accuracy": dm["balanced_accuracy"], "pr_auc": None})
    tables.append(I.table("baselines", "Comparación con las dos referencias obligatorias (Prueba)",
                          [("name", "Método"), ("precision", "Precisión"), ("recall", "Exhaustividad"), ("f1", "F1"),
                           ("mcc", "MCC"), ("balanced_accuracy", "Exac. balanceada"), ("pr_auc", "PR-AUC")], brow,
                          f"Mismas etiquetas y misma partición de Prueba (n = {n_test}). Detectores: beaconing + puertos inusuales "
                          "con la configuración por defecto.", I.baseline_comparison(brow)))
    return {"figures": figs, "tables": tables, "friedman": fr, "metric": metric, "n_folds": n_folds,
            "models": [{"run_id": r["run_id"], "model_id": r["model_id"], "name": model_es(r), "model_type": r["model_type"]}
                       for r in runs], "test_n": n_test, "prevalence": prev}


def compute_evaluation(run_ids: list[int], log=lambda m: None) -> dict:
    from app.ml.training import prepare_from_version

    runs = load_runs([int(x) for x in run_ids])
    if len({x["dataset_version_id"] for x in runs}) != 1 or len({x["job_id"] for x in runs}) != 1:
        raise ValueError("Las ejecuciones deben pertenecer al mismo trabajo de entrenamiento (misma partición y pliegues)")
    log(f"Evaluando {len(runs)} modelos")
    det = None
    try:
        seed = runs[0]["config"].get("seed", 42)
        flows, meta, prep = prepare_from_version(runs[0]["dataset_version_id"], seed)
        test = prep.part == 2
        from app.ml.data import labelled_frame

        d = labelled_frame(flows, meta["label_map"])
        det_all = baselines.flagged_for_prepared(d, prep.aux, prep.unit, prep.window_minutes)
        det = det_all[test]
        if len(det) != len(runs[0]["preds"]["test"]["y"]):
            raise ValueError("La partición de Prueba recalculada no coincide con la guardada")
    except Exception as e:  # los detectores son una referencia: no deben impedir la evaluación
        log(f"No se pudieron evaluar los detectores deterministas: {e}")
    return build_evaluation(runs, det, runs[0]["config"].get("metric", "pr_auc"))


def evaluate_job(r: JobRunner) -> dict:
    res = compute_evaluation(r.params["run_ids"], r.log)
    r.log("Evaluación lista")
    return res
