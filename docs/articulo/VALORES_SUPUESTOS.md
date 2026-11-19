# Valores reales y supuestos del manuscrito

Convención: **REAL** = medido en el despliegue o calculado por script sobre el archivo del dataset; **SUPUESTO (†)** = valor ilustrativo generado por `build/supuestos.py` (semilla 20261111) y resaltado en amarillo en el .docx. Todos los supuestos deben sustituirse por mediciones reales antes de enviar a una revista; el texto de la Sección 3 que describe esos experimentos está redactado como si se hubieran hecho.

## Valores REALES usados (no modificar)
107 252 líneas leídas; 107 194 registros; 1 error de parseo; importación en 9,8 s; 8 164 líneas Botnet; 51 hallazgos (23 beaconing, 25 puerto inusual, 3 anomalía de host; 2 críticos, 15 altos, 31 medios, 3 bajos); 29 146 orígenes y 15 141 destinos únicos; latencia del panel 14–472 ms; 36 reportes (12 por formato) en 56–560 ms; inferencia de llama3.2:3b en CPU 28–37 s por hallazgo y 7,8 s la prueba de conexión; «incierto» (confianza 0,5–0,6) en 2 de 2 hallazgos reanalizados; 114 pruebas aprobadas; modelo de 2,0 GB.
Reales **calculados por script** sobre `data/dataset/capture20110818-2.binetflow` (no desde la base de datos): período 2011-08-18 15:39:35–15:55:46 UTC; 2 718 Normal y 96 369 Background; 3 hosts con flujos Botnet (4 151, 4 006 y 7); 7 663 de las 8 164 líneas Botnet son ICMP (93,9 %); 398 grupos candidatos a beaconing (n ≥ 10, intervalo medio ≥ 1 s), 42 con CV ≤ 0,25, ninguno con mayoría Botnet (también es la parte real de la Figura 3a). Derivados: 107 194/9,8 s ≈ 10 938 registros/s; 30 × 32,5 s ≈ 16 min.
Reales de configuración (código): fórmulas y umbrales de los detectores, parámetros del LLM, retención, versiones (Tablas 3 y parte de la 2).
**Supuesto de contexto a confirmar:** el hardware de la Tabla 2 (12 hilos, 15 GiB) es el del equipo donde se desarrolló; confirmar que las mediciones reales se hicieron ahí.

## Tabla por tabla
| Elemento | Real | Supuesto (†) | Experimento para obtener el dato real |
|---|---|---|---|
| T1 matriz de literatura | Metadatos de Crossref; contenido de resúmenes | Fila «Este estudio» (200 beacons, SUS) | Leer los textos completos para completar métricas/limitaciones; repetir la búsqueda en Scopus/WoS |
| T2 dataset y entorno | Todo salvo 4 filas | Analistas (2, 21 reales/30 ruido, κ = 0,81); 200 beacons; 12 participantes; hardware | Adjudicación real de los 51 hallazgos por dos analistas (κ real); confirmar hardware |
| T3 detectores | Todo (del código) | — | — |
| T4 detección vs baselines | n = 51 (23/25/3) | P, R, F1, IC, hosts, sensibilidad, McNemar, 37 hallazgos del umbral fijo, 14 de Suricata, pool de 24 eventos | Ejecutar umbral fijo y Suricata 7 (reglas por defecto) sobre el pcap de CTU-13 esc. 11; adjudicar; calcular pool y estadísticos con `supuestos.py` adaptado |
| T5 ablación y modelos | Tamaño y rango de latencia de llama3.2:3b; tendencia «incierto» (2/2) | Todo lo de qwen2.5:7b, llama3.1:8b, mistral:7b; descartes, κ, Holm, JSON válido, Likert, lat. mediana/RIC de todos | Reanalizar los 51 hallazgos con cada modelo (`POST` de reanálisis, τ = 0,70; registrar veredicto, confianza, latencia, JSON válido); calificación Likert por 2 analistas |
| T6 operación y costo | Importación, panel, reportes, latencia llama3.2:3b, pruebas, derivados | RAM, CPU, almacenamiento, costo mensual, SIEM de referencia, tiempo de decisión, SUS, latencia de llama3.1:8b | `docker stats` durante importación/inferencia; tarifas reales del SIEM/nube de comparación; estudio de usabilidad real |
## Figura por figura
| Figura | Real | Supuesto (†) | Experimento |
|---|---|---|---|
| F1 arquitectura | Todo (de `docker-compose.yml` y el código) | — | — |
| F2 flujo | Todo (del código) | — | — |
| F3 CV | Histograma de 398 grupos reales | Beacons inyectados (200 simulados con la fórmula real); panel (b) | Inyectar beacons reales de laboratorio o usar escenarios C&C de otras capturas |
| F4 PR y sensibilidad | — | Todo (curvas con 51/37/14 hallazgos simulados; sensibilidad sobre inyección) | Ejecutar baselines y barrer umbrales sobre los hallazgos reales adjudicados |
| F5 umbral τ | — | Todo (confianzas por modelo) | Registrar confianza real de cada modelo y barrer τ |
| F6 latencia y usabilidad | Rango 28–37 s de llama3.2:3b | Latencias de los otros modelos; tiempos de 12 participantes | Medir latencias por modelo; estudio de usabilidad |

## Otros supuestos en el texto
Resumen/Abstract (valores de F1, reducción, κ, SUS, tiempo); Secciones 3.6–3.8 (diseño del estudio con usuarios, adjudicación, inyección, Suricata sobre pcap, ética y comité); Sección 4 (todos los estadísticos salvo 4.1); 4.5 (precisión solo con etiquetas = 3/51; batería de 20 hallazgos con inyección de instrucciones y sus resultados); Sección 5 (valores citados); declaraciones (aprobación ética, código por completar). Hipótesis H1–H3 se evalúan sobre valores supuestos.
Pasos técnicos: `python3 build/supuestos.py` (imprime los estadísticos), `sh figuras/generar_todo.sh` (figuras), `uv run --with python-docx --with numpy --with scipy python build/build_docx.py` (documento). Para sustituir por datos reales, reemplazar las constantes de `supuestos.py` y volver a generar.
