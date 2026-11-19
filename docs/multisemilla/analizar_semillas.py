"""Resume la CV anidada repetida con varias semillas: PR-AUC externa y de Prueba (media ± DE entre semillas),
mejora sobre el Dummy, y precisión/F1 de Prueba reponderadas a prevalencias realistas de Botnet."""
import json, subprocess, itertools, numpy as np
from scipy import stats

SQL = """select r.id, r.job_id, r.model_type, (r.config->>'seed')::int seed, r.test_metrics::text,
 (select json_agg((f.outer_metrics->>'pr_auc')::float order by f.outer_fold) from ml_fold_results f where f.run_id=r.id)::text
 from ml_runs r join ml_jobs j on j.id=r.job_id where j.kind='train' and j.status='succeeded' order by r.id"""
raw = subprocess.run(["docker", "compose", "exec", "-T", "db", "psql", "-U", "netsentinel", "-d", "netsentinel", "-At", "-F", "\t", "-c", SQL],
                     capture_output=True, text=True, cwd="../..").stdout
R = {}
for ln in raw.strip().splitlines():
    rid, jid, m, seed, tm, folds = ln.split("\t")
    R.setdefault(m, {})[int(seed)] = {"test": json.loads(tm), "folds": json.loads(folds) if folds else []}
seeds = sorted({s for m in R.values() for s in m})
NAMES = {"dummy": "Dummy", "logreg": "Regresión logística", "random_forest": "Random Forest", "hist_gb": "GB histogramas", "xgboost": "XGBoost"}
print("Semillas:", seeds)
def ms(v): v = [x for x in v if x is not None]; return (np.mean(v), np.std(v, ddof=1) if len(v) > 1 else 0.0)
print("\nPR-AUC externa (media de 5 pliegues por semilla; media ± DE entre semillas) y PR-AUC en Prueba")
rows = {}
for m, d in R.items():
    ext = [np.mean(v["folds"]) for v in d.values() if v["folds"]]
    tst = [v["test"].get("pr_auc") for v in d.values()]
    rows[m] = (ext, tst)
    e, t = ms(ext), ms(tst)
    print(f"{NAMES[m]:22s} externa {e[0]:.4f} ± {e[1]:.4f} | prueba {t[0]:.4f} ± {t[1]:.4f} | n_semillas={len(ext)}")
print("\nMejora de PR-AUC externa sobre el Dummy (por semilla, media ± DE)")
for m in R:
    if m == "dummy": continue
    diff = [np.mean(R[m][s]["folds"]) - np.mean(R["dummy"][s]["folds"]) for s in seeds if s in R[m] and s in R["dummy"]]
    print(f"{NAMES[m]:22s} +{np.mean(diff):.4f} ± {np.std(diff, ddof=1):.4f}")
print("\nPrecisión y F1 en Prueba (umbral 0,5) reponderadas a prevalencia de Botnet (media entre semillas)")
print(f"{'modelo':22s} " + " ".join(f"π={p:>5.2f}(prec/F1)" for p in (0.75, 0.10, 0.01)))
for m, d in R.items():
    out = []
    for pi in (0.75, 0.10, 0.01):
        pr, f1 = [], []
        for v in d.values():
            t = v["test"]; tp, fn, fp, tn = t["tp"], t["fn"], t["fp"], t["tn"]
            tpr = tp / (tp + fn) if tp + fn else 0; fpr = fp / (fp + tn) if fp + tn else 0
            den = tpr * pi + fpr * (1 - pi); p = tpr * pi / den if den else 0
            pr.append(p); f1.append(2 * p * tpr / (p + tpr) if p + tpr else 0)
        out.append(f"{np.mean(pr):.3f}/{np.mean(f1):.3f}")
    print(f"{NAMES[m]:22s} " + "   ".join(f"{o:>16s}" for o in out))
print("\nWilcoxon pareado entre modelos sobre las PR-AUC por (semilla×pliegue); NO son independientes: úsese como orientación")
names = [m for m in R if m != "dummy"]
res = []
for a, b in itertools.combinations(names, 2):
    xs = [(x, y) for s in seeds if s in R[a] and s in R[b] for x, y in zip(R[a][s]["folds"], R[b][s]["folds"])]
    x, y = np.array([p[0] for p in xs]), np.array([p[1] for p in xs])
    try: p = stats.wilcoxon(x, y).pvalue
    except ValueError: p = float("nan")
    res.append((a, b, len(xs), float(np.mean(x - y)), p))
order = np.argsort([r[4] for r in res]); m_ = len(res)
run = 0
for rank, i in enumerate(order):
    a, b, n, d, p = res[i]; run = max(run, (m_ - rank) * p); print(f"{NAMES[a]:20s} vs {NAMES[b]:20s} n={n} dif={d:+.4f} p={p:.4g} p_Holm={min(1, run):.4g}")
