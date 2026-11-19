"""F3. Regularidad de los intervalos entre conexiones (coeficiente de variación, CV) por grupo origen-destino-puerto-protocolo,
calculada con el detector real (backend/app/services/detectors/beaconing.py) sobre el archivo CTU-13 escenario 11."""
import sys, json
from pathlib import Path
import numpy as np, pandas as pd
import matplotlib.pyplot as plt
import estilo
from estilo import C, num

RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ / "backend"))
from app.services.detectors.beaconing import group_from_series, score_beaconing, _is_group_destination  # noqa: E402
from app.services.detectors.common import DetectionConfig  # noqa: E402

BOTNET = {"147.32.84.165", "147.32.84.191", "147.32.84.192"}
cfg = DetectionConfig()  # valores por defecto: n >= 10, CV <= 0,25, puntaje >= 60

df = pd.read_csv(RAIZ / "data/dataset/capture20110818-2.binetflow")
df["t"] = pd.to_datetime(df.StartTime)
import ipaddress
def _priv(ip):
    try: return ipaddress.ip_address(ip).is_private and not ip.startswith("224.")
    except ValueError: return False
# tráfico saliente: origen en la red de la universidad (147.32.0.0/16), destino externo (ni de la misma red ni privado)
df = df[df.SrcAddr.str.startswith("147.32.") & ~df.DstAddr.str.startswith("147.32.") & ~df.DstAddr.map(_priv)]
rows = []
for (s, d, p, pr), g in df.groupby(["SrcAddr", "DstAddr", "Dport", "Proto"], dropna=False):
    if len(g) < cfg.beacon_min_connections:
        continue
    ts = [x.to_pydatetime() for x in g.t]
    bg = group_from_series(s, d, None if pd.isna(p) else int(float(p)) if str(p).isdigit() else None, pr, ts, list(g.SrcBytes.fillna(0)))
    cv = bg.stdev_interval_s / bg.mean_interval_s if bg.mean_interval_s > 0 else np.nan
    res = score_beaconing(bg, cfg)
    rows.append(dict(src=s, dst=d, dport=p, proto=pr, n=len(g), mean_s=bg.mean_interval_s, cv=cv,
                     score=None if res is None else res[0], grupo_destino=_is_group_destination(d), botnet=s in BOTNET))
R = pd.DataFrame(rows)
R["emitido"] = (R.score.fillna(0) >= cfg.beacon_min_score) & ~R.grupo_destino
Path("datos").mkdir(exist_ok=True)
R.to_csv("datos/F3_regularidad_grupos.csv", index=False)
print("grupos con n>=10:", len(R), "| CV<=0,25:", int((R.cv <= .25).sum()), "| emitidos (código actual):", int(R.emitido.sum()),
      "| de hosts botnet:", int(R.botnet.sum()))

estilo.aplicar()
fig, ax = plt.subplots(figsize=(estilo.ANCHO, 3.4))
R2 = R[R.mean_s >= 1.0].copy()
cvp = R2.cv.clip(lower=1e-4)
m1 = R2.cv > cfg.beacon_max_cv
m2 = (R2.cv <= cfg.beacon_max_cv) & ~R2.emitido
m3 = R2.emitido
ax.scatter(R2.n[m1], cvp[m1], s=11, color=C["gris_claro"], edgecolor=C["gris"], linewidth=0.4, label=f"CV > 0,25: sin hallazgo (n = {int(m1.sum())})", zorder=2)
ax.scatter(R2.n[m2], cvp[m2], s=16, marker="s", color=C["celeste"], edgecolor=C["azul"], linewidth=0.5, label=f"CV ≤ 0,25 sin hallazgo: puntaje < 60 o destino de grupo (n = {int(m2.sum())})", zorder=3)
ax.scatter(R2.n[m3], cvp[m3], s=20, marker="D", color=C["bermellon"], edgecolor="black", linewidth=0.4, label=f"Hallazgo de beaconing emitido (n = {int(m3.sum())})", zorder=4)
if R2.botnet.any():
    b = R2[R2.botnet]
    ax.scatter(b.n, b.cv.clip(lower=1e-4), s=36, marker="o", facecolor="none", edgecolor=C["negro"], linewidth=1.0, label=f"Equipo infectado (n = {len(b)})", zorder=5)
ax.axhline(cfg.beacon_max_cv, color=C["negro"], ls="--", lw=0.8)
ax.text(R2.n.max() * 0.95, cfg.beacon_max_cv * 1.12, "umbral CV = 0,25", ha="right", va="bottom", fontsize=6.8)
ax.set_xscale("log"); ax.set_yscale("log")
ax.set_xlabel("Conexiones del grupo en 16 min (escala logarítmica)")
ax.set_ylabel("CV de los intervalos (escala logarítmica)")
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.17), ncol=1, frameon=False)
fig.savefig("F3_regularidad_intervalos.png")
print("ok")
