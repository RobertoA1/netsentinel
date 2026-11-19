"""Tablas y gráficos del entrenamiento (convergencia, dispersión, brecha de optimismo, estabilidad de hiperparámetros)."""
from __future__ import annotations

import numpy as np

from app.ml import interpret as I
from app.ml import models as M
from app.ml.metrics import METRIC_ES


def training_analysis(job_params: dict, partition: dict | None, runs: list[dict]) -> dict:
    """runs: [{run_id, model_type, config, summary, folds:[{outer,best_params,inner,metrics,curve,n_trials,n_pruned}], final_params}]"""
    figs, tables = [], []
    metric = (runs[0]["config"].get("metric") if runs else "pr_auc") or "pr_auc"
    mes_ = METRIC_ES.get(metric, metric)
    n_outer = runs[0]["config"].get("n_outer", 5) if runs else 5
    n_inner = runs[0]["config"].get("n_inner", 3) if runs else 3
    if partition:
        tables.append(I.table("partition", "Clase × partición (filas y grupos)",
                              [("partition", "Partición"), ("rows_botnet", "Filas Botnet"), ("rows_normal", "Filas Normal"),
                               ("groups_botnet", "Grupos Botnet"), ("groups_normal", "Grupos Normal")], partition["rows"],
                              f"Partición 70/15/15 por grupos y estratificada, n = {partition['n']} filas. Prueba se usa una sola vez al final; "
                              "Validación elige el umbral y calibra.", I.partition(partition)))
    dispersion, gap_models, gap_inner, gap_outer = [], [], [], []
    for r in runs:
        if r["model_type"] == "dummy":
            continue
        mes = M.MODEL_ES[r["model_type"]]
        folds = r["folds"]
        outer_v = [f["metrics"].get(metric) for f in folds]
        inner_v = [f["inner"] for f in folds]
        dispersion.append({"name": mes, "values": outer_v})
        gap_models.append(mes)
        gap_inner.append(inner_v)
        gap_outer.append(outer_v)
        # convergencia por pliegue externo
        series = []
        for f in folds:
            xs = [c["trial"] + 1 for c in f["curve"] if c.get("best") is not None]
            ys = [c["best"] for c in f["curve"] if c.get("best") is not None]
            series.append({"name": f"Pliegue {f['outer']}", "x": xs, "y": ys})
        npr = sum(f["n_pruned"] for f in folds)
        ntr = sum(f["n_trials"] for f in folds)
        best_curve = folds[0]["curve"] if folds else []
        figs.append(I.fig(f"conv_{r['run_id']}", "lines", f"Convergencia de la búsqueda — {mes}",
                          {"series": series, "xlabel": "Trial", "ylabel": f"Mejor {mes_} interno hasta el momento"},
                          f"Una curva por pliegue externo ({len(folds)}); cada punto es el mejor valor de CV interna ({n_inner} pliegues) hasta ese trial.",
                          I.convergence(mes, best_curve, npr // max(len(folds), 1), ntr // max(len(folds), 1))))
        # estabilidad de hiperparámetros
        keys = sorted({k for f in folds for k in f["best_params"]})
        rows = []
        for f in folds:
            rows.append({"fold": f["outer"], **{k: f["best_params"].get(k) for k in keys}, "inner": f["inner"],
                         "outer": f["metrics"].get(metric)})
        rows.append({"fold": "Final (Desarrollo)", **{k: r["final_params"].get(k) for k in keys}, "inner":
                     r["summary"].get("final_inner_best"), "outer": None})
        tables.append(I.table(f"hp_{r['run_id']}", f"Mejores hiperparámetros por pliegue — {mes}",
                              [("fold", "Pliegue")] + [(k, k) for k in keys] + [("inner", f"{mes_} interno"), ("outer", f"{mes_} externo")],
                              rows, f"n = {len(folds)} pliegues externos; la última fila es el modelo final sobre todo Desarrollo.",
                              I.hparam_stability(mes, {k: [f["best_params"].get(k) for f in folds] for k in keys})))
    if dispersion:
        figs.insert(0, I.fig("dispersion", "dots", f"Dispersión de {mes_} entre pliegues externos",
                             {"groups": dispersion, "ylabel": mes_},
                             f"Una observación por pliegue externo (n = {n_outer}); la marca es la media.",
                             I.cv_dispersion(dispersion[0]["name"], _agg(dispersion[0]["values"]), mes_)))
        gaps = []
        for m, i_, o_ in zip(gap_models, gap_inner, gap_outer):
            gaps.append((m, i_, o_))
        figs.insert(1, I.fig("gap", "bars", f"Brecha interna–externa de {mes_} (optimismo de la selección)",
                             {"labels": [f"{m}" for m, _, _ in gaps],
                              "series": [{"name": "Interna (búsqueda)", "values": [_mean(i) for _, i, _ in gaps]},
                                         {"name": "Externa (pliegue reservado)", "values": [_mean(o) for _, _, o in gaps]}],
                              "ylabel": mes_},
                             f"Media de {n_outer} pliegues; interna = mejor valor de CV de {n_inner} pliegues sobre outer_train; externa = valor en outer_val.",
                             I.optimism_gap(gaps[0][0], gaps[0][1], gaps[0][2], mes_)))
    return {"figures": figs, "tables": tables, "metric": metric}


def _mean(v):
    v = [x for x in v if x is not None]
    return float(np.mean(v)) if v else None


def _agg(values):
    from app.ml.metrics import aggregate

    return aggregate(values)
