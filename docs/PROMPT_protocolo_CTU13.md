# Prompt mejorado: protocolo de entrenamiento (alcance fijo: solo CTU-13)

Sustituye al prompt de la sección «Prompt» de `FICHA_NS-01_y_prompt.md`, que se redactó cuando solo se usaba el escenario 11. Se adjunta la ficha NS-01 y se pega el texto de abajo. Las cifras salen de los scripts de `docs/validacion-externa/` y del código del Laboratorio (`backend/app/ml/`).

## Qué se cambió respecto al prompt original y por qué

| Prompt original | Prompt mejorado | Motivo |
|---|---|---|
| «Experto desarrollador de aplicaciones» | Ingeniero senior de ML y ciberseguridad, con validación sin fuga | El trabajo es de validación estadística sobre flujos de red, no de desarrollo de aplicaciones. |
| «Tema detallado en el fichero adjunto» | Bloque de datos reales dentro del propio prompt | La ficha describe la etapa de un solo escenario (11, 10 882 flujos). Hoy son 12 escenarios y 678 636 flujos etiquetados. |
| Streamlit | Laboratorio ML de NetSentinel (FastAPI + React) | Ya existe y tiene partición por grupos, CV anidada y Optuna. Se indican los cambios que necesita. |
| 70/15/15 sin unidad | 70/15/15 sobre escenarios completos (8/2/2) con restricciones por familia | Partir por flujos o por bloques de tiempo filtra información. Con bloques de 10 s dio PR-AUC ≈ 1,0 que no se sostuvo entre escenarios. |
| Sin alcance | Solo CTU-13, con CIC-IDS2017 declarado como resultado negativo | Las conclusiones deben acotarse a lo que se midió. |
| «Parámetros de búsqueda de hiperparámetros» | Presupuesto de trials, sampler y pruner con corrección del uso previo | La búsqueda previa fue de hecho aleatoria y sin poda (ver «Corrección metodológica» en la ficha). |
| Sin desbalance, umbral ni costo | Reglas de desbalance, dos políticas de umbral, calibración y plan por fases con costo | El umbral por exactitud balanceada marcó 25–41 % del Background; las corridas completas tardan horas. |
| Sin formato ni reglas de honestidad | 12 secciones, tablas con interpretación, `[SUPUESTO]` y prohibición de inventar cifras | Evita que el modelo de lenguaje rellene huecos con resultados falsos. |

## Prompt

```text
ROL
Actúa como ingeniero senior de aprendizaje automático y ciberseguridad, con experiencia en detección de botnets sobre flujos de red (Argus/NetFlow), validación estadística sin fuga de datos y diseño de experimentos reproducibles en CPU.

TAREA
Prepara un protocolo de entrenamiento riguroso y detallado para el tema de la ficha NS-01 adjunta (detección explicable de tráfico botnet en logs de firewall/IDS), eligiendo y justificando la técnica de entrenamiento más apropiada. Se implementará en Python en el Laboratorio ML de NetSentinel (backend FastAPI + scikit-learn + XGBoost + Optuna, interfaz React), no en Streamlit. Entrega el protocolo, no resultados: no inventes ninguna cifra de rendimiento. Lo que no esté en este mensaje ni en la ficha márcalo como [SUPUESTO].

ALCANCE (fijo; no lo amplíes)
1. Solo CTU-13. Toda conclusión se acota a «dentro de CTU-13, entre escenarios». No afirmes utilidad en otras redes, en producción ni con logs de firewall reales: CTU-13 es tráfico de laboratorio de 2011.
2. Una validación externa en CIC-IDS2017 (entrenando con los 12 escenarios) fue negativa: PR-AUC 0,02–0,08 con variables de flujo y 0,01–0,03 con contexto de host, frente a 0,010 del azar (una semilla). No forma parte del protocolo. Decláralo en las amenazas a la validez como la principal limitación de generalización.
3. Si la ficha adjunta habla de un solo escenario (el 11) o de una CV 5x3 por bloques de 10 s, esa parte queda superada por este mensaje.

DATOS REALES
12 escenarios etiquetados (el 10 falta: solo hay pcap, sin .binetflow). Flujos etiquetados y % Botnet (que es el PR-AUC del Dummy):
 1 Neris 71 335 (57,4 %) | 2 Neris 30 052 (69,7 %) | 3 Rbot 143 553 (18,7 %) | 4 Rbot 27 837 (9,3 %) | 5 Virut 5 577 (16,2 %) | 6 Menti 12 119 (38,2 %)
 7 Sogou 1 739 (3,6 %; 63 Botnet) | 8 Murlo 78 903 (7,8 %) | 9 Neris 214 943 (86,1 %) | 11 Rbot 10 882 (75,0 %) | 12 NSIS.ay 9 793 (22,1 %) | 13 Virut 71 903 (55,6 %)
Total: 678 636. El tráfico Background (sin etiqueta, millones de flujos) se excluye del entrenamiento. Unidad de análisis: flujo bidireccional. Para que ningún escenario domine, el entrenamiento usa un tope de 2 500 flujos por escenario con submuestreo estratificado (el 7 conserva sus 63 Botnet).
Variables A (16, versión 1.0.0 del Laboratorio): duration, bytes_out, bytes_in, bytes_total, packets, bytes_per_packet, ratio_out, bytes_per_s, pkts_per_s, dst_port y las categóricas proto, state, dir, direction, dst_port_class, src_port_class. Prohibidas por fuga: IP, marca de tiempo absoluta, identificadores, escenario y etiqueta.
Variante B (secundaria): variables A + 20 agregados causales de la IP de origen en una ventana de W minutos (W = 1 o 5), calculados solo con flujos anteriores o iguales al evaluado.
Hardware: i5-12450H (12 hilos), 15 GB de RAM + 15 GB de zram, sin GPU, Docker Compose.

EVIDENCIA PREVIA (para dimensionar el diseño; no la presentes como resultado del protocolo nuevo)
- Dejando un escenario fuera (12 pliegues), 10 trials, 5 semillas (11, 22, 33, 44, 55), PR-AUC media: Dummy 0,383; regresión logística 0,886; Random Forest 0,906; HistGB 0,911; XGBoost 0,897; ensamble LR+RF+HGB 0,918 ± 0,006. Con Holm ninguna diferencia por pares es significativa (p ajustado mínimo 0,161) y los IC 95 % por bootstrap de escenarios se solapan (ancho ≈ 0,15–0,18).
- Escenarios difíciles: 7 Sogou (0,40–0,64), 8 Murlo (0,68–0,89) y 12 NSIS.ay (0,63–0,77), con desviaciones entre semillas de hasta 0,157.
- La cobertura de la familia en el entrenamiento domina: con 4 escenarios los árboles quedaron por debajo del azar en Rbot (ROC-AUC 0,13–0,32); con 11 escenarios, PR-AUC en Rbot de 0,96 a 1,00.
- Con variante B no causal (ventana de 5 min, que incluye flujos futuros) el ensamble llegó a 0,985, pero la versión causal no tiene resultados completos y la no causal no es utilizable en línea.
- Evaluación realista en 3 escenarios (una semilla, Background como Normal, sin submuestreo): con el umbral por exactitud balanceada se marcó entre 25 % y 41 % del Background y la precisión operativa fue del 2–4 %.
- La búsqueda de hiperparámetros ejecutada usó TPE con n_startup_trials = 10 (valor por defecto) y solo 10 trials, es decir, fue de hecho aleatoria, y su MedianPruner nunca podó porque no se llamaba a trial.report. El nuevo protocolo debe corregirlo.

REGLAS OBLIGATORIAS
1. Partición 70/15/15 por escenarios completos, nunca por flujos ni por bloques de tiempo. Los flujos de un escenario comparten hosts, captura y familia; partir por bloques de 10 s dio PR-AUC ≈ 1,0 que no se sostuvo entre escenarios. Con 12 unidades usa 8 Desarrollo / 2 Validación / 2 Prueba (66,7/16,7/16,7 %) e informa la proporción real en flujos. Asignación determinista por semilla con estas restricciones: (a) las familias con varios escenarios (Neris 1, 2, 9; Rbot 3, 4, 11; Virut 5, 13) tienen al menos uno en Desarrollo; (b) el escenario 7 no es de Prueba; (c) cada escenario de Validación y de Prueba se etiqueta «familia vista» o «familia no vista» y no se mezclan ambos casos en un mismo promedio. Con solo 2 escenarios de Prueba la estimación es ruidosa: repite la partición con al menos 5 semillas, informa los escenarios de Prueba de cada una y calcula los IC por bootstrap sobre escenarios, no sobre particiones (comparten escenarios). Roles: Desarrollo = entrenar y buscar hiperparámetros; Validación = umbral, calibración y elección del finalista; Prueba = una sola evaluación del finalista congelado.
2. Sin fuga. Todo el preprocesamiento (logaritmo, escalado, codificación, imputación) se ajusta solo con el entrenamiento de cada pliegue. Ninguna decisión usa Prueba. Declara que el análisis exploratorio previo ya empleó los 12 escenarios, de modo que la Prueba no es virgen respecto a la elección de modelos candidatos; mitiga congelando la lista de candidatos y el criterio de elección antes de ejecutar.
3. CV anidada dentro de Desarrollo. Externo: dejar un escenario fuera sobre los 8 de Desarrollo (8 pliegues). Interno: CV agrupada por escenario con 4 grupos sobre los 7 restantes. En cada pliegue externo: (a) Optuna sobre los grupos internos con PR-AUC media como objetivo, (b) reentrenar con los mejores hiperparámetros sobre los 7 escenarios, (c) evaluar UNA vez sobre el escenario externo. Agrega los 8 resultados. Después, el finalista se reentrena con todo Desarrollo, el umbral y la calibración se fijan en Validación y se evalúa una vez en Prueba. Semillas de ejecución: 11, 22, 33, 44, 55. Si un grupo interno tiene una sola clase o menos de 10 Botnet, detén el entrenamiento y explica por qué.
4. Búsqueda de hiperparámetros. Parte de los espacios de abajo. Especifica n_trials ≥ 30 por modelo y pliegue externo, TPE con n_startup_trials = 8 (menor que un tercio de n_trials), MedianPruner(n_startup_trials = 5) con trial.report de la PR-AUC acumulada tras cada grupo interno y poda real, timeout por estudio y semilla fija. Indica qué condición de parada se activa primero. Plan por fases: cribado barato (10 trials, 2 semillas) para descartar modelos y confirmación (30 trials, 5 semillas) solo para los finalistas.
5. Desbalance. La prevalencia por escenario va de 3,6 % a 86,1 %. Define el tratamiento solo dentro del entrenamiento (class_weight o scale_pos_weight; no remuestrees Validación ni Prueba). Optimiza PR-AUC y justifica por qué no accuracy. Compara SIEMPRE con Dummy: nunca presentes un PR-AUC sin su mejora sobre la prevalencia del escenario. El promedio entre escenarios es macro (cada escenario pesa igual). Informa Prueba con y sin el tope de 2 500 flujos.
6. Umbral y calibración, en Validación. Dos políticas: (a) máxima exactitud balanceada; (b) tasa de falsos positivos objetivo configurable, medida con el Background como Normal y sin submuestreo en los escenarios de Validación. Con (a) el Background marcado fue del 25–41 %. Calibración (Platt o isotónica) ajustada en Validación; informa Brier, ECE, curva de fiabilidad y alertas por 100 000 flujos.

MODELOS
Dummy (prevalencia), regresión logística, Random Forest, Gradient Boosting de histogramas (HistGB) y XGBoost, más ensambles por voto suave (candidato: LR+RF+HGB, reutilizando los hiperparámetros ya hallados por miembro; sin repetir la búsqueda).
Espacios del Laboratorio (tipo, rango por defecto):
- logreg: C 1e-3 a 1e2 (log); penalty {l2, l1}; class_weight {none, balanced}. Fijos: solver liblinear, max_iter 2000, logaritmo en 8 columnas de volumen y ritmo, escalado y one-hot.
- random_forest: n_estimators 200–800 (paso 100); max_depth 4–30; min_samples_leaf 1–20 (log); max_features {sqrt, log2, 0,5}; class_weight {none, balanced, balanced_subsample}.
- hist_gb: learning_rate 0,01–0,3 (log); max_iter 100–500; max_leaf_nodes 8–64; l2_regularization 1e-6–10 (log); min_samples_leaf 5–100; class_weight {none, balanced}. Hoy sin parada temprana.
- xgboost: eta 0,01–0,3 (log); max_depth 2–10; subsample 0,5–1; colsample_bytree 0,4–1; min_child_weight 1–20 (log); gamma 0–5; reg_lambda 0,01–20 (log); scale_pos_weight 1–50 (log). Fijos: n_estimators 300, tree_method hist.
Para cada modelo entrega: justificación y supuestos; parámetros iniciales y fijos; espacio de búsqueda (tipo, rango por defecto, rango duro, escala y porqué); trials, sampler y pruner con su configuración; condiciones de parada (iteraciones máximas, parada temprana con métrica, paciencia y conjunto vigilado, que debe ser un grupo interno y nunca Validación ni Prueba; tolerancia; timeout; máximo de trials) y cuál se activa primero; costo estimado. Cierra con una tabla comparativa.

VARIANTE B (contexto del host)
Diséñala como experimento secundario preregistrado: mismos pliegues que A, solo versión causal, W elegido con Validación y no con Prueba. Aclara que clasifica por el comportamiento del host en la ventana y no por el flujo aislado, y que una alerta solo puede emitirse con W minutos de retraso en la versión no causal. Si la ventaja desaparece sin mirar el futuro, repórtalo.

COSTO Y EJECUCIÓN
Estima el número de ajustes (pliegues externos × trials × grupos internos × modelos × semillas × particiones) y conviértelo a horas con una medida real: la CV anidada de 12 escenarios con 5 modelos, 10 trials y 5 semillas tomó varias horas. Lección medida: la sobresuscripción de hilos (OpenMP de HistGB × n_jobs de Random Forest y XGBoost) multiplicó el tiempo en torno a 7 veces. Fija OMP_NUM_THREADS y n_jobs para que el total no pase de 12 hilos, no ejecutes más de 3–4 procesos pesados a la vez (15 GB de RAM), guarda resultados de forma incremental y permite reanudar. Define criterios de aborto por fase.

MONITOREO Y REPRODUCIBILIDAD
Eventos en tiempo real (partición, pliegue, trial, poda, fin), métricas mostradas y cancelación segura. Semillas, versiones (Python, scikit-learn, XGBoost, Optuna), hash SHA-256 de cada archivo de datos, FEATURE_SPEC_VERSION, hash del modelo y registro de auditoría.

EVALUACIÓN
Métricas: PR-AUC (principal), ROC-AUC, sensibilidad, precisión, exactitud balanceada, F1, MCC y Brier, por escenario y en macro-promedio, con media ± desviación entre semillas, mediana y peor escenario. Pruebas: Friedman, Wilcoxon con Holm y bootstrap por escenarios (10 000 remuestreos, IC 95 %). Con 8–12 escenarios el estudio previo no encontró diferencias significativas entre modelos tras Holm: no declares un modelo ganador que no sobreviva a esa corrección y presenta lo demás como tendencia. Los ensambles comparten miembros, así que Friedman que los incluya no es una prueba independiente.
Explicabilidad: SHAP global y local, importancia por permutación, PDP/ICE y oclusión; compara la importancia entre escenarios. Severidad por alerta con umbrales configurables sobre la probabilidad calibrada.

AMENAZAS A LA VALIDEZ (obligatorias)
Solo CTU-13 y de 2011; sin logs de firewall reales; CIC-IDS2017 negativo; escenario 10 ausente; Background sin etiqueta fiable; 2 escenarios de Prueba por partición; dependencia de la cobertura de familia; escenario 7 con 63 positivos; presupuesto de Optuna; Prueba no virgen respecto a los candidatos; sesgo optimista al elegir W y el ensamble con los mismos resultados.

INTEGRACIÓN EN EL LABORATORIO ML
Reutiliza groups.py (partition_groups, nested_folds, FRACS = 0,70 / 0,15 / 0,15), nested.py (search, con trial.report y poda), models.py (SEARCH_SPACES) y features.py. Indica los cambios necesarios: (1) clave de agrupación «escenario» (hoy solo host de origen, par origen-destino y bloque temporal) e ingesta multiescenario con tope por escenario; (2) partición determinista por escenarios con las restricciones de la regla 1 en lugar de la búsqueda aleatoria actual; (3) el validador exige al menos 3 grupos por clase y partición (MIN_GROUPS_PER_PARTITION_CLASS), lo que bloquea una Prueba de 2 escenarios: justifica cómo relajarlo; (4) MAX_FOLDS_HARD = 10 alcanza para 8 pliegues externos pero no para el leave-one-scenario-out de 12; (5) política de umbral por tasa de falsos positivos objetivo; (6) la validación entre escenarios se hizo con scripts (docs/validacion-externa/), no desde el Laboratorio: indica cómo migrarla.

FORMATO
Secciones numeradas: (1) técnica elegida y por qué no k-fold por flujos, (2) partición 70/15/15 con tabla escenario → partición → familia → flujos → Botnet, (3) CV anidada y búsqueda de hiperparámetros, (4) fichas por modelo y ensambles, (5) tabla comparativa, (6) desbalance, umbral y calibración, (7) variante B, (8) costo y plan por fases, (9) monitoreo y reproducibilidad, (10) evaluación estadística, explicabilidad y severidad, (11) amenazas a la validez, (12) integración en el Laboratorio ML. Cada tabla y figura lleva una breve interpretación (qué significa y con qué cuidado leerla). Español técnico, cifras concretas, sin resultados inventados.
```
