import json, glob, csv, statistics as st
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

R = {json.load(open(f))["prueba"]: json.load(open(f)) for f in glob.glob("resultados/*/resumen.json")}
doc = Document()
for s in doc.sections: s.left_margin = s.right_margin = Cm(2.2); s.top_margin = s.bottom_margin = Cm(2)
doc.styles["Normal"].font.name = "Calibri"; doc.styles["Normal"].font.size = Pt(11)

def shade(cell, color):
    tcPr = cell._tc.get_or_add_tcPr(); sh = OxmlElement("w:shd"); sh.set(qn("w:val"), "clear"); sh.set(qn("w:color"), "auto"); sh.set(qn("w:fill"), color); tcPr.append(sh)
def table(head, rows, widths=None):
    t = doc.add_table(rows=1, cols=len(head)); t.style = "Table Grid"; t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, h in enumerate(head):
        c = t.rows[0].cells[i]; c.text = ""; r = c.paragraphs[0].add_run(h); r.bold = True; r.font.size = Pt(9.5); shade(c, "D9E2F3")
    for row in rows:
        cells = t.add_row().cells
        for i, v in enumerate(row):
            cells[i].text = ""; r = cells[i].paragraphs[0].add_run(str(v)); r.font.size = Pt(9.5)
            if i: cells[i].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph()
def p(text, bold=False, italic=False):
    para = doc.add_paragraph(); r = para.add_run(text); r.bold = bold; r.italic = italic; return para
CAP = []
def total_txt(corrida):
    k = corrida.split("/")[1]; r = R[k]; t = r["total_gui"]; se = r["sesion"]
    return f"fila TOTAL con {t['muestras']} muestras, 95% Line ≈ {t['p95']} ms y Error % ≈ {str(t['error_pct']).replace('.', ',')} %" + (f"; fila «Sesion tipica» con 95% Line ≈ {se['p95']} ms" if se else "")
def captura(n, titulo, listener, corrida, que_debe_verse):
    if "Aggregate" in listener: que_debe_verse = total_txt(corrida) + ". " + que_debe_verse
    CAP.append((n, titulo, listener, corrida, que_debe_verse))
    t = doc.add_table(rows=1, cols=1); t.style = "Table Grid"; c = t.rows[0].cells[0]; shade(c, "FFF2CC"); c.text = ""
    r = c.paragraphs[0].add_run(f"[PEGAR AQUÍ LA CAPTURA {n}]"); r.bold = True; r.font.color.rgb = RGBColor(0xC0, 0x50, 0x00)
    for k, v in (("Listener en JMeter", listener), ("Archivo a cargar (Browse…)", corrida), ("Debe verse", que_debe_verse)):
        q = c.add_paragraph(); a = q.add_run(k + ": "); a.bold = True; a.font.size = Pt(9.5); b = q.add_run(v); b.font.size = Pt(9.5)
    for _ in range(7): c.add_paragraph()
    pie = doc.add_paragraph(); x = pie.add_run(f"Figura {n}. {titulo}"); x.italic = True; x.font.size = Pt(9.5); pie.alignment = WD_ALIGN_PARAGRAPH.CENTER
def imagen(path, ancho, pie):
    doc.add_picture(path, width=Cm(ancho)); doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    q = doc.add_paragraph(); x = q.add_run(pie); x.italic = True; x.font.size = Pt(9.5); q.alignment = WD_ALIGN_PARAGRAPH.CENTER

def f1(x): return str(x).replace(".", ",")
def fila(r):
    se = r["sesion"]
    return [r["usuarios"], f1(r["error_pct"]), r["p95"], r["peor_p95_sin_login"], r["login_p95"] if r["login_p95"] is not None else "-", se["p95"] if se else "-", f1(r["rps"])]
H = ["Usuarios", "Errores % (peticiones)", "p95 peticiones (ms)", "p95 peor endpoint sin login (ms)", "p95 login (ms)", "p95 sesión completa (ms)", "Peticiones/s"]
def fila_db(r):
    se = r["sesion"]
    return [r["usuarios"], f1(r["error_pct"]), r["p95"], r["peor_p95_sin_login"], se["p95"] if se else "-", f1(r["rps"])]
HD = ["Usuarios", "Errores % (consultas)", "p95 consultas (ms)", "p95 consulta más lenta (ms)", "p95 sesión completa (ms)", "Sesiones·consultas/s"]

doc.add_heading("Informe de pruebas de carga, estrés, potencia y rendimiento", 0)
p("Sistema bajo prueba: NetSentinel (analista de logs de firewall/IDS). Herramienta: Apache JMeter 5.6.3. Fecha: 18 de noviembre de 2026.", italic=True)

doc.add_heading("1. Resumen ejecutivo", 1)
table(["Umbral", "API completa (HTTP)", "Base de datos (SQL directo)"], [
    ["Buen servicio: 0 % de errores y p95 del peor endpoint ≤ 1 s", "190 usuarios (3 de 3 corridas). Recomendado declarar 175", "75 usuarios (2 de 2 corridas); 90 en una corrida. Con 100 falla (consulta de agregación: ≈1390 y ≈1010 ms)"],
    ["Sin errores, pero lento (2–8 s)", "hasta 600 usuarios", "hasta 200 usuarios; con 300 aparecen los primeros errores (0,08 %)"],
    ["Colapso", "700 usuarios (10,7 % de errores y backend bloqueado)", "400 usuarios (3,7 % de errores en consultas)"]])
p("Número máximo de usuarios conectados simultáneamente: 600 en la API sin que el sistema colapse; 190 con tiempos de respuesta aceptables en todos los endpoints (175 recomendado). La base de datos sostiene 75–90 con buen servicio. El servidor se satura en unas 95 peticiones por segundo.", bold=True)

doc.add_heading("2. Entorno y metodología", 1)
for t in ["Una sola máquina (12 núcleos, 15 GB de RAM) con JMeter, backend FastAPI (1 proceso uvicorn), PostgreSQL 16 y frontend en Docker. JMeter compite por CPU con la aplicación, por lo que las cifras son conservadoras y válidas solo para este entorno.",
          "Base de datos con 214 388 registros en firewall_logs durante todas las pruebas (la mitad era una carga duplicada del mismo dataset, eliminada después; con 107 194 los tiempos de las consultas de agregación serían menores).",
          "Usuario virtual: inicia sesión una vez y recorre 9 endpoints (salud, perfil, 4 consultas del panel, hallazgos, logs, alertas) con 1–2 s de espera después de cada petición. JMeter registra además una muestra «Sesion tipica» que agrupa las 9 peticiones del recorrido.",
          "Cada escalón: rampa de 20 s y 90 s sostenidos. «# Samples» cuenta peticiones, no usuarios: cada usuario repite el recorrido durante toda la prueba.",
          "Criterio de buen servicio: 0 % de errores y percentil 95 (p95) ≤ 1000 ms en cada endpoint (o consulta) por separado, sin contar el login. El login se ejecuta una vez por usuario durante la rampa y se informa aparte.",
          "Los p95 de este informe se calculan con la regla del Aggregate Report de JMeter; pueden diferir en menos de 1 % de lo que muestre su ventana por el método de redondeo del percentil.",
          "Cómo leer las tablas: «peticiones» agrupa las 9 individuales; «peor endpoint» es el más lento; «sesión completa» es la muestra «Sesion tipica» (suma de las 9). La fila TOTAL del Aggregate Report de JMeter incluye todas, sesión incluida, por eso sus cifras difieren de las de «peticiones».",
          "Planes: plan/netsentinel.jmx (API), plan/netsentinel_login.jmx (login continuo), plan/netsentinel_db.jmx (consultas SQL de solo lectura, pool de 80 conexiones). Las credenciales se leen de .env y no se guardan."]:
    doc.add_paragraph(t, style="List Bullet")

doc.add_heading("3. Prueba de carga escalonada de la API", 1)
carga = sorted({r["usuarios"]: r for n, r in R.items() if n.startswith("carga_") and "_r" not in n}.values(), key=lambda r: r["usuarios"])
table(H, [fila(r) for r in carga])
imagen("evidencias/curva_carga.png", 14, "Figura 1. Tiempo de respuesta, peticiones por segundo y errores según usuarios (mediana y rango de corridas).")
captura(2, "Resumen de la corrida de 190 usuarios (límite con buen servicio)", "Aggregate Report", "resultados/carga_0190/resultados.jtl",
        "Una fila por endpoint con 0,00 % de errores.")
captura(3, "Tiempos de respuesta en el tiempo, 190 usuarios", "Response Time Graph (pestaña Settings: Interval = 30000 ms, luego Apply filter y Display graph)", "resultados/carga_0190/resultados.jtl",
        "Una línea por endpoint, estable y por debajo de 1000 ms durante toda la prueba.")
captura(4, "Corrida de 250 usuarios (sobre el límite)", "Aggregate Report", "resultados/carga_0250/resultados.jtl",
        "Endpoints con 95% Line por encima de 1000 ms y sin errores.")
captura(5, "Corrida de 600 usuarios (máximo sin errores)", "Aggregate Report", "resultados/carga_0600/resultados.jtl",
        "Sin errores y con respuestas de varios segundos.")
captura(6, "Corrida de 700 usuarios (colapso)", "Aggregate Report", "resultados/carga_0700/resultados.jtl",
        "Errores y timeouts (≈30 000 ms).")

doc.add_heading("4. Variabilidad entre corridas", 1)
p("Cada punto cercano al límite se repitió 3 veces. Se muestra el p95 del peor endpoint, sin contar el login. De la corrida original de 200 usuarios solo se conserva en resultados/ la segunda; el archivo se había contaminado con datos de otras ejecuciones y se restauró a la ventana de esa corrida.")
rows = []
for u in (175, 190, 200, 250):
    ps = [R[n]["peor_p95_sin_login"] for n in (f"carga_{u:04d}", f"carga_{u:04d}_r2", f"carga_{u:04d}_r3")]
    rows.append([u] + ps + ["Sí, 3 de 3" if max(ps) <= 1000 else ("No, 0 de 3" if min(ps) > 1000 else f"Variable ({sum(x <= 1000 for x in ps)} de 3)")])
table(["Usuarios", "p95 peor endpoint, corrida 1 (ms)", "corrida 2 (ms)", "corrida 3 (ms)", "¿Cumple ≤ 1 s?"], rows)
p("La variación entre corridas llega a ±30 %, atribuible a que JMeter y la aplicación comparten máquina.")

doc.add_heading("5. Barrido fino de usuarios simultáneos (400–1600)", 1)
fino = [R[f"carga_{u:04d}"] for u in (400, 500, 600, 700, 800, 900, 1000, 1100, 1200, 1600)]
table(H, [fila(r) for r in fino])
p("Tras el escalón de 700 usuarios el backend quedó bloqueado y se reinició antes del siguiente; por eso 900 (1,8 % de errores) es mejor que 700 y no debe leerse como una mejora. Las celdas con «-» no tuvieron ninguna sesión completa registrada.")

doc.add_heading("6. Pruebas contra la base de datos", 1)
dbm = {}
for n, r in R.items():
    if n.startswith("db_") and "_r" not in n: dbm[r["usuarios"]] = r
table(HD, [fila_db(dbm[u]) for u in sorted(dbm)])
p("Repeticiones: 75 usuarios, p95 de la consulta más lenta de 690 y 426 ms; 100 usuarios, ≈1390 y ≈1010 ms. La consulta más lenta es siempre la de agregación sobre firewall_logs (recorre toda la tabla sin caché), salvo con 400 usuarios, donde fue la serie temporal por hora. Los errores desde 300–400 usuarios son esperas agotadas (10 s) por el pool de conexiones. Límite con buen servicio: 75 usuarios (confirmado) a 90 (una corrida); sin errores hasta 200.")
p("Aviso al leer JMeter: el p95 de todas las consultas juntas (≈530 ms con 100 usuarios) oculta la consulta pesada, porque las otras responden en 1–4 ms. La fila TOTAL de JMeter incluye además la sesión completa, y por eso marca 1006–1010 ms. Para decidir el límite se usa la consulta más lenta.")
imagen("evidencias/curva_bd.png", 14, "Figura 7. Base de datos frente a la API: p95 y errores según usuarios.")
captura(8, "Base de datos, 100 usuarios (ya sobre el límite)", "Aggregate Report", "resultados/db_0100/resultados.jtl (cargar con el plan netsentinel_db.jmx abierto)",
        "«Resumen: agregados…» con 95% Line ≈ 1390 ms y las consultas simples en 1–4 ms.")
captura(9, "Base de datos, 400 usuarios (inicio de errores)", "Aggregate Report", "resultados/db_0400/resultados.jtl",
        "Errores en todas las consultas y fila «Sesion tipica» con ≈ 39 % de errores.")

doc.add_heading("7. Estrés (pico) y recuperación", 1)
pk, rc = R["pico_0600"], R["recuperacion_0050"]
p(f"Pico de 600 usuarios en 10 s: {f1(pk['error_pct'])} % de errores en peticiones (timeouts) y p95 de {pk['p95']} ms.")
p("Defecto hallado: tras el pico, el backend quedó bloqueado. PostgreSQL mostraba 20 conexiones en estado idle in transaction durante minutos, el log del backend registraba «QueuePool limit of size 10 overflow 10 reached» y la CPU estaba en 0 %. La prueba de recuperación con 50 usuarios dio 100 % de errores. Solo reiniciar el contenedor lo restauró. Causa probable (no confirmada en el código): bloqueo mutuo entre el pool de conexiones (20) y el grupo de hilos de FastAPI. Recomendación: ajustar el pool, limitar la concurrencia (varios workers de uvicorn, timeouts) y repetir la prueba tras el cambio.")
captura(10, "Pico de 600 usuarios", "Aggregate Report", "resultados/pico_0600/resultados.jtl", "Timeouts de ≈ 30 000 ms.")
captura(11, "Recuperación: 50 usuarios tras el pico (backend bloqueado)", "Aggregate Report", "resultados/recuperacion_0050/resultados.jtl",
        "Todas las peticiones fallan con ≈ 30 000 ms (evidencia del bloqueo).")

doc.add_heading("8. Login continuo y resistencia", 1)
lg, rs = R["login_0020"], R["resistencia_0150_10min"]
p(f"Login continuo con 20 usuarios (Argon2): {f1(lg['rps'])} inicios de sesión por segundo, media {lg['media_ms']} ms, p95 {lg['p95']} ms, p99 {lg['p99']} ms, {f1(lg['error_pct'])} % de errores. El cifrado de contraseñas limita los inicios de sesión simultáneos.")
p(f"Resistencia: 150 usuarios durante 10 minutos ({rs['muestras']} peticiones): {f1(rs['error_pct'])} % de errores, {f1(rs['rps'])} peticiones/s, media {rs['media_ms']} ms, p95 {rs['p95']} ms (peor endpoint {rs['peor_p95_sin_login']} ms) y p99 {rs['p99']} ms. No hay degradación progresiva, pero la media por intervalos de 30 s muestra picos periódicos (los endpoints llegan a unos 360 ms y la sesión completa a unos 1800 ms) que se recuperan solos; su causa no se determinó (no coinciden con las ingestas programadas de n8n).")
captura(12, "Resistencia de 10 minutos con 150 usuarios", "Response Time Graph (pestaña Settings: Interval = 30000 ms, luego Apply filter y Display graph)", "resultados/resistencia_0150_10min/resultados.jtl",
        "Media por intervalo de 30 s: los endpoints entre ≈20 y ≈360 ms, con picos periódicos (≈11:58:30, 12:01:00, 12:04:30) y valles de ≈50–100 ms; la línea «Sesion tipica» entre ≈330 y ≈1800 ms. Sin tendencia ascendente: los picos no se acumulan.")
captura(13, "Login continuo con 20 usuarios", "Aggregate Report", "resultados/login_0020/resultados.jtl (con el plan netsentinel_login.jmx)",
        "Una sola fila, POST /auth/login, y la fila TOTAL con los mismos valores.")

doc.add_heading("9. Conclusiones", 1)
for t in ["Usuarios simultáneos sin colapso: 600 en la API; 700 provoca errores y bloqueo del backend.",
          "Usuarios simultáneos con tiempos aceptables (p95 ≤ 1 s en todos los endpoints): 190 (declarar 175 con margen). Base de datos: 75–90.",
          "Cuello de botella: la API satura a ~95 peticiones/s; en la base de datos, las consultas de agregación sin caché sobre firewall_logs.",
          "Defecto a corregir: bloqueo del pool de conexiones ante picos de carga.",
          "Mejoras sugeridas: varios workers, caché de las consultas del panel, índices y vistas agregadas, y ajuste del pool y de los timeouts."]:
    doc.add_paragraph(t, style="List Bullet")

doc.add_heading("10. Limitaciones", 1)
p("Cliente y servidor en la misma máquina; un solo proceso del backend; una sola corrida en los escalones fuera de los rangos repetidos (175–250 en la API; 75 y 100 en la base de datos). «Usuario conectado» equivale a un usuario activo con ~1,5 s entre acciones. La base de datos se probó sin pasar por la API. Los informes HTML de JMeter están en resultados/<prueba>/informe/index.html.")

doc.add_page_break()
doc.add_heading("Anexo. Lista de capturas que debe pegar", 1)
p("Abra JMeter con el plan indicado (jmeter -t docs/pruebas-jmeter/plan/netsentinel.jmx; para las figuras 8 y 9 use netsentinel_db.jmx y para la 13 netsentinel_login.jmx). Clic derecho en el grupo de hilos → Add → Listener → el indicado → Browse… → cargue el .jtl. Capture la ventana de JMeter (no todo el escritorio) y péguela en el recuadro amarillo correspondiente, borrando el texto del recuadro.")
table(["Fig.", "Listener", "Archivo .jtl (en docs/pruebas-jmeter/)", "Plan"],
      [[n, l, c.split(" (")[0], "netsentinel_db.jmx" if "db_" in c else ("netsentinel_login.jmx" if "login_" in c else "netsentinel.jmx")] for n, t, l, c, d in CAP])
p("Las figuras 1 y 7 (gráficos) ya están insertadas.", italic=True)
doc.save("INFORME_PRUEBAS_JMETER.docx")
print("ok", len(CAP))
