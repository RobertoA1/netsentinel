"""F1. Arquitectura y despliegue de NetSentinel (servicios de docker-compose.yml y flujos del README)."""
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import estilo
from estilo import C
estilo.aplicar()
fig, ax = plt.subplots(figsize=(estilo.ANCHO, 4.4)); ax.set_xlim(0, 100); ax.set_ylim(0, 62); ax.axis("off"); ax.grid(False)
def caja(x, y, w, h, t, fc="#FFFFFF", ec=C["negro"], fs=5.4, bold=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.25,rounding_size=1", fc=fc, ec=ec, lw=0.8))
    ax.text(x + w / 2, y + h / 2, t, ha="center", va="center", fontsize=fs, fontweight="bold" if bold else "normal", linespacing=1.25)
def flecha(a, b, t=None, ls="-", both=False, off=(0, 1.2)):
    ax.add_patch(FancyArrowPatch(a, b, arrowstyle="<|-|>" if both else "-|>", mutation_scale=7, lw=0.8, ls=ls, color=C["negro"], shrinkA=0, shrinkB=0))
    if t: ax.text((a[0] + b[0]) / 2 + off[0], (a[1] + b[1]) / 2 + off[1], t, fontsize=5.8, ha="center", color=C["gris"])
# red del cliente
ax.add_patch(FancyBboxPatch((0.5, 2), 99, 58, boxstyle="round,pad=0.2,rounding_size=2", fc="#F7F7F7", ec=C["gris"], lw=0.8, ls="--"))
ax.text(2, 57.8, "Servidor de la organización (Docker Compose; los datos no salen de la red)", fontsize=6.4, fontweight="bold", color=C["gris"], va="center")
caja(3, 40, 17, 11, "OPNsense / Suricata\n(filterlog, eve.json)\nCTU-13 (demostración)", fc="#E8F1FA")
caja(3, 20, 17, 10, "Carpeta de ingesta\ndata/ingest/<fuente>", fc="#E8F1FA")
caja(28, 38, 21, 14, "Backend FastAPI\nanalizadores · detectores\ndeterministas · RBAC ·\nbitácora de auditoría", fc="#FDEBD0", bold=False)
caja(28, 12, 21, 14, "Laboratorio ML\n(ml-worker, Optuna,\nSHAP, conformal)", fc="#FDEBD0")
caja(57, 44, 18, 8, "Cadena LangChain\n(salida estructurada)", fc="#DDF0E8")
caja(57, 31, 18, 8, "Ollama\nllama3.2:3b (CPU)", fc="#DDF0E8")
caja(57, 14, 18, 11, "PostgreSQL 16\nfirewall_logs · hallazgos\nml_* · auditoría", fc="#EFE3EE")
caja(82, 44, 16, 8, "Interfaz React\n(nginx)", fc="#FFFFFF")
caja(80.5, 28, 19, 12, "n8n\n01 ingesta (15 min)\n02 alertas (5 min)\n03 mantenimiento", fc="#FFFFFF", fs=5.0)
caja(82, 8, 16, 11, "Webhook o SMTP\ndel cliente", fc="#FFFFFF")
flecha((20, 45), (28, 46)); flecha((20, 25), (28, 40), "archivos")
flecha((49, 48), (57, 48), "hallazgo +\nevidencia", off=(-2.2, 3.4)); flecha((66, 44), (66, 39), both=True)
flecha((49, 42), (57, 20), both=True); flecha((38.5, 38), (38.5, 26), "  puntuación", both=True, off=(5, 0))
ax.add_patch(FancyArrowPatch((82, 30), (43, 38), connectionstyle="angle,angleA=0,angleB=90,rad=0", arrowstyle="-|>", mutation_scale=7, lw=0.8, ls="--", color=C["negro"]))
ax.text(64, 28.2, "POST /ingest/run (cada 15 min)", fontsize=5.6, ha="center", color=C["gris"]); flecha((90, 28), (90, 19), "alertas")
flecha((82, 48), (75, 50), both=True)
ax.text(66, 54.2, "interpretación (no calcula métricas)", fontsize=5.4, ha="center", color=C["verde"], fontweight="bold")
ax.text(50, 4.2, "Cálculo determinista y evidencia en el backend; el modelo de lenguaje solo clasifica y explica lo ya calculado.", fontsize=5.8, ha="center", style="italic")
fig.savefig("F1_arquitectura.png")
