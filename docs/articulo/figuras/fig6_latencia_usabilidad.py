"""F6: (a) latencia por hallazgo en CPU por modelo (llama3.2:3b dentro del intervalo REAL 28-37 s; los demas SUPUESTOS †);
(b) tiempo de decision con y sin explicacion en 12 administradores (SUPUESTO †)."""
from estilo import *
import numpy as np, supuestos as S
fig, ax = plt.subplots(1, 2, figsize=(7.2, 3.1), gridspec_kw=dict(width_ratios=[1.1, 1]))
data = [S.LAT[m] for m in S.MODELOS]; cols = [OK['gris'], OK['celeste'], OK['verde'], OK['rojo']]
bp = ax[0].boxplot(data, widths=.5, patch_artist=True, showfliers=False, medianprops=dict(color='k', lw=1.2))
for b, c in zip(bp['boxes'], cols): b.set_facecolor(c); b.set_alpha(.75)
r = np.random.default_rng(3)
for i, d in enumerate(data, 1): ax[0].plot(i + r.uniform(-.12, .12, len(d)), d, '.', color='k', ms=2.5, alpha=.5)
ax[0].axhspan(S.REAL['llm_min'], S.REAL['llm_max'], xmin=0.03, xmax=0.27, color='none', ec=OK['negro'], ls=':', lw=0.8)
ax[0].set_xticks(range(1, 5)); ax[0].set_xticklabels([m.replace(':', ':\n') for m in S.MODELOS], fontsize=7)
ax[0].set_ylabel('Latencia por hallazgo en CPU (s)'); ax[0].set_title('(a) Inferencia local (n = 30 por modelo) †', loc='left')
ax[0].text(0.62, 12, 'rango real medido\n(llama3.2:3b): 28–37 s', fontsize=6.3); ax[0].set_ylim(0, 130)
for a, b in zip(S.T_SIN, S.T_CON): ax[1].plot([0, 1], [a, b], color=OK['gris'], lw=.8, marker='o', ms=3)
ax[1].plot([0, 1], [np.median(S.T_SIN), np.median(S.T_CON)], color=OK['azul'], lw=2.2, marker='D', ms=6, label='Mediana'); ax[1].set_ylim(55, 195)
ax[1].set_xticks([0, 1]); ax[1].set_xticklabels(['Solo evidencia', 'Con explicación\ny recomendación']); ax[1].set_xlim(-.3, 1.3)
ax[1].set_ylabel('Tiempo de decisión por hallazgo (s)'); ax[1].set_title('(b) Estudio de usabilidad (N = 12) †', loc='left'); ax[1].legend(frameon=False, loc='upper center')
fig.tight_layout(); save(fig, 'F6_latencia_usabilidad.png')
