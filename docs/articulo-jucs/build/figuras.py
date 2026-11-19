"""Genera las figuras del articulo J.UCS a partir de datos.json (analisis.py). Ancho 12,2 cm = area de texto de la plantilla."""
import json, numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle
D = json.load(open("datos.json")); OUT = "../figuras/"
plt.rcParams.update({"font.family": "Liberation Serif", "font.size": 7.5, "axes.linewidth": 0.6, "axes.spines.top": False, "axes.spines.right": False,
                     "figure.dpi": 300, "savefig.dpi": 300, "xtick.major.width": 0.6, "ytick.major.width": 0.6, "legend.frameon": False})
W = 4.8
ESC = D["escenarios"]; FAM = {int(k): v for k, v in D["familia"].items()}
COL = {"logreg": "#0072B2", "random_forest": "#009E73", "hist_gb": "#E69F00", "xgboost": "#CC79A7", "LR+RF+HGB": "#222222"}
LAB = {"logreg": "Reg. logística", "random_forest": "Random forest", "hist_gb": "HistGB", "xgboost": "XGBoost", "LR+RF+HGB": "RL+RF+HGB"}
MK = {"logreg": "o", "random_forest": "s", "hist_gb": "^", "xgboost": "D", "LR+RF+HGB": "*"}
FAMCOL = {"Neris": "#D55E00", "Rbot": "#0072B2", "Virut": "#009E73", "Menti": "#F0E442", "Sogou": "#CC79A7", "Murlo": "#56B4E9", "NSIS.ay": "#999999"}

# ---------------- Fig. 2: particion de ejemplo (el flujo de entrenamiento esta en figura_flujo.py)
fig, ax = plt.subplots(figsize=(W, 2.0)); ax.set_xlim(0, 102); ax.set_ylim(55.5, 100); ax.axis("off")
held = 7; x0, bw, gap = 1.5, 6.6, 1.55
for i, e in enumerate(ESC):
    x = x0 + i * (bw + gap)
    ax.add_patch(Rectangle((x, 84), bw, 7, fc=FAMCOL[FAM[e]], ec="black", lw=1.6 if e == held else 0.4, hatch="////" if e == held else None))
    ax.text(x + bw / 2, 87.5, str(e), ha="center", va="center", fontsize=7.5, fontweight="bold", bbox=dict(fc="white", ec="none", pad=0.6, alpha=0.85) if e == held else None)
    ax.text(x + bw / 2, 82.5, FAM[e], ha="center", va="top", fontsize=5.4)
ax.text(1, 97, "12 escenarios etiquetados de CTU-13 (tope de 2 500 flujos por escenario)", fontsize=7.3, va="center", fontweight="bold")
ax.text(1, 74.5, "Trama = escenario excluido: no participa en el ajuste y se usa una sola vez como prueba (ejemplo: 7).", fontsize=6.2, va="center", style="italic")
train = [e for e in ESC if e != held]; order = np.random.default_rng(11).permutation(train); groups = [sorted(order[i::4].tolist()) for i in range(4)]
ax.text(1, 68.5, "Validación interna: los 11 escenarios restantes en 4 grupos (sorteo por semilla)", fontsize=7.0, va="center", fontweight="bold")
gw = 23.2
for gi, g in enumerate(groups):
    x = 1.5 + gi * (gw + 2.4)
    ax.add_patch(FancyBboxPatch((x, 58), gw, 6.0, boxstyle="round,pad=0.2,rounding_size=1.0", fc="#EEEEEE", ec="black", lw=0.5))
    ax.text(x + gw / 2, 61, f"G{gi+1}: " + ", ".join(str(v) for v in g), ha="center", va="center", fontsize=6.6)
fig.savefig(OUT + "fig1_particion.png", bbox_inches="tight", pad_inches=0.03); plt.close(fig)

# ---------------- Fig. 3: PR-AUC por escenario
fig, ax = plt.subplots(figsize=(W, 3.0))
ms = ["logreg", "random_forest", "hist_gb", "xgboost", "LR+RF+HGB"]
src = {m: (D["flujo"][m] if m in D["flujo"] else D["ensambles"][m]) for m in ms}
offs = np.linspace(-0.28, 0.28, 5)
for j, m in enumerate(ms):
    ax.errorbar(np.arange(12) + offs[j], src[m]["per_esc_mean"], yerr=src[m]["per_esc_sd"], fmt=MK[m], ms=3.6 if m != "LR+RF+HGB" else 5, color=COL[m], ecolor=COL[m], elinewidth=0.5, capsize=0, label=LAB[m], mfc=COL[m] if m != "xgboost" else "white")
prev = [D["prevalencia"][str(e)] for e in ESC]
ax.hlines(prev, np.arange(12) - 0.4, np.arange(12) + 0.4, color="black", lw=1.4, label="Dummy (= prevalencia)")
ax.set_xticks(range(12)); ax.set_xticklabels([f"{e}\n{FAM[e]}" for e in ESC], fontsize=6.2); ax.set_ylim(0, 1.04); ax.set_ylabel("PR-AUC en el escenario excluido")
ax.set_xlim(-0.6, 11.6); ax.grid(axis="y", lw=0.3, alpha=0.6); ax.legend(ncol=3, fontsize=6.2, loc="lower center", bbox_to_anchor=(0.5, 1.0), columnspacing=1.0, handletextpad=0.3)
fig.savefig(OUT + "fig3_pr_por_escenario.png", bbox_inches="tight", pad_inches=0.03); plt.close(fig)

# ---------------- Fig. 3: flujo vs contexto de host (ensamble LR+RF+HGB)
fig, ax = plt.subplots(figsize=(W, 2.7))
a = D["ensambles"]["LR+RF+HGB"]["per_esc_mean"]; b = D["host_W1"]["LR+RF+HGB"]["per_esc_mean"]; c = D["host_W5"]["LR+RF+HGB"]["per_esc_mean"]; x = np.arange(12)
for i in x: ax.plot([i, i, i], [a[i], b[i], c[i]], color="#bbbbbb", lw=0.8, zorder=1)
ax.scatter(x - 0.12, a, marker="o", s=16, facecolor="white", edgecolor="black", lw=0.8, label="solo flujo", zorder=3)
ax.scatter(x, b, marker="^", s=16, color="#E69F00", label="flujo + host, W = 1 min", zorder=3)
ax.scatter(x + 0.12, c, marker="s", s=14, color="#0072B2", label="flujo + host, W = 5 min", zorder=3)
ax.set_xticks(x); ax.set_xticklabels([f"{e}\n{FAM[e]}" for e in ESC], fontsize=6.2); ax.set_ylim(0.35, 1.03); ax.set_ylabel("PR-AUC (ensamble RL+RF+HGB)"); ax.grid(axis="y", lw=0.3, alpha=0.6)
ax.legend(ncol=3, fontsize=6.2, loc="lower center", bbox_to_anchor=(0.5, 1.0), columnspacing=1.0, handletextpad=0.3)
fig.savefig(OUT + "fig4_contexto_host.png", bbox_inches="tight", pad_inches=0.03); plt.close(fig)

# ---------------- Fig. 4: evaluacion realista (Background como Normal), semilla 11, escenarios 1-3
fo = D["fondo"]; names = {"logreg": "RL", "random_forest": "RF", "hist_gb": "HGB", "xgboost": "XGB", "LR+RF+HGB": "Ens."}
fig, axs = plt.subplots(2, 3, figsize=(W, 3.3), sharey="row")
for k, e in enumerate((1, 2, 3)):
    rows = {r["model"]: r for r in fo if r["held_out"] == e}; xs = np.arange(5)
    for rowi, (key1, key2, yl) in enumerate((("pr_auc_solo_etiquetados", "pr_auc_realista", "PR-AUC"), (None, "fpr_background", "Background marcado"))):
        ax = axs[rowi, k]
        if key1:
            ax.bar(xs - 0.2, [rows[m][key1] for m in names], 0.38, color="#bbbbbb", label="solo etiquetados"); ax.bar(xs + 0.2, [rows[m][key2] for m in names], 0.38, color="#D55E00", label="realista (Background = Normal)"); ax.set_ylim(0, 1.05)
        else:
            ax.bar(xs, [100 * rows[m][key2] for m in names], 0.6, color="#0072B2"); ax.set_ylim(0, 50)
        ax.set_xticks(xs); ax.set_xticklabels([names[m] for m in names], fontsize=6.2)
        if rowi == 0: ax.set_title(f"Esc. {e} ({FAM[e]})", fontsize=7.5)
        if k == 0: ax.set_ylabel(yl if rowi == 0 else "Background marcado (%)", fontsize=6.8)
h, l = axs[0, 0].get_legend_handles_labels(); fig.legend(h, l, ncol=2, fontsize=6.4, loc="upper center", bbox_to_anchor=(0.5, 1.03))
fig.tight_layout(h_pad=0.6, w_pad=0.5, rect=(0, 0, 1, 0.95)); fig.savefig(OUT + "fig5_evaluacion_realista.png", bbox_inches="tight", pad_inches=0.03); plt.close(fig)

# ---------------- Fig. 5: CIC-IDS2017
fig, axs = plt.subplots(1, 2, figsize=(W, 2.3)); mods = ["logreg", "random_forest", "hist_gb", "xgboost", "LR+RF+HGB"]
cf = {r["model"]: r for r in D["cic_flow"]}; ch = {r["model"]: r for r in D["cic_host"]}; xs = np.arange(5); prev0 = D["cic_flow"][0]["prevalencia"]
for ax, key, yl, ref in ((axs[0], "pr_auc", "PR-AUC", prev0), (axs[1], "roc_auc", "ROC-AUC", 0.5)):
    ax.bar(xs - 0.2, [cf[m][key] for m in mods], 0.38, color="#0072B2", label="solo flujo"); ax.bar(xs + 0.2, [ch[m][key] for m in mods], 0.38, color="#E69F00", label="flujo + host (causal)")
    ax.axhline(ref, color="black", lw=0.9, ls="--"); ax.set_xticks(xs); ax.set_xticklabels([names[m] for m in mods], fontsize=6.5); ax.set_ylabel(yl)
    ax.set_xlim(-0.6, 5.3); ax.text(4.62, ref, "azar", ha="left", va="center", fontsize=6.2)
axs[0].set_ylim(0, 0.1); axs[1].set_ylim(0, 1.0); axs[0].legend(fontsize=6.2, loc="upper right")
fig.tight_layout(w_pad=1.0); fig.savefig(OUT + "fig6_cic.png", bbox_inches="tight", pad_inches=0.03); plt.close(fig)
print("ok")
