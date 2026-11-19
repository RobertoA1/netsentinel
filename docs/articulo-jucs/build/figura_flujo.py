"""Figura 1 del articulo: flujo de entrenamiento y validacion de un modelo (un escenario excluido, una semilla).
Cada valor del dibujo sale del codigo de los experimentos (docs/validacion-externa/multiescenario.py y backend/app/ml/models.py).
Uso: python figura_flujo.py   (escribe ../figuras/fig2_flujo.png; ancho 12,2 cm = area de texto de la plantilla)"""
import textwrap, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

plt.rcParams.update({"font.family": "Liberation Serif", "font.size": 7, "figure.dpi": 300, "savefig.dpi": 300})
OUT = "../figuras/"
fig, ax = plt.subplots(figsize=(4.8, 5.55)); ax.set_xlim(0, 101); ax.set_ylim(0, 116); ax.axis("off")
FS = 6.3
GRIS, AZUL, VERDE, NARANJA = "#EEEEEE", "#DCE9F5", "#DDF0E6", "#FBE9D0"

def caja(x, y, w, h, texto, fc="white", ec="black", lw=0.6, ls="-", fs=FS, ha="center", bold_first=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.15,rounding_size=1.0", fc=fc, ec=ec, lw=lw, ls=ls))
    if ha == "center":
        ax.text(x + w / 2, y + h / 2, texto, ha="center", va="center", fontsize=fs, linespacing=1.3)
    else:
        ax.text(x + 1.6, y + h - 1.4, texto, ha="left", va="top", fontsize=fs, linespacing=1.3)

def flecha(x0, y0, x1, y1, ls="-", lw=0.7):
    ax.annotate("", xy=(x1, y1), xytext=(x0, y0), arrowprops=dict(arrowstyle="-|>", lw=lw, color="black", ls=ls, shrinkA=0, shrinkB=0, mutation_scale=6))

L, WL = 1, 61          # columna izquierda
R, WR = 66, 34.5         # columna derecha (notas)
cx = L + WL / 2

# ------------------------------------------------------------ columna izquierda: pasos
ax.text(L, 114, "Flujo de entrenamiento (un modelo, un escenario excluido k, una semilla)", fontsize=7.2, fontweight="bold", va="center")
caja(L, 98, WL, 12, "1. Datos y partición externa\nSubmuestreo estratificado de cada escenario\n(≤ 2 500 flujos); el escenario k se aparta como prueba")
caja(L, 83, WL, 11, "2. Partición interna\nLos 11 escenarios restantes se reparten en\n4 grupos (sorteo con la semilla; 3, 3, 3 y 2)")
flecha(cx, 98, cx, 94.4); flecha(cx, 83, cx, 80.4)

# bloque de busqueda (iterativo)
ax.add_patch(FancyBboxPatch((L, 40), WL, 40, boxstyle="round,pad=0.15,rounding_size=1.0", fc=GRIS, ec="black", lw=0.8, ls=(0, (4, 2))))
ax.text(L + 2, 77.2, "3. Búsqueda con Optuna: intento t = 1, …, 10", fontsize=FS, fontweight="bold", va="center")
caja(L + 5, 64.5, WL - 8, 8.2, "3a. Muestrear una combinación de hiperparámetros\n(espacio de la Tabla 2)", fc="white")
caja(L + 5, 52, WL - 8, 9.2, "3b. Para cada grupo g de los 4 (rotación):\nentrenar con los otros 3 y predecir g", fc="white")
caja(L + 5, 42.6, WL - 8, 6.4, "3c. Valor del intento: PR-AUC media por escenario", fc="white")
xm = L + 5 + (WL - 8) / 2
flecha(xm, 64.5, xm, 61.6); flecha(xm, 52, xm, 49.4)
# retorno del bucle (3c -> 3a)
xr = L + 2.2
ax.plot([L + 5, xr, xr], [45.8, 45.8, 68.6], color="black", lw=0.7); flecha(xr, 68.6, L + 4.9, 68.6)
ax.text(xr + 0.7, 57.2, "t < 10", fontsize=5.6, rotation=90, va="center", ha="left", style="italic")
flecha(cx, 40, cx, 37.4)
ax.text(cx + 1.2, 38.7, "t = 10", fontsize=5.6, va="center", ha="left", style="italic")

caja(L, 25, WL, 12, "4. Umbral de decisión\nMejores hiperparámetros → predicciones internas →\ncuantil (de 199) con máxima exactitud balanceada")
caja(L, 12.5, WL, 9.5, "5. Reentrenamiento con los 11 escenarios\n(hiperparámetros y umbral ya fijos)")
caja(L, 0.5, WL, 9.5, "6. Evaluación única en el escenario k\nPR-AUC, ROC-AUC, sensibilidad, precisión\ny exactitud balanceada")
flecha(cx, 25, cx, 22.4); flecha(cx, 12.5, cx, 10.4)

# ------------------------------------------------------------ columna derecha: notas
def nota(y, h, titulo, lineas, fc):
    ax.add_patch(FancyBboxPatch((R, y), WR, h, boxstyle="round,pad=0.15,rounding_size=1.0", fc=fc, ec="black", lw=0.5))
    ax.text(R + 1.6, y + h - 1.6, titulo, fontsize=FS + 0.2, fontweight="bold", va="top")
    cuerpo = "\n".join(textwrap.fill("• " + t, 34, subsequent_indent="  ") for t in lineas)
    ax.text(R + 1.6, y + h - 5.4, cuerpo, fontsize=5.7, va="top", linespacing=1.25)

nota(84, 26, "Condiciones iniciales", [
    "Semillas 11, 22, 33, 44, 55",
    "Estudio de Optuna nuevo, sin historial",
    "Los primeros 10 intentos son aleatorios (TPE)",
    "Sin hiperparámetros previos; sin umbral previo",
    "Preprocesamiento aún sin ajustar"], AZUL)
nota(50, 31, "Parametrización", [
    "Espacios de búsqueda: Tabla 2",
    "10 intentos por modelo y escenario k",
    "Objetivo: maximizar la PR-AUC media por escenario",
    "Umbral: 199 cuantiles (1\u00a0% a 99\u00a0%)",
    "Otros valores: Tabla 3"], VERDE)
nota(0.5, 46, "Condiciones de parada", [
    "Búsqueda: 10 intentos; sin tiempo límite; sin poda efectiva",
    "RL: tol = 0,0001 o 2 000 iteraciones",
    "RF: n_estimators fijo por intento",
    "HGB: max_iter; sin parada temprana",
    "XGB: 300 rondas; sin parada temprana",
    "Protocolo: fin tras las 300 evaluaciones"], NARANJA)
# conectores punteados hacia los pasos que acotan
for y0, y1 in ((95, 100), (62, 62), (18, 18)):
    ax.plot([L + WL + 0.3, R - 0.3], [y0, y1], color="#666666", lw=0.5, ls=(0, (1.5, 1.5)))
fig.savefig(OUT + "fig2_flujo.png", bbox_inches="tight", pad_inches=0.03); plt.close(fig)
print("figura escrita")
