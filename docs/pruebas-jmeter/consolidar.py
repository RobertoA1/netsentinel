import json, glob, csv, re
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
R = [json.load(open(f)) for f in glob.glob("resultados/*/resumen.json")]
import statistics as _s
_all = [r for r in R if r["prueba"].startswith("carga_")]
with open("evidencias/tabla_replicas.csv","w",newline="") as _f:
    _w=__import__("csv").writer(_f); _w.writerow(["prueba","usuarios","error_pct","rps","p95"])
    for r in sorted(_all,key=lambda r:(r["usuarios"],r["prueba"])): _w.writerow([r["prueba"],r["usuarios"],r["error_pct"],r["rps"],r["p95"]])
carga=[]
for u in sorted({r["usuarios"] for r in _all}):
    g=[r for r in _all if r["usuarios"]==u]; m=dict(g[0])
    for k in ["error_pct","rps","media_ms","p50","p90","p95","p99","max_ms","muestras"]: m[k]=_s.median(r[k] for r in g)
    m["n_corridas"]=len(g); m["p95_min"]=min(r["p95"] for r in g); m["p95_max"]=max(r["p95"] for r in g); carga.append(m)
_dbr = [r for r in R if r["prueba"].startswith("db_")]
db = []
for u in sorted({r["usuarios"] for r in _dbr}):
    g = [r for r in _dbr if r["usuarios"] == u]; m = dict(g[0])
    for k in ["error_pct","rps","media_ms","p50","p90","p95","p99","max_ms","muestras","peor_p95_sin_login"]: m[k] = _s.median(r[k] for r in g)
    db.append(m)
with open("evidencias/tabla_carga.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["usuarios", "muestras", "error_pct", "rps", "media_ms", "p50", "p90", "p95", "p99", "max_ms"])
    for r in carga: w.writerow([r[k] for k in ["usuarios", "muestras", "error_pct", "rps", "media_ms", "p50", "p90", "p95", "p99", "max_ms"]])
x = [r["usuarios"] for r in carga]
fig, ax = plt.subplots(3, 1, figsize=(8, 9), sharex=True)
ax[0].fill_between(x,[r["p95_min"] for r in carga],[r["p95_max"] for r in carga],alpha=.2); ax[0].plot(x, [r["p95"] for r in carga], "o-", label="p95 (mediana y rango)"); ax[0].plot(x, [r["media_ms"] for r in carga], "s-", label="media")
ax[0].axhline(1000, ls="--", c="r", lw=1, label="umbral 1 s"); ax[0].set_yscale("log"); ax[0].set_ylabel("Tiempo de respuesta (ms)"); ax[0].legend()
ax[1].plot(x, [r["rps"] for r in carga], "o-g"); ax[1].set_ylabel("Peticiones/s")
ax[2].plot(x, [r["error_pct"] for r in carga], "o-r"); ax[2].set_ylabel("Errores (%)"); ax[2].set_xlabel("Usuarios virtuales simultáneos"); ax[2].axhline(1, ls="--", c="gray", lw=1)
for a in ax: a.grid(alpha=.3)
for a in ax: a.set_xscale("log")
plt.tight_layout(); plt.savefig("evidencias/curva_carga.png", dpi=150)
import csv as _c
with open("evidencias/tabla_bd.csv","w",newline="") as f:
    w=_c.writer(f); w.writerow(["usuarios","muestras","error_pct","rps","media_ms","p50","p90","p95","p99","max_ms"])
    for r in db: w.writerow([r[k] for k in ["usuarios","muestras","error_pct","rps","media_ms","p50","p90","p95","p99","max_ms"]])
fig, ax = plt.subplots(2, 1, figsize=(8, 6), sharex=True); xd=[r["usuarios"] for r in db]
ax[0].plot(xd,[r["p95"] for r in db],"o-",label="p95 BD (todas las consultas)"); ax[0].plot(xd,[r["peor_p95_sin_login"] for r in db],"^-",c="purple",label="p95 BD consulta más lenta"); ax[0].plot(x,[r["p95"] for r in carga],"s--",label="p95 API (todas las peticiones)",alpha=.6)
ax[0].axhline(1000,ls="--",c="r",lw=1); ax[0].set_yscale("log"); ax[0].set_ylabel("ms"); ax[0].legend()
ax[1].plot(xd,[r["error_pct"] for r in db],"o-r",label="BD"); ax[1].plot(x,[r["error_pct"] for r in carga],"s--",c="gray",label="API"); ax[1].set_ylabel("Errores (%)"); ax[1].set_xlabel("Usuarios virtuales"); ax[1].legend()
for a in ax: a.set_xscale("log"); a.grid(alpha=.3)
plt.tight_layout(); plt.savefig("evidencias/curva_bd.png", dpi=150)
for r in R:
    if not r["prueba"].startswith(("carga_","db_")): print(json.dumps(r, ensure_ascii=False))
