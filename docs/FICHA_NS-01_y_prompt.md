# NS-01. Detección explicable de tráfico botnet en logs de firewall/IDS mediante aprendizaje automático con validación por grupos

## Ficha técnica (archivo adjunto)

**Problema.** Los analistas reciben miles de registros de firewall/IDS y no pueden revisarlos uno a uno. Las reglas fijas dejan pasar comportamientos como el beaconing, y los modelos de caja negra no explican por qué marcan un flujo.

**Vacío de conocimiento (hipótesis a confirmar con revisión bibliográfica).** Gran parte de los estudios sobre CTU-13 mezcla flujos de un mismo host entre entrenamiento y prueba y sobreestima el rendimiento. Falta evaluación con validación agrupada, calibración, incertidumbre y explicación por alerta.

**Pregunta.** ¿En qué medida un clasificador explicable, evaluado con CV anidada agrupada y sin fuga de datos, detecta flujos Botnet frente a Normal mejor que una línea base trivial y que la regresión logística, con probabilidades calibradas y explicaciones útiles para el analista?

**Objetivo general.** Desarrollar y validar un clasificador Botnet vs Normal integrado en NetSentinel, con severidad por alerta y explicación SHAP.

**Objetivos específicos.**
1. Construir y versionar un dataset etiquetado (CTU-13) con metadata, procedencia y hash.
2. Validar los grupos y la partición 70/15/15 sin fuga.
3. Comparar Dummy, regresión logística, Random Forest, Gradient Boosting de histogramas y XGBoost.
4. Evaluar con CV anidada 5x3 y prueba final única.
5. Explicar las predicciones (SHAP, permutación, oclusión) y asignar severidad.

**Datos.** CTU-13, escenario 11 (Rbot; CTU-Malware-Capture-Botnet-52), Stratosphere Laboratory, CTU Praga. Licencia: uso libre citando a García, Grill, Stiborek y Zunino, *Computers & Security* 45 (2014) 100-123.
- 107 194 flujos únicos tras eliminar 107 194 duplicados de carga (el mismo dataset se había ingerido dos veces).
- 8 164 Botnet, 2 718 Normal y 96 312 Background (excluidos: sin verdad conocida).
- Se entrena y evalúa con los 10 882 flujos etiquetados: 75,0 % Botnet y 25,0 % Normal.
- Unidad de análisis: flujo. Agrupación: bloques temporales de 10 s.

**Diseño.** Observacional, retrospectivo y predictivo. Variable dependiente: Botnet=1 / Normal=0. Optimización con Optuna sobre PR-AUC. Validación: StratifiedGroupKFold, 5 pliegues externos x 3 internos. Partición 70/15/15. Python (backend FastAPI) e interfaz React. Hardware: i5-12450H (12 hilos), 15 GB de RAM, CPU sin GPU, Docker Compose.

**Evaluación.** Precisión, exhaustividad, F1, especificidad, exactitud balanceada, MCC, ROC-AUC, PR-AUC y Brier. Calibración: curva de fiabilidad y ECE. Comparación: Friedman, Wilcoxon con Holm, McNemar y bootstrap pareado por grupos con IC 95 %. Interpretabilidad: SHAP, permutación, PDP/ICE y oclusión. Siempre se reporta la mejora sobre la línea base trivial: con 75 % de Botnet, el PR-AUC del Dummy ya ronda 0,75.

**Limitaciones y amenazas a la validez.**
- Un solo escenario (11): no hay validación externa entre escenarios ni entre botnets; la agrupación por bloques de 10 s evita fuga temporal inmediata pero no mide generalización a otras familias.
- Prevalencia de Botnet (75 %) invertida respecto a un entorno real.
- Con solo 5 pliegues externos, el p mínimo alcanzable de Wilcoxon es 0,0625: las comparaciones por pares tienen poca potencia.
- Resultados válidos para este conjunto; no se extrapolan a tráfico de producción sin nuevas pruebas.

**Trabajo futuro.** Ingerir otros escenarios de CTU-13 para validación externa por escenario.

---

## Prompt

> **Superado.** Este prompt corresponde a la etapa de un solo escenario (11). La versión vigente, con alcance fijo en CTU-13 (12 escenarios), partición 70/15/15 por escenarios y presupuesto de búsqueda corregido, está en `docs/PROMPT_protocolo_CTU13.md`. Se conserva aquí como registro.

```text
ROL
Actúa como ingeniero senior de aprendizaje automático y ciberseguridad, con experiencia en detección de botnets sobre flujos de red y en validación estadística sin fuga de datos.

CONTEXTO Y ARCHIVO ADJUNTO
Adjunto la ficha técnica NS-01 de NetSentinel (analista de logs de firewall/IDS: backend FastAPI + SQLAlchemy + PostgreSQL, frontend React, trabajos ML en segundo plano). Los datos son flujos de red tabulares; no hay imágenes. Usa solo lo que dice la ficha. Las cifras de la ficha son reales: entrena y evalúa con los 10 882 flujos etiquetados, no con los 107 194. Si falta un dato, márcalo como [SUPUESTO] y no lo inventes.

TAREA
Prepara un protocolo de entrenamiento riguroso y reproducible para el tema de la ficha, eligiendo y justificando la técnica más apropiada. Debe implementarse en el Laboratorio ML de NetSentinel, no en Streamlit.

REGLAS OBLIGATORIAS
1. Partición por clase: 70 % Desarrollo, 15 % Validación y 15 % Prueba. Indica el rol de cada subconjunto; Prueba se usa una sola vez. Incluye la tabla Clase x (Desarrollo, Validación, Prueba) con conteos reales.
2. Sin fuga: pliegues estratificados y agrupados (bloques temporales de 10 s) con semilla fija. El preprocesamiento se ajusta solo con entrenamiento de cada pliegue. Lista las variables descartadas por riesgo de fuga.
3. CV anidada 5 externos x 3 internos. En cada pliegue externo: (a) Optuna sobre los internos, (b) reentrenar con los mejores hiperparámetros sobre outer_train, (c) evaluar UNA vez sobre outer_val. Agrega los 5 resultados. Si algún pliegue tiene pocos positivos, detén el entrenamiento y explica por qué.
4. Desbalance: la prevalencia de Botnet es 75 %, invertida respecto a un entorno real; define el tratamiento solo dentro del entrenamiento. Optimiza PR-AUC y justifica por qué no accuracy. Compara SIEMPRE con la línea base trivial (Dummy): nunca presentes el PR-AUC sin la mejora sobre ella.

MODELOS
Dummy (prevalencia), regresión logística, Random Forest, Gradient Boosting de histogramas y XGBoost. Para cada uno entrega:
- justificación y supuestos;
- parámetros iniciales y fijos;
- espacio de búsqueda (tipo, rango por defecto, rango duro, escala y porqué);
- trials por pliegue, sampler (TPE) y pruner con su configuración;
- condiciones de parada (iteraciones máximas, early stopping con métrica, paciencia y conjunto vigilado sin tocar outer_val, tolerancia, timeout, máximo de trials) y cuál se activa primero;
- costo computacional estimado en el hardware de la ficha.
Cierra con una tabla comparativa.

MONITOREO Y REPRODUCIBILIDAD
Eventos en tiempo real (pliegue, trial, poda, fin), métricas mostradas y cancelación segura. Semillas, versiones, hash del dataset y del modelo, y registro de auditoría.

EVALUACIÓN
Métricas y pruebas estadísticas de la ficha, con media ± desviación entre pliegues externos. Advierte la limitación de 5 pliegues (p mínimo de Wilcoxon 0,0625).
Explicabilidad: SHAP global y local, permutación, PDP/ICE y oclusión como equivalente tabular de los mapas de atención. Incluye la severidad por alerta con umbrales configurables.

LIMITACIONES
Declara en amenazas a la validez que solo se usa un escenario (el 11), por lo que no hay validación externa entre escenarios ni botnets, y propón como trabajo futuro ingerir otros escenarios.

FORMATO
Secciones numeradas: (1) técnica elegida, (2) partición, (3) CV anidada, (4) fichas por modelo, (5) tabla comparativa, (6) monitoreo y reproducibilidad, (7) evaluación estadística, (8) explicabilidad y severidad, (9) amenazas a la validez, (10) integración en el Laboratorio ML. Cada tabla y figura lleva una breve interpretación (qué significa y con qué cuidado leerla). Español técnico, cifras concretas y sin resultados inventados.
```

---

## Resultados de validación adicionales (para citar en el estudio)

**Repetición con varias semillas (CV anidada 5x3).** Semillas 42, 123 y 31337 viables; 7 y 2024 bloqueadas por el validador (un pliegue con una sola clase, o con menos de 10 flujos Botnet). PR-AUC externa: Dummy 0,470; regresión logística, Random Forest y XGBoost 1,000; GB histogramas 0,992 ± 0,007. Sin diferencias significativas entre modelos (Holm ≥ 0,61). Detalle: `docs/multisemilla/resumen_semillas.txt`.

**Validación entre escenarios (entrena en uno, prueba en el otro; escenarios 11 y 12 de CTU-13).** Escenario 12: 9 793 flujos etiquetados, 22,1 % Botnet. Mismos hiperparámetros del escenario 11. Detalle: `docs/validacion-externa/resultado_entre_escenarios.json`.

| Entrena -> Prueba | Modelo | PR-AUC | ROC-AUC | Exhaustividad | Precisión |
|---|---|---|---|---|---|
| 11 -> 12 (línea base 0,221) | Regresión logística | 0,647 | 0,735 | 0,526 | 0,696 |
| | Random Forest | 0,776 | 0,911 | 0,249 | 0,957 |
| | GB histogramas | 0,694 | 0,879 | 0,165 | 0,862 |
| | XGBoost | 0,686 | 0,846 | 0,495 | 0,724 |
| 12 -> 11 (línea base 0,750) | Regresión logística | 0,988 | 0,958 | 0,998 | 0,816 |
| | Random Forest | 0,746 | 0,290 | 0,022 | 0,087 |
| | GB histogramas | 0,697 | 0,180 | 0,007 | 0,026 |
| | XGBoost | 0,769 | 0,321 | 0,076 | 0,718 |

**Lectura.** Los resultados casi perfectos dentro del escenario 11 no se sostienen entre escenarios. De 11 a 12 los modelos de árboles conservan buena separación (ROC-AUC 0,85-0,91) pero detectan solo el 16-50 % de los flujos Botnet con umbral 0,5. De 12 a 11 los árboles quedan por debajo del azar (ROC-AUC 0,18-0,32): aprenden señales específicas de la botnet y la red de cada escenario. Solo la regresión logística generaliza en esa dirección. La conclusión honesta es que el clasificador no es transferible entre botnets con estas variables, y que la validación interna por bloques temporales sobreestima el rendimiento.

**Estado.** El escenario 10 (Botnet-51) no se pudo incluir: el zip descargado contiene solo capturas pcap y no el `.binetflow` etiquetado.

---

## Validación dejando un escenario completo fuera (4 escenarios de CTU-13)

Escenarios: 9 (Neris; 214 943 flujos etiquetados, 86,1 % Botnet), 11 (Rbot; 10 882, 75,0 %), 12 (NSIS.ay; 9 793, 22,1 %) y 13 (Virut; 71 903, 55,6 %). Se entrena con tres escenarios y se prueba en el cuarto, rotando; umbral 0,5; hiperparámetros del Laboratorio ML (CV anidada del escenario 11). Detalle: `docs/validacion-externa/resultado_dejar_uno_fuera.json`.

| Escenario fuera (prevalencia) | Reg. logística PR-AUC / exhaust. | Random Forest | GB histogramas | XGBoost |
|---|---|---|---|---|
| 9 Neris (0,861) | 0,987 / 0,752 | 0,997 / 0,910 | 0,997 / 0,911 | 0,997 / 0,950 |
| 12 NSIS.ay (0,221) | 0,909 / 0,963 | 0,620 / 0,613 | 0,857 / 0,911 | 0,745 / 0,934 |
| 13 Virut (0,556) | 0,984 / 0,994 | 0,998 / 0,990 | 0,999 / 0,997 | 0,998 / 0,999 |
| 11 Rbot (0,750) | 1,000 / 1,000 | 0,991 / 0,029 | 0,780 / 0,028 | 0,697 / 0,023 |

**Lectura.** Entrenar con varios escenarios mejora mucho la generalización respecto al entrenamiento con uno solo: en los escenarios 9, 12 y 13 los modelos superan con claridad la línea base (PR-AUC 0,62-0,999 frente a 0,22-0,86). El caso difícil es el escenario 11 (Rbot): los modelos de árboles tienen ROC-AUC de 0,14 a 0,98 y, con umbral 0,5, exhaustividad de solo 0,02-0,03 (casi no detectan Botnet), mientras la regresión logística acierta (PR-AUC 1,000). Con el escenario 11 como único entrenamiento, los árboles ya habían fallado al transferirse. La conclusión es que el rendimiento depende fuertemente de la familia de botnet y que un solo umbral fijo no es fiable entre redes.

**Cautelas.** (1) Los hiperparámetros se ajustaron con el escenario 11, por lo que ese escenario es el menos independiente; para 9, 12 y 13 no hay fuga de ajuste. (2) El escenario 9 domina el entrenamiento (215 mil flujos): cuando está en el entrenamiento, sesga los modelos hacia su comportamiento. (3) Una sola ejecución por escenario fuera, semilla 42, sin repeticiones ni intervalos de confianza. (4) Se usan solo flujos Botnet y Normal; el Background (casi 4 millones de flujos sin etiqueta fiable) queda fuera, lo que no refleja el tráfico real.

---

## CV anidada por escenario con Optuna y 3 semillas (versión final de la validación externa)

Diseño: externo = dejar fuera 1 de 4 escenarios (9 Neris, 11 Rbot, 12 NSIS.ay, 13 Virut). Interno = leave-one-scenario-out sobre los 3 restantes; Optuna (6 trials, PR-AUC media; búsqueda de hecho aleatoria, ver «Corrección metodológica» más abajo) elige hiperparámetros y el umbral se elige con las predicciones internas (máx. exactitud balanceada). Cada escenario se submuestrea a 4 000 flujos (estratificado) para que ninguno domine. Semillas 11, 22 y 33; media ± DE. El escenario de prueba nunca participa en el ajuste. Detalle: `docs/validacion-externa/resultado_anidada_escenarios.json` y `anidada_por_escenario.log`.

| Escenario fuera (prevalencia) | Reg. logística | Random Forest | GB histogramas | XGBoost |
|---|---|---|---|---|
| 9 Neris (0,86) | 0,986 ± 0,002 | 0,984 ± 0,007 | 0,994 ± 0,001 | 0,993 ± 0,001 |
| 12 NSIS.ay (0,22) | 0,908 ± 0,005 | 0,713 ± 0,022 | 0,856 ± 0,066 | 0,805 ± 0,075 |
| 13 Virut (0,56) | 0,983 ± 0,001 | 0,996 ± 0,001 | 0,996 ± 0,000 | 0,996 ± 0,001 |
| 11 Rbot (0,75) | 1,000 ± 0,000 | 0,768 ± 0,003 | 0,691 ± 0,019 | 0,747 ± 0,019 |

(PR-AUC en el escenario de prueba; líneas base del Dummy: 0,86 / 0,22 / 0,56 / 0,75.)

**Lectura.** (1) La regresión logística es la única estable en los cuatro escenarios (PR-AUC ≥ 0,908, con la mayor mejora sobre la línea base en NSIS.ay). (2) Los modelos de árboles son mejores en Neris y Virut, pero en Rbot quedan en o por debajo de la línea base y con ROC-AUC de 0,13 a 0,32, es decir, peores que el azar: aprenden regularidades de otras botnets que en Rbot se invierten. (3) Reajustar hiperparámetros con validación por escenarios y elegir el umbral con datos internos no corrige ese fallo: es un problema de las variables y de la deriva entre familias, no del ajuste. (4) Elegir el umbral por exactitud balanceada mejora poco respecto a 0,5 y a veces empeora (por ejemplo, regresión logística en Virut), así que no se recomienda como solución general.

**Recomendación del estudio.** Usar la regresión logística como modelo base robusto y reportar los árboles como más potentes dentro de las familias vistas, pero no confiables ante familias nuevas. Con solo 4 escenarios y submuestreo de 4 000 flujos, las conclusiones son orientativas.

**Limitaciones que persisten.** 4 de 13 escenarios; submuestreo (se pierde información del escenario 9); 6 trials de Optuna por modelo (espacio de búsqueda explorado de forma ligera); sin tráfico Background; sin datos de otra red ni de logs reales de firewall.

---

## Diagnóstico del fallo de los árboles en Rbot (ablación por grupos de variables)

Dejando un escenario fuera, hiperparámetros por defecto, 3 semillas, 4 000 flujos por escenario. PR-AUC / ROC-AUC en cada escenario de prueba. Scripts: `docs/validacion-externa/ablacion_variables.py`; resultados: `ablacion_robusta.json`.

| Conjunto de variables | Modelo | 9 Neris | 12 NSIS.ay | 13 Virut | 11 Rbot |
|---|---|---|---|---|---|
| Completo | Reg. logística | 0,99 / 0,92 | 0,90 / 0,96 | 0,98 / 0,97 | 0,99 / 0,97 |
| | Random Forest | 0,99 / 0,97 | 0,59 / 0,91 | 1,00 / 1,00 | 0,74 / 0,31 |
| | XGBoost | 0,99 / 0,97 | 0,86 / 0,96 | 1,00 / 1,00 | 0,71 / 0,21 |
| Sin volumen (bytes, paquetes, tasas) | Random Forest | 0,99 / 0,93 | 0,43 / 0,79 | 0,98 / 0,97 | 0,92 / 0,74 |
| | XGBoost | 0,99 / 0,93 | 0,71 / 0,90 | 0,98 / 0,98 | 0,82 / 0,47 |
| Sin puertos ni variables categóricas | Random Forest | 0,99 / 0,95 | 0,55 / 0,88 | 0,99 / 0,99 | 0,78 / 0,32 |
| Sin volumen absoluto ni tasas ni puerto de destino | Random Forest | 0,99 / 0,95 | 0,61 / 0,89 | 0,99 / 0,99 | 0,84 / 0,51 |

**Hallazgos.**
1. El fallo en Rbot no se debe a los puertos ni a las variables categóricas (protocolo, estado, dirección): quitarlos no lo corrige.
2. Está ligado a las variables de volumen (bytes, paquetes, tasas): al quitarlas, Random Forest en Rbot pasa de ROC-AUC 0,31 a 0,74 y de PR-AUC 0,74 a 0,92. Los umbrales de volumen aprendidos en Neris, NSIS.ay y Virut se invierten en Rbot.
3. Quitar el volumen cuesta rendimiento en los demás escenarios (por ejemplo, Random Forest en NSIS.ay baja de 0,59 a 0,43 de PR-AUC), de modo que no existe un conjunto de variables simple que sea mejor en los cuatro. Ninguna combinación probada iguala a la regresión logística con transformación logarítmica y escalado, que es estable en todos.
4. Conclusión: es un desplazamiento de distribución entre familias de botnet que este conjunto de 14 variables por flujo no resuelve. Se supera con la regresión logística como modelo robusto y con más variedad de escenarios, no con ajuste de variables.

---

## Ampliación a 12 escenarios de CTU-13 (corrige las conclusiones anteriores sobre Rbot)

Escenarios usados: 1, 2 y 9 (Neris), 3, 4 y 11 (Rbot), 5 y 13 (Virut), 6 (Menti), 7 (Sogou), 8 (Murlo), 12 (NSIS.ay). El 10 no se usa: su carpeta publica solo capturas y NetFlow unidireccional, sin el `.binetflow` bidireccional con etiquetas. Prevalencia de Botnet por escenario: 0,04 a 0,86. El escenario 7 tiene solo 63 flujos Botnet: sus métricas como escenario de prueba son inestables. Scripts: `docs/validacion-externa/multiescenario.py`; resultados: `multi_rapido.json`.

**Comparación rápida (dejando un escenario fuera, parámetros por defecto, 3 semillas, 3 000 flujos por escenario).** PR-AUC / ROC-AUC, media sobre los 12 escenarios de prueba:

| Representación | Modelo | PR-AUC media | ROC-AUC media | Peor ROC-AUC |
|---|---|---|---|---|
| Variables crudas | Reg. logística | 0,902 | 0,954 | 0,87 |
| | Random Forest | 0,898 | 0,976 | 0,91 |
| | GB histogramas | 0,931 | 0,973 | 0,84 |
| | XGBoost | 0,912 | 0,971 | 0,83 |
| Rango percentil por escenario | Reg. logística | 0,901 | 0,944 | 0,81 |
| | Random Forest | 0,875 | 0,912 | 0,76 |
| | GB histogramas | 0,891 | 0,915 | 0,61 |
| | XGBoost | 0,879 | 0,923 | 0,78 |

**Correcciones a lo dicho antes.**
1. El fallo de los árboles en Rbot (ROC-AUC 0,13-0,32 con 4 escenarios) desaparece al entrenar con 11 escenarios: con los escenarios 3 y 4 (también Rbot) en el entrenamiento, el escenario 11 se predice con PR-AUC 1,00 y ROC-AUC 1,00. La causa era la falta de cobertura de la familia en el entrenamiento, no un defecto de las variables ni una inversión imposible de corregir.
2. La recomendación de la regresión logística como único modelo estable ya no se sostiene: con 12 escenarios, los modelos de árboles (en especial GB histogramas y Random Forest) son iguales o mejores en media y no hay modelo con fallos graves salvo en escenarios muy distintos.
3. La normalización por rango dentro del escenario (adaptación de dominio sin etiquetas) no mejora: empeora los modelos de árboles. Resultado negativo, se descarta.

**Escenarios más difíciles.** NSIS.ay (12), la única botnet P2P: PR-AUC entre 0,61 y 0,86. Sogou (7), con 63 positivos: 0,33 a 0,74 (inestable). Murlo (8) con XGBoost: 0,71.


## Resultado final: CV anidada por escenario con 12 escenarios (Optuna, 2 semillas)

**Diseño.** Se deja un escenario fuera (12 escenarios CTU-13: 1–9, 11, 12, 13; falta el 10). Con los otros 11 se hace búsqueda de hiperparámetros con Optuna (10 intentos por modelo; ver «Corrección metodológica» al final de esta sección: fue de hecho búsqueda aleatoria) usando validación interna agrupada por escenario (4 grupos), PR-AUC como objetivo; el umbral se elige por exactitud balanceada en las predicciones internas. Tope de 2500 flujos por escenario (submuestreo estratificado), variables crudas, semillas 11 y 22. Evaluación en el escenario excluido. Dummy siempre como referencia. Archivos: `docs/validacion-externa/multiescenario.py`, `multi_anidado_crudas_11.json`, `multi_anidado_crudas_22.json`, `multi_anidado_s11.log`, `multi_anidado_s22.log` (120 filas, 60 por semilla).

**PR-AUC por escenario excluido (media de 2 semillas).**

| Esc. | Familia | Dummy | Regr. log. | Random forest | HistGB | XGBoost |
|---|---|---|---|---|---|---|
| 1 | Neris | 0,574 | 0,939 | 0,961 | 0,952 | 0,957 |
| 2 | Neris | 0,697 | 0,986 | 0,998 | 0,997 | 0,997 |
| 3 | Rbot | 0,187 | 0,993 | 1,000 | 0,998 | 0,999 |
| 4 | Rbot | 0,093 | 0,978 | 0,959 | 0,988 | 0,989 |
| 5 | Virut | 0,162 | 0,887 | 0,948 | 0,947 | 0,936 |
| 6 | Menti | 0,382 | 0,999 | 1,000 | 1,000 | 1,000 |
| 7 | Sogou | 0,036 | 0,451 | 0,470 | 0,535 | 0,295 |
| 8 | Murlo | 0,078 | 0,616 | 0,904 | 0,655 | 0,884 |
| 9 | Neris | 0,861 | 0,985 | 0,995 | 0,995 | 0,996 |
| 11 | Rbot | 0,750 | 0,999 | 1,000 | 0,997 | 1,000 |
| 12 | NSIS.ay | 0,221 | 0,783 | 0,700 | 0,645 | 0,703 |
| 13 | Virut | 0,556 | 0,984 | 0,998 | 0,998 | 0,998 |

**Resumen entre escenarios.**

| | Dummy | Regr. log. | Random forest | HistGB | XGBoost |
|---|---|---|---|---|---|
| PR-AUC media | 0,383 | 0,883 | **0,911** | 0,892 | 0,896 |
| PR-AUC mediana | 0,302 | 0,981 | 0,978 | 0,992 | 0,992 |
| Peor escenario | 0,036 | 0,451 | 0,470 | 0,535 | 0,295 |
| ROC-AUC media | 0,500 | 0,951 | 0,981 | 0,968 | 0,972 |
| Sensibilidad media | 0 | 0,886 | 0,933 | 0,907 | 0,921 |
| Precisión media | 0 | 0,725 | 0,741 | 0,724 | 0,715 |
| Exactitud balanceada | 0,500 | 0,882 | 0,897 | 0,887 | 0,895 |
| Rango medio (1 = mejor) | | 3,50 | **1,75** | 2,42 | 2,33 |

**Pruebas estadísticas (12 escenarios).** Friedman entre los 4 modelos: χ² = 11,5; p = 0,009. Wilcoxon de XGBoost contra regresión logística y contra random forest: p = 0,18; contra HistGB: p = 0,57. Con 12 escenarios no se detectan diferencias entre pares; solo se detecta que los modelos no son equivalentes (la regresión logística queda última en rango).

**Conclusiones.**
1. Todos los modelos superan a Dummy en todos los escenarios. Donde la prevalencia es alta (2, 9, 11) Dummy ya da PR-AUC 0,70–0,86 y la ganancia es pequeña por construcción.
2. En 8 de 12 escenarios la PR-AUC de random forest y de XGBoost es ≥ 0,95. El fallo anterior con Rbot desaparece (0,96–1,00 en los tres escenarios Rbot): se debía a que Rbot no estaba en el entrenamiento.
3. Los casos débiles son el escenario 7 (Sogou; solo 63 positivos, PR-AUC 0,30–0,54), el 12 (NSIS.ay; 0,65–0,78) y el 8 (Murlo; regresión logística 0,62 y HistGB 0,66 frente a 0,88–0,90 de random forest y XGBoost). Una familia desconocida y de poca prevalencia sigue siendo el punto de fallo.
4. Random forest tiene la mejor media y el mejor rango, pero la diferencia con XGBoost y HistGB no es significativa.
5. La variabilidad entre semillas es grande en los escenarios débiles: la diferencia máxima de PR-AUC entre las dos semillas es 0,35 en HistGB, 0,23 en XGBoost, 0,12 en regresión logística y 0,07 en random forest. Con 2 semillas no se puede acotar bien la incertidumbre; random forest es el más estable.

**Limitaciones que siguen vigentes.** Falta el escenario 10 (solo hay pcap; sin binetflow no se pudo etiquetar). Todo es tráfico de laboratorio CTU-13 (2011), sin logs de firewall reales ni otra red. Presupuesto de Optuna ligero (10 intentos). Solo 2 semillas. La validación entre escenarios se hizo con scripts, no desde el Laboratorio ML de la aplicación. Los flujos «Background» (sin etiqueta) se excluyeron. Submuestreo a 2500 flujos por escenario, lo que cambia la prevalencia respecto a los datos completos.

**Corrección metodológica (aplica a esta sección y a las posteriores que reutilizan sus hiperparámetros).** Los scripts `anidada_por_escenario.py` (6 intentos), `multiescenario.py` (10) y `cic.py` (10) crean el estudio con `TPESampler(seed=...)` y `MedianPruner()` por defecto. El `TPESampler` de Optuna usa `n_startup_trials = 10`: con 6 o 10 intentos todos los puntos se muestrean al azar y el modelo TPE nunca interviene, de modo que **la búsqueda fue aleatoria**, no bayesiana. Además el objetivo no llama a `trial.report`, así que el `MedianPruner` nunca podó. Los resultados siguen siendo válidos como evaluación entre escenarios con búsqueda aleatoria de 10 puntos, pero el texto «TPE + MedianPruner» era incorrecto y refuerza la limitación del presupuesto: el espacio se exploró de forma muy ligera. El Laboratorio ML sí hace lo correcto (`nested.py::search` informa y poda; `n_startup_trials = 8`). Las ejecuciones de ensambles y de contexto de host reutilizan esos hiperparámetros, por lo que heredan la limitación. El prompt nuevo (`docs/PROMPT_protocolo_CTU13.md`) exige ≥ 30 intentos, arranque de 8 y poda real.


## Actualización: la misma CV anidada con 5 semillas (sustituye a la tabla de 2 semillas)

Mismo diseño (12 escenarios, 10 intentos de Optuna, tope de 2500 flujos, variables crudas), ahora con las semillas 11, 22, 33, 44 y 55 (300 resultados). Archivos: `docs/validacion-externa/multi_anidado_crudas_{11,22,33,44,55}.json` y sus `.log`. Se corrigió además el script para limitar los hilos (`NJ`) y poder reanudar. Con 2 semillas se reportó random forest como mejor modelo en media; con 5 el orden por media cambia, y eso se muestra aquí.

**PR-AUC por escenario excluido (media ± desviación entre las 5 semillas).**

| Esc. | Familia | Dummy | Regr. log. | Random forest | HistGB | XGBoost |
|---|---|---|---|---|---|---|
| 1 | Neris | 0,574 | 0,940 ± 0,005 | 0,961 ± 0,004 | 0,954 ± 0,006 | 0,956 ± 0,004 |
| 2 | Neris | 0,697 | 0,986 ± 0,001 | 0,997 ± 0,001 | 0,996 ± 0,001 | 0,996 ± 0,001 |
| 3 | Rbot | 0,187 | 0,992 ± 0,006 | 0,999 ± 0,002 | 0,998 ± 0,001 | 0,998 ± 0,002 |
| 4 | Rbot | 0,093 | 0,978 ± 0,008 | 0,956 ± 0,013 | 0,988 ± 0,005 | 0,990 ± 0,005 |
| 5 | Virut | 0,162 | 0,888 ± 0,002 | 0,951 ± 0,006 | 0,949 ± 0,010 | 0,939 ± 0,014 |
| 6 | Menti | 0,382 | 0,998 ± 0,001 | 1,000 ± 0,000 | 0,999 ± 0,000 | 0,999 ± 0,000 |
| 7 | Sogou | 0,036 | 0,435 ± 0,044 | 0,434 ± 0,079 | 0,640 ± 0,157 | 0,399 ± 0,134 |
| 8 | Murlo | 0,078 | 0,677 ± 0,136 | 0,893 ± 0,015 | 0,786 ± 0,125 | 0,813 ± 0,080 |
| 9 | Neris | 0,861 | 0,985 ± 0,002 | 0,995 ± 0,001 | 0,995 ± 0,002 | 0,995 ± 0,001 |
| 11 | Rbot | 0,750 | 0,999 ± 0,001 | 1,000 ± 0,000 | 0,999 ± 0,002 | 1,000 ± 0,000 |
| 12 | NSIS.ay | 0,221 | 0,766 ± 0,025 | 0,690 ± 0,035 | 0,629 ± 0,023 | 0,677 ± 0,056 |
| 13 | Virut | 0,556 | 0,985 ± 0,001 | 0,999 ± 0,000 | 0,998 ± 0,001 | 0,998 ± 0,001 |

**Resumen.** PR-AUC media (media ± desviación de las 5 medias por semilla): Dummy 0,383; regresión logística 0,886 ± 0,013; random forest 0,906 ± 0,007; **HistGB 0,911 ± 0,022**; XGBoost 0,897 ± 0,008. Mediana: 0,982 / 0,978 / 0,991 / 0,992. Peor escenario: 0,435 / 0,434 / 0,629 / 0,399. ROC-AUC media: 0,951 / 0,979 / 0,970 / 0,972. Sensibilidad: 0,881 / 0,928 / 0,906 / 0,918; precisión: 0,741 / 0,740 / 0,733 / 0,723; exactitud balanceada: 0,886 / 0,894 / 0,894 / 0,893. Rango medio (1 = mejor): regresión logística 3,42; random forest **1,50**; HistGB 2,50; XGBoost 2,58.

**Pruebas.** Friedman entre los 4 modelos: χ² = 13,3; p = 0,004. Wilcoxon por pares (sin corrección): regresión logística–HistGB p = 0,034; random forest–XGBoost p = 0,021; el resto p > 0,15. Con Holm sobre las 6 comparaciones **ninguna diferencia por pares es significativa** (el menor valor, 0,021 × 6 = 0,13). Solo se sostiene que los modelos no son equivalentes y que la regresión logística queda última en rango.

**Qué cambia respecto a las 2 semillas.**
- Ningún modelo gana en todo: random forest tiene el mejor rango (gana de forma consistente en escenarios fáciles), HistGB la mejor media y mediana por el escenario 7, y regresión logística el mejor resultado en el escenario 12 (0,766).
- La diferencia entre modelos se concentra en tres escenarios difíciles: 7 (Sogou, 63 positivos), 8 (Murlo) y 12 (NSIS.ay). En el resto todos superan 0,94 salvo regresión logística en el escenario 5 (0,888).
- La variabilidad entre semillas es alta justo ahí: desviación de hasta 0,157 (HistGB, escenario 7) y 0,136 (regresión logística, escenario 8). Las conclusiones sobre esos escenarios son frágiles aunque haya 5 semillas.
- Por eso no se declara un modelo ganador: se recomienda random forest por rango y estabilidad (desviación entre semillas de la media global más baja: 0,007), con la advertencia de que la diferencia no es significativa.

**Limitaciones (actualizadas).** Se superó el número de semillas (de 2 a 5). No se ejecutó la comparación con 30 intentos de Optuna: el presupuesto de 10 intentos sigue siendo ligero y es una limitación abierta. Sin cambios: falta el escenario 10, solo hay tráfico de laboratorio CTU-13 (2011) sin logs de firewall reales, la validación entre escenarios es por scripts y no desde el Laboratorio ML, y se excluyó el tráfico «Background» y se submuestreó a 2500 flujos por escenario.


## Ensambles por voto suave (5 semillas, 12 escenarios)

**Diseño.** Promedio de probabilidades de modelos individuales, con los mejores hiperparámetros ya hallados por Optuna para cada modelo, escenario excluido y semilla (no se repite la búsqueda). El umbral se elige igual que antes: exactitud balanceada sobre las predicciones internas (grupos de escenarios) promediadas. Cuatro ensambles: RF+HGB, LR+RF+HGB (regresión logística, random forest, HistGB), RF+HGB+XGB y los 4 modelos. Archivos: `docs/validacion-externa/ensambles.py`, `ensambles_{11,22,33,44,55}.json` y `.log`.

| | PR-AUC media ± sd entre semillas | Mediana | Peor escenario | ROC-AUC | Sensib. | Precisión | Exact. balanc. | Rango medio (8 modelos) | sd máx. entre semillas en un escenario |
|---|---|---|---|---|---|---|---|---|---|
| Regr. log. | 0,886 ± 0,013 | 0,982 | 0,435 | 0,951 | 0,881 | 0,741 | 0,886 | 7,08 | 0,136 |
| Random forest | 0,906 ± 0,007 | 0,978 | 0,434 | 0,979 | 0,928 | 0,740 | 0,894 | 3,25 | 0,079 |
| HistGB | 0,911 ± 0,022 | 0,991 | 0,629 | 0,970 | 0,906 | 0,733 | 0,894 | 5,50 | 0,157 |
| XGBoost | 0,897 ± 0,008 | 0,992 | 0,399 | 0,972 | 0,918 | 0,723 | 0,893 | 5,83 | 0,134 |
| RF+HGB | 0,917 ± 0,010 | 0,987 | 0,537 | 0,979 | 0,928 | 0,726 | 0,891 | **2,50** | 0,098 |
| **LR+RF+HGB** | **0,918 ± 0,006** | 0,992 | 0,507 | 0,977 | 0,930 | **0,761** | **0,915** | 4,25 | **0,057** |
| RF+HGB+XGB | 0,912 ± 0,008 | 0,990 | 0,490 | 0,977 | 0,923 | 0,728 | 0,898 | 3,75 | 0,076 |
| Los 4 | 0,914 ± 0,005 | 0,992 | 0,476 | 0,977 | 0,922 | 0,748 | 0,907 | 3,83 | 0,058 |

**Resultado.**
- Los ensambles mejoran la PR-AUC media en 0,6–1,2 puntos respecto a random forest y 0,1–0,7 respecto a HistGB; la mejora es pequeña y **no es significativa** (Wilcoxon contra random forest p = 0,42–0,85; contra HistGB p = 0,15–0,57; 12 escenarios).
- Lo más claro es la **estabilidad**: LR+RF+HGB y «los 4» tienen la menor desviación entre semillas (0,006 y 0,005 en la media global; 0,057–0,058 en el peor escenario, frente a 0,079–0,157 de los modelos individuales).
- LR+RF+HGB da la mejor exactitud balanceada (0,915 frente a 0,891–0,898) y la mejor precisión (0,761) con sensibilidad igual a la de random forest (0,930 frente a 0,928). Es el ensamble que mejor equilibra falsos positivos y negativos con el umbral interno.
- **No resuelve los escenarios difíciles:** en el 7 (Sogou) HistGB solo (0,640) supera a todos los ensambles (0,476–0,537); en el 12 (NSIS.ay) la regresión logística sola (0,766) supera a todos (0,674–0,739), aunque LR+RF+HGB se acerca (0,739). El ensamble promedia errores, no crea información que falte en los datos.
- El rango medio favorece a RF+HGB (2,50), pero la prueba de Friedman entre 8 modelos (p < 0,001) incluye ensambles que comparten miembros, así que no es una prueba independiente.

**Conclusión.** Se recomienda **LR+RF+HGB** como candidato por su estabilidad y su equilibrio sensibilidad/precisión, con la advertencia explícita de que la ganancia en PR-AUC sobre un modelo individual no es estadísticamente demostrable con 12 escenarios. Para mejorar los escenarios 7, 8 y 12 haría falta información nueva (variables de comportamiento por host o más datos de esas familias), no más combinaciones de los mismos modelos. Los hiperparámetros se eligieron para cada modelo por separado, no para el ensamble; no se probó ponderación de miembros ni apilamiento (stacking).


## Variables de contexto del host (flujo + agregados de ventana host-tiempo), 5 semillas

**Diseño.** A cada flujo se le añaden las 23 variables de ventana de la app (`WINDOW_NUMERIC`: nº de conexiones, destinos y puertos únicos, entropías, proporciones TCP/UDP/ICMP, proporción de intentos sin respuesta y RST, estadísticos del intervalo entre conexiones, regularidad tipo *beaconing*) de su IP de origen en la ventana de W minutos que lo contiene (W = 1 y 5). Las variables se calculan sin etiquetas. Mismo protocolo (12 escenarios, dejar uno fuera, semillas 11, 22, 33, 44, 55, mismos flujos submuestreados). Se **reutilizan los hiperparámetros de Optuna hallados para flujos** (no se reajustan para las variables nuevas: es una elección conservadora). Umbral interno por exactitud balanceada. Archivos: `docs/validacion-externa/hibrido.py`, `hibrido_{11,22,33,44,55}.json` y `.log`.

**PR-AUC media entre escenarios (media ± desviación entre semillas).**

| Modelo | Solo flujo | Flujo + host, W = 1 min | Flujo + host, W = 5 min |
|---|---|---|---|
| Regresión logística | 0,886 ± 0,013 | 0,957 ± 0,013 | 0,857 ± 0,049 |
| Random forest | 0,906 ± 0,007 | 0,954 ± 0,023 | 0,980 ± 0,008 |
| HistGB | 0,911 ± 0,022 | 0,960 ± 0,012 | 0,965 ± 0,019 |
| XGBoost | 0,897 ± 0,008 | 0,968 ± 0,008 | 0,970 ± 0,009 |
| LR+RF+HGB | 0,918 ± 0,006 | 0,960 ± 0,023 | **0,985 ± 0,004** |

Peor escenario del ensamble LR+RF+HGB: 0,507 (solo flujo), 0,608 (W = 1), **0,895** (W = 5). Métricas operativas del ensamble: solo flujo, sensibilidad 0,930 / precisión 0,761 / exactitud balanceada 0,915; W = 1, 0,988 / 0,900 / 0,957; W = 5, 0,932 / 0,900 / 0,929.

**Por escenario, ensamble LR+RF+HGB (media ± sd).**

| Esc. | Familia | Solo flujo | W = 1 | W = 5 |
|---|---|---|---|---|
| 1 | Neris | 0,959 ± 0,004 | 1,000 | 0,999 |
| 4 | Rbot | 0,989 ± 0,005 | 0,983 ± 0,019 | 0,969 ± 0,021 |
| 5 | Virut | 0,944 ± 0,005 | 1,000 | 1,000 |
| 7 | Sogou | 0,507 ± 0,057 | 0,999 ± 0,001 | 0,993 ± 0,014 |
| 8 | Murlo | 0,892 ± 0,017 | 0,608 ± 0,279 | 0,895 ± 0,019 |
| 11 | Rbot | 1,000 | 0,946 ± 0,054 | 0,976 ± 0,041 |
| 12 | NSIS.ay | 0,739 ± 0,028 | 0,985 ± 0,005 | 0,990 ± 0,006 |
| 2, 3, 6, 9, 13 | varias | ≥ 0,995 | 1,000 | 1,000 |

**Pruebas (Wilcoxon, 12 escenarios, híbrido contra solo flujo, mismo modelo, sin corrección).** W = 5: random forest +0,074 (p = 0,052), LR+RF+HGB +0,067 (p = 0,064), XGBoost +0,074 (p = 0,20), HistGB +0,054 (p = 0,30), regresión logística −0,029 (p = 0,79). W = 1: random forest +0,048 (p = 0,043), XGBoost +0,071 (p = 0,077), resto p > 0,15. Entre los modelos híbridos Friedman no encuentra diferencias (W = 5: p = 0,65; W = 1: p = 0,16). Con la corrección por comparaciones múltiples ninguna mejora individual es significativa; la mejora es de tamaño grande pero se concentra en los escenarios 7 y 12 (y, con W = 1, también en el 1 y el 5), así que no se sostiene como mejora uniforme.

**Comprobación de fuga indirecta** (`comprobacion_background.py`, semilla 11, W = 1, escenarios 7, 5 y 12). Los archivos de trabajo solo contienen flujos Botnet/Normal, por lo que las ventanas de un host infectado contenían solo flujos botnet. Se evaluaron los mismos flujos etiquetados con la ventana «pura» (sin Background) y con la ventana «real» (calculada sobre todo el archivo original, Background incluido): las diferencias de PR-AUC fueron de 0,000 a 0,008 (p. ej. escenario 7, random forest: 0,996 frente a 0,993). La mejora no depende de esa pureza **en la evaluación**; el entrenamiento sí se hizo con ventanas puras del resto de escenarios. No se comprobó el escenario 8 ni los demás.

**Conclusiones y advertencias.**
1. El contexto del host mejora de forma clara los escenarios que fallaban con solo flujo: 7 (Sogou, 0,51 → 0,99) y 12 (NSIS.ay, 0,74 → 0,99). El mejor resultado global es LR+RF+HGB con W = 5 (PR-AUC 0,985; peor escenario 0,895).
2. **No mejora todo:** Murlo (8) con W = 1 empeora (0,89 → 0,61, con gran variación entre semillas) y los escenarios Rbot 4 y 11 bajan algo (11: 1,000 → 0,95–0,98). En esos casos el comportamiento del host de Rbot no se distingue tan bien como el flujo individual.
3. **Selección con sesgo optimista:** el tamaño de ventana y el modelo se comparan sobre los mismos resultados de «dejar un escenario fuera» en que se evalúan; elegir W = 5 y el ensamble por ser el mejor resultado sobreestima el rendimiento esperado. Se reportan ambas ventanas y todos los modelos por esa razón.
4. **Es otra pregunta:** cada flujo se clasifica por lo que hizo su host de origen en la ventana, no por sí mismo; sirve para alertar sobre un equipo comprometido, no para decidir un flujo aislado. Además es **no causal**: la ventana incluye flujos posteriores al flujo evaluado, así que una detección en línea solo puede darse al cerrar la ventana (1 o 5 minutos de retraso).
5. En CTU-13 los hosts infectados se distinguen bien de los normales (infraestructura de laboratorio de 2011, pocas IP infectadas por escenario); no se ha comprobado que esto se mantenga en otra red.
6. No se probó ninguna otra combinación (otros tamaños de ventana, ponderación o apilamiento), ni el reajuste de Optuna con las variables nuevas, ni la versión de ventana pura de la app (una fila por ventana).


## Correcciones de limitaciones: lo completado, lo parcial y lo no ejecutado

### Completado: intervalos de confianza y corrección de Holm (`docs/validacion-externa/intervalos.py`, `intervalos.json`)
Bootstrap por escenarios (10 000 remuestreos de los 12 escenarios, sobre la PR-AUC media de las 5 semillas). PR-AUC media [IC 95 %]: solo flujo, ensamble LR+RF+HGB 0,918 [0,827; 0,984], random forest 0,906 [0,801; 0,982], HistGB 0,911 [0,829; 0,980]; con contexto de host a 5 minutos, ensamble 0,985 [0,966; 0,998], random forest 0,980 [0,959; 0,995]. Los intervalos se solapan ampliamente. Con Holm sobre 10 comparaciones (híbrido contra solo flujo, mismo modelo) el menor p ajustado es 0,425; entre pares de modelos solo flujo, 0,161. **Ninguna comparación es estadísticamente significativa tras la corrección.** Dos intervalos de la diferencia excluyen el cero por poco (random forest a 5 min: +0,074 [+0,003; +0,173]; ensamble a 5 min: +0,067 [+0,002; +0,160]), pero no resisten Holm. Las conclusiones sobre superioridad de modelos o de variables deben leerse como tendencias.

### Parcial: evaluación realista con Background como normal y sin submuestreo (`fondo.py`; semilla 11; solo escenarios 1, 2 y 3 de 12)
Se evalúa el escenario excluido con todo su tráfico (millones de flujos), tratando el Background como Normal, con el umbral elegido en la validación interna. La corrida se detuvo tras 3 escenarios por su coste de cómputo (`fondo_11_parcial.json`); no hay otras semillas ni los otros 9 escenarios.

| Esc. | Flujos | Bots | PR-AUC solo etiquetados | PR-AUC realista | Sensibilidad | FP sobre Background | Precisión realista |
|---|---|---|---|---|---|---|---|
| 1 Neris | 2 824 132 | 40 961 (1,45 %) | 0,941–0,965 | 0,062–0,260 | 0,76–0,87 | 0,28–0,36 | 0,035–0,042 |
| 2 Neris | 1 807 765 | 20 941 (1,16 %) | 0,986–0,998 | 0,179–0,508 | 0,81–0,93 | 0,33–0,41 | 0,019–0,029 |
| 3 Rbot | 4 705 297 | 26 822 (0,57 %) | 0,994–0,999 | 0,161–0,949 | 0,99–1,00 | 0,25–0,34 | 0,017–0,022 |

(Rangos entre los 5 modelos: regresión logística, random forest, HistGB, XGBoost y LR+RF+HGB.) Lectura: **los resultados sobre flujos etiquetados sobreestiman el rendimiento operativo.** Con el umbral de la validación interna, entre una cuarta parte y dos quintas partes del tráfico Background se marca como botnet (25 000–41 000 alertas por 100 000 flujos) y la precisión queda en el 2–4 %, aunque la sensibilidad se mantiene alta. La PR-AUC realista varía mucho entre modelos (en el escenario 3 llega a 0,95 con HistGB y XGBoost, pero 0,16 con regresión logística), lo que indica que el orden de los puntajes puede ser bueno aunque el umbral no se transfiere: fue elegido sobre datos con otra prevalencia. Un despliegue requeriría fijar el umbral para una tasa de falsos positivos objetivo sobre tráfico real. Advertencias: el Background no es verdad conocida y puede contener tráfico malicioso sin etiquetar o tráfico atípico legítimo; son 3 escenarios con una semilla.

### Implementado y verificado, sin resultados completos: variables de host causales (`causal.py`, `hibrido_causal.py`)
Agregados del host solo con los flujos de su IP en la ventana hasta el flujo actual (sin futuro), 20 variables (se omiten las de *beaconing*). Comprobadas contra un cálculo ingenuo: 150 flujos al azar, 0 discrepancias. La evaluación de la versión causal se detuvo a medias (semilla 22, ventana de 1 minuto, 5 de 12 escenarios; semilla 11, 1 escenario; los JSON parciales están en `causal_{11,22}_parcial.json`) y **no se reporta ningún resultado**: no se sabe si la ventaja del contexto de host se mantiene sin mirar el futuro.

### Preparado y no ejecutado: validación externa en CIC-IDS2017 (`cic.py`)
Se obtuvo `GeneratedLabelledFlows.zip`. El viernes por la mañana contiene 1 966 flujos Bot y 189 067 benignos (1,03 %); los equipos infectados también generan tráfico benigno (p. ej. 192.168.10.9), por lo que es una prueba más exigente que CTU-13. Problemas verificados: marca de tiempo con resolución de minuto (241 valores distintos), sin campo de estado de conexión de Argus, longitudes de carga útil en lugar de bytes totales. Se escribió el protocolo (entrenar con los 12 escenarios CTU-13, probar en CIC con variables comunes) pero **no se ejecutó**. La limitación de «solo CTU-13» sigue abierta.

### Lo que sigue sin hacerse
Validación en un segundo conjunto de datos, comparación con métodos publicados o con líneas base adicionales, reajuste de Optuna (más intentos y para el híbrido), resultados causales, evaluación realista completa (12 escenarios, varias semillas), calibración del umbral para una tasa de falsos positivos objetivo, y la integración en la interfaz del Laboratorio ML. Con lo hecho, la contribución defendible es el **protocolo de validación entre escenarios y el análisis honesto de sus límites** (incluido el hallazgo de que la evaluación solo sobre flujos etiquetados es optimista), no un detector mejor que los existentes.


## Validación externa en CIC-IDS2017 (resultado negativo; semilla 11, solo variables de flujo)

**Diseño** (`docs/validacion-externa/cic.py`, `cic_flow_11.json`, `cic_flow_s11.log`). Se entrena con los 12 escenarios CTU-13 (flujos etiquetados, submuestreo a 2 500 por escenario) y se prueba en un conjunto de otra red y otro exportador de flujos: CIC-IDS2017, viernes por la mañana (`Friday-WorkingHours-Morning`): 191 033 flujos, 1 966 Bot (1,03 %), el resto BENIGN. Se usan solo las variables comunes a ambos formatos (duración, bytes enviados y recibidos, paquetes, bytes por paquete, proporción de salida, bytes y paquetes por segundo, puerto destino, protocolo, clases de puerto); se excluyen `state`, `dir` y `direction`, específicas de Argus. Hiperparámetros: Optuna (10 intentos) con validación interna agrupada por escenarios CTU-13 (4 grupos); umbral por exactitud balanceada sobre las predicciones internas (PR-AUC interna: regresión logística 0,833; random forest 0,875; HistGB 0,875; XGBoost 0,880).

| Modelo | PR-AUC | ROC-AUC | Sensibilidad | Falsos positivos (benignos marcados) | Precisión | Alertas por 100 000 flujos |
|---|---|---|---|---|---|---|
| Referencia (azar) | 0,010 | 0,500 | — | — | 0,010 | — |
| Regresión logística | **0,080** | **0,861** | 0,756 | 0,198 | 0,038 | 20 422 |
| Random forest | 0,019 | 0,717 | 1,000 | 0,585 | 0,017 | 58 884 |
| HistGB | 0,029 | 0,773 | 1,000 | 0,457 | 0,022 | 46 227 |
| XGBoost | 0,023 | 0,751 | 0,756 | 0,314 | 0,024 | 31 894 |
| LR+RF+HGB | 0,045 | 0,811 | 0,771 | 0,274 | 0,028 | 27 905 |

**Resultado.** El detector entrenado en CTU-13 **no se transfiere** a CIC-IDS2017 con estas variables. La PR-AUC es de 0,02 a 0,08 (el azar da 0,010) y la ROC-AUC de 0,72 a 0,86: hay señal por encima del azar, pero insuficiente. Con el umbral heredado de CTU-13 se marca entre el 20 % y el 58 % del tráfico benigno y la precisión queda en el 2–4 %. Los modelos de árboles, los mejores dentro de CTU-13, son los que peor transfieren; la regresión logística (con log y escalado de las variables) es la menos mala. Este resultado contradice cualquier lectura de que el 0,9–1,0 de PR-AUC dentro de CTU-13 sea generalizable a otras redes.

**Advertencias sobre este resultado.** (1) Una sola semilla y una sola variante; no se probó el contexto de host ni la normalización por rangos, que podrían cambiarlo. (2) Las variables no significan lo mismo en los dos formatos: CIC mide longitudes de carga útil y Argus bytes totales, no hay estado de conexión en CIC y la marca de tiempo de CIC tiene resolución de minuto. Parte del fallo puede ser una diferencia de medición y no de comportamiento de botnet; con estos datos no es posible separar ambos efectos. (3) CIC-IDS2017 tiene errores de construcción de flujos y de etiquetado documentados en la literatura; el Bot de ese conjunto es una sola familia (Ares) en una sola red. (4) El umbral se eligió en CTU-13 y no se recalibró para CIC; las métricas independientes del umbral (ROC-AUC, PR-AUC) son las más comparables.

**Consecuencia para el trabajo.** La conclusión defendible es que el protocolo de validación entre escenarios sí detecta fallos de generalización: sobre un conjunto externo el rendimiento cae de 0,9–1,0 a 0,02–0,08 de PR-AUC. Esa es una contribución honesta (resultado negativo y cuantificado) y debe presentarse como tal, no como un detector validado.


### CIC-IDS2017 con contexto causal del host (variante `host`; semilla 11; `cic_host_11.json`, `cic_host_s11.log`)
Se añaden 8 variables causales del host de origen (ventana de 5 minutos; nº de conexiones, destinos y puertos únicos, entropía de puertos y de destinos, proporción TCP/UDP/ICMP), elegidas por no depender del estado de conexión ni de la resolución temporal. Mismo entrenamiento (12 escenarios CTU-13) y mismo conjunto de prueba. PR-AUC interna en CTU-13: regresión logística 0,791; random forest 0,900; HistGB 0,891; XGBoost 0,904.

| Modelo | PR-AUC | ROC-AUC | Sensibilidad | Benignos marcados | Precisión |
|---|---|---|---|---|---|
| Referencia (azar) | 0,010 | 0,500 | — | — | 0,010 |
| Regresión logística | 0,0095 | 0,477 | 0,260 | 0,296 | 0,009 |
| Random forest | 0,014 | 0,650 | 1,000 | 0,967 | 0,011 |
| HistGB | 0,030 | 0,665 | 1,000 | 0,861 | 0,012 |
| XGBoost | 0,013 | 0,599 | 1,000 | 0,860 | 0,012 |
| LR+RF+HGB | 0,013 | 0,602 | 1,000 | 0,967 | 0,011 |

**Resultado.** El contexto del host **empeora** la transferencia a CIC-IDS2017: la ROC-AUC pasa de 0,72–0,86 (solo flujo) a 0,48–0,67, es decir, entre el azar y una señal muy débil; la regresión logística queda incluso por debajo del azar (0,477). Los umbrales heredados de CTU-13 marcan entre el 86 % y el 97 % del tráfico benigno (el umbral de HistGB es degenerado, 2,6·10⁻⁸). Las variables de host que ayudan dentro de CTU-13 (escenarios 7 y 12) no se trasladan a una red con otra estructura: en CIC los equipos infectados también generan tráfico benigno, hay NAT interno y el tamaño y la actividad típicos de un host distan de los de las capturas CTU-13.

**Advertencias.** Una sola semilla; la marca de tiempo de CIC tiene resolución de minuto, lo que degrada el orden de los flujos dentro de la ventana causal; sin recalibrar el umbral; una sola familia de botnet en CIC. Con estos datos tampoco se puede separar el efecto de comportamiento del de diferencias de medición entre Argus y CIC.

**Conclusión de la validación externa.** Ni con variables de flujo (PR-AUC 0,02–0,08) ni con contexto del host (0,01–0,03) el detector entrenado en CTU-13 funciona en CIC-IDS2017. El mejor resultado dentro de CTU-13 (ensamble con host, PR-AUC 0,985) no es evidencia de utilidad en otra red. Cualquier afirmación del trabajo debe acotarse a «dentro de CTU-13, entre escenarios» y declarar este resultado negativo como principal limitación de generalización.
