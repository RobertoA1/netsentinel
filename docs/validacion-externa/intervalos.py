"""Intervalos de confianza (bootstrap por escenarios) y corrección de Holm para las comparaciones principales. Lee los JSON de resultados."""
import json, itertools, numpy as np, pandas as pd
from scipy.stats import wilcoxon
rs = np.random.default_rng(2026); SEEDS = (11, 22, 33, 44, 55)
Bf = pd.concat([pd.DataFrame(json.load(open(f'multi_anidado_crudas_{s}.json'))) for s in SEEDS]); E = pd.concat([pd.DataFrame(json.load(open(f'ensambles_{s}.json'))) for s in SEEDS])
H = pd.concat([pd.DataFrame(json.load(open(f'hibrido_{s}.json'))) for s in SEEDS])
MS = ['logreg', 'random_forest', 'hist_gb', 'xgboost', 'LR+RF+HGB']
flujo = pd.concat([Bf, E]); flujo = flujo[flujo.model.isin(MS)].pivot_table(index='held_out', columns='model', values='pr_auc', aggfunc='mean')[MS]
T = {'flujo': flujo}
for W in (1.0, 5.0): T[f'host W={W:g}'] = H[H.W == W].pivot_table(index='held_out', columns='model', values='pr_auc', aggfunc='mean')[MS]
B = 10000; idx = rs.integers(0, 12, size=(B, 12))
def ci(v): m = np.array(v)[idx].mean(1); return float(np.mean(v)), float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))
out = {'media': {}, 'diferencias': [], 'pares_modelos': []}
for k, t in T.items():
    for m in MS: out['media'][f'{k} | {m}'] = ci(t[m].values)
print("PR-AUC media entre escenarios [IC 95 % bootstrap por escenarios]")
for k in T:
    print(' ', k, ' '.join(f"{m}={out['media'][f'{k} | {m}'][0]:.3f}[{out['media'][f'{k} | {m}'][1]:.3f},{out['media'][f'{k} | {m}'][2]:.3f}]" for m in MS))
# familia 1: híbrido contra solo flujo, mismo modelo (10 comparaciones)
fam = []
for k in ('host W=1', 'host W=5'):
    for m in MS:
        d = (T[k][m] - T['flujo'][m]).values; mean, lo, hi = ci(d); p = wilcoxon(T[k][m], T['flujo'][m]).pvalue; fam.append((f'{k} - flujo | {m}', mean, lo, hi, p))
def holm(ps):
    o = np.argsort(ps); adj = np.empty(len(ps)); run = 0
    for r, i in enumerate(o): run = max(run, (len(ps) - r) * ps[i]); adj[i] = min(1, run)
    return adj
adj = holm([f[4] for f in fam])
print("\nHíbrido contra solo flujo (diferencia de PR-AUC [IC 95 %], p Wilcoxon, p Holm; 10 comparaciones)")
for f, a in zip(fam, adj): print(f"  {f[0]:32s} {f[1]:+.3f} [{f[2]:+.3f},{f[3]:+.3f}] p={f[4]:.3f} Holm={a:.3f}"); out['diferencias'].append({'comparacion': f[0], 'dif': f[1], 'ic': [f[2], f[3]], 'p': f[4], 'p_holm': a})
# familia 2: pares de modelos dentro de solo flujo (10 comparaciones)
fam2 = []
for a, b in itertools.combinations(MS, 2):
    d = (T['flujo'][a] - T['flujo'][b]).values; mean, lo, hi = ci(d); fam2.append((f'flujo | {a} - {b}', mean, lo, hi, wilcoxon(T['flujo'][a], T['flujo'][b]).pvalue))
adj2 = holm([f[4] for f in fam2])
print("\nSolo flujo, pares de modelos (10 comparaciones)")
for f, a in zip(fam2, adj2): print(f"  {f[0]:36s} {f[1]:+.3f} [{f[2]:+.3f},{f[3]:+.3f}] p={f[4]:.3f} Holm={a:.3f}"); out['pares_modelos'].append({'comparacion': f[0], 'dif': f[1], 'ic': [f[2], f[3]], 'p': f[4], 'p_holm': a})
json.dump(out, open('intervalos.json', 'w'), indent=1)
