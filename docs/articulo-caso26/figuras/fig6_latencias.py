"""F6. Tiempos observados por operación (escala logarítmica). Bases de datos y artefactos para ingesta, entrenamiento e intervalos entre reportes;
registro de la prueba de despliegue para endpoints y modelo de lenguaje (ver nota de la tabla 6)."""
import csv, json
import matplotlib.pyplot as plt
import estilo
from estilo import C
estilo.aplicar()
gaps = [float(l.split("|")[4]) for l in open("datos/raw/db/report_gaps.txt").read().splitlines()[1:] if l.count("|") >= 4 and l.split("|")[4].strip()]
tr = {l.split("|")[1]: float(l.split("|")[3]) for l in open("datos/raw/db/ml_runs.txt").read().splitlines()[1:] if l.count("|") >= 4 and l.split("|")[1] != "dummy"}
filas = [  # (etiqueta, mín s, máx s, fuente)
    ("Endpoints del panel", 0.014, 0.472, "reg"), ("Intervalo entre reportes (n = 35)", min(gaps) / 1000, max(gaps) / 1000, "bd"),
    ("Importación de 107 194 registros", 9.66, 9.66, "bd"), ("Análisis LLM por hallazgo (CPU)", 28, 37, "reg"),
    ("Narración bajo demanda (LLM)", 74.5, 74.5, "reg"), ("Entrenamiento por modelo (validación anidada)", min(tr.values()), max(tr.values()), "bd")]
fig, ax = plt.subplots(figsize=(estilo.ANCHO, 2.9))
for i, (l, a, b, f) in enumerate(filas[::-1]):
    c = C["azul"] if f == "bd" else C["naranja"]
    if b > a * 1.001: ax.plot([a, b], [i, i], color=c, lw=5, solid_capstyle="butt")
    ax.plot([a, b], [i, i], "o", color=c, ms=4)
    f_ = lambda v: (f"{v:,.0f}".replace(",", " ") if v >= 1000 else f"{v:.3g}".replace(".", ","))
    ax.text(b * 1.25, i, f_(a) + (f" – {f_(b)} s" if b > a * 1.001 else " s"), va="center", fontsize=6.5)
ax.set_yticks(range(len(filas))); ax.set_yticklabels([f[0] for f in filas[::-1]]); ax.set_xscale("log"); ax.set_xlim(0.008, 40000)
ax.set_xlabel("Tiempo (s, escala logarítmica)"); ax.grid(axis="y", visible=False)
from matplotlib.lines import Line2D
ax.legend([Line2D([], [], color=C["azul"], lw=4), Line2D([], [], color=C["naranja"], lw=4)], ["Leído de la base de datos o de los artefactos", "Registro de la prueba de despliegue"], loc="upper right", frameon=False)
fig.savefig("F6_latencias.png")
json.dump([dict(operacion=l, min_s=a, max_s=b, fuente=f) for l, a, b, f in filas], open("datos/F6_tiempos.json", "w"), ensure_ascii=False, indent=1)
print(filas)
