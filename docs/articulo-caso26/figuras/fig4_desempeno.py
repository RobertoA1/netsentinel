"""F4. Curvas precisión-exhaustividad y ROC en Prueba (n = 1 525) y matriz de confusión de XGBoost, con las predicciones reales guardadas."""
import json
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import precision_recall_curve, roc_curve, auc, confusion_matrix
import estilo
from estilo import C
estilo.aplicar()
runs = {6: "Línea base trivial", 7: "Regresión logística", 8: "Random Forest", 9: "Boosting de histogramas", 12: "XGBoost"}
col = {6: C["gris"], 7: C["azul"], 8: C["naranja"], 9: C["verde"], 12: C["bermellon"]}
ls = {6: ":", 7: "-", 8: "--", 9: "-.", 12: "-"}
fig, axs = plt.subplots(1, 3, figsize=(estilo.ANCHO, 2.5), gridspec_kw={"width_ratios": [1, 1, 0.9]})
rows = []
for r, nom in sorted(runs.items(), key=lambda kv: kv[0] != 12 and kv[0] != 6, reverse=False):
    p = json.load(open(f"datos/raw/runs/run{r}_preds.json"))["test"]
    y, s = np.array(p["y"]), np.array(p["p"])
    pr, rc, _ = precision_recall_curve(y, s); fpr, tpr, _ = roc_curve(y, s)
    axs[0].plot(rc, pr, ls[r], color=col[r], label=nom, lw=1.0 if r not in (12, 6) else 2.6, zorder=3 if r not in (12, 6) else 2)
    axs[1].plot(fpr, tpr, ls[r], color=col[r], lw=1.0 if r not in (12, 6) else 2.6, zorder=3 if r not in (12, 6) else 2)
    rows.append((nom, auc(rc, pr), auc(fpr, tpr)))
    if r == 12: cm = confusion_matrix(y, (s >= 0.5).astype(int))
axs[0].set_xlabel("Exhaustividad"); axs[0].set_ylabel("Precisión"); axs[0].set_xlim(0, 1.01); axs[0].set_ylim(0.6, 1.02)
axs[0].axhline(1118 / 1525, color=C["gris"], lw=0.6); axs[0].text(0.02, 1118 / 1525 + 0.01, "prevalencia 0,733", fontsize=6)
axs[1].plot([0, 1], [0, 1], color=C["gris"], lw=0.6); axs[1].set_xlabel("Tasa de falsos positivos"); axs[1].set_ylabel("Tasa de verdaderos positivos")
axs[1].set_xlim(-0.01, 1); axs[1].set_ylim(0, 1.02)
ax = axs[2]; ax.grid(False)
ax.imshow(cm, cmap="Blues", vmin=0, vmax=cm.max())
for i in range(2):
    for j in range(2):
        ax.text(j, i, f"{cm[i, j]:,}".replace(",", " "), ha="center", va="center", fontsize=9, color="white" if cm[i, j] > 600 else "black", fontweight="bold")
ax.set_xticks([0, 1]); ax.set_xticklabels(["Normal", "Botnet"]); ax.set_yticks([0, 1]); ax.set_yticklabels(["Normal", "Botnet"])
ax.set_xlabel("Clase predicha"); ax.set_ylabel("Clase real"); ax.spines[:].set_visible(False)
for a, l in zip(axs, "abc"): estilo.etiqueta_panel(a, l)
for a in axs[:2]: estilo.coma(a)
h, lab = axs[0].get_legend_handles_labels()
fig.legend(h, lab, loc="upper center", bbox_to_anchor=(0.5, 0.0), ncol=5, frameon=False, fontsize=6.5)
fig.tight_layout(w_pad=1.2)
fig.savefig("F4_desempeno_prueba.png")
json.dump([dict(modelo=a, auc_pr_trapecio=b, auc_roc=c) for a, b, c in rows], open("datos/F4_areas.json", "w"), ensure_ascii=False, indent=1)
print(rows, cm.tolist())
