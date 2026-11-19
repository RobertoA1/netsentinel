"""Contenido del articulo (espanol). Las cifras de tablas se calculan desde datos.json (analisis.py); las del texto se verifican en verificar.py.
Marcado en linea: *cursiva*, ^superindice^ (sin negritas). Bloques: ('h1'|'h2', texto, clave), ('p1'|'p', texto), ('fig', archivo, ancho_cm, leyenda, clave),
('tabla_ref', tabla, clave) con tabla = ('tabla', leyenda, encabezado, filas, anchos_cm, opciones).
Referencias cruzadas con fichas [[S:clave]] (seccion), [[T:clave]] (tabla), [[F:clave]] (figura): se numeran solas segun el orden de aparicion."""
import json, re

D = json.load(open("datos.json"))
NB = "\u00a0"
def f(x, d=3): return f"{x:.{d}f}".replace(".", ",")
def pm(m, s, d=3): return f"{f(m, d)} ± {f(s, d)}"
def n(x): return f"{x:,}".replace(",", NB)
ESC = D["escenarios"]; FAM = {int(k): v for k, v in D["familia"].items()}
FL, EN, H1, H5 = D["flujo"], D["ensambles"], D["host_W1"], D["host_W5"]
NOMBRE = {"dummy": "Dummy", "logreg": "RL", "random_forest": "RF", "hist_gb": "HGB", "xgboost": "XGB", "RF+HGB": "RF+HGB", "LR+RF+HGB": "RL+RF+HGB", "RF+HGB+XGB": "RF+HGB+XGB", "los 4": "Los cuatro"}
IV = D["intervalos"]; INT = {r["comparacion"]: r for r in IV["diferencias"] + IV["pares_modelos"]}
NA = "n. a."

TITULO = "Validación entre escenarios para la detección de tráfico botnet en CTU-13: protocolo anidado, contexto del host y límites de generalización"
TITLE_EN = "Cross-Scenario Validation for Botnet Traffic Detection on CTU-13: Nested Protocol, Host Context and Generalization Limits"
CORTO = "Validación entre escenarios para la detección de tráfico botnet en CTU-13…"

RESUMEN = ("Es habitual evaluar detectores de botnets con particiones que mezclan flujos de una misma captura. Esa práctica no indica si el detector funcionará con otra captura o con otra familia de botnet. "
           "Este trabajo toma el escenario completo como unidad de partición y aplica un protocolo que lo deja fuera: la búsqueda de hiperparámetros es anidada y agrupada por escenario, el umbral se fija solo con datos internos "
           f"y el análisis estadístico se hace entre escenarios. El protocolo se ejecuta sobre 12 escenarios de CTU-13 ({n(678636)} flujos etiquetados) con cuatro clasificadores, ensambles por voto suave, variables de contexto del host y cinco semillas, "
           "y se documentan sus pasos de entrenamiento, su parametrización, sus condiciones iniciales y sus condiciones de parada. La PR-AUC media entre escenarios va de 0,886 a 0,918 (referencia trivial: 0,383), "
           "pero ninguna diferencia por pares entre modelos resiste la corrección de Holm. El contexto del host eleva la media a 0,985 con una ventana de 5 minutos que incluye flujos posteriores al evaluado, de modo que no sirve en línea. "
           "Dos pruebas de realismo moderan ese optimismo. Si el tráfico Background se trata como normal, se marca como botnet entre el 25 % y el 41 % de él, y un detector entrenado con CTU-13 no se transfiere a CIC-IDS2017 "
           "(PR-AUC de 0,02 a 0,08 frente a 0,010 del azar). Lo que se aporta es el protocolo y la medición de sus límites; un detector listo para operar queda fuera del alcance.")
PALABRAS = " detección de botnets, CTU-13, validación por escenarios, validación cruzada anidada, fuga de información, ensambles, contexto del host"
CATEGORIAS = " I.2.6, I.5.2, C.2.0, C.2.3, K.6.5"

# ---------------------------------------------------------------- tablas
T1 = [("1", "Neris", 71335, "57,4"), ("2", "Neris", 30052, "69,7"), ("3", "Rbot", 143553, "18,7"), ("4", "Rbot", 27837, "9,3"), ("5", "Virut", 5577, "16,2"), ("6", "Menti", 12119, "38,2"),
      ("7", "Sogou", 1739, "3,6"), ("8", "Murlo", 78903, "7,8"), ("9", "Neris", 214943, "86,1"), ("11", "Rbot", 10882, "75,0"), ("12", "NSIS.ay", 9793, "22,1"), ("13", "Virut", 71903, "55,6")]
assert sum(r[2] for r in T1) == 678636
tab1_rows = [[a, b, n(c), d] for a, b, c, d in T1] + [["Total", "", n(678636), ""]]
tab1 = ("tabla", "Tabla [[T:esc]]: Escenarios de CTU-13 usados. Flujos con etiqueta Botnet o Normal; el tráfico Background no se cuenta. Prevalencia = porcentaje de Botnet entre los flujos etiquetados, que es también la PR-AUC de la referencia Dummy. "
        "Elaboración propia a partir de los archivos binetflow.", ["Esc.", "Familia", "Flujos etiquetados", "Botnet (%)"], tab1_rows, [1.6, 3.0, 4.2, 3.0], {"al": "cccc", "negrita_ultima": True})

tab2 = ("tabla", "Tabla [[T:esp]]: Hiperparámetros buscados por modelo (rango por defecto del Laboratorio ML; «log» = escala logarítmica). Parámetros fijos: regresión logística, solver liblinear y 2 000 iteraciones como máximo; "
        "XGBoost, 300 árboles y tree_method hist; HistGB sin parada temprana.", ["Modelo", "Parámetros y rangos"],
        [["RL", "C: 10^-3^ a 10^2^ (log); penalty: {L2, L1}; class_weight: {ninguno, balanced}"],
         ["RF", "n_estimators: 200 a 800 (paso 100); max_depth: 4 a 30; min_samples_leaf: 1 a 20 (log); max_features: {sqrt, log2, 0,5}; class_weight: {ninguno, balanced, balanced_subsample}"],
         ["HGB", "learning_rate: 0,01 a 0,3 (log); max_iter: 100 a 500; max_leaf_nodes: 8 a 64; l2_regularization: 10^-6^ a 10 (log); min_samples_leaf: 5 a 100; class_weight: {ninguno, balanced}"],
         ["XGB", "eta: 0,01 a 0,3 (log); max_depth: 2 a 10; subsample: 0,5 a 1; colsample_bytree: 0,4 a 1; min_child_weight: 1 a 20 (log); gamma: 0 a 5; reg_lambda: 0,01 a 20 (log); scale_pos_weight: 1 a 50 (log)"]],
        [1.6, 10.6], {"al": "lj", "dividir": True})

tab3 = ("tabla", "Tabla [[T:par]]: Parámetros del protocolo de entrenamiento y validación.", ["Parámetro", "Valor"],
        [["Escenarios", "12 (1 a 9, 11, 12 y 13); el 10 no se usa"],
         ["Flujos por escenario", "máximo 2 500, submuestreo estratificado; el escenario 7 conserva sus 1 739"],
         ["Flujos por experimento", "29 239 (los 12 escenarios ya submuestreados)"],
         ["Variables", "16 de flujo; 23 más de contexto del host; 13 comunes con CIC-IDS2017"],
         ["Partición externa", "un escenario excluido por vez (12 particiones)"],
         ["Partición interna", "4 grupos de escenarios (3, 3, 3 y 2) con rotación completa"],
         ["Modelos", "Dummy, RL, RF, HGB y XGB; 4 ensambles por voto suave"],
         ["Muestreador", "TPE de Optuna 5.0.0 con n_startup_trials = 10"],
         ["Podador", "MedianPruner por defecto (n_startup_trials = 5, n_warmup_steps = 0)"],
         ["Intentos de búsqueda", "10 por modelo, escenario excluido y semilla"],
         ["Objetivo de la búsqueda", "maximizar la PR-AUC media por escenario predicho"],
         ["Umbral", "199 cuantiles (del 1 % al 99 %) de las puntuaciones internas; el de máxima exactitud balanceada"],
         ["Semillas", "11, 22, 33, 44 y 55"],
         ["Evaluaciones", "5 modelos × 12 escenarios × 5 semillas = 300"]],
        [4.0, 8.2], {"al": "ll", "dividir": True})

tab4 = ("tabla", "Tabla [[T:ini]]: Condiciones iniciales de cada experimento (una combinación de semilla, escenario excluido y modelo).", ["Elemento", "Estado inicial"],
        [["Datos", "Escenarios en formato binetflow con flujos Botnet y Normal; el preprocesamiento aún no está ajustado (se ajusta dentro de cada pliegue)"],
         ["Submuestreo", "Generador de NumPy inicializado con la semilla y aplicado a los escenarios en orden; al menos un flujo por clase"],
         ["Escenario de prueba", "Apartado antes de cualquier ajuste; no interviene en la búsqueda, en el umbral ni en el reentrenamiento"],
         ["Grupos internos", "Permutación de los 11 escenarios de entrenamiento con un generador inicializado con la semilla; reparto cíclico en 4 grupos"],
         ["Estudio de Optuna", "Nuevo, sin historial ni arranque en caliente; muestreador TPE con la semilla; dirección de maximización"],
         ["Primeros intentos", "Los 10 primeros intentos se muestrean al azar del espacio de la Tabla [[T:esp]]; no se parte de hiperparámetros por defecto"],
         ["Modelos", "random_state igual a la semilla; los hiperparámetros que no se buscan toman los valores fijos de la Tabla [[T:esp]]"],
         ["Umbral", "No existe hasta terminar la búsqueda (Dummy usa 0,5)"],
         ["Registro", "Un archivo JSON por semilla; al reanudar se omiten las combinaciones ya completadas"]],
        [3.2, 9.0], {"al": "ll", "dividir": True})

tab5 = ("tabla", "Tabla [[T:parada]]: Condiciones de parada por componente. Ningún componente usa parada temprana: todos terminan por un límite fijo o por convergencia numérica.", ["Componente", "Criterio de parada", "Valor"],
        [["Protocolo completo", "Se agotan las combinaciones pendientes (semilla, escenario, modelo)", "300 evaluaciones; reanudable"],
         ["Búsqueda de Optuna", "Número de intentos", "10; sin tiempo límite (timeout = None)"],
         ["Poda de intentos", "MedianPruner", "Sin efecto: el objetivo no informa valores intermedios"],
         ["Validación interna", "Rotación completa de los grupos", "4 ajustes por intento"],
         ["RL (liblinear)", "Convergencia o límite de iteraciones", "tol = 0,0001 (por defecto) o 2 000 iteraciones"],
         ["RF", "Número fijo de árboles; cada árbol crece hasta max_depth, min_samples_leaf o nodos puros", "n_estimators: 200 a 800 (buscado)"],
         ["HGB", "Límite de iteraciones, sin parada temprana", "max_iter: 100 a 500 (buscado); early_stopping = False"],
         ["XGB", "Número fijo de rondas, sin parada temprana", "300 rondas; sin early_stopping_rounds"],
         ["Umbral", "Recorrido completo de los candidatos", "199 cuantiles"],
         ["Dummy", "No hay entrenamiento iterativo", "Umbral 0,5"]],
        [2.7, 5.6, 3.9], {"al": "lll", "dividir": True})

tab_uno = ("tabla", "Tabla [[T:uno]]: PR-AUC al pasar de un escenario a varios (umbral independiente). Fila 1: partición de prueba del escenario 11 con CV anidada 5×3 por bloques de 10 s (3 semillas). Filas 2 y 3: entrenamiento en un escenario y prueba en otro. "
        "Fila 4: diseño previo con 4 escenarios (9, 11, 12, 13; 6 puntos de búsqueda, tope de 4 000 flujos, 3 semillas). Fila 5: 11 escenarios de entrenamiento, 5 semillas (Tabla [[T:pes]]).",
        ["Situación", "Referencia", "RL", "RF", "HGB", "XGB"],
        [["Dentro del esc. 11 (bloques de 10 s)", "0,733", "0,995", "0,996", "0,995", "0,996"],
         ["Entrena 11, prueba 12", "0,221", "0,647", "0,776", "0,694", "0,686"],
         ["Entrena 12, prueba 11", "0,750", "0,988", "0,746", "0,697", "0,769"],
         ["Prueba 11; entrena 9, 12, 13 (sin Rbot)", "0,750", "1,000", "0,768", "0,691", "0,747"],
         ["Prueba 11; entrena los otros 11 (con Rbot 3 y 4)", "0,750", "0,999", "1,000", "0,999", "1,000"]],
        [4.9, 1.6, 1.15, 1.15, 1.15, 1.15], {"al": "lcccccc"})
# verificacion cruzada de la fila 5 contra datos.json
_i11 = ESC.index(11)
for k, v in (("logreg", "0,999"), ("random_forest", "1,000"), ("hist_gb", "0,999"), ("xgboost", "1,000")): assert f(FL[k]["per_esc_mean"][_i11]) == v, (k, FL[k]["per_esc_mean"][_i11])

def t4_rows():
    rows = []
    for i, e in enumerate(ESC):
        rows.append([str(e), FAM[e], f(D["prevalencia"][str(e)])] + [pm(FL[m]["per_esc_mean"][i], FL[m]["per_esc_sd"][i]) for m in ("logreg", "random_forest", "hist_gb", "xgboost")])
    return rows
tab_pes = ("tabla", "Tabla [[T:pes]]: PR-AUC en el escenario excluido (media ± desviación entre 5 semillas). Dummy = prevalencia. Negrita: mejor media del escenario.", ["Esc.", "Familia", "Dummy", "RL", "RF", "HGB", "XGB"], t4_rows(),
        [0.9, 1.6, 1.3, 2.1, 2.1, 2.1, 2.1], {"al": "ccccccc", "mejor_fila": True})

def t5_rows():
    rows = [["Dummy", f(0.383), f(D["flujo"]["dummy"]["pr_median"]), f"{f(D['flujo']['dummy']['pr_worst'])} (7)", f(0.5), NA, NA, f(0.5), NA]]
    for m in ("logreg", "random_forest", "hist_gb", "xgboost"):
        s = FL[m]; rows.append([NOMBRE[m], pm(s["pr_mean"], s["pr_sd_seeds"]), f(s["pr_median"]), f"{f(s['pr_worst'])} ({s['pr_worst_esc']})", f(s["roc"]), f(s["recall"]), f(s["precision"]), f(s["bacc"]), f(D["rango8"][m], 2)])
    for m in ("RF+HGB", "LR+RF+HGB", "RF+HGB+XGB", "los 4"):
        s = EN[m]; rows.append([NOMBRE[m], pm(s["pr_mean"], s["pr_sd_seeds"]), f(s["pr_median"]), f"{f(s['pr_worst'])} ({s['pr_worst_esc']})", f(s["roc"]), f(s["recall"]), f(s["precision"]), f(s["bacc"]), f(D["rango8"][m], 2)])
    return rows
tab_res = ("tabla", "Tabla [[T:res]]: Resumen entre los 12 escenarios (macropromedio). PR-AUC: media ± desviación entre las 5 medias por semilla; mediana y peor escenario (entre paréntesis) sobre las medias por escenario. "
        "Sensibilidad, precisión y exactitud balanceada con el umbral interno. Rango medio entre los 8 modelos (1 = mejor).",
        ["Modelo", "PR-AUC", "Mediana", "Peor esc.", "ROC-AUC", "Sens.", "Prec.", "Ex. bal.", "Rango"], t5_rows(), [2.2, 2.0, 1.3, 1.5, 1.2, 0.95, 0.95, 1.05, 1.05], {"al": "lcccccccc", "separador_antes": [5]})

def t6_rows():
    rows = []
    for m in ("logreg", "random_forest", "hist_gb", "xgboost", "LR+RF+HGB"):
        a = EN[m] if m == "LR+RF+HGB" else FL[m]; b, c = H1[m], H5[m]
        rows.append([NOMBRE[m], pm(a["pr_mean"], a["pr_sd_seeds"]), pm(b["pr_mean"], b["pr_sd_seeds"]), pm(c["pr_mean"], c["pr_sd_seeds"]), f"{f(a['pr_worst'])} / {f(b['pr_worst'])} / {f(c['pr_worst'])}"])
    return rows
tab_host = ("tabla", "Tabla [[T:hostt]]: PR-AUC media entre escenarios con variables de flujo y con contexto del host no causal (ventana W; media ± desviación entre 5 semillas) y PR-AUC del peor escenario (solo flujo / W = 1 / W = 5). "
        "Hiperparámetros reutilizados de la búsqueda con flujos.", ["Modelo", "Solo flujo", "Flujo + host, W = 1 min", "Flujo + host, W = 5 min", "Peor escenario"], t6_rows(), [2.2, 2.0, 2.3, 2.3, 3.4], {"al": "lcccc"})

def fmtd(r, d=3): return f"{r['dif']:+.{d}f}".replace(".", ",") + f" [{r['ic'][0]:+.{d}f}; {r['ic'][1]:+.{d}f}]".replace(".", ",")
def t7_rows():
    sel = [("flujo | logreg - LR+RF+HGB", "Solo flujo: RL menos RL+RF+HGB"), ("flujo | random_forest - xgboost", "Solo flujo: RF menos XGB"), ("flujo | logreg - hist_gb", "Solo flujo: RL menos HGB"),
           ("host W=5 - flujo | random_forest", "W = 5 menos solo flujo: RF"), ("host W=5 - flujo | LR+RF+HGB", "W = 5 menos solo flujo: RL+RF+HGB"), ("host W=1 - flujo | random_forest", "W = 1 menos solo flujo: RF"),
           ("host W=1 - flujo | xgboost", "W = 1 menos solo flujo: XGB"), ("host W=5 - flujo | logreg", "W = 5 menos solo flujo: RL")]
    return [[lab, fmtd(INT[k]), f(INT[k]["p"]), f(INT[k]["p_holm"])] for k, lab in sel]
tab_par2 = ("tabla", "Tabla [[T:pareadas]]: Comparaciones pareadas entre escenarios (diferencia de PR-AUC media por escenario, IC 95 % por bootstrap sobre escenarios, p de Wilcoxon exacto bilateral y p ajustado por Holm). "
        "Cada bloque pertenece a una familia de 10 comparaciones. Se muestran las de menor p ajustado y algunas de interés.", ["Comparación", "Diferencia [IC 95 %]", "p", "p Holm"], t7_rows(), [4.6, 4.2, 1.7, 1.7], {"al": "lccc", "separador_antes": [3]})

fo = D["fondo"]
def rg(es, k, d=3, sc=1.0):
    v = [r[k] * sc for r in fo if r["held_out"] == es]; return f"{f(min(v), d)} a {f(max(v), d)}"
def t8_rows():
    rows = []
    for e in (1, 2, 3):
        r0 = next(r for r in fo if r["held_out"] == e)
        rows.append([f"{e} {FAM[e]}", f"{n(r0['n_flujos'])} ({f(100 * r0['prevalencia'], 2)} %)", rg(e, "pr_auc_solo_etiquetados", 2), rg(e, "pr_auc_realista", 2), rg(e, "recall", 2), rg(e, "fpr_background", 1, 100), rg(e, "precision_realista", 1, 100)])
    return rows
tab_bg = ("tabla", "Tabla [[T:bg]]: Evaluación con todo el tráfico del escenario excluido (sin submuestreo), con el Background tratado como Normal (semilla 11; rango entre los cinco modelos). PR-AUC etiq. = calculada solo con los flujos etiquetados. "
        "Umbral fijado en la validación interna.", ["Esc.", "Flujos (% Botnet)", "PR-AUC etiq.", "PR-AUC realista", "Sens.", "Background marcado (%)", "Prec. (%)"], t8_rows(), [1.4, 2.8, 1.7, 1.7, 1.5, 2.0, 1.1], {"al": "lrccccc"})

cf = {r["model"]: r for r in D["cic_flow"]}; ch = {r["model"]: r for r in D["cic_host"]}
def t9_rows():
    rows = [["Referencia (azar)", f(cf["logreg"]["prevalencia"]), f(0.5), NA, NA, NA, f(cf["logreg"]["prevalencia"]), f(0.5), NA]]
    for m in ("logreg", "random_forest", "hist_gb", "xgboost", "LR+RF+HGB"):
        a, b = cf[m], ch[m]
        rows.append([NOMBRE[m], f(a["pr_auc"]), f(a["roc_auc"]), f(a["recall"], 2), f(100 * a["fpr"], 1) + " %", f(a["precision"]), f(b["pr_auc"]), f(b["roc_auc"]), f(100 * b["fpr"], 1) + " %"])
    return rows
tab_cic = ("tabla", "Tabla [[T:cic]]: Entrenamiento con los 12 escenarios de CTU-13 y prueba en CIC-IDS2017 (viernes por la mañana: 191 033 flujos, 1 966 Bot, 1,03 %; semilla 11). FP = porcentaje de flujos benignos marcados como Bot con el umbral heredado de CTU-13.",
        ["Modelo", "PR-AUC", "ROC-AUC", "Sens.", "FP", "Prec.", "PR-AUC", "ROC-AUC", "FP"], t9_rows(), [2.6, 1.2, 1.3, 1.0, 1.2, 1.1, 1.2, 1.3, 1.2],
        {"al": "lcccccccc", "grupos": [("", 1), ("Solo variables de flujo", 5), ("Flujo + host (causal)", 3)]})

# ---------------------------------------------------------------- cuerpo
B = []
def add(*x): B.append(x)

# ===== 1. Introducción
add("h1", "Introducción", "intro")
add("p1", "Los firewalls y los sistemas de detección de intrusiones (IDS) generan más eventos de los que un analista puede revisar, y las reglas fijas pasan por alto comportamientos como el *beaconing* de las botnets. "
    "Una respuesta frecuente es aplicar aprendizaje automático a los flujos de red [García, 14; Shinan, 21; Velasco-Mata, 21]. CTU-13 [García, 14] es uno de los conjuntos públicos más usados para ello. "
    "Reúne 13 capturas, llamadas escenarios, con tráfico de siete familias de botnet mezclado con tráfico normal y de fondo, y con una etiqueta por flujo.")
add("p", "Queda por saber si un detector entrenado con unas capturas funcionará en otras. La literatura señala sesgos de muestreo y ajuste con datos de prueba en el aprendizaje automático aplicado a seguridad [Sommer, 10; Arp, 22], "
    "y presenta la fuga de información entre entrenamiento y evaluación como un problema general [Kapoor, 23]. Cuando los datos tienen estructura, la validación debe dividir por bloques que la respeten [Roberts, 17]. "
    "En los flujos de red esa estructura es, ante todo, el escenario: sus flujos comparten hosts, infraestructura, familia de botnet y periodo de captura. Una partición aleatoria por flujos, o por bloques de tiempo dentro de un escenario, "
    "tampoco mide la generalización a otro escenario. No revisamos de forma sistemática cuántos estudios sobre CTU-13 siguen esa práctica; su efecto se documenta con datos propios en la Sección [[S:r_uno]].")
add("p", "Este trabajo toma el escenario como unidad de partición y hace cuatro contribuciones. (C1) Un protocolo que deja fuera un escenario completo, con búsqueda de hiperparámetros anidada y agrupada por escenario y con el umbral de decisión fijado "
    "solo con datos internos. Se ejecuta sobre 12 escenarios de CTU-13, cuatro clasificadores, ensambles por voto suave y cinco semillas, y se describe con sus pasos de entrenamiento, su parametrización, sus condiciones iniciales y sus condiciones de parada. "
    "(C2) Una cuantificación de la incertidumbre con intervalos de confianza por *bootstrap* sobre escenarios y pruebas con corrección de Holm; con 12 escenarios, ninguna diferencia por pares entre modelos resulta significativa. "
    "(C3) Un estudio de variables de contexto del host, con la salvedad de que la versión evaluada usa información posterior al flujo. "
    "(C4) Dos pruebas de realismo, una evaluación con el tráfico *Background* tratado como normal y una validación externa en CIC-IDS2017, cuyos resultados negativos delimitan lo que puede afirmarse.")
add("p", "No se propone un detector que supere el estado del arte ni se afirma utilidad operativa. El alcance es solo CTU-13, de modo que toda conclusión vale dentro de CTU-13 y entre escenarios, "
    "y el resultado negativo en CIC-IDS2017 se presenta como la principal limitación de generalización. La Sección [[S:rel]] resume el trabajo relacionado; la Sección [[S:met]] describe los datos, el entrenamiento y el análisis; "
    "la Sección [[S:res]] presenta los resultados; la Sección [[S:dis]] los discute junto con las amenazas a la validez, y la Sección [[S:con]] concluye y plantea el trabajo futuro.")

# ===== 2. Trabajo relacionado
add("h1", "Trabajo relacionado", "rel")
add("h2", "Detección de botnets con aprendizaje automático sobre flujos", "rel1")
add("p1", "García et al. [García, 14] presentaron CTU-13 y compararon métodos de detección de botnets sobre sus escenarios, con una metodología y un error de evaluación propios. Estudios posteriores aplican selección de variables y árboles de decisión [Velasco-Mata, 21], "
    "ensambles con selección híbrida de variables [Hossain, 23] y análisis en ventanas de un segundo [Velasco-Mata, 23]. Shinan et al. [Shinan, 21] revisan la detección de botnets con aprendizaje automático en redes definidas por software, "
    "y Oškera et al. [Oškera, 25] aprovechan los patrones periódicos del tráfico de mando y control, una idea cercana a las variables de regularidad temporal de la Sección [[S:host]]. "
    "No se compara con estos métodos porque sus métricas y protocolos difieren de los de este trabajo, cuyo propósito es el protocolo de validación.")
add("h2", "Evaluación sin fuga y desplazamiento de distribución", "rel2")
add("p1", "Sommer y Paxson [Sommer, 10] explican por qué evaluar la detección de intrusiones con aprendizaje automático es más difícil que en otras aplicaciones, y Arp et al. [Arp, 22] catalogan errores recurrentes, entre ellos el sesgo de muestreo y el espionaje de datos. "
    "Kapoor y Narayanan [Kapoor, 23] documentan la fuga de información como causa de irreproducibilidad en numerosos campos. Para datos con estructura, Roberts et al. [Roberts, 17] recomiendan dividir por bloques que respeten la dependencia. "
    "Cawley y Talbot [Cawley, 10] muestran el sesgo que aparece al seleccionar modelos con la misma validación con la que se informa su rendimiento, lo que motiva la validación anidada, y Bates et al. [Bates, 24] estudian qué estima realmente la validación cruzada y con qué incertidumbre. "
    "Sobre la generalización en IDS, Cantone et al. [Cantone, 24] hacen un estudio entre conjuntos de datos y Verkerken et al. [Verkerken, 22] la abordan con técnicas no supervisadas. "
    "Engelen et al. [Engelen, 21] documentan errores de construcción de flujos y de etiquetado en CIC-IDS2017 [Sharafaldin, 18], y Sarhan et al. [Sarhan, 22] proponen un conjunto estándar de variables para homogeneizar conjuntos de datos. "
    "El desplazamiento de distribución entre el entrenamiento y el uso es un problema general [Quiñonero-Candela, 08].")
add("h2", "Comparación estadística entre clasificadores", "rel3")
add("p1", "Demšar [Demšar, 06] recomienda comparar clasificadores sobre varios conjuntos de datos con la prueba de Friedman [Friedman, 37] y la prueba de rangos con signo de Wilcoxon [Wilcoxon, 45], con la corrección de Holm [Holm, 79] para comparaciones múltiples. "
    "Aquí los escenarios cumplen la función de los conjuntos de datos, y los intervalos de confianza se obtienen por *bootstrap* [Efron, 79] remuestreando escenarios.")

# ===== 3. Materiales y métodos
add("h1", "Materiales y métodos", "met")
add("h2", "Datos", "datos")
add("p1", "Se usan 12 de los 13 escenarios de CTU-13 [García, 14] en formato *binetflow*: flujos bidireccionales exportados con Argus y etiquetados como Background, Normal o Botnet. Se omite el escenario 10 (Rbot) porque la copia disponible solo publica "
    "capturas de paquetes y NetFlow unidireccional, sin *binetflow* etiquetado. Los flujos Background, millones de registros sin etiqueta fiable, quedan fuera del entrenamiento y de la evaluación principal; solo se usan en la evaluación de la Sección [[S:fondo]]. "
    "La Tabla [[T:esc]] resume los escenarios: 678 636 flujos etiquetados y una prevalencia de Botnet entre 3,6 % y 86,1 %, es decir, un factor de 24 entre el escenario más desbalanceado y el menos. "
    "Las familias se reparten de forma desigual. Neris (escenarios 1, 2 y 9), Rbot (3, 4 y 11) y Virut (5 y 13) tienen varios escenarios; Menti, Sogou, Murlo y NSIS.ay tienen uno cada una. "
    "El escenario 7 reúne solo 1 739 flujos, 63 de ellos Botnet.")
add("tabla_ref", tab1, "esc")
add("p", "Para que ningún escenario domine el entrenamiento (el 9 aporta 214 943 flujos, unas 124 veces los del 7), cada escenario se submuestrea de forma estratificada a un máximo de 2 500 flujos por semilla, y el 7 conserva todos los suyos. "
    "El submuestreo mantiene la prevalencia de cada escenario y también se aplica al escenario de prueba, de modo que cada experimento usa 29 239 flujos. La evaluación sin submuestreo se describe en la Sección [[S:fondo]].")
add("h2", "Variables y preprocesamiento", "vars")
add("p1", "Cada flujo se describe con 16 variables (versión 1.0.0 de la especificación del Laboratorio ML de NetSentinel): diez numéricas (duración, bytes enviados y recibidos, bytes totales, paquetes, bytes por paquete, proporción de bytes salientes, "
    "bytes y paquetes por segundo y puerto de destino) y seis categóricas (protocolo, estado de la conexión, sentido del flujo, dirección de red y clase de puerto de destino y de origen). "
    "Quedan prohibidas como variables las direcciones IP, la marca de tiempo absoluta, los identificadores, el escenario y la etiqueta. "
    "El preprocesamiento forma parte del *pipeline* y se ajusta solo con el entrenamiento de cada pliegue: imputación por mediana; para la regresión logística, logaritmo log(1+x) y estandarización de las ocho variables de volumen y ritmo; "
    "y codificación *one-hot* de las categóricas, con las categorías de menos de 20 apariciones agrupadas.")
add("h2", "Modelos", "modelos")
add("p1", "Se comparan cinco modelos. Dummy predice la prevalencia del entrenamiento; su PR-AUC en un escenario coincide con la prevalencia de ese escenario y sirve de referencia. Los otros cuatro son la regresión logística (RL, solver liblinear), "
    "el random forest (RF) [Breiman, 01], el gradient boosting de histogramas (HGB), ambos de scikit-learn [Pedregosa, 11], y XGBoost (XGB) [Chen, 16]. HGB se entrena sin parada temprana y XGB con 300 árboles fijos. "
    "El desbalance de clases se trata con pesos (*class_weight* o *scale_pos_weight*), cuya elección entra en la búsqueda y usa solo datos de entrenamiento. Los hiperparámetros buscados y sus rangos se describen en la Sección [[S:param]].")
add("h2", "Flujo de entrenamiento y validación", "flujo")
add("p1", "El entrenamiento sigue una validación dejando un escenario fuera (*leave-one-scenario-out*) con búsqueda de hiperparámetros anidada. La Figura [[F:part]] muestra un ejemplo de partición y la Figura [[F:flujo]] resume los pasos. "
    "Para cada semilla, cada modelo y cada uno de los 12 escenarios se procede así. (i) Se submuestrea cada escenario (Sección [[S:datos]]) y se aparta el escenario excluido como prueba; no participa en ningún ajuste. "
    "(ii) Los 11 escenarios restantes se reparten al azar en 4 grupos de escenarios (de 3, 3, 3 y 2). "
    "(iii) Optuna [Akiba, 19] evalúa 10 combinaciones de hiperparámetros. Cada una se valora con validación interna agrupada: se entrena con tres grupos, se predice cada escenario del cuarto y se rota; el objetivo es la PR-AUC media por escenario predicho. "
    "(iv) Con la mejor combinación se reconstruyen las predicciones internas y con ellas se fija el umbral (Sección [[S:umbral]]). "
    "(v) El modelo se reentrena con los 11 escenarios y se evalúa una sola vez en el escenario de prueba. "
    "(vi) El procedimiento se repite para los 12 escenarios, los cinco modelos y las cinco semillas.")
add("fig", "fig1_particion.png", 9.6, "Figura [[F:part]]: Ejemplo de partición con la semilla 11 y el escenario 7 excluido; los grupos G1 a G4 son los que resultan de esa semilla.", "part")
add("fig", "fig2_flujo.png", 12.0, "Figura [[F:flujo]]: Flujo de entrenamiento y validación de un modelo para un escenario excluido k y una semilla. Los recuadros laterales resumen la parametrización, las condiciones iniciales y las condiciones de parada, que detallan las Tablas [[T:par]] a [[T:parada]].", "flujo")
add("p", "La agrupación interna también es por escenario. Por eso ni la búsqueda ni el umbral ven flujos del escenario evaluado, y ningún escenario aparece a la vez en el entrenamiento y en la validación. "
    "El resultado de un escenario es la media de sus cinco semillas. En total hay 5 × 12 × 5 = 300 evaluaciones, incluido Dummy.")
add("h2", "Parametrización", "param")
add("p1", "La Tabla [[T:esp]] recoge los hiperparámetros buscados y sus rangos, que son los valores por defecto del Laboratorio ML de NetSentinel. Lo que no se busca queda fijo: la regresión logística usa el solver liblinear con 2 000 iteraciones como máximo, "
    "XGBoost usa 300 árboles con tree_method hist y HGB no usa parada temprana. La Tabla [[T:par]] reúne el resto de los parámetros del protocolo.")
add("tabla_ref", tab2, "esp")
add("tabla_ref", tab3, "par")
add("h2", "Condiciones iniciales", "inic")
add("p1", "Cada experimento arranca de un estado que la semilla determina por completo (Tabla [[T:ini]]). La semilla (11, 22, 33, 44 o 55) controla el submuestreo, el sorteo de grupos, el muestreador de Optuna y los modelos. "
    "El estudio de Optuna empieza vacío, sin historial ni hiperparámetros previos. El muestreador TPE [Bergstra, 11] de Optuna 5.0.0 comienza con 10 puntos de arranque (*n_startup_trials* = 10) muestreados al azar; "
    "con 10 intentos en total, el modelo bayesiano nunca interviene y la búsqueda equivale a una búsqueda aleatoria de 10 puntos [Bergstra, 12]. "
    "Lo detectamos al preparar este manuscrito. Los resultados siguen siendo una evaluación válida entre escenarios, pero el espacio de hiperparámetros se exploró de forma muy ligera (Sección [[S:d_amen]]).")
add("tabla_ref", tab4, "ini")
add("h2", "Condiciones de parada", "parada")
add("p1", "Ningún componente del entrenamiento se detiene por falta de mejora (Tabla [[T:parada]]). La búsqueda termina al completar 10 intentos y no tiene tiempo límite. Se configuró el podador MedianPruner por defecto, "
    "pero el objetivo no informaba resultados intermedios y por eso nunca podó un intento. Cada modelo se detiene por un límite fijo: la regresión logística, por convergencia de liblinear (tolerancia 0,0001) o por sus 2 000 iteraciones; "
    "RF, por el número de árboles de cada intento; HGB, por *max_iter* sin parada temprana; y XGB, por sus 300 rondas. El protocolo completo termina al agotar las 300 evaluaciones. "
    "No se completó una comparación con 30 intentos por búsqueda; queda como trabajo futuro (Sección [[S:con]]).")
add("tabla_ref", tab5, "parada")
add("h2", "Umbral y métricas", "umbral")
add("p1", "El umbral de decisión se obtiene de las predicciones internas fuera de grupo de los 11 escenarios de entrenamiento. Entre 199 cuantiles de las puntuaciones (del 1 % al 99 %) se elige el que maximiza la exactitud balanceada; el escenario de prueba no interviene. "
    "La métrica principal es la PR-AUC (precisión promedio), más informativa que la ROC-AUC cuando la clase positiva es minoritaria [Saito, 15]. La PR-AUC de un clasificador sin información es igual a la prevalencia, que aquí va de 0,036 a 0,861; "
    "por eso toda cifra se acompaña de la referencia Dummy del mismo escenario. Se informan además la ROC-AUC y, con el umbral fijado, la sensibilidad, la precisión y la exactitud balanceada. "
    "Los promedios entre escenarios son macropromedios, en los que cada escenario pesa igual.")
add("h2", "Ensambles", "ens")
add("p1", "Se evalúan cuatro ensambles por voto suave, es decir, promedios de las probabilidades de sus miembros [Dietterich, 00]: RF+HGB, RL+RF+HGB, RF+HGB+XGB y los cuatro modelos juntos. "
    "Cada miembro usa los mejores hiperparámetros de su búsqueda individual para ese escenario excluido y esa semilla, sin repetir la búsqueda, de modo que los hiperparámetros se eligieron por modelo y ninguno se ajustó para el ensamble. "
    "El umbral se elige con las predicciones internas promediadas.")
add("h2", "Variables de contexto del host", "host")
add("p1", "Para medir si el comportamiento del host aporta información que el flujo aislado no tiene, a cada flujo se le añaden agregados de su IP de origen en una ventana temporal de W minutos (W = 1 y 5). Se calculan sin etiquetas e incluyen "
    "el número de conexiones, de destinos y de puertos distintos, las entropías de puertos y de destinos, las proporciones de TCP, UDP e ICMP, las proporciones de intentos sin respuesta y de reinicios, estadísticos del intervalo entre conexiones "
    "y medidas de regularidad tipo *beaconing* (23 variables en total). La versión evaluada con CTU-13 usa ventanas fijas que contienen flujos posteriores al evaluado, por lo que no es causal: una alerta solo podría emitirse al cerrar la ventana. "
    "Los hiperparámetros se reutilizan de la búsqueda con flujos, sin reajuste. Los archivos de trabajo contienen solo flujos Botnet y Normal, de modo que las ventanas son «puras»; para acotar ese efecto se recalcularon las ventanas con todo el tráfico, "
    "Background incluido, en los escenarios 5, 7 y 12 (semilla 11, W = 1). También se implementó una versión causal (20 variables acumuladas hasta el flujo actual, verificada sin discrepancias contra un cálculo directo en 150 flujos al azar); "
    "su evaluación completa en CTU-13 no llegó a terminarse y no se informa.")
add("h2", "Evaluación con tráfico Background", "fondo")
add("p1", "Para los escenarios excluidos 1, 2 y 3 (semilla 11) se evaluó el modelo sobre todo el tráfico del escenario, sin submuestreo y con el Background tratado como Normal, usando el umbral de la validación interna. "
    "Se informan la PR-AUC realista, la sensibilidad, la fracción de Background marcada y la precisión. Los tres escenarios tienen 2 824 132, 1 807 765 y 4 705 297 flujos; la corrida se detuvo tras ellos por su costo de cómputo.")
add("h2", "Validación externa en CIC-IDS2017", "cicm")
add("p1", "Se entrena con los 12 escenarios de CTU-13 (tope de 2 500 flujos) y se prueba en el viernes por la mañana de CIC-IDS2017 [Sharafaldin, 18]: 191 033 flujos, de los cuales 1 966 son de la clase Bot (1,03 %). Solo se usan las 13 variables comunes a ambos formatos "
    "(duración, bytes enviados, recibidos y totales, paquetes, bytes por paquete, proporción de salida, bytes y paquetes por segundo, puerto de destino, protocolo y clases de puerto); se excluyen el estado, el sentido y la dirección, propios de Argus. "
    "La búsqueda (10 puntos, validación interna por grupos de escenarios de CTU-13) y el umbral se obtienen solo con CTU-13, sin recalibrar para CIC. Una segunda variante añade 8 variables causales del host (ventana de 5 minutos). "
    "Las variables no significan lo mismo en ambos formatos (CIC mide longitudes de carga útil y Argus bytes totales), CIC tiene marca de tiempo con resolución de minuto y sus errores de construcción de flujos y de etiquetado están documentados [Engelen, 21].")
add("h2", "Análisis estadístico", "stats")
add("p1", "Se promedian las cinco semillas por escenario y los escenarios se tratan como bloques. Entre modelos se aplica la prueba de Friedman; por pares, la prueba de rangos con signo de Wilcoxon (exacta, bilateral) con la corrección de Holm sobre cada familia de comparaciones. "
    "Los intervalos de confianza del 95 % son percentiles de 10 000 remuestreos de los 12 escenarios. Las comparaciones que incluyen ensambles son dependientes porque comparten miembros, y sus pruebas son orientativas. "
    "Con 12 escenarios, el p mínimo alcanzable del Wilcoxon exacto es 0,0005, pero con efectos pequeños y variabilidad entre escenarios la potencia es baja.")
add("h2", "Implementación y reproducibilidad", "impl")
add("p1", "El código está en Python 3.11 con scikit-learn 1.9.1, XGBoost 3.2.0, Optuna 5.0.0, SciPy 1.17.1, NumPy 2.4.6 y pandas 3.1.1, sobre el *backend* del Laboratorio ML de NetSentinel, ejecutado con Docker Compose en una CPU Intel Core i5-12450H (12 hilos), 15 GB de RAM y sin GPU. "
    "Cada ejecución escribe sus resultados por semilla en archivos JSON de forma incremental y puede reanudarse. Las 300 evaluaciones del protocolo principal sumaron unas 10 horas de tiempo de reloj acumulado. "
    "Una sobresuscripción de hilos (el paralelismo OpenMP de HGB multiplicado por el de RF y XGB) ralentizó en torno a siete veces las ejecuciones iniciales de HGB y obligó a fijar los hilos por proceso, algo que conviene hacer al reproducir el trabajo. "
    "Los scripts, los resultados crudos y el recálculo de todas las tablas y figuras de este artículo están disponibles (Sección «Declaraciones»).")
add("h2", "Uso de herramientas de inteligencia artificial", "ia")
add("p1", "Siguiendo la posición del Committee on Publication Ethics [COPE, 23], se declara el uso de herramientas de inteligencia artificial. Se usó Claude Sonnet 5.5 (identificador de modelo *claude-sonnet-5-5*; Anthropic) a través del agente de programación Claude Code (versión 2.1.319) con estos fines: "
    "(a) escribir y modificar los scripts de experimentación en Python y el código del Laboratorio ML; (b) lanzar y supervisar las ejecuciones; (c) recalcular tablas, intervalos y figuras a partir de los resultados crudos; "
    "(d) redactar el manuscrito en español, reordenarlo, parafrasearlo, revisar su estilo y darle formato con la plantilla de J.UCS; y (e) consultar metadatos bibliográficos en Crossref para verificar las referencias. "
    "La herramienta no generó datos ni resultados: todas las cifras proceden de ejecuciones registradas en archivos JSON y se recalcularon por script. Los autores revisaron el contenido, verificaron las cifras contra los archivos de resultados "
    "y asumen la plena responsabilidad por la integridad, la exactitud y la originalidad del manuscrito. La herramienta no figura entre los autores.")

# ===== 4. Resultados
add("h1", "Resultados", "res")
add("h2", "De un escenario a varios", "r_uno")
add("p1", "Como punto de partida se evaluó cada modelo dentro del escenario 11 con una CV anidada 5×3 agrupada por bloques de 10 s y una partición de prueba reservada (tres semillas). En esa partición la PR-AUC fue de 0,995 a 0,996 en los cuatro modelos, "
    "frente a 0,733 del Dummy (Tabla [[T:uno]]). Al entrenar con el escenario 11 y probar en el 12, la PR-AUC del mejor modelo (RF) cae a 0,776 (referencia 0,221), con una sensibilidad de solo 0,249 al umbral 0,5. "
    "Al entrenar con el 12 y probar en el 11, los tres modelos de árboles quedan en la referencia o por debajo (PR-AUC de 0,691 a 0,769 frente a 0,750; ROC-AUC de 0,18 a 0,32, peor que el azar) y solo la regresión logística acierta (0,988). "
    "La validación por bloques de tiempo dentro de un escenario sobreestima, por tanto, el rendimiento ante otro escenario.")
add("tabla_ref", tab_uno, "uno")
add("p", "Con cuatro escenarios, la exclusión del 11 (Rbot) tampoco se predijo bien con modelos de árboles: la ROC-AUC fue de 0,13 a 0,32 con tres escenarios de entrenamiento y ninguno de la misma familia, mientras que la regresión logística alcanzó 1,000. "
    "Con los otros 11 escenarios, entre los que hay dos Rbot más (3 y 4), el escenario 11 se predice con una PR-AUC de 0,999 a 1,000 en todos los modelos. El fallo se debía a que la familia no estaba representada en el entrenamiento; "
    "la cobertura de familias es, por tanto, un factor dominante del rendimiento.")
add("h2", "Resultados entre 12 escenarios", "r_doce")
add("p1", "La Tabla [[T:pes]] y la Figura [[F:pes]] muestran la PR-AUC por escenario excluido, y la Tabla [[T:res]] el resumen. Todos los modelos superan al Dummy en los 12 escenarios. En nueve escenarios (1 a 6, 9, 11 y 13) los tres modelos de árboles superan 0,93 de PR-AUC "
    "y la regresión logística supera 0,88. Cuando la prevalencia es alta (escenarios 2, 9 y 11), el Dummy ya alcanza de 0,70 a 0,86, así que la ganancia es pequeña por construcción. "
    "Los escenarios débiles son el 7 (Sogou; PR-AUC de 0,399 a 0,640), el 8 (Murlo; de 0,677 a 0,893) y el 12 (NSIS.ay, la única botnet P2P; de 0,629 a 0,766), con desviaciones entre semillas de hasta 0,157.")
add("tabla_ref", tab_pes, "pes")
add("fig", "fig3_pr_por_escenario.png", 11.4, "Figura [[F:pes]]: PR-AUC por escenario excluido (media de 5 semillas; barras = desviación entre semillas). Las rayas negras son la prevalencia (referencia Dummy). Ensamble RL+RF+HGB descrito en la Sección [[S:r_ens]].", "pes")
add("p", "Ningún modelo gana en todo. HGB tiene la mejor media (0,911 ± 0,022), en buena parte por el escenario 7, y XGB la mejor mediana (0,992). RF tiene el mejor rango medio (1,50 entre cuatro modelos) y la menor variación entre semillas de la media global (0,007), "
    "y la regresión logística obtiene el mejor resultado en el escenario 12. La prueba de Friedman entre los cuatro modelos rechaza la equivalencia (χ^2^ = 13,3; 3 g. l.; p = 0,004), con la regresión logística en último rango (3,42). "
    "Las comparaciones por pares, en cambio, no resisten la corrección: el menor p de Wilcoxon, 0,021 (RF frente a XGB), pasa a 0,126 con Holm sobre las 6 comparaciones entre los cuatro modelos y a 0,189 sobre las 10 de la Tabla [[T:pareadas]]. "
    "Los intervalos del 95 % de la PR-AUC media se solapan ampliamente (por ejemplo, RF 0,906 [0,801; 0,982] y HGB 0,911 [0,829; 0,980]). No se declara un modelo ganador.")
add("h2", "Ensambles", "r_ens")
add("p1", "La Tabla [[T:res]] incluye los cuatro ensambles. Elevan la PR-AUC media entre 0,6 y 1,2 puntos respecto a RF y entre 0,1 y 0,7 respecto a HGB, una mejora que no es significativa (Wilcoxon sin corregir: p de 0,42 a 0,85 frente a RF y de 0,15 a 0,57 frente a HGB). "
    "Lo más claro es la estabilidad: RL+RF+HGB y el ensamble de los cuatro modelos tienen la menor desviación entre semillas de la media global (0,006 y 0,005) y la menor desviación máxima en un escenario (0,057 y 0,058, frente a 0,079 a 0,157 en los modelos individuales). "
    "RL+RF+HGB logra además la mejor exactitud balanceada (0,915; el resto de modelos y ensambles, de 0,886 a 0,907), la mejor precisión (0,761) y una sensibilidad (0,930) igual o mayor que la de cualquier otro (RF, 0,928). "
    "Los ensambles no resuelven los escenarios difíciles: en el 7 el HGB solo (0,640) supera a todos ellos (0,476 a 0,537), y en el 12 la regresión logística sola (0,766) supera a todos (0,674 a 0,739). "
    "Como los miembros reciben las mismas variables, el ensamble solo promedia sus errores.")
add("tabla_ref", tab_res, "res")
add("h2", "Variables de contexto del host", "r_host")
add("p1", "El contexto del host eleva de forma marcada la PR-AUC media (Tabla [[T:hostt]] y Figura [[F:host]]). El ensamble RL+RF+HGB pasa de 0,918 ± 0,006 con solo flujo a 0,960 ± 0,023 con W = 1 y a 0,985 ± 0,004 con W = 5, y su peor escenario sube de 0,507 a 0,608 y a 0,895. "
    "La mejora se concentra en los escenarios que fallaban con solo flujo: el 7 (Sogou) pasa de 0,507 a 0,999 (W = 1) y 0,993 (W = 5), y el 12 (NSIS.ay) de 0,739 a 0,985 y 0,990. "
    "No todo mejora: el escenario 8 (Murlo) empeora con W = 1 (de 0,892 a 0,608, con gran variación entre semillas), y dos de los tres escenarios Rbot bajan algo con W = 5 (el 11, de 1,000 a 0,976; el 4, de 0,989 a 0,969). "
    "La regresión logística no se beneficia con W = 5 (0,857 frente a 0,886).")
add("tabla_ref", tab_host, "hostt")
add("fig", "fig4_contexto_host.png", 11.4, "Figura [[F:host]]: PR-AUC del ensamble RL+RF+HGB por escenario con solo variables de flujo y con contexto del host no causal (W = 1 y 5 min). Media de 5 semillas.", "host")
add("p", "Los contrastes pareados (Tabla [[T:pareadas]]) dan las mayores diferencias con W = 5: RF +0,074 (IC 95 % [+0,003; +0,173]; p = 0,052) y RL+RF+HGB +0,067 ([+0,002; +0,160]; p = 0,064). "
    "Con la corrección de Holm, ningún contraste del contexto del host tiene un p ajustado menor que 0,425, y los dos intervalos que excluyen el cero lo hacen por poco y no resisten la corrección. "
    "La mejora es grande, pero depende de pocos escenarios. Además, el tamaño de ventana y el ensamble se compararon con los mismos resultados con los que se informan, lo que sesga la selección hacia el optimismo; por eso se informan ambas ventanas y todos los modelos.")
add("tabla_ref", tab_par2, "pareadas")
add("p", "Para comprobar la pureza de las ventanas se recalcularon con todo el tráfico (Background incluido) en los escenarios 5, 7 y 12. Respecto a la ventana pura, la PR-AUC cambió entre 0,000 y 0,007 en los cuatro modelos (por ejemplo, escenario 7, RF: 0,996 frente a 0,993). "
    "La mejora no depende de esa pureza en la evaluación; el entrenamiento sí se hizo con ventanas puras y los demás escenarios no se comprobaron. "
    "Esta variante responde a otra pregunta: cada flujo se clasifica por lo que hizo su host de origen en la ventana. Sirve para señalar equipos comprometidos y no puede operar en línea. "
    "Sigue sin demostrarse que la ventaja se mantenga sin usar flujos futuros.")
add("h2", "Evaluación con tráfico Background", "r_fondo")
add("p1", "La Tabla [[T:bg]] y la Figura [[F:bg]] contrastan la evaluación sobre flujos etiquetados con la realista. Con el umbral de la validación interna, entre una cuarta parte y dos quintas partes del tráfico Background se marca como botnet (25 000 a 41 000 alertas por 100 000 flujos) "
    "y la precisión queda entre 1,7 % y 4,2 %, aunque la sensibilidad se mantiene alta (0,76 a 0,997). La PR-AUC realista (0,06 a 0,95) es mucho menor que la calculada solo con flujos etiquetados (0,94 a 0,999) y varía entre modelos: en el escenario 3 llega a 0,949 con HGB y es de 0,161 con la regresión logística. "
    "El orden de las puntuaciones puede ser bueno aunque el umbral no se transfiera, porque se fijó con otra prevalencia (0,6 % a 1,5 % en estos escenarios completos, frente a 3,6 % a 86,1 % tras etiquetar). "
    "Estos datos piden cautela: el Background no es verdad conocida y puede contener tráfico malicioso sin etiquetar o tráfico legítimo atípico, y la prueba cubre tres escenarios y una semilla.")
add("tabla_ref", tab_bg, "bg")
add("fig", "fig5_evaluacion_realista.png", 11.0, "Figura [[F:bg]]: Arriba, PR-AUC calculada solo con flujos etiquetados y con todo el tráfico (Background = Normal). Abajo, porcentaje del tráfico Background marcado como botnet. Escenarios 1, 2 y 3, semilla 11. RL: regresión logística; Ens.: RL+RF+HGB.", "bg")
add("h2", "Validación externa en CIC-IDS2017", "r_cic")
add("p1", "El detector entrenado con CTU-13 no se transfiere a CIC-IDS2017 (Tabla [[T:cic]] y Figura [[F:cic]]). Con variables de flujo, la PR-AUC va de 0,019 a 0,080 (el azar da 0,010) y la ROC-AUC de 0,717 a 0,861: hay señal por encima del azar, pero insuficiente. "
    "Con el umbral heredado se marca entre el 20 % y el 58 % del tráfico benigno y la precisión es de 1,7 % a 3,8 %. Los modelos de árboles, los mejores dentro de CTU-13, son los que peor se transfieren, y la regresión logística (con logaritmo y escalado) es la menos mala. "
    "El contexto causal del host empeora la transferencia: la ROC-AUC baja a entre 0,477 y 0,665, y la regresión logística queda por debajo del azar. "
    "Con ese contexto, los umbrales heredados marcan entre el 86 % y el 97 % del tráfico benigno en los modelos de árboles (el de HGB es degenerado, 2,6·10^-8^). "
    "Una explicación plausible, aunque no probada, es que en CIC los equipos infectados también generan tráfico benigno, hay NAT interno y la actividad típica de un host difiere de la de las capturas de CTU-13.")
add("tabla_ref", tab_cic, "cic")
add("fig", "fig6_cic.png", 10.4, "Figura [[F:cic]]: PR-AUC y ROC-AUC en CIC-IDS2017 de los modelos entrenados con CTU-13, con solo variables de flujo y con contexto causal del host. La línea punteada es el azar (PR-AUC = prevalencia, 0,010; ROC-AUC = 0,5). Semilla 11.", "cic")

# ===== 5. Discusión
add("h1", "Discusión", "dis")
add("h2", "Lo que se sostiene y lo que no", "d_sost")
add("p1", "El escenario es la unidad de partición adecuada: la misma familia de modelos que obtiene una PR-AUC de 0,995 a 0,996 dentro de un escenario (Tabla [[T:uno]]) cae por debajo de la referencia al cambiar de escenario, y la cobertura de familias explica buena parte de la diferencia. "
    "Con 11 escenarios de entrenamiento, el rendimiento entre escenarios es alto en la mayoría (PR-AUC de 0,88 a 1,00 en nueve de los doce), pero la media (0,886 a 0,918) esconde tres escenarios difíciles, donde la elección del modelo importa y la variabilidad entre semillas es grande. "
    "Esa elección no puede fundamentarse con 12 escenarios: ninguna diferencia por pares resiste Holm, y los ensambles aportan sobre todo estabilidad, con una ganancia de PR-AUC que no puede demostrarse. "
    "El contexto del host es prometedor (0,985 en la mejor configuración, con un peor escenario de 0,895), pero no está establecido: la versión evaluada no es causal, la selección de W y del modelo es optimista y la ventaja no se trasladó a CIC-IDS2017. "
    "Por último, las métricas sobre flujos etiquetados sobreestiman el rendimiento operativo y el detector no se transfiere a otra red.")
add("p", "La contribución defendible es el protocolo y la medición de sus límites. Los resultados de CTU-13 no deben leerse como evidencia de que el detector sirva en otra red, y la cifra de 0,985 con contexto del host no debe citarse sin su salvedad de causalidad.")
add("h2", "Amenazas a la validez", "d_amen")
add("p1", "*Validez interna.* La búsqueda de hiperparámetros fue aleatoria, de 10 puntos, sin componente bayesiano ni poda (Sección [[S:parada]]); con presupuestos mayores el orden entre modelos podría cambiar, en especial entre los modelos de boosting, más sensibles a sus hiperparámetros. "
    "Tampoco se reajustó la búsqueda para las variables de contexto del host, y el número de iteraciones de RL (2 000) y de árboles de XGB (300) se fijó sin estudiar su efecto. "
    "El análisis exploratorio usó los 12 escenarios para comparar modelos, ventanas y ensambles, así que no existe una prueba sellada sobre escenarios nunca vistos. Con cinco semillas, la variabilidad en los escenarios débiles sigue siendo alta (hasta 0,157).")
add("p", "*Validez de constructo.* Las etiquetas de CTU-13 proceden de sus autores y el Background carece de verdad conocida; la evaluación realista lo trata como normal, lo que penaliza posibles falsos positivos que en realidad son detecciones. "
    "El submuestreo a 2 500 flujos altera la prevalencia respecto a los datos completos. La PR-AUC depende de la prevalencia, por lo que solo es interpretable junto con la referencia Dummy. Las ventanas de host se calcularon con archivos que solo contienen flujos etiquetados.")
add("p", "*Validez externa.* CTU-13 es tráfico de laboratorio de 2011, con pocas IP infectadas por escenario y sin registros reales de firewall. La única validación externa es CIC-IDS2017, con una familia (Bot), una semilla y variables que no significan lo mismo en ambos formatos; "
    "con estos datos no se puede separar la diferencia de medición del comportamiento de las botnets. No se recalibró el umbral para CIC y falta el escenario 10.")
add("p", "*Validez de conclusión estadística.* Con 12 escenarios la potencia es baja. Las semillas no son réplicas independientes de los escenarios y las comparaciones con ensambles son dependientes. "
    "Se corrigió por comparaciones múltiples dentro de cada familia, pero no entre todos los experimentos del trabajo, así que cualquier resultado nominalmente significativo debe leerse con cautela.")

# ===== 6. Conclusiones
add("h1", "Conclusiones y trabajo futuro", "con")
add("p1", "Se presentó y ejecutó un protocolo de validación que deja fuera escenarios completos de CTU-13, con búsqueda de hiperparámetros anidada y umbral interno, sobre 12 escenarios, cuatro clasificadores, ensambles y cinco semillas. "
    "Sus pasos de entrenamiento, su parametrización, sus condiciones iniciales y sus condiciones de parada quedaron documentados para poder repetirlo. "
    "Entre escenarios, los modelos superan con claridad a la referencia trivial (PR-AUC media de 0,886 a 0,918 frente a 0,383), sin diferencias significativas entre ellos tras la corrección de Holm y con tres escenarios difíciles. "
    "En su versión no causal, el contexto del host mejora los escenarios débiles, aunque su ventaja en línea no está demostrada. Las evaluaciones con tráfico Background y en CIC-IDS2017 muestran que los resultados sobre flujos etiquetados de CTU-13 no equivalen a utilidad operativa. "
    "A quien evalúe detectores sobre CTU-13 se le recomienda particionar por escenario, informar la referencia Dummy, acompañar toda cifra con intervalos entre escenarios y declarar la limitación de generalización.")
add("p", "Como trabajo futuro se plantean seis líneas. (i) Una partición 70/15/15 por escenarios completos (8 de desarrollo, 2 de validación y 2 de prueba, con la prueba sellada y repetida con varias semillas) para fijar umbral, calibración y elección del modelo sin contaminar la prueba. "
    "(ii) Una búsqueda con al menos 30 intentos, con TPE de arranque menor que el presupuesto, poda real y parada temprana en los modelos de boosting. (iii) La evaluación completa de la versión causal del contexto del host. "
    "(iv) Una evaluación realista en los 12 escenarios y con varias semillas, con el umbral calibrado para una tasa de falsos positivos objetivo. "
    "(v) La calibración de probabilidades y las explicaciones por alerta (SHAP) con severidad configurable, ya previstas en el Laboratorio ML. (vi) La validación en más conjuntos de datos y con registros reales de firewall.")

add("agr", "Declaraciones")
add("p1", "*Ética.* El estudio usa conjuntos de datos públicos de tráfico de red y no involucra personas ni animales, por lo que no requirió la aprobación de un comité de ética.")
add("p", "*Disponibilidad de datos y código.* CTU-13 [García, 14] y CIC-IDS2017 [Sharafaldin, 18] son públicos. Los scripts, los resultados crudos por semilla (JSON) y el código del Laboratorio ML de NetSentinel están disponibles en [URL del repositorio: por completar por los autores].")
add("p", "*Financiamiento.* Este trabajo no recibió financiamiento.")
add("p", "*Conflicto de intereses.* Los autores declaran no tener conflictos de intereses.")
add("p", "*Autor de correspondencia.* Roberto Enrique Quezada-Rodríguez (requezadaro@unitru.edu.pe).")
add("p", "*Uso de inteligencia artificial.* Véase la Sección [[S:ia]].")

# ---------------------------------------------------------------- numeracion automatica y espacios duros
def _nbsp(s): return re.sub(r"(?<=\d) (?=\d{3}(?!\d))", NB, s)

def _numerar():
    h1 = h2 = 0; sec, tab, fig = {}, {}, {}
    for b in B:
        if b[0] == "h1": h1 += 1; h2 = 0; sec[b[2]] = str(h1)
        elif b[0] == "h2": h2 += 1; sec[b[2]] = f"{h1}.{h2}"
        elif b[0] == "tabla_ref": tab[b[2]] = len(tab) + 1
        elif b[0] == "fig": fig[b[4]] = len(fig) + 1
    mapa = {"S": sec, "T": tab, "F": fig}
    def T(s):
        s = re.sub(r"\[\[([STF]):(\w+)\]\]", lambda m: str(mapa[m.group(1)][m.group(2)]), s)
        return _nbsp(s)
    out = []
    for b in B:
        if b[0] in ("h1", "h2", "agr", "p1", "p"): out.append((b[0], T(b[1])) + tuple(b[2:]))
        elif b[0] == "fig": out.append(("fig", b[1], b[2], T(b[3])) + tuple(b[4:]))
        elif b[0] == "tabla_ref":
            k, leyenda, enc, filas, anchos, o = b[1]
            if "grupos" in o: o = {**o, "grupos": [(T(l), sp) for l, sp in o["grupos"]]}
            out.append(("tabla_ref", (k, T(leyenda), [T(h) for h in enc], [[T(c) for c in fila] for fila in filas], anchos, o)) + tuple(b[2:]))
        else: raise ValueError(b[0])
    return out, mapa

B, MAPA = _numerar()
RESUMEN = _nbsp(RESUMEN)
