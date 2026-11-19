"""F2. Flujo de procesamiento (a) y protocolo de validación con las cifras reales del conjunto etiquetado (b)."""
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import estilo
from estilo import C
estilo.aplicar()
fig, axs = plt.subplots(2, 1, figsize=(estilo.ANCHO, 3.9), gridspec_kw={"height_ratios": [0.75, 1.15]})
def caja(ax, x, y, w, h, t, fc, fs=5.5):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.2,rounding_size=0.8", fc=fc, ec="black", lw=0.7))
    ax.text(x + w / 2, y + h / 2, t, ha="center", va="center", fontsize=fs, linespacing=1.2)
def fl(ax, a, b):
    ax.add_patch(FancyArrowPatch(a, b, arrowstyle="-|>", mutation_scale=7, lw=0.8, color="black", shrinkA=0, shrinkB=0))
ax = axs[0]; ax.set_xlim(0, 100); ax.set_ylim(0, 19); ax.axis("off"); ax.grid(False)
pas = [("Ingesta\n(cron 15 min)\nParser → registro\nnormalizado", "#E8F1FA"), ("Detectores\ndeterministas\n(beaconing, puertos,\nvolumen, IDS, host)", "#FDEBD0"),
       ("Lista de permitidos/\ndenegados y\ncriticidad del activo", "#FDEBD0"), ("Cadena LLM:\nveredicto real/ruido/\nincierto + explicación", "#DDF0E8"),
       ("Alerta + reporte\n(PDF, DOCX, XLSX)\n+ bitácora", "#EFE3EE")]
w = 17.2
for i, (t, fc) in enumerate(pas):
    x = 1 + i * 19.6; caja(ax, x, 4, w, 13, t, fc)
    if i: fl(ax, (x - 2.4, 10.5), (x, 10.5))
ax.text(50, 0.4, "Si el modelo no responde o devuelve una salida inválida, se usa una plantilla determinista", ha="center", fontsize=5.6, style="italic")
estilo.etiqueta_panel(ax, "a")
ax = axs[1]; ax.set_xlim(0, 100); ax.set_ylim(0, 30); ax.axis("off"); ax.grid(False)
caja(ax, 1, 20, 18, 8, "107 194 flujos\nCTU-13 esc. 11", "#E8F1FA")
caja(ax, 22, 20, 20, 8, "10 882 etiquetados\n(8 164 Botnet, 2 718 Normal)\n96 312 Background excluidos", "#E8F1FA", fs=5.2)
caja(ax, 45, 20, 19, 8, "Agrupación por bloques\ntemporales de 10 s\n(97 grupos)", "#FDEBD0")
caja(ax, 67, 20, 32, 8, "Partición 70/15/15\npor grupos, estratificada,\nsemilla 42", "#FDEBD0", fs=5.4)
fl(ax, (19, 24), (22, 24)); fl(ax, (42, 24), (45, 24)); fl(ax, (64, 24), (67, 24))
caja(ax, 1, 4, 30, 11, "Desarrollo: 7 694 flujos\nValidación cruzada anidada 5 × 3\n(StratifiedGroupKFold); Optuna (TPE,\npoda), 20 pruebas por pliegue", "#DDF0E8", fs=5.3)
caja(ax, 36, 4, 28, 11, "Validación: 1 663 flujos\numbral (F1) y calibración;\nmodelo final", "#DDF0E8", fs=5.3)
caja(ax, 69, 4, 30, 11, "Prueba: 1 525 flujos\n(1 118 Botnet, 407 Normal)\nevaluada una sola vez", "#EFE3EE", fs=5.3)
for x in (16, 50, 84): fl(ax, (x, 20), (x, 15))
ax.text(50, 0.8, "El preprocesamiento se ajusta dentro de cada pliegue; sin IP, marca de tiempo absoluta ni etiqueta como variables", ha="center", fontsize=5.6, style="italic")
estilo.etiqueta_panel(ax, "b")
fig.tight_layout(h_pad=0.8); fig.savefig("F2_flujo_y_protocolo.png")
