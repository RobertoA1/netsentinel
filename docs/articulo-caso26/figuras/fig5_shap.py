"""F5. Importancia de variables de XGBoost: |SHAP| medio y caída de PR-AUC por permutación (artefactos reales del trabajo de explicabilidad)."""
import json
import numpy as np, matplotlib.pyplot as plt
import estilo
from estilo import C
estilo.aplicar()
r = json.load(open("datos/raw/job3_explain_xgboost.json"))
fig_ = {f["id"]: f for f in r["figures"]}
sh = fig_["shap_bar"]["data"]; pm = fig_["perm_bar"]["data"]
n = 9
lab = sh["labels"][:n][::-1]; val = np.array(sh["series"][0]["values"][:n])[::-1]
fig, axs = plt.subplots(1, 2, figsize=(estilo.ANCHO, 2.7), gridspec_kw={"width_ratios": [1, 1]})
axs[0].barh(lab, val, color=C["azul"]); axs[0].set_xlabel("|SHAP| medio (log-odds)")
tot = sum(sh["series"][0]["values"])
axs[0].text(val[-1] * 0.97, n - 1, f"{100 * val[-1] / tot:,.0f} % del total".replace(".", ","), ha="right", va="center", color="white", fontsize=6.5, fontweight="bold")
labp = pm["labels"][:n][::-1]; vp = np.array(pm["series"][0]["values"][:n])[::-1]; er = np.array(pm["series"][0]["err"][:n])[::-1]
axs[1].barh(labp, vp, xerr=er, color=C["naranja"], ecolor="black", capsize=2); axs[1].set_xlabel("Caída de PR-AUC al permutar (media ± desv., 5 repeticiones)")
for a, l in zip(axs, "ab"): estilo.etiqueta_panel(a, l); a.grid(axis="y", visible=False)
fig.tight_layout(w_pad=1.5)
fig.savefig("F5_importancia_variables.png")
json.dump(dict(shap=dict(zip(sh["labels"], sh["series"][0]["values"])), permutacion=dict(zip(pm["labels"], pm["series"][0]["values"]))), open("datos/F5_importancias.json", "w"), ensure_ascii=False, indent=1)
print(100 * val[-1] / tot)
