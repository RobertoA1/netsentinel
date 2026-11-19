"""Datos JSON de un estudio Optuna para que el frontend dibuje sus gráficos (sin HTML de Plotly)."""
from __future__ import annotations

import math

import numpy as np
import optuna

from app.ml import interpret as I

STATE_ES = {"COMPLETE": "completo", "PRUNED": "podado", "RUNNING": "en curso", "FAIL": "fallido", "WAITING": "en espera"}


def load_study(storage, name: str):
    return optuna.load_study(study_name=name, storage=storage)


def trials_rows(study) -> list[dict]:
    rows = []
    t0 = None
    for t in study.get_trials(deepcopy=False):
        if t.datetime_start and (t0 is None or t.datetime_start < t0):
            t0 = t.datetime_start
    for t in study.get_trials(deepcopy=False):
        dur = (t.datetime_complete - t.datetime_start).total_seconds() if t.datetime_complete and t.datetime_start else None
        rows.append({"number": t.number, "state": t.state.name.lower(), "state_es": STATE_ES.get(t.state.name, t.state.name),
                     "value": t.value, "params": t.params, "duration_s": dur,
                     "start_s": (t.datetime_start - t0).total_seconds() if t.datetime_start and t0 else None,
                     "end_s": (t.datetime_complete - t0).total_seconds() if t.datetime_complete and t0 else None,
                     "pruned": t.state.name == "PRUNED"})
    return rows


def summary(study, rows: list[dict]) -> dict:
    done = [r for r in rows if r["state"] == "complete"]
    best = max(done, key=lambda r: r["value"], default=None)
    return {"n_trials": len(rows), "n_complete": len(done), "n_pruned": sum(r["pruned"] for r in rows),
            "n_running": sum(r["state"] == "running" for r in rows),
            "best_value": best["value"] if best else None, "best_number": best["number"] if best else None,
            "best_params": best["params"] if best else {}, "direction": "maximizar"}


def figures(study, rows: list[dict], space: list[dict], metric_es: str) -> list[dict]:
    done = [r for r in rows if r["state"] == "complete"]
    figs: list[dict] = []
    if not done:
        return figs
    s = summary(study, rows)
    # historial
    best, run = [], -math.inf
    for r in sorted(done, key=lambda r: r["number"]):
        run = max(run, r["value"])
        best.append(run)
    figs.append(I.fig("history", "lines", "Historial de optimización",
                      {"series": [{"name": "Valor del trial", "x": [r["number"] for r in done], "y": [r["value"] for r in done],
                                   "mode": "markers"},
                                  {"name": "Mejor hasta ahora", "x": [r["number"] for r in sorted(done, key=lambda r: r["number"])], "y": best,
                                   "bold": True}],
                       "xlabel": "Trial", "ylabel": metric_es},
                      f"n = {s['n_trials']} trials ({s['n_complete']} completos, {s['n_pruned']} podados).",
                      I.optuna_history(s["best_value"], s["n_trials"], s["n_pruned"],
                                       next((r["number"] for r in sorted(done, key=lambda r: r["number"]) if r["value"] >= s["best_value"] - 1e-12), None))))
    pnames = [p["name"] for p in space]
    # importancia (fANOVA)
    imp = []
    try:
        if len(done) >= 5:
            imps = optuna.importance.get_param_importances(
                study, evaluator=optuna.importance.FanovaImportanceEvaluator(seed=0))
            imp = [{"param": k, "value": float(v)} for k, v in imps.items()]
    except Exception:
        imp = []
    if imp:
        figs.append(I.fig("importance", "bars", "Importancia de hiperparámetros (fANOVA)",
                          {"labels": [i["param"] for i in imp], "series": [{"name": "Importancia", "values": [i["value"] for i in imp]}],
                           "horizontal": True, "xlabel": "Fracción de la varianza explicada"},
                          f"n = {len(done)} trials completos; fANOVA con bosque aleatorio.", I.optuna_importance(imp)))
    # coordenadas paralelas
    axes = []
    for p in space:
        if p["type"] == "categorical":
            axes.append({"name": p["name"], "categories": [str(c) for c in p["choices"]]})
        else:
            vals = [r["params"].get(p["name"]) for r in done if p["name"] in r["params"]]
            axes.append({"name": p["name"], "min": float(min(vals)) if vals else p["low"],
                         "max": float(max(vals)) if vals else p["high"], "log": bool(p.get("log"))})
    lines = []
    for r in done:
        vals = []
        for p, a in zip(space, axes):
            v = r["params"].get(p["name"])
            vals.append(str(v) if p["type"] == "categorical" else (None if v is None else float(v)))
        lines.append({"values": vals, "value": r["value"], "number": r["number"]})
    figs.append(I.fig("parcoords", "parcoords", "Coordenadas paralelas", {"axes": axes, "lines": lines, "objective": metric_es},
                      f"Cada línea es un trial completo (n = {len(done)}); color = valor de {metric_es}.",
                      I.interp([f"Las líneas de color más intenso (mejor valor) se agrupan en "
                                + ", ".join(f"{k}≈{I.n(v, 3) if isinstance(v, float) else v}" for k, v in list(s['best_params'].items())[:3]) + "."],
                               ["Es un gráfico exploratorio: no demuestra efectos por separado."])))
    # cortes por parámetro
    for p in space:
        if p["type"] == "categorical":
            cats = {}
            for r in done:
                cats.setdefault(str(r["params"].get(p["name"])), []).append(r["value"])
            figs.append(I.fig(f"slice_{p['name']}", "bars", f"Corte: {p['name']}",
                              {"labels": list(cats), "series": [{"name": "Valor medio", "values": [float(np.mean(v)) for v in cats.values()],
                                                                  "err": [float(np.std(v)) for v in cats.values()]}],
                               "ylabel": metric_es}, f"Media ± desv. del valor por categoría; n = {len(done)} trials.",
                              I.interp([f"La categoría con mayor valor medio es {max(cats, key=lambda k: np.mean(cats[k]))}."], ["Los cortes ignoran interacciones."])))
        else:
            x = [r["params"][p["name"]] for r in done if p["name"] in r["params"]]
            y = [r["value"] for r in done if p["name"] in r["params"]]
            if len(set(x)) > 1:
                rho = float(np.corrcoef(np.log10(x) if p.get("log") else x, y)[0, 1]) if np.std(y) > 0 else 0.0
                figs.append(I.fig(f"slice_{p['name']}", "lines", f"Corte: {p['name']}",
                                  {"series": [{"name": "Trials", "x": x, "y": y, "mode": "markers"}], "xlabel": p["name"],
                                   "ylabel": metric_es, "xlog": bool(p.get("log"))},
                                  f"Cada punto es un trial completo (n = {len(x)}).",
                                  I.interp([f"Correlación {I.n(rho)} entre {p['name']} y el valor: "
                                            + ("valores altos tienden a rendir mejor." if rho > 0.3 else "valores bajos tienden a rendir mejor." if rho < -0.3 else "relación débil.")],
                                           ["Los cortes ignoran interacciones entre parámetros."])))
    # contorno de pares (2 más importantes)
    top = [i["param"] for i in imp][:2] if len(imp) >= 2 else [p["name"] for p in space if p["type"] != "categorical"][:2]
    if len(top) == 2 and len(done) >= 6:
        pa = next(p for p in space if p["name"] == top[0])
        pb = next(p for p in space if p["name"] == top[1])
        if pa["type"] != "categorical" and pb["type"] != "categorical":
            xs = np.array([r["params"][top[0]] for r in done])
            ys = np.array([r["params"][top[1]] for r in done])
            vs = np.array([r["value"] for r in done])
            fx = np.log10(xs) if pa.get("log") else xs
            fy = np.log10(ys) if pb.get("log") else ys
            nb = 6
            ex, ey = np.linspace(fx.min(), fx.max() + 1e-9, nb + 1), np.linspace(fy.min(), fy.max() + 1e-9, nb + 1)
            ix, iy = np.digitize(fx, ex[1:-1]), np.digitize(fy, ey[1:-1])
            mat = [[None] * nb for _ in range(nb)]
            for a in range(nb):
                for b in range(nb):
                    m = (ix == a) & (iy == b)
                    mat[b][a] = round(float(vs[m].mean()), 4) if m.any() else None
            f_ = (lambda v: 10 ** v) if pa.get("log") else (lambda v: v)
            g_ = (lambda v: 10 ** v) if pb.get("log") else (lambda v: v)
            figs.append(I.fig("contour", "heatmap", f"Contorno de pares: {top[0]} × {top[1]}",
                              {"rows": [I.n(float(g_((ey[i] + ey[i + 1]) / 2)), 3) for i in range(nb)],
                               "cols": [I.n(float(f_((ex[i] + ex[i + 1]) / 2)), 3) for i in range(nb)], "values": mat,
                               "vlabel": f"{metric_es} medio", "scale": "seq", "vmin": float(vs.min()), "vmax": float(vs.max()),
                               "xlabel": top[0], "ylabel": top[1], "annotate": True},
                              f"Media del valor en 6×6 celdas de los dos hiperparámetros más importantes; n = {len(done)} trials.",
                              I.interp([f"La región de mayor {metric_es} medio es {I.n(float(np.nanmax([v for r in mat for v in r if v is not None])), 3)}."],
                                       ["Celdas vacías no fueron exploradas; con pocos trials el contorno es ruidoso."])))
    # línea de tiempo
    seg = [{"name": f"Trial {r['number']}", "x": [r["start_s"], r["end_s"]], "y": [r["number"], r["number"]],
            "state": r["state"]} for r in rows if r["start_s"] is not None and r["end_s"] is not None]
    if seg:
        figs.append(I.fig("timeline", "lines", "Línea de tiempo de trials",
                          {"series": seg, "xlabel": "Segundos desde el inicio del estudio", "ylabel": "Trial", "mode": "segments",
                           "legend": False},
                          f"Cada barra es un trial ({len(seg)}); naranja = podado.",
                          I.interp([f"El trial más largo duró {I.n(max(r['duration_s'] or 0 for r in rows), 1)} s y el más corto {I.n(min(r['duration_s'] or 0 for r in rows if r['duration_s'] is not None), 1)} s."],
                                   ["Los trials podados terminan antes: ahorran tiempo de cómputo."])))
    return figs
