from fmt import *
import supuestos as S
SUP = "† Contiene valores supuestos (ilustrativos), resaltados en amarillo; deben sustituirse por mediciones reales antes del envío a una revista."
def definiciones(R, REAL, DS):
    T, F = {}, {}
    t4 = {r['nombre']: r for r in R['t4']}; t5 = {m['m']: m for m in R['t5']}
    # ---- T1
    T['T1'] = dict(
        caption="Tabla 1. Matriz comparativa de trabajos relacionados y brecha que aborda este estudio",
        header=["Estudio", "Problema", "Datos", "Método", "Métricas", "Hallazgo principal", "Limitación / brecha"],
        widths=[2.0, 2.3, 2.2, 2.6, 1.6, 2.7, 3.6], fs=6.5,
        rows=[
         ["García et al. @@garcia2014@@", "Comparar detectores de botnets de forma reproducible", "CTU-13: 13 capturas con etiquetas Botnet, Normal y Background", "Comparación empírica de métodos de detección de botnets", "Métrica de error propuesta por los autores", "Establece una base común de comparación", "Evaluación fuera de línea; sin interpretación ni operación en pymes"],
         ["Bilge et al. @@bilge2012@@", "Detectar servidores de C&C", "NetFlow a gran escala", "Aprendizaje supervisado sobre características de flujo", "Detección y falsos positivos", "Viabilidad de detectar C&C solo con flujos", "Requiere datos etiquetados e infraestructura de recolección; sin explicación"],
         ["Borchani @@borchani2020@@", "Beaconing oculto en tráfico cifrado", "Tráfico empresarial cifrado", "Detección de beaconing con inteligencia artificial", "No detalladas en el resumen consultado", "Motiva detectar beaconing sin ver el contenido", "Sin comparación con baselines en el resumen consultado"],
         ["Pietraszek @@pietraszek2004@@", "Falsos positivos de IDS", "Alertas de IDS", "Clasificación adaptativa con retroalimentación del analista", "Falsos positivos y negativos", "Reduce falsos positivos con supervisión", "Exige etiquetado humano sostenido"],
         ["Tariq et al. @@tariq2025@@", "Fatiga de alertas en SOC", "Revisión de literatura e industria", "Automatización, aumento y colaboración humano–IA", "No aplica (revisión)", "Identifica cuatro causas de fatiga y límites de las soluciones", "Foco en SOC; sin evaluación de herramientas ligeras"],
         ["Palma et al. @@palma2025@@", "Clasificar y explicar logs de seguridad", "Logs de ciberseguridad (tarea de vulnerabilidades)", "LLM locales (incluye qwen2.5:7b y llama3.2:3b) con prompt y análisis robusto", "F1 con IC 95 %", "F1 0,928 frente a 0,555 de XGBoost", "No es tráfico de firewall; sin evidencia calculada ni latencia en CPU"],
         ["Greshake et al. @@greshake2023@@", "Inyección indirecta de instrucciones", "Aplicaciones reales con LLM", "Demostración de ataques", "No aplica", "Los datos recuperados pueden contener instrucciones", "No aborda logs de red ni defensas específicas"],
         ["Rombaldo et al. @@rombaldo2026@@", "Ciberseguridad en pymes", "1 090 estudios filtrados a 132 (2017–2024)", "Revisión sistemática", "44 temas identificados", "Investigación sobre pymes poco desarrollada", "No evalúa herramientas de detección"],
         ["González-Granadillo et al. @@gonzalez2021@@", "Funcionalidad y tendencias de SIEM", "Revisión de SIEM", "Revisión", "No aplica", "SIEM convergen con analítica de datos masivos", "Foco en infraestructuras críticas; costo para pymes no medido"],
         ["Sommer y Paxson @@sommer2010@@", "Aprendizaje automático en detección de intrusiones", "Análisis conceptual", "Análisis crítico", "No aplica", "La detección de anomalías en operación exige cautela especial", "No propone un sistema ni lo evalúa"],
         ["**Este estudio**", "Analista de logs para pymes con filtro local de ruido", "CTU-13 escenario 11 (107 194 registros), 51 hallazgos, 200 beacons inyectados †", "DSR; detectores deterministas con fórmulas + LLM local", "P, R, F1, IC 95 %, κ, latencia, SUS †", "Ver Secciones 4 y 5", "Un escenario corto; verdad de referencia parcial"],
        ],
        notes="Nota. Elaboración propia a partir de los resúmenes y metadatos verificados en Crossref (consultados el 11 de noviembre de 2026). «No aplica» indica que el trabajo no reporta ese elemento por su naturaleza; «resumen consultado» indica que el detalle no estaba en el resumen disponible. † La fila de este estudio contiene datos supuestos para los elementos marcados.")
    # ---- T2
    T['T2'] = dict(
        caption="Tabla 2. Características del conjunto de datos y del entorno experimental †",
        header=["Atributo", "Valor", "Origen"], widths=[4.6, 9.2, 3.2], fs=8,
        rows=[
         ["Conjunto de datos", "CTU-13, escenario 11 (CTU-Malware-Capture-Botnet-52, botnet Rbot); archivo binetflow de flujos bidireccionales", "Real"],
         ["Período de captura", f"{DS['inicio']} a {DS['fin']} UTC (≈ 16 min)", "Real (script)"],
         ["Líneas leídas / registros normalizados / errores", f"{n(REAL['lineas'])} / {n(REAL['registros'])} / {REAL['errores_parseo']} (57 omitidas por diseño)", "Real"],
         ["Etiquetas de flujo", f"Botnet {n(DS['botnet'])} (7,6 %); Normal {n(DS['normal'])}; Background {n(DS['fondo'])}", "Real (script)"],
         ["Hosts con flujos Botnet", "3 (4 151, 4 006 y 7 flujos); 93,9 % del tráfico etiquetado Botnet es ICMP", "Real (script)"],
         ["Orígenes / destinos únicos", f"{n(REAL['origenes'])} / {n(REAL['destinos'])}", "Real"],
         ["Grupos candidatos a beaconing (n ≥ 10, μ_Δ ≥ 1 s)", "398 grupos; 42 con c ≤ 0,25; ninguno con mayoría Botnet", "Real (script)"],
         ["Hallazgos del despliegue", f"{REAL['hallazgos']}: {REAL['beacon']} beaconing, {REAL['puerto']} puerto inusual, {REAL['talker']} anomalía de host; severidad: {REAL['crit']} críticos, {REAL['alto']} altos, {REAL['medio']} medios, {REAL['bajo']} bajos", "Real"],
         ["Hallazgos adjudicados por analistas", A("2 analistas independientes; 21 reales y 30 ruido; κ entre analistas = 0,81"), "†"],
         ["Beacons inyectados", A("200 series de 2 h (5 periodos × 5 niveles de jitter × 8 condiciones de pérdida)"), "†"],
         ["Participantes del estudio de usabilidad", A("12 administradores de TI de pymes"), "†"],
         ["Hardware de las mediciones", A("12 hilos de CPU, 15 GiB de RAM, sin GPU (equipo local; confirmar)"), "†"],
         ["Software", "PostgreSQL 16; n8n 2.47.4; Ollama con llama3.2:3b (2,0 GB); Python 3.11; FastAPI ≥ 0,115; React 19; 114 pruebas aprobadas", "Real"],
        ],
        notes="Nota. «Real» = medido en el despliegue; «Real (script)» = calculado por script sobre el archivo del dataset, no extraído de la base de datos; † = valor supuesto. μ_Δ: intervalo medio entre conexiones; c: coeficiente de variación (Ecuación 1). " + SUP)
    # ---- T3
    T['T3'] = dict(
        caption="Tabla 3. Detectores, variables de entrada e hiperparámetros por defecto",
        header=["Detector", "Variables de entrada", "Hiperparámetros por defecto", "Puntaje y límites"], widths=[2.4, 4.2, 6.0, 4.4], fs=7.5,
        rows=[
         ["Beaconing", "n, μ_Δ, σ_Δ, μ_b, σ_b, T, puerto", "n_min = 10; c_max = 0,25; S_min = 60; μ_Δ ≥ 1 s; κ = 0,7 si puerto 53 o 123; exclusión de destinos multicast, de enlace local y difusión; 400 grupos máx.", "Ecuaciones 1–6; severidad por puntaje"],
         ["Puerto inusual", "Puerto, protocolo, n_p, N_o, B", "25 puertos comunes; historial de 14 días; mínimo 3 conexiones; puertos esperados por origen", "Ecuación 7; ≤ 25 hallazgos; severidad ≤ alta"],
         ["Exfiltración", "B_sal, B_ent, historial de volumen", "B_mín = 52 428 800 B; z ≥ 3; ≥ 3 intervalos de historial; razón ≥ 3 sin historial", "Ecuaciones 8–9"],
         ["Anomalía de host", "Conexiones, destinos únicos, historial o pares", "200 conexiones o 25 destinos mínimos; z ≥ 3; ≥ 5 hosts para comparación con pares", "Ecuaciones 8 y 10; severidad ≤ alta"],
         ["Alertas IDS", "Firma, severidad, conteo, orígenes", "Base 70/50/30 según severidad 1/2/3 de Suricata", "Base + 20·acotar(log₁₀ n/3) + 5·acotar(orígenes/10)"],
         ["Cadena LLM", "Hallazgo con evidencia y contexto", "Temperatura 0,1; 500 tokens; tiempo de espera 60 s; 2 intentos; τ = 0,70; ≤ 30 hallazgos por ejecución; ventana de 24 h", "Veredicto, confianza, explicación, recomendación; Ecuación 11"],
        ],
        notes="Nota. Valores tomados de la configuración y del código del sistema (módulos de detección y de interpretación). Severidad por puntaje: crítica ≥ 85, alta ≥ 70, media ≥ 50, baja ≥ 30. acotar(x) = mín(máx(x, 0), 1) salvo indicación; B: bytes; N_o: orígenes distintos.")
    # ---- T4
    rows = []
    def sc(r): return ("—" if r['s'] is None else f"{r['s']} de 200 ({pc(r['s']/200,1)})")
    for nom, r in t4.items():
        n_cell = str(r['n']) if nom.startswith('NetSentinel') and 'LLM' not in nom and '+' not in nom else A(str(r['n']))
        if nom.startswith('NetSentinel determinista') or nom in ('NetSentinel: beaconing', 'NetSentinel: puerto inusual', 'NetSentinel: anomalía de host'): n_cell = str(r['n'])
        rows.append([nom.replace('NetSentinel + ', 'NetSentinel + '), n_cell,
                     A(f"{d(r['p'])} {ci(*r['p_ci'])}"), A(f"{d(r['r'])} {ci(*r['r_ci'])}"), A(f"{d(r['f1'])} {ci(*r['f1_ci'])}"),
                     A(f"{r['hosts']}/3"), A(sc(r)) if r['s'] is not None else "—"])
    T['T4'] = dict(
        caption="Tabla 4. Desempeño de la detección de NetSentinel frente a baselines (escenario 11 de CTU-13 y beacons inyectados) †",
        header=["Método", "Hallazgos (n)", "Precisión [IC 95 %]", "Cobertura relativa [IC 95 %]", "F1 [IC 95 %]", "Hosts infectados", "Sensibilidad en beacons inyectados"],
        widths=[3.7, 1.2, 2.5, 2.5, 2.5, 1.3, 2.4], fs=7, rows=rows,
        notes=f"Nota. Precisión: hallazgos adjudicados como reales / hallazgos emitidos. Cobertura relativa: eventos reales detectados / {S.POOL} eventos reales de referencia (conjunto agrupado). IC 95 %: Wilson para P, R y sensibilidad; bootstrap percentil (4 000 réplicas) para F1. Hosts infectados: detectados de 3 con flujos Botnet. El número de hallazgos de NetSentinel (51; 23, 25 y 3 por detector) es real; el resto de valores es supuesto. Sensibilidad de la fila «determinista» = {R['K']['det']}/200. McNemar exacto sobre los eventos de referencia: NetSentinel frente a umbral fijo, {R['mc_fix']['b']} frente a {R['mc_fix']['c']} eventos discordantes ({pv(R['mc_fix']['p'])}); frente a Suricata, {R['mc_sur']['b']} frente a {R['mc_sur']['c']} ({pv(R['mc_sur']['p'])}). " + SUP)
    # ---- T5
    hs = ['Sin filtro (determinista)'] + S.MODELOS
    def row(lbl, f, base=''):
        return [lbl, (A(base) if base not in ('0', '0 %') else base) if base else "—"] + [f(t5[m]) for m in S.MODELOS]
    adj = dict(zip(S.MODELOS, holm([t5[m]['mc_p'] for m in S.MODELOS])))
    det = t4['NetSentinel determinista (unión)']
    T['T5'] = dict(
        caption="Tabla 5. Ablación del filtro de ruido y comparación de modelos locales (τ = 0,70; 51 hallazgos) †",
        header=["Métrica", "Sin filtro (determinista)"] + S.MODELOS, widths=[4.2, 2.3, 2.6, 2.6, 2.6, 2.6], fs=7,
        rows=[
         row("Descartados como ruido (n)", lambda t: A(str(t['fp']+t['rl'])), "0"),
         row("   de ellos, ruido real", lambda t: A(str(t['fp'])), "0"),
         row("   de ellos, reales (falsos negativos)", lambda t: A(str(t['rl'])), "0"),
         row("Reducción de alertas [IC 95 %]", lambda t: A(f"{pc(t['red'])} {pci(*t['red_ci'])}"), "0 %"),
         row("Precisión tras el filtro [IC 95 %]", lambda t: A(f"{d(t['p'])} {ci(*t['p_ci'])}"), f"{d(det['p'])}"),
         row("κ de Cohen frente a analistas [IC 95 %]", lambda t: A(f"{d(t['kappa'])} {ci(*t['kappa_ci'])}")),
         row("McNemar exacto (descartados: ruido/real)", lambda t: A(f"{t['b']}/{t['c']}; {pv(t['mc_p'])}")),
         row("p ajustado (Holm, 4 comparaciones)", lambda t: A(d(adj[t['m']], 3))),
         row("Veredicto «incierto» (n de 51)", lambda t: A(str(t['unc']))),
         row("JSON válido al primer intento (n de 51)", lambda t: A(str(t['json']))),
         row("Calidad de la explicación (Likert 1–5; media ± DE)", lambda t: A(f"{d(t['lik'])} ± {d(t['lik_sd'])}")),
         row("Latencia por hallazgo en CPU, mediana [RIC] (s)", lambda t: A(f"{d(t['lat_med'],1)} [{d(t['lat_q'][0],1)}; {d(t['lat_q'][1],1)}]")),
         ["Tamaño del modelo (GB)", "—", d(t5['llama3.2:3b']['ram'],1)] + [A(d(t5[m]['ram'],1)) for m in S.MODELOS[1:]],
         row("Beacons inyectados descartados (de %d detectados)" % R['K']['det'], lambda t: A(str(t['supr_beacons'])), "0"),
        ],
        notes="Nota. RIC: rango intercuartílico. κ: acuerdo entre la decisión de suprimir (veredicto «ruido» con confianza ≥ 0,70) y la clasificación «ruido» de los analistas (30 ruido, 21 reales). Reales: 21 hallazgos adjudicados. Valores reales: el rango de latencia de llama3.2:3b (28–37 s por hallazgo), su tamaño (2,0 GB) y la tendencia a responder «incierto» observada en 2 de 2 hallazgos; el resto de valores es supuesto. " + SUP)
    # ---- T6
    T['T6'] = dict(
        caption="Tabla 6. Rendimiento operativo y costo de NetSentinel frente a una referencia de SIEM †",
        header=["Métrica", "NetSentinel", "Referencia / comparador", "Origen"], widths=[4.4, 4.6, 5.6, 2.4], fs=7.5,
        rows=[
         ["Importación de 107 194 registros", f"{d(REAL['import_s'],1)} s (≈ {n(REAL['registros']/REAL['import_s'])} registros/s)", "—", "Real"],
         ["Latencia de los endpoints del panel", f"{REAL['lat_min']}–{REAL['lat_max']} ms", "—", "Real"],
         ["Generación de 36 reportes (12 PDF, 12 Word, 12 Excel)", f"{REAL['rep_min']}–{REAL['rep_max']} ms", "—", "Real"],
         ["Inferencia LLM (llama3.2:3b, CPU)", f"{REAL['llm_min']}–{REAL['llm_max']} s por hallazgo; prueba de conexión {d(REAL['llm_test'],1)} s", "llama3.1:8b: " + A(f"{d(t5['llama3.1:8b']['lat_med'],0)} s por hallazgo"), "Real / †"],
         ["Ejecución completa con tope de 30 hallazgos", "≈ 16 min (30 × 32,5 s)", "llama3.1:8b: " + A(f"≈ {int(round(30*t5['llama3.1:8b']['lat_med']/60))} min"), "Real (derivado) / †"],
         ["Pruebas automatizadas", f"{REAL['tests']} aprobadas", "—", "Real"],
         ["Memoria RAM del conjunto de servicios", A("1,6 GB sin LLM; 4,3 GB con llama3.2:3b cargado"), A("SIEM autoalojado de referencia: ≥ 16 GB"), "†"],
         ["Uso de CPU (12 hilos)", A("3 % en reposo; 92 % durante la inferencia"), "—", "†"],
         ["Almacenamiento por millón de registros", A("≈ 0,45 GB (con índices)"), A("≈ 1,1 GB en un SIEM de referencia"), "†"],
         ["Costo mensual estimado (hardware amortizado y energía)", A("USD 38"), A("SIEM comercial en la nube: USD 600–2 400 según volumen"), "†"],
         ["Tiempo de decisión por hallazgo (mediana)", A(f"{d(R['us_time']['con'],1)} s con explicación"), A(f"{d(R['us_time']['sin'],0)} s solo con evidencia"), "†"],
         ["Usabilidad SUS (N = 12)", A(f"{d(R['sus']['mean'],1)} {ci(*R['sus']['ci'],1)}"), "Referencia empírica ≈ 70 puntos @@bangor2008@@", "†"],
        ],
        notes="Nota. Los valores de la columna «Origen» marcados como Real fueron medidos en el despliegue; «Real (derivado)» se obtiene por cálculo a partir de mediciones reales; † = valor supuesto. Los costos de referencia son estimaciones ilustrativas y no corresponden a la oferta de un proveedor concreto. " + SUP)
    # ---- Figuras
    F['F1'] = dict(file='F1_arquitectura.png', w=15.5, caption="Figura 1. Arquitectura y despliegue de NetSentinel (Docker Compose en una sola máquina).", notes="Nota. Los logs permanecen en la organización; el único canal saliente es el webhook o SMTP configurado por el cliente. Elaboración propia.")
    F['F2'] = dict(file='F2_flujo_procesamiento.png', w=16, caption="Figura 2. Flujo de procesamiento desde la ingesta con n8n hasta las alertas y la bitácora.", notes="Nota. Los pasos 3 a 7 son deterministas; los pasos 8 a 10 corresponden a la interpretación del modelo de lenguaje. Elaboración propia.")
    F['F3'] = dict(file='F3_cv_beaconing.png', w=16, caption="Figura 3. Coeficiente de variación (CV) de los intervalos: grupos del dataset frente a beacons inyectados †", notes="Nota. (a) Los grupos del dataset (origen, destino, puerto, protocolo; n ≥ 10 y intervalo medio ≥ 1 s) se recalcularon desde el archivo binetflow (datos reales; ninguno con mayoría Botnet); los beacons inyectados son simulados (†). (b) Fracción de beacons detectados por la Ecuación 6 según el jitter y la pérdida de latidos (†).")
    F['F4'] = dict(file='F4_curvas_precision_cobertura.png', w=16, caption="Figura 4. Curvas de precisión–cobertura relativa y sensibilidad frente al jitter †", notes="Nota. (a) Barrido del umbral de puntaje (NetSentinel), del número de conexiones (umbral fijo) y de la severidad (Suricata); los marcadores muestran las variantes con LLM (τ = 0,70). Cobertura relativa respecto de 24 eventos reales de referencia. (b) Sensibilidad sobre 200 beacons inyectados. Valores supuestos (†); los puntos finales coinciden con la Tabla 4.")
    F['F5'] = dict(file='F5_umbral_confianza_llm.png', w=16, caption="Figura 5. Reducción de alertas y hallazgos reales descartados según el umbral de confianza del LLM †", notes="Nota. Sobre los 51 hallazgos del despliegue, con adjudicación por analistas supuesta (†). La línea punteada marca el umbral por defecto τ = 0,70, cuyos valores coinciden con la Tabla 5.")
    F['F6'] = dict(file='F6_latencia_usabilidad.png', w=16, caption="Figura 6. Latencia de inferencia local por modelo y tiempo de decisión en el estudio de usabilidad †", notes="Nota. (a) Cajas: mediana y rango intercuartílico; los puntos son los 30 hallazgos por modelo. El rango de llama3.2:3b (28–37 s) es real; los demás datos son supuestos (†). (b) Líneas: 12 participantes; rombo: mediana (†).")
    return T, F
