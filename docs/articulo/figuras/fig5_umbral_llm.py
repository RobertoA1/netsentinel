"""F5: reduccion de alertas y hallazgos reales descartados segun el umbral de confianza del LLM. Datos SUPUESTOS †."""
from estilo import *
import numpy as np, supuestos as S
R = S.calcula()['sweep']
cols = dict(zip(S.MODELOS, [OK['gris'], OK['celeste'], OK['verde'], OK['rojo']])); mk = dict(zip(S.MODELOS, 'ovsD'))
fig, ax = plt.subplots(1, 2, figsize=(7.2, 3.0))
for m in S.MODELOS:
    t = [a[0] for a in R[m]]; red = [(a[1]+a[2])/51*100 for a in R[m]]; fn = [a[2] for a in R[m]]
    ax[0].step(t, red, where='post', color=cols[m], marker=mk[m], ms=3.5, lw=1.3, label=m)
    ax[1].step(t, fn, where='post', color=cols[m], marker=mk[m], ms=3.5, lw=1.3, label=m)
for a in ax: a.axvline(0.7, color='k', ls='--', lw=.9); a.set_xlabel('Umbral de confianza para descartar como ruido (τ)'); a.set_xlim(0.48, 1.02)
ax[0].text(0.705, 40, 'τ por\ndefecto', fontsize=6.5); ax[0].set_ylim(-1, 43)
ax[0].set_ylabel('Alertas descartadas (% de 51)'); ax[0].set_title('(a) Reducción de alertas †', loc='left'); ax[0].legend(frameon=False, fontsize=6.5, loc='upper right', ncol=2)
ax[1].set_ylabel('Hallazgos reales descartados (de 21)'); ax[1].set_title('(b) Falsos negativos introducidos †', loc='left'); ax[1].set_yticks(range(0, 6)); ax[1].set_ylim(-0.2, 5.2)
fig.tight_layout(); save(fig, 'F5_umbral_confianza_llm.png')
