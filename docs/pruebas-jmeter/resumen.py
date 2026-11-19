"""Resumen de un .jtl. Tres vistas: 'peticiones' (muestras individuales), 'sesion' (muestra Transaction Controller) y 'total' (= fila TOTAL del Aggregate Report de JMeter)."""
import csv, sys, statistics as st, json
f, name, users = sys.argv[1], sys.argv[2], int(sys.argv[3])
SES = "Sesion tipica: panel + hallazgos + logs"
allr = list(csv.DictReader(open(f)))
def pct(el, q):  # misma regla que el Aggregate Report de JMeter: valor en la posicion floor(n*q) (base 1)
    el = sorted(el); return el[max(0, int(q * len(el)) - 1)] if el else None
def vista(rows):
    if not rows: return None
    el = [int(r["elapsed"]) for r in rows]; n = len(el); ok = sum(r["success"] == "true" for r in rows)
    t0 = min(int(r["timeStamp"]) for r in rows); t1 = max(int(r["timeStamp"]) + int(r["elapsed"]) for r in rows)
    return dict(muestras=n, error_pct=round(100 * (n - ok) / n, 2), rps=round(n / ((t1 - t0) / 1000), 1), media_ms=round(st.mean(el)),
                p50=pct(el, .5), p90=pct(el, .9), p95=pct(el, .95), p99=pct(el, .99), max_ms=max(el))
req = [r for r in allr if r["label"] not in (SES, "vacio")]; ses = [r for r in allr if r["label"] == SES]
if not req: print(name, "sin muestras"); sys.exit()
res = vista(req); res.update(prueba=name, usuarios=users)
codes = {}
for r in req:
    if r["success"] != "true": codes[r["responseCode"]] = codes.get(r["responseCode"], 0) + 1
res["errores"] = codes
res["sesion"] = vista(ses); res["total_gui"] = vista(allr)
labels = {}
for r in req: labels.setdefault(r["label"], []).append(int(r["elapsed"]))
peor = max(labels, key=lambda k: pct(labels[k], .95)); res["peor_endpoint"] = peor; res["peor_p95"] = pct(labels[peor], .95)
# El login ocurre una sola vez por usuario durante la rampa (Argon2) y no representa el uso sostenido: se informa aparte.
res["login_p95"] = pct(labels["POST /auth/login"], .95) if "POST /auth/login" in labels else None
sl = {k: v for k, v in labels.items() if k != "POST /auth/login"}
pe = max(sl, key=lambda k: pct(sl[k], .95)) if sl else None; res["peor_endpoint_sin_login"] = pe; res["peor_p95_sin_login"] = pct(sl[pe], .95) if pe else None
json.dump(res, open(f.replace("resultados.jtl", "resumen.json"), "w"), indent=1, ensure_ascii=False)
print(json.dumps(res, ensure_ascii=False))
