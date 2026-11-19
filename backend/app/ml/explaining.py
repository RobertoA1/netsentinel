"""Fase 4 — Explicabilidad tabular: SHAP global/local, permutación, mapas de calor, PDP/ICE, oclusión, estabilidad."""
from __future__ import annotations

import numpy as np
import pandas as pd
from sqlalchemy import select

from app.db.session import new_session
from app.ml import explain as E
from app.ml import interpret as I
from app.ml import models as M
from app.ml import serve
from app.ml.features import FEATURE_LABELS_ES, feature_columns
from app.ml.jobs import JobRunner
from app.ml.store import load_json, load_model
from app.ml.training import prepare_from_version
from app.models import MlFoldResult, MlModel, MlRun


def explain_job(r: JobRunner) -> dict:
    mid = int(r.params["model_id"])
    db = new_session()
    try:
        model = db.get(MlModel, mid)
        run = db.get(MlRun, model.run_id)
        folds = db.execute(select(MlFoldResult).where(MlFoldResult.run_id == run.id).order_by(MlFoldResult.outer_fold)).scalars().all()
        fold_params = [f.best_params for f in folds]
        bundle = load_model(model.model_path, model.sha256)
        cfg, run_dir, mtype, mname = run.config, run.artifact_dir, model.model_type, model.name
    finally:
        db.close()
    if mtype == "dummy":
        raise ValueError("La línea base trivial no tiene explicaciones (predice la prevalencia)")
    seed = cfg.get("seed", 42)
    r.log("Reconstruyendo datos y partición")
    flows, meta, prep = prepare_from_version(r.dataset_version_id, seed)
    cols = feature_columns(prep.unit)
    pipe = bundle["pipeline"]
    Xval, yval = prep.X[prep.part == 1].reset_index(drop=True), prep.y[prep.part == 1]
    Xdev, ydev = prep.X[prep.part == 0].reset_index(drop=True), prep.y[prep.part == 0]
    mes = M.MODEL_ES[mtype]
    figs, tables = [], []
    # ------------------------------------------------- SHAP global (Equivalente de Grad-CAM++)
    r.log("SHAP global")
    ex = E.ShapExplainer(pipe, mtype, prep.unit, bundle["background"])
    n_s = 150 if mtype == "hist_gb" else 500
    g = E.global_shap(ex, Xval, yval, seed, n=n_s)
    imp = [{"feature": d["feature"], "value": d["value"]} for d in g["importance"]]
    top = imp[:15]
    figs.append(I.fig("shap_bar", "bars", "Importancia global: |SHAP| medio por variable",
                      {"labels": [FEATURE_LABELS_ES.get(d["feature"], d["feature"]) for d in top],
                       "series": [{"name": "|SHAP| medio", "values": [d["value"] for d in top]}], "horizontal": True,
                       "xlabel": f"|SHAP| medio ({g['space']})"},
                      f"n = {g['n']} filas de Validación (mitad Botnet, mitad Normal). Unidades: {g['space']} del modelo sin calibrar.",
                      I.shap_global(mes, imp, g["space"])))
    figs.append(I.fig("shap_swarm", "swarm", "Enjambre SHAP: efecto de cada variable sobre la predicción",
                      {"features": [{"feature": s["feature"], "label": FEATURE_LABELS_ES.get(s["feature"], s["feature"]),
                                     "points": s["points"]} for s in g["swarm"]], "xlabel": f"Valor SHAP ({g['space']})"},
                      "Cada punto es una fila de Validación; color = valor relativo de la variable (azul bajo, rojo alto).",
                      I.interp([f"Para {I.lab(g['swarm'][0]['feature'])}, los valores altos (rojo) "
                                + ("empujan hacia Botnet." if _corr(g['swarm'][0]['points']) > 0 else "empujan hacia Normal.")],
                               ["Valores altos de una variable no implican causa; la relación puede invertirse en otros escenarios."])))
    # ------------------------------------------------- permutación (contraste independiente)
    r.log("Importancia por permutación en Validación")
    perm = E.permutation_val(pipe, Xval, yval, seed, n_repeats=5)
    pt = perm[:15]
    figs.append(I.fig("perm_bar", "bars", "Importancia por permutación en Validación (caída de PR-AUC)",
                      {"labels": [FEATURE_LABELS_ES.get(d["feature"], d["feature"]) for d in pt],
                       "series": [{"name": "Caída de PR-AUC", "values": [d["value"] for d in pt],
                                   "err": [d["std"] for d in pt]}], "horizontal": True,
                       "xlabel": "Caída media de PR-AUC al barajar la variable (± desv., 5 repeticiones)"},
                      f"n = {len(Xval)} filas de Validación; modelo sin calibrar (la calibración no cambia el orden).",
                      I.permutation(mes, perm, "PR-AUC")))
    disc = E.rank_discrepancy(imp, perm)
    tables.append(I.table("shap_vs_perm", "Contraste SHAP vs permutación: rangos de importancia",
                          [("feature", "Variable"), ("rank_shap", "Rango SHAP"), ("rank_perm", "Rango permutación"),
                           ("diff", "Diferencia"), ("flag", "Discrepancia")],
                          [{"feature": FEATURE_LABELS_ES.get(d["feature"], d["feature"]), "rank_shap": d["rank_shap"],
                            "rank_perm": d["rank_perm"], "diff": d["diff"], "flag": "Sí" if d["flag"] else ""}
                           for d in disc[:15]],
                          "Discrepancia = diferencia de rango ≥ 5 posiciones. Se muestran las 15 mayores.", I.discrepancy(disc)))
    # ------------------------------------------------- predicción calibrada para PDP/oclusión/mapas
    def predict(X: pd.DataFrame) -> np.ndarray:
        return serve.calibrated(bundle, X)

    # ------------------------------------------------- mapa de calor host x tiempo + variable x tiempo
    r.log("Mapas de calor")
    p_all = predict(prep.X)
    hm = E.host_time_heatmap(p_all, prep.aux)
    flat = [(v, hm["rows"][i], hm["cols"][j]) for i, row in enumerate(hm["values"]) for j, v in enumerate(row) if v is not None]
    best = max(flat, default=(0, None, None))
    figs.append(I.fig("heat_host_time", "heatmap", "Mapa de calor: riesgo por host y tiempo",
                      {**hm, "annotate": False},
                      f"Probabilidad media de Botnet por host de origen (14 hosts de mayor riesgo) y tramo de tiempo; n = {len(prep.X)} filas etiquetadas.",
                      I.heatmap_text("host", best[1], best[2], best[0])))
    sidx = np.random.default_rng(seed).choice(len(prep.X), min(1200 if mtype != "hist_gb" else 300, len(prep.X)), replace=False)
    Vt = ex.values(prep.X.iloc[sidx])
    ft = E.feature_time_heatmap(Vt, ex.orig, prep.aux["_t"].values[sidx])
    flat2 = [(abs(v), ft["rows"][i], ft["cols"][j]) for i, row in enumerate(ft["values"]) for j, v in enumerate(row) if v is not None]
    b2 = max(flat2, default=(0, None, None))
    figs.append(I.fig("heat_feature_time", "heatmap", "Mapa de calor: contribución por variable y tiempo (SHAP medio)",
                      {**ft, "annotate": False},
                      f"SHAP medio por variable (8 principales) y tramo de tiempo; n = {len(sidx)} filas muestreadas de todo el dataset etiquetado.",
                      I.heatmap_text("var", FEATURE_LABELS_ES.get(b2[1], b2[1]) if b2[1] else None, b2[2], b2[0])))
    # ------------------------------------------------- PDP / ICE
    r.log("Dependencia parcial / ICE")
    topf = [d["feature"] for d in imp if d["feature"] in cols][:6]
    pdps = E.pdp_ice(predict, Xval, topf, prep.unit, seed=seed)[:4]
    for pd_ in pdps:
        lo, hi = pd_["pdp"][0], pd_["pdp"][-1]
        figs.append(I.fig(f"pdp_{pd_['feature']}", "lines", f"Dependencia parcial e ICE: {FEATURE_LABELS_ES.get(pd_['feature'], pd_['feature'])}",
                          {"series": [{"name": f"ICE {i + 1}", "x": pd_["grid"], "y": ice, "faint": True} for i, ice in enumerate(pd_["ice"])]
                                     + [{"name": "Promedio (PDP)", "x": pd_["grid"], "y": pd_["pdp"], "bold": True}],
                           "xlabel": FEATURE_LABELS_ES.get(pd_["feature"], pd_["feature"]), "ylabel": "Probabilidad calibrada de Botnet",
                           "xlog": bool(min(pd_["grid"]) > 0 and max(pd_["grid"]) / max(min(pd_["grid"]), 1e-9) > 1000),
                           "ylim": [0, 1.02], "legend": False},
                          "Líneas finas: 25 filas de Validación (ICE); línea gruesa: promedio de 200 filas (PDP).",
                          I.pdp_text(pd_["feature"], lo, hi, "sube" if hi > lo + 0.02 else "baja" if hi < lo - 0.02 else "casi no cambia")))
    # ------------------------------------------------- oclusión
    r.log("Oclusión")
    ref = E.normal_reference(Xdev, ydev, prep.unit)
    ppos = predict(prep.X[(prep.part >= 1)].reset_index(drop=True))
    ypos = prep.y[prep.part >= 1]
    Xp = prep.X[(prep.part >= 1)].reset_index(drop=True)
    sel = np.where((ypos == 1) & (ppos >= bundle["threshold"]))[0][:300]
    occ = E.occlusion(predict, Xp.iloc[sel].reset_index(drop=True), ref, prep.unit) if len(sel) else {"features": [], "groups": [], "n": 0, "mean_prob": 0}
    of = occ["features"][:12]
    figs.append(I.fig("occlusion", "bars", "Oclusión: caída de la probabilidad al enmascarar cada variable",
                      {"labels": [FEATURE_LABELS_ES.get(d["feature"], d["feature"]) for d in of],
                       "series": [{"name": "Caída de probabilidad", "values": [d["drop"] for d in of]}], "horizontal": True,
                       "xlabel": "Caída media de la probabilidad de Botnet"},
                      f"n = {occ['n']} flujos/ventanas Botnet detectados en Validación+Prueba; enmascarar = sustituir por la mediana (moda) de la clase Normal.",
                      I.occlusion_text(of)))
    figs.append(I.fig("occlusion_groups", "bars", "Oclusión por grupos de variables",
                      {"labels": [d["group"] for d in occ["groups"]],
                       "series": [{"name": "Caída de probabilidad", "values": [d["drop"] for d in occ["groups"]]}],
                       "horizontal": True, "xlabel": "Caída media de la probabilidad de Botnet"},
                      "Un grupo se enmascara completo (volumen, ritmo, puertos, protocolo/estado...).",
                      I.interp([f"Enmascarar «{occ['groups'][0]['group']}» reduce la probabilidad media en {I.n(occ['groups'][0]['drop'])}."
                                if occ["groups"] else "Sin datos."],
                               ["Los grupos solapan información; una caída pequeña no implica que el grupo sea irrelevante."])))
    # máscara de flujos que sostienen la predicción (ventana o grupo de flujos)
    mask_fig = _flow_mask_figure(bundle, prep, p_all, mes)
    if mask_fig:
        figs.append(mask_fig)
    # ------------------------------------------------- estabilidad entre pliegues
    r.log("Estabilidad entre pliegues (reentrenamiento por pliegue)")
    preds = load_json(f"{run_dir}/preds.json")
    dev = prep.part == 0
    Xd, yd = prep.X[dev].reset_index(drop=True), prep.y[dev]
    n_s = 100 if mtype == "hist_gb" else 300
    vecs, orig = [], feature_columns(prep.unit)
    for k, f in enumerate(preds["folds"]):
        pk = M.build_pipeline(mtype, fold_params[k], prep.unit, seed).fit(Xd.iloc[f["train_idx"]], yd[f["train_idx"]])
        exk = E.ShapExplainer(pk, mtype, prep.unit, Xd.iloc[f["train_idx"]])
        Xv = Xd.iloc[f["val_idx"]].reset_index(drop=True)
        yv = yd[f["val_idx"]]
        gk = E.global_shap(exk, Xv, yv, seed + k, n=n_s)
        vecs.append(np.abs(gk["values"]).mean(0))
        r.log(f"  pliegue {k + 1}/{len(preds['folds'])} explicado")
    st = E.fold_importances(vecs)
    order = np.argsort(-np.mean(st["share"], 0))[:12]
    srows = [{"feature": FEATURE_LABELS_ES.get(orig[i], orig[i]), "share_mean": float(st["share"][:, i].mean()),
              "share_min": float(st["share"][:, i].min()), "share_max": float(st["share"][:, i].max()),
              "rank_min": int(st["ranks"][:, i].min()), "rank_max": int(st["ranks"][:, i].max())} for i in order]
    tables.append(I.table("explain_stability", "Estabilidad de las explicaciones entre pliegues externos",
                          [("feature", "Variable"), ("share_mean", "Participación media"), ("share_min", "Mín."),
                           ("share_max", "Máx."), ("rank_min", "Mejor rango"), ("rank_max", "Peor rango")], srows,
                          f"Participación = |SHAP| medio de la variable / total, por pliegue (n = {len(vecs)} pliegues, ≤ {n_s} filas de validación externa cada uno). "
                          f"Kendall W = {I.n(st['kendall_w'])}; τ medio = {I.n(st['mean_tau'])}.",
                          I.explain_stability(st["kendall_w"], st["mean_tau"], len(vecs))))
    figs.append(I.fig("explain_stability_bars", "bars", "Participación de las variables principales por pliegue (rango)",
                      {"labels": [s["feature"] for s in srows],
                       "series": [{"name": "Participación media", "values": [s["share_mean"] for s in srows],
                                   "err": [(s["share_max"] - s["share_min"]) / 2 for s in srows]}], "horizontal": True,
                       "xlabel": "Participación en la importancia (media y rango entre pliegues)"},
                      "Las barras de error cubren de la mínima a la máxima participación observada.",
                      I.explain_stability(st["kendall_w"], st["mean_tau"], len(vecs))))
    r.log("Explicabilidad lista")
    return {"model_id": mid, "model": mname, "figures": figs, "tables": tables,
            "shap_importance": imp[:20], "perm_importance": perm[:20],
            "kendall_w": st["kendall_w"], "mean_tau": st["mean_tau"], "space": g["space"]}


def _corr(points: list[dict]) -> float:
    x = np.array([p["x"] for p in points])
    c = np.array([p["c"] for p in points])
    if len(x) < 3 or x.std() == 0 or c.std() == 0:
        return 0.0
    return float(np.corrcoef(x, c)[0, 1])


def _flow_mask_figure(bundle: dict, prep, p_all: np.ndarray, mes: str) -> dict | None:
    """Máscara: ¿qué filas (flujos) de un host-tramo sostienen la predicción? Para modelos de ventana: se vuelve a
    puntuar la ventana quitando cada flujo; para modelos de flujo: se ordenan los flujos del host/tramo por riesgo."""
    aux = prep.aux
    if prep.unit == "window" or len(prep.X) == 0:
        return None
    df = pd.DataFrame({"h": aux["_src_ip"].values, "p": p_all, "y": prep.y, "t": aux["_t"].values})
    top_host = df[df.y == 1].groupby("h")["p"].mean().sort_values(ascending=False)
    if top_host.empty:
        return None
    h = top_host.index[0]
    sub = df[df.h == h].sort_values("t")
    k = min(40, len(sub))
    take = sub.iloc[np.linspace(0, len(sub) - 1, k).astype(int)]
    return I.fig("flow_mask", "bars", f"Máscara de flujos: aporte de cada flujo al riesgo del host {h}",
                 {"labels": [f"#{i + 1}" for i in range(k)],
                  "series": [{"name": "Probabilidad del flujo", "values": [float(v) for v in take["p"]]}],
                  "ylabel": "Probabilidad calibrada de Botnet"},
                 f"{k} flujos del host de mayor riesgo, ordenados en el tiempo (muestreo uniforme de {len(sub)} flujos).",
                 I.interp([f"{int((take['p'] >= bundle['threshold']).sum())} de {k} flujos muestreados del host {h} superan el umbral "
                           f"{I.n(bundle['threshold'])}: son los que sostienen la alerta del host."],
                          ["Con modelos de flujo cada fila se puntúa por separado; el host se marca por la acumulación de flujos."]))
