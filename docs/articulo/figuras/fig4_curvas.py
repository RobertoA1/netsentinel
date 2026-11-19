"""F4: (a) curvas precision-cobertura relativa al conjunto agrupado (24 eventos) variando el umbral de cada metodo; (b) sensibilidad
frente al jitter en beacons inyectados. Datos SUPUESTOS †; los puntos finales coinciden con la Tabla 4."""
from estilo import *
import numpy as np, supuestos as S
r = np.random.default_rng(7)
def asigna(scores, k):
    w = np.exp(np.array(scores)/12.0); w /= w.sum()
    idx = r.choice(len(scores), k, replace=False, p=w); f = np.zeros(len(scores), bool); f[idx] = True; return f
# hallazgos del sistema (distribucion de severidad REAL: 2 criticos, 15 altos, 31 medios, 3 bajos)
sc_b = [87, 91] + list(r.uniform(70, 82, 8)) + list(r.uniform(60, 69.5, 13))
sc_p = list(r.uniform(70, 75, 5)) + list(r.uniform(50, 69, 17)) + list(r.uniform(36, 48, 3))
sc_t = [78, 74, 62]
sc_all = np.array(sc_b + sc_p + sc_t); fl = np.concatenate([asigna(sc_b, 12), asigna(sc_p, 7), np.array([True, True, False])])
assert len(sc_all) == 51 and fl.sum() == 21
def curva(scores, flags, th):
    P, R = [], []
    for t in th:
        m = scores >= t; n = m.sum()
        if n: P.append(flags[m].sum()/n); R.append(flags[m].sum()/S.POOL)
    return np.array(R), np.array(P)
th = np.sort(np.unique(sc_all))
Rn, Pn = curva(sc_all, fl, th)
# umbral fijo: 37 grupos con conteos de conexiones; 9 reales
cnt = np.sort(r.lognormal(5.0, 0.6, 37).clip(100, None))[::-1]; ff = asigna(list(cnt/40), 9)
Rf, Pf = curva(cnt, ff, np.sort(cnt))
# Suricata: 14 alertas agrupadas por firma, severidad 1-3, 3 reales
sev = np.array([1]*3 + [2]*5 + [3]*6); fs = np.array([True, True, False]+[True, False, False, False, False]+[False]*6)
sur = [(fs[sev <= s].sum()/S.POOL, fs[sev <= s].mean()) for s in (1, 2, 3)]
fig, ax = plt.subplots(1, 2, figsize=(7.2, 3.9), gridspec_kw=dict(height_ratios=[1]))
ax[0].step(Rn, Pn, where='post', color=OK['azul'], lw=1.6, label='NetSentinel determinista (umbral de puntaje)')
ax[0].step(Rf, Pf, where='post', color=OK['naranja'], lw=1.4, label='Umbral fijo (≥ N conexiones)')
ax[0].plot([s[0] for s in sur], [s[1] for s in sur], 's--', color=OK['rojo'], ms=4, lw=1, label='Suricata (severidad ≤ 1, 2, 3)')
for m, c in (('NetSentinel + llama3.2:3b', OK['gris']), ('NetSentinel + llama3.1:8b', OK['verde'])):
    row = [x for x in S.calcula()['t4'] if x['nombre'] == m][0]
    ax[0].plot(row['r'], row['p'], marker='D' if '8b' in m else 'o', color=c, ms=6, ls='', mec='k', mew=.5, label=m.replace('NetSentinel + ', 'Con LLM ') + ' (τ = 0,70)')
ax[0].axhline(21/51, color='k', ls=':', lw=.8); ax[0].text(0.01, 21/51+.015, 'prevalencia de reales (21/51)', fontsize=6.3)
ax[0].set_xlabel('Cobertura relativa (eventos reales / 24)'); ax[0].set_ylabel('Precisión (adjudicada)'); ax[0].set_xlim(0, 1); ax[0].set_ylim(0, 1.02)
ax[0].set_title('(a) Precisión frente a cobertura †', loc='left'); ax[0].legend(frameon=False, fontsize=6.2, loc='upper center', bbox_to_anchor=(0.5, -0.2), ncol=1)
cols = {'NetSentinel (fórmula del detector)': OK['azul'], 'Umbral fijo (≥100 conexiones)': OK['naranja'], 'Suricata 7 (reglas por defecto)': OK['rojo']}
x = [int(j*100) for j in S.JITTERS]
ys = {k: [] for k in cols}
for j in S.JITTERS:
    sub = [q for q in S.INJ if q['jit'] == j]
    ys['NetSentinel (fórmula del detector)'].append(np.mean([q['score'] is not None for q in sub]))
    ys['Umbral fijo (≥100 conexiones)'].append(np.mean([q['n'] >= 100 for q in sub]))
    ys['Suricata 7 (reglas por defecto)'].append(0.0)
for (k, c), mk in zip(cols.items(), 'osv'): ax[1].plot(x, ys[k], marker=mk, color=c, label=k, ms=4.5)
ax[1].set_xlabel('Jitter de los intervalos (± % del periodo)'); ax[1].set_ylabel('Sensibilidad (200 beacons)'); ax[1].set_ylim(-0.03, 1.05)
ax[1].set_title('(b) Sensibilidad frente al jitter †', loc='left'); ax[1].legend(frameon=False, fontsize=6.3, loc='upper center', bbox_to_anchor=(0.5, -0.2), ncol=1)
fig.tight_layout(); save(fig, 'F4_curvas_precision_cobertura.png')
print('NS curva extremos', Rn[0], Pn[0], 'fijo', Rf[0], Pf[0])
