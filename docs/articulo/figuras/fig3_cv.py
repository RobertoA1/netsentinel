"""F3: CV de intervalos en grupos (origen, destino, puerto, protocolo) del dataset real (>=10 conexiones, intervalo medio >=1 s)
frente a beacons sinteticos inyectados (SUPUESTO †). Los CV 'reales' se recalculan aqui desde el archivo binetflow."""
from estilo import *
import csv, collections, statistics as st, numpy as np
from datetime import datetime
import supuestos as S
DS = os.path.join(HERE, '..', '..', '..', 'data', 'dataset', 'capture20110818-2.binetflow')
g = collections.defaultdict(list)
for x in csv.DictReader(open(DS)):
    t = datetime.strptime(x['StartTime'], '%Y/%m/%d %H:%M:%S.%f').timestamp()
    lab = 'bot' if 'Botnet' in x['Label'] else ('norm' if 'Normal' in x['Label'] else 'bg')
    g[(x['SrcAddr'], x['DstAddr'], x['Dport'], x['Proto'])].append((t, lab))
cv_real = []; n_bot = 0
for k, v in g.items():
    if len(v) < 10: continue
    v.sort(); gaps = [b[0]-a[0] for a, b in zip(v, v[1:])]; m = st.fmean(gaps)
    if m < 1: continue
    cv_real.append(st.pstdev(gaps)/m)
    if sum(1 for _, l in v if l == 'bot')/len(v) >= .5: n_bot += 1
cv_real = np.array(cv_real); cv_inj = np.array([x['cv'] for x in S.INJ if x['n'] >= 10])
print('grupos reales', len(cv_real), 'con CV<=0.25', int((cv_real <= .25).sum()), 'grupos botnet', n_bot, 'inyectados', len(cv_inj))
fig, ax = plt.subplots(1, 2, figsize=(7.2, 3.0), gridspec_kw=dict(width_ratios=[1.25, 1]))
bins = np.linspace(0, 3.0, 31)
ax[0].hist(np.clip(cv_real, 0, 2.99), bins=bins, color=OK['azul'], alpha=.75, label=f'Grupos del dataset (n = {len(cv_real)})')
ax[0].hist(np.clip(cv_inj, 0, 2.99), bins=bins, color=OK['naranja'], alpha=.85, label=f'Beacons inyectados † (n = {len(cv_inj)})')
ax[0].axvline(0.25, color='k', ls='--', lw=1); ax[0].text(0.29, ax[0].get_ylim()[1]*0.93, 'umbral CV = 0,25', fontsize=7)
ax[0].set_xlabel('Coeficiente de variación de los intervalos (CV; último intervalo = CV ≥ 3)'); ax[0].set_ylabel('Número de grupos'); ax[0].set_title('(a) Distribución del CV', loc='left')
ax[0].legend(frameon=False, loc='upper right', fontsize=6.8)
# (b) deteccion segun perdida de latidos y jitter
miss = sorted(set(x['miss'] for x in S.INJ)); cols = [OK['azul'], OK['celeste'], OK['verde'], OK['naranja'], OK['rojo']]
for jit, c in zip(S.JITTERS, cols):
    ys = [np.mean([x['score'] is not None for x in S.INJ if x['jit'] == jit and x['miss'] == m]) for m in miss]
    ax[1].plot([m*100 for m in miss], ys, marker='o', ms=3.5, color=c, label=f'jitter ±{int(jit*100)} %')
ax[1].set_xlabel('Latidos perdidos (%)'); ax[1].set_ylabel('Fracción detectada'); ax[1].set_ylim(-0.03, 1.05); ax[1].set_title('(b) Detección de beacons inyectados †', loc='left')
ax[1].legend(frameon=False, fontsize=6.5, loc='lower left')
fig.tight_layout(); save(fig, 'F3_cv_beaconing.png')
