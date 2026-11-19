"""Recalcula desde los JSON crudos todas las cifras del articulo J.UCS (no se copian de la ficha). Salida: datos.json."""
import json, glob, numpy as np
from scipy import stats
V = "/home/robertoa1/Datos/proyectos/software-s12/docs/validacion-externa/"
SEEDS = [11, 22, 33, 44, 55]
FAM = {1: "Neris", 2: "Neris", 3: "Rbot", 4: "Rbot", 5: "Virut", 6: "Menti", 7: "Sogou", 8: "Murlo", 9: "Neris", 11: "Rbot", 12: "NSIS.ay", 13: "Virut"}
ESC = sorted(FAM)
flow = [o for s in SEEDS for o in json.load(open(f"{V}multi_anidado_crudas_{s}.json"))]
ens = [o for s in SEEDS for o in json.load(open(f"{V}ensambles_{s}.json"))]
hyb = [o for s in SEEDS for o in json.load(open(f"{V}hibrido_{s}.json"))]
assert len(flow) == 300 and len(ens) == 240, (len(flow), len(ens)); print("hibrido filas", len(hyb))
def table(rows, model_key="model", filt=lambda o: True):
    """-> {modelo: {metrica: array [seed, escenario]}}"""
    out = {}
    for o in rows:
        if not filt(o): continue
        d = out.setdefault(o[model_key], {})
        for m in ("pr_auc", "roc_auc", "recall", "precision", "balanced_acc"):
            d.setdefault(m, {}).setdefault(o["seed"], {})[o["held_out"]] = o[m]
    res = {}
    for mod, d in out.items():
        res[mod] = {m: np.array([[d[m][s][e] for e in ESC] for s in SEEDS]) for m in d}
    return res
F = table(flow); E = table(ens); H1 = table(hyb, filt=lambda o: o["W"] == 1.0); H5 = table(hyb, filt=lambda o: o["W"] == 5.0)
def summ(t):
    pr = t["pr_auc"]; per_seed = np.nanmean(pr, axis=1); per_esc = np.nanmean(pr, axis=0)
    return {"pr_mean": float(per_seed.mean()), "pr_sd_seeds": float(per_seed.std(ddof=1)), "pr_median": float(np.median(per_esc)), "pr_worst": float(per_esc.min()),
            "pr_worst_esc": int(ESC[int(per_esc.argmin())]), "roc": float(np.nanmean(t["roc_auc"], axis=1).mean()), "recall": float(np.nanmean(t["recall"], axis=1).mean()),
            "precision": float(np.nanmean(t["precision"], axis=1).mean()), "bacc": float(np.nanmean(t["balanced_acc"], axis=1).mean()),
            "per_esc_mean": per_esc.tolist(), "per_esc_sd": pr.std(axis=0, ddof=1).tolist(), "max_sd_esc": float(pr.std(axis=0, ddof=1).max())}
D = {"escenarios": ESC, "familia": FAM}
D["flujo"] = {m: summ(F[m]) for m in F}; D["ensambles"] = {m: summ(E[m]) for m in E}
D["host_W1"] = {m: summ(H1[m]) for m in H1}; D["host_W5"] = {m: summ(H5[m]) for m in H5}
# prevalencia (Dummy)
D["prevalencia"] = {int(e): float(F["dummy"]["pr_auc"][0, i]) for i, e in enumerate(ESC)}
# rangos medios entre los 4 modelos (flujo) y entre los 8 (flujo + ensambles)
def ranks(models):
    M = np.array([np.nanmean({**F, **E}[m]["pr_auc"], axis=0) for m in models]); R = np.array([stats.rankdata(-M[:, j]) for j in range(M.shape[1])]); return dict(zip(models, R.mean(axis=0).tolist())), M
base = ["logreg", "random_forest", "hist_gb", "xgboost"]
r4, M4 = ranks(base); D["rango4"] = r4
fr = stats.friedmanchisquare(*M4); D["friedman4"] = {"chi2": float(fr.statistic), "p": float(fr.pvalue)}
pairs = {}
import itertools
raw = []
for a, b in itertools.combinations(range(4), 2):
    w = stats.wilcoxon(M4[a], M4[b]); raw.append((base[a], base[b], float(w.pvalue)))
ps = np.array([p for *_, p in raw]); order = np.argsort(ps); holm = np.empty(len(ps)); run = 0
for rank_i, idx in enumerate(order):
    run = max(run, (len(ps) - rank_i) * ps[idx]); holm[idx] = min(1, run)
D["wilcoxon4"] = [{"a": a, "b": b, "p": p, "p_holm": float(holm[i])} for i, (a, b, p) in enumerate(raw)]
all8 = base + ["RF+HGB", "LR+RF+HGB", "RF+HGB+XGB", "los 4"]
r8, M8 = ranks(all8); D["rango8"] = r8
D["friedman8"] = {"chi2": float(stats.friedmanchisquare(*M8).statistic), "p": float(stats.friedmanchisquare(*M8).pvalue)}
# ensamble vs individuales (Wilcoxon sin corregir)
ensw = {}
for e in ["RF+HGB", "LR+RF+HGB", "RF+HGB+XGB", "los 4"]:
    for b in ("random_forest", "hist_gb"):
        ensw[f"{e} vs {b}"] = float(stats.wilcoxon(np.nanmean(E[e]["pr_auc"], 0), np.nanmean(F[b]["pr_auc"], 0)).pvalue)
D["ens_vs_ind"] = ensw
# contexto de host vs flujo (Wilcoxon sin corregir; diferencia media)
hw = {}
for tag, H in (("W1", H1), ("W5", H5)):
    for m in H:
        a = np.nanmean(H[m]["pr_auc"], 0); b = np.nanmean(F[m]["pr_auc"] if m in F else E[m]["pr_auc"], 0)
        hw[f"{tag} {m}"] = {"dif": float((a - b).mean()), "p": float(stats.wilcoxon(a, b).pvalue)}
D["host_vs_flujo"] = hw
D["intervalos"] = json.load(open(V + "intervalos.json"))
# umbral: mejora de exactitud balanceada respecto a 0.5 no disponible en JSON de ensambles; se omite
# evaluacion realista parcial
D["fondo"] = json.load(open(V + "fondo_11_parcial.json"))
D["cic_flow"] = json.load(open(V + "cic_flow_11.json")); D["cic_host"] = json.load(open(V + "cic_host_11.json"))
D["comp_bg"] = json.load(open(V + "comprobacion_background_11.json"))
# hiperparametros: segundos por ajuste y trials
D["secs_total_flujo_h"] = float(sum(o["secs"] for o in flow) / 3600)
D["threshold_stats"] = {m: {"min": float(min(o["threshold"] for o in flow if o["model"] == m)), "max": float(max(o["threshold"] for o in flow if o["model"] == m))} for m in base}
json.dump(D, open("datos.json", "w"), indent=1)
for k in ("flujo", "ensambles", "host_W1", "host_W5"):
    print("==", k)
    for m, s in D[k].items(): print(f"{m:11s} PR {s['pr_mean']:.3f}±{s['pr_sd_seeds']:.3f} med {s['pr_median']:.3f} peor {s['pr_worst']:.3f}(esc {s['pr_worst_esc']}) ROC {s['roc']:.3f} rec {s['recall']:.3f} prec {s['precision']:.3f} BA {s['bacc']:.3f}")
print("rango4", D["rango4"]); print("friedman4", D["friedman4"]); print("wil4", D["wilcoxon4"]); print("rango8", D["rango8"], D["friedman8"]); print("ens_vs_ind", ensw)
print("secs total flujo (h, suma de ajustes finales/inner)", D["secs_total_flujo_h"]); print(D["threshold_stats"])
