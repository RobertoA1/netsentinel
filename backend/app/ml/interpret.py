"""Capa de interpretabilidad: genera, de forma DETERMINISTA a partir de los números reales, el bloque
«Qué significa» (1-3 frases) y «Precaución» de cada tabla y gráfico. Ningún texto es fijo: todos dependen de los datos.

Contrato de salida común (lo consume el componente `FigureCard`/`DataTable` del frontend y los reportes):
  figura: {"id","kind","title","note","data":{...},"interpretation":{"meaning":[...],"caution":[...]}}
  tabla : {"id","kind":"table","title","note","columns":[{"key","label"}],"rows":[{...}],"interpretation":{...}}
"""
from __future__ import annotations

import math
from typing import Any

from app.ml.features import FEATURE_LABELS_ES

LOW_POWER_N = 8


def n(x: Any, d: int = 2) -> str:
    """Número en formato es-PE (coma decimal)."""
    if x is None or (isinstance(x, float) and (math.isnan(x) or math.isinf(x))):
        return "n/d"
    if isinstance(x, int) and not isinstance(x, bool):
        return f"{x:,}".replace(",", " ")
    return f"{x:.{d}f}".replace(".", ",")


def pct(x: Any, d: int = 1) -> str:
    return "n/d" if x is None else f"{n(100 * float(x), d)} %"


def lab(c: str) -> str:
    return FEATURE_LABELS_ES.get(c, c)


def interp(meaning: list[str], caution: list[str] | None = None) -> dict:
    return {"meaning": [m for m in meaning if m][:3], "caution": [c for c in (caution or []) if c]}


def fig(id_: str, kind: str, title: str, data: dict, note: str, ip: dict) -> dict:
    return {"id": id_, "kind": kind, "title": title, "note": note, "data": data, "interpretation": ip}


def table(id_: str, title: str, columns: list[tuple[str, str]], rows: list[dict], note: str, ip: dict) -> dict:
    return {"id": id_, "kind": "table", "title": title, "note": note,
            "columns": [{"key": k, "label": l} for k, l in columns], "rows": rows, "interpretation": ip}


# ---------------------------------------------------------------- Fase 1: datos
def class_distribution(n_botnet: int, n_normal: int, n_excluded: int, unit_es: str) -> dict:
    tot = max(n_botnet + n_normal, 1)
    prev = n_botnet / tot
    meaning = [f"De {n(tot)} {unit_es} con etiqueta conocida, {n(n_botnet)} son Botnet ({pct(prev)}) y {n(n_normal)} son "
               f"Normal ({pct(1 - prev)}).",
               f"Un clasificador trivial que dijera siempre «{'Botnet' if prev >= 0.5 else 'Normal'}» acertaría "
               f"{pct(max(prev, 1 - prev))} sin aprender nada: ese es el piso que un modelo debe superar."]
    caution = []
    if min(prev, 1 - prev) < 0.10:
        caution.append(f"Desbalance fuerte (clase rara {pct(min(prev, 1 - prev))}): la exactitud engaña; use PR-AUC, F1 o MCC.")
    if n_excluded:
        caution.append(f"{n(n_excluded)} {unit_es} Background/sin etiqueta se excluyen del entrenamiento y la evaluación "
                       "(no tienen verdad conocida); sí pueden puntuarse en inferencia.")
    caution.append("Datos de un solo escenario de CTU-13: los resultados no se pueden extrapolar a otras redes sin validarlos.")
    return interp(meaning, caution)


def validation(v: dict) -> dict:
    """v: resultado de validate_key para la clave elegida (+ recomendación global)."""
    label = v.get("label", "")
    cs = v.get("class_stats", {})
    nb, nn = cs.get("Botnet", {}).get("groups", 0), cs.get("Normal", {}).get("groups", 0)
    if v.get("viable"):
        meaning = [f"Con la agrupación «{label}» hay {n(nb)} grupos de Botnet y {n(nn)} de Normal: alcanza para 5 pliegues "
                   "externos y 3 internos sin que un grupo quede repartido entre particiones."]
    else:
        meaning = [f"Con la agrupación «{label}» solo hay {n(nb)} grupo(s) de Botnet y {n(nn)} de Normal: la validación anidada "
                   "no es viable y el entrenamiento queda BLOQUEADO."]
    meaning.append("Los " + ("pliegues no comparten grupos: ningún grupo está a la vez en entrenamiento y validación."
                             if v.get("groups_split_across_partitions", 0) == 0 else
                             f"grupos repartidos entre particiones son {n(v['groups_split_across_partitions'])}: hay fuga."))
    return interp(meaning, list(v.get("blocking", [])) + list(v.get("warnings", [])))


def validation_global(g: dict) -> dict:
    rec, k = g.get("recommended"), g.get("chosen")
    from app.ml.groups import GROUP_KEYS
    meaning = []
    if g["n_hosts_botnet"] <= 5:
        meaning.append(f"Solo {n(g['n_hosts_botnet'])} hosts generan flujos Botnet: agrupar por host NO permite 5 pliegues "
                       "(cada pliegue necesita al menos un host Botnet distinto en validación y otro en entrenamiento).")
    if rec is None:
        meaning.append("Ninguna agrupación probada es viable con este dataset: cargue más escenarios o más tiempo de captura.")
    else:
        extra = f" con bloques de {n(g.get('recommended_block_seconds'), 0)} s" if rec == "time_block" else ""
        meaning.append(f"Agrupación recomendada: «{GROUP_KEYS[rec]}»{extra}. "
                       + ("Es la más exigente de las viables." if rec == "src_ip" else
                          "Es una validación MENOS exigente que por host y generaliza peor a hosts nuevos."))
    caution = []
    if k != rec and rec is not None:
        caution.append(f"La agrupación elegida («{GROUP_KEYS.get(k, k)}») no es la recomendada.")
    return interp(meaning, caution)


def partition(pt: dict) -> dict:
    rows = pt["rows"]
    tot_b = sum(r["rows_botnet"] for r in rows) or 1
    tot_n = sum(r["rows_normal"] for r in rows) or 1
    d, v, t = rows
    meaning = [f"Desarrollo recibe {pct(d['rows_botnet'] / tot_b, 0)} de los Botnet y {pct(d['rows_normal'] / tot_n, 0)} de los "
               f"Normal; Validación {pct(v['rows_botnet'] / tot_b, 0)} / {pct(v['rows_normal'] / tot_n, 0)}; Prueba "
               f"{pct(t['rows_botnet'] / tot_b, 0)} / {pct(t['rows_normal'] / tot_n, 0)} (objetivo 70/15/15).",
               f"Prueba contiene {n(t['groups_botnet'])} grupo(s) de Botnet y {n(t['groups_normal'])} de Normal que el modelo "
               "nunca ve durante el entrenamiento ni la selección."]
    caution = []
    if min(t["groups_botnet"], v["groups_botnet"]) < 5:
        caution.append("Pocos grupos de Botnet en Validación/Prueba: la métrica depende de muy pocos grupos y su "
                       "incertidumbre es alta.")
    return interp(meaning, caution)


def ks_table(rows: list[dict]) -> dict:
    top = sorted(rows, key=lambda r: -(r.get("ks") or 0))[:3]
    meaning = ["Las variables que mejor separan las clases (mayor estadístico KS) son: "
               + ", ".join(f"{lab(r['feature'])} (KS {n(r['ks'])})" for r in top) + "."]
    if top and top[0]["ks"] >= 0.9:
        meaning.append("Una separación casi total en una sola variable indica que la tarea es fácil en este escenario; "
                       "no garantiza buen rendimiento en otras redes.")
    return interp(meaning, ["KS mide diferencias de distribución, no causalidad."])


def missing_outliers(rows: list[dict]) -> dict:
    m = [r for r in rows if r.get("missing_pct", 0) > 0]
    o = sorted(rows, key=lambda r: -(r.get("outlier_pct") or 0))[:2]
    meaning = [(f"{n(len(m))} variable(s) tienen valores faltantes (la mayor: {lab(max(m, key=lambda r: r['missing_pct'])['feature'])}, "
                f"{n(max(r['missing_pct'] for r in m))} %); se imputan con la mediana dentro del pipeline."
                if m else "No hay valores faltantes en las variables del modelo."),
               "Más atípicos (regla IQR 1,5): " + ", ".join(f"{lab(r['feature'])} ({n(r['outlier_pct'])} %)" for r in o) + "."]
    return interp(meaning, ["Un atípico en tráfico de red suele ser comportamiento real (descargas grandes), no un error."])


def correlation(pairs: list[dict], n_feat: int) -> dict:
    high = [p for p in pairs if abs(p["rho"]) >= 0.9]
    top = pairs[0] if pairs else None
    meaning = [(f"La mayor correlación de Spearman es {n(top['rho'])} entre {lab(top['a'])} y {lab(top['b'])}." if top else
                "Sin pares calculables."),
               f"{n(len(high))} par(es) de {n(n_feat)} variables superan |ρ| ≥ 0,90."]
    caution = []
    if high:
        caution.append("Variables muy correlacionadas se reparten la importancia (SHAP/permutación) y desestabilizan los "
                       "coeficientes de la regresión logística.")
    return interp(meaning, caution)


# ---------------------------------------------------------------- Fase 2: entrenamiento
def partition_split_table(pt: dict) -> dict:
    return partition(pt)


def cv_dispersion(model_es: str, agg: dict, metric_es: str) -> dict:
    a = agg
    if not a or a.get("mean") is None:
        return interp(["Sin datos de pliegues."])
    spread = (max(a["values"]) - min(a["values"])) if a["values"] else 0
    meaning = [f"{model_es}: {metric_es} media {n(a['mean'], 3)} ± {n(a['std'], 3)} entre {a['n']} pliegues externos "
               f"(IC 95 % t: {n(a['ci_t'][0], 3)} a {n(a['ci_t'][1], 3)}).",
               f"El mejor y el peor pliegue difieren en {n(spread, 3)}."]
    caution = []
    if a["n"] < LOW_POWER_N:
        caution.append(f"Con n = {a['n']} pliegues el IC es amplio y poco fiable (cada pliegue cuenta como una sola observación).")
    if spread > 0.1:
        caution.append("Los pliegues difieren mucho: el rendimiento depende de qué grupos caen en validación.")
    return interp(meaning, caution)


def optimism_gap(model_es: str, inner: list[float], outer: list[float], metric_es: str) -> dict:
    pairs = [(i, o) for i, o in zip(inner, outer) if i is not None and o is not None]
    if not pairs:
        return interp(["Sin datos."])
    gaps = [i - o for i, o in pairs]
    g = sum(gaps) / len(gaps)
    meaning = [f"{model_es}: la {metric_es} de la búsqueda interna supera a la externa en {n(g, 3)} en promedio "
               f"(rango {n(min(gaps), 3)} a {n(max(gaps), 3)}).",
               "Esa brecha estima el optimismo de elegir hiperparámetros con los mismos datos con que se mide."]
    caution = []
    if g > 0.05:
        caution.append("Brecha notable: la selección de hiperparámetros sobreajusta la validación interna.")
    if g < -0.02:
        caution.append("Brecha negativa: los pliegues externos fueron más fáciles que los internos (varianza entre grupos).")
    return interp(meaning, caution)


def hparam_stability(model_es: str, params: dict[str, list]) -> dict:
    unstable = []
    for k, vals in params.items():
        nums = [v for v in vals if isinstance(v, (int, float))]
        if len(nums) >= 3 and sum(nums) != 0:
            m = sum(nums) / len(nums)
            sd = (sum((x - m) ** 2 for x in nums) / (len(nums) - 1)) ** 0.5
            if m and sd / abs(m) > 0.5:
                unstable.append(k)
        elif len(set(map(str, vals))) > 1 and len(vals) >= 3:
            unstable.append(k)
    meaning = [f"{model_es}: {n(len(unstable))} de {n(len(params))} hiperparámetros cambian mucho entre pliegues"
               + (": " + ", ".join(unstable) + "." if unstable else ".")]
    caution = ["Hiperparámetros inestables suelen indicar una superficie plana: varias configuraciones rinden igual."
               if unstable else ""]
    return interp(meaning, caution)


def convergence(model_es: str, curve: list[dict], n_pruned: int, n_trials: int) -> dict:
    vals = [c["best"] for c in curve if c.get("best") is not None]
    if not vals:
        return interp(["Sin trials completados."])
    first, last = vals[0], vals[-1]
    when = next((i for i, v in enumerate(vals) if v >= last - 1e-12), 0) + 1
    meaning = [f"{model_es}: el mejor valor pasó de {n(first, 3)} a {n(last, 3)}; se alcanzó en el trial {n(when)} de {n(n_trials)}.",
               f"Se podaron {n(n_pruned)} trials ({pct(n_pruned / max(n_trials, 1), 0)}) por rendimiento inferior a la mediana."]
    caution = []
    if when >= 0.9 * len(vals) and len(vals) > 5:
        caution.append("La mejora llegó al final: más trials podrían seguir mejorando.")
    return interp(meaning, caution)


# ---------------------------------------------------------------- Fase 3: evaluación
def metrics_table(rows: list[dict], metric_es: str) -> dict:
    best = max((r for r in rows if r.get("pr_auc") is not None), key=lambda r: r["pr_auc"], default=None)
    meaning = []
    if best:
        meaning.append(f"El mayor PR-AUC en pliegues externos es de {best['model']} ({n(best['pr_auc'], 3)}).")
    base = next((r for r in rows if r.get("model_type") == "dummy"), None)
    if base and base.get("pr_auc") is not None:
        meaning.append(f"La línea base trivial obtiene PR-AUC {n(base['pr_auc'], 3)} (igual a la prevalencia): todo lo "
                       "que esté por encima es aprendizaje real.")
    return interp(meaning, ["Los IC con 5 pliegues son amplios; diferencias pequeñas entre modelos no son concluyentes."])


def confusion_text(c: dict, thr: float, model_es: str) -> dict:
    tp, fp, fn, tn = c["tp"], c["fp"], c["fn"], c["tn"]
    rec = tp / (tp + fn) if (tp + fn) else None
    prec = tp / (tp + fp) if (tp + fp) else None
    spec = tn / (tn + fp) if (tn + fp) else None
    meaning = []
    if rec is not None:
        meaning.append(f"Al umbral {n(thr)}, la exhaustividad de {n(rec)} indica que {n(round((1 - rec) * 100))} de cada 100 flujos "
                       f"de botnet pasarían sin alerta ({n(fn)} de {n(tp + fn)}).")
    if prec is not None:
        meaning.append(f"La precisión de {n(prec)} significa que {n(round((1 - prec) * 100))} de cada 100 alertas serían falsas "
                       f"({n(fp)} falsas alarmas de {n(tp + fp)} alertas).")
    caution = []
    if spec is not None and spec < 0.9:
        caution.append(f"La especificidad es {n(spec)}: una parte relevante del tráfico normal se marcaría como botnet.")
    if tp + fn < 30:
        caution.append(f"Solo {n(tp + fn)} casos positivos en la evaluación: la matriz es muy sensible al azar.")
    return interp(meaning, caution)


def roc_text(model_es: str, auc: float | None, sd: float | None, folds: int) -> dict:
    m = [f"{model_es}: ROC-AUC {n(auc, 3)}" + (f" ± {n(sd, 3)} entre {folds} pliegues" if sd is not None else "")
         + ". Equivale a la probabilidad de que un flujo Botnet reciba más riesgo que uno Normal elegido al azar."]
    return interp(m, ["Con clases muy desbalanceadas el ROC puede verse optimista; contraste con la curva PR."])


def pr_text(model_es: str, ap: float | None, prevalence: float) -> dict:
    m = [f"{model_es}: PR-AUC {n(ap, 3)} frente a {n(prevalence, 3)} de un clasificador al azar (la prevalencia).",
         "Cuanto más se acerca la curva a la esquina superior derecha, menos falsas alarmas por cada botnet detectada."]
    return interp(m, [])


def calibration_text(model_es: str, ece: float | None, brier: float | None) -> dict:
    meaning = [f"{model_es}: error de calibración esperado (ECE) {n(ece, 3)} y Brier {n(brier, 3)}."]
    if ece is not None:
        meaning.append("Las probabilidades " + ("son confiables como porcentaje." if ece < 0.05 else
                                                 "no son confiables como porcentaje: úselas solo para ordenar riesgo."))
    return interp(meaning, ["Puntos con pocos casos (tamaño del marcador) son ruidosos."])


def stat_tests(friedman: dict, rows: list[dict], n_folds: int, metric_es: str) -> dict:
    meaning = []
    if friedman.get("applicable"):
        meaning.append(f"Friedman sobre {n(friedman['n_folds'])} pliegues y {n(friedman['k_models'])} modelos: "
                       f"χ² = {n(friedman['statistic'])}, p = {n(friedman['p_value'], 3)} "
                       f"({'diferencias detectables' if friedman['p_value'] < 0.05 else 'sin diferencias detectables'}).")
    else:
        meaning.append("Friedman no aplica: " + friedman.get("reason", "n/d") + ".")
    sig = [r for r in rows if r.get("significant_005")]
    meaning.append(f"Tras la corrección de Holm, {n(len(sig))} de {n(len(rows))} comparaciones por pares son significativas al 5 %.")
    minp = 2.0 / (2 ** n_folds)
    caution = [f"Potencia baja: con n = {n_folds} pliegues el p mínimo alcanzable de Wilcoxon bilateral es {n(minp, 4)}; "
               "aun sin errores de ningún tipo, tras Holm casi nunca se llega a p < 0,05. Un resultado no significativo "
               "NO prueba que los modelos sean equivalentes."]
    return interp(meaning, caution)


def baseline_comparison(rows: list[dict]) -> dict:
    ml = [r for r in rows if r.get("kind") == "model"]
    det = next((r for r in rows if r.get("kind") == "detectors"), None)
    base = next((r for r in rows if r.get("kind") == "dummy"), None)
    meaning = []
    if ml and det:
        b = max(ml, key=lambda r: r.get("f1") or 0)
        meaning.append(f"En Prueba, {b['name']} logra F1 {n(b.get('f1'))} frente a {n(det.get('f1'))} de los detectores "
                       "deterministas actuales de NetSentinel (mismas etiquetas y misma partición).")
    if det and det.get("recall") is not None:
        meaning.append(f"Los detectores actuales dejan pasar {n(round((1 - det['recall']) * 100))} de cada 100 flujos botnet de Prueba.")
    caution = ["Los detectores se aplican sobre todo el dataset como una sola ventana y se mapean a flujos "
               "(un flujo es positivo si pertenece a un grupo marcado); es una aproximación, no la operación real por ventanas de 24 h."]
    if base:
        caution.append(f"Referencia trivial: PR-AUC {n(base.get('pr_auc'), 3)}.")
    return interp(meaning, caution)


# ---------------------------------------------------------------- Fase 4: explicabilidad
def shap_global(model_es: str, imp: list[dict], space: str) -> dict:
    top = imp[:3]
    tot = sum(i["value"] for i in imp) or 1
    share = sum(i["value"] for i in top) / tot
    meaning = [f"{model_es}: las 3 variables más influyentes son " + ", ".join(lab(i["feature"]) for i in top)
               + f" y concentran {pct(share, 0)} de la contribución total (|SHAP| medio, {space}).",
               "Valores SHAP positivos empujan la predicción hacia Botnet; negativos hacia Normal."]
    return interp(meaning, ["Atribución no es causalidad: indica qué usa el modelo, no por qué ocurre el tráfico.",
                            "Variables correlacionadas se reparten la importancia."])


def permutation(model_es: str, imp: list[dict], metric_es: str) -> dict:
    top = imp[:3]
    meaning = [f"Al barajar {lab(top[0]['feature'])} la {metric_es} cae {n(top[0]['value'], 3)} en Validación; es la variable "
               f"de la que más depende {model_es}." if top else "Sin datos.",
               "Es un contraste independiente del modelo: mide la pérdida real de rendimiento, no la contribución interna."]
    return interp(meaning, ["Con variables correlacionadas, barajar una sola puede subestimarla (la otra la reemplaza)."])


def discrepancy(rows: list[dict]) -> dict:
    d = [r for r in rows if r.get("flag")]
    meaning = [f"{n(len(d))} variable(s) con rangos muy distintos entre SHAP y permutación"
               + (": " + ", ".join(lab(r["feature"]) for r in d[:4]) + "." if d else ".")]
    caution = ["Una discrepancia suele indicar correlación entre variables o que el modelo usa la variable de forma "
               "redundante: revíselas juntas." if d else ""]
    return interp(meaning, caution)


def heatmap_text(kind: str, top_row: str | None, top_col: str | None, vmax: float) -> dict:
    meaning = [f"El riesgo medio más alto ({n(vmax)}) se concentra en {top_row} durante {top_col}."
               if top_row else "Sin celdas con riesgo."]
    return interp(meaning, ["El mapa muestra dónde y cuándo el modelo ve riesgo, no si hubo un ataque.",
                            "Celdas con pocos flujos pueden ser extremas por azar."])


def pdp_text(feature: str, lo: float, hi: float, direction: str) -> dict:
    meaning = [f"A medida que {lab(feature)} aumenta, la probabilidad media de Botnet {direction} (de {n(lo)} a {n(hi)})."]
    return interp(meaning, ["La dependencia parcial promedia sobre el resto de variables; las líneas ICE muestran la "
                            "variación individual. Sin causalidad."])


def occlusion_text(rows: list[dict]) -> dict:
    top = rows[:2]
    meaning = ["Al enmascarar " + " o ".join(lab(r["feature"]) for r in top) + " (sustituyéndola por la mediana del tráfico "
               f"normal) la probabilidad media cae {n(top[0]['drop'])}." if top else "Sin datos."]
    return interp(meaning, ["Enmascarar una variable fuera de su distribución real puede crear combinaciones imposibles; "
                            "interprételo como sensibilidad, no como causa."])


def explain_stability(kendall_w: float | None, tau: float | None, k: int) -> dict:
    meaning = [f"Concordancia de Kendall W = {n(kendall_w)} y τ medio = {n(tau)} entre los {k} pliegues "
               f"({'explicaciones estables' if (kendall_w or 0) >= 0.7 else 'explicaciones poco estables'})."]
    caution = ["W cercano a 1 = el orden de importancia se repite en todos los pliegues; cercano a 0 = depende de los datos." ]
    return interp(meaning, caution)


# ---------------------------------------------------------------- Fase 7: Optuna
def optuna_history(best: float | None, n_trials: int, n_pruned: int, first_best_trial: int | None) -> dict:
    meaning = [f"Mejor valor {n(best, 4)} tras {n(n_trials)} trials ({n(n_pruned)} podados); se halló en el trial {n(first_best_trial)}."]
    caution = []
    if first_best_trial is not None and first_best_trial >= 0.9 * n_trials and n_trials > 10:
        caution.append("El mejor valor apareció al final: el espacio podría no estar agotado.")
    return interp(meaning, caution)


def optuna_importance(imp: list[dict]) -> dict:
    top = imp[:2]
    meaning = ["Los hiperparámetros que más explican la variación del valor (fANOVA) son "
               + " y ".join(f"{i['param']} ({pct(i['value'], 0)})" for i in top) + "." if top else "Sin importancias."]
    return interp(meaning, ["fANOVA es aproximado y necesita varios trials completados; con pocos datos es inestable."])


# ---------------------------------------------------------------- Fase 6: inferencia
def severity_text(sev: str, steps: list[dict]) -> dict:
    final = steps[-1] if steps else {}
    return interp([f"Severidad {sev}: " + final.get("text", "")], [])
