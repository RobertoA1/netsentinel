"""Estilo común de las figuras: paleta de Okabe-Ito (apta para daltónicos), 600 DPI, rótulos en español."""
import matplotlib as mpl
import matplotlib.pyplot as plt

DPI = 600
ANCHO = 6.5  # pulgadas = ancho útil de la página (9 404 twips)
C = {"azul": "#0072B2", "naranja": "#E69F00", "celeste": "#56B4E9", "verde": "#009E73",
     "bermellon": "#D55E00", "purpura": "#CC79A7", "amarillo": "#F0E442", "negro": "#000000", "gris": "#6B6B6B",
     "gris_claro": "#D9D9D9"}

def aplicar():
    mpl.rcParams.update({
        "font.family": "DejaVu Sans", "font.size": 7.5, "axes.titlesize": 8, "axes.labelsize": 7.5,
        "xtick.labelsize": 7, "ytick.labelsize": 7, "legend.fontsize": 6.8, "axes.spines.top": False,
        "axes.spines.right": False, "axes.linewidth": 0.7, "lines.linewidth": 1.2, "figure.dpi": 150,
        "savefig.dpi": DPI, "savefig.bbox": "tight", "savefig.pad_inches": 0.04, "axes.grid": True,
        "grid.color": "#E6E6E6", "grid.linewidth": 0.5, "axes.axisbelow": True,
    })

def num(x, nd=3):
    """Formato decimal con coma (español)."""
    return f"{x:.{nd}f}".replace(".", ",")

def coma(ax, ejes="xy"):
    """Eje con separador decimal coma (convención del español)."""
    from matplotlib.ticker import FuncFormatter
    f = FuncFormatter(lambda v, _: (f"{v:g}").replace(".", ","))
    if "x" in ejes: ax.xaxis.set_major_formatter(f)
    if "y" in ejes: ax.yaxis.set_major_formatter(f)

def etiqueta_panel(ax, letra):
    ax.text(-0.02, 1.04, letra, transform=ax.transAxes, fontsize=9, fontweight="bold", va="bottom", ha="right")
