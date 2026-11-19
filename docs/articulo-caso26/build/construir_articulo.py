"""Construye Articulo_Caso26_NetSentinel.docx a partir de la plantilla ArticuloEjemplo_mejorado.docx.

Conserva estilos, tipografías, márgenes, orden de secciones y estilo de leyendas/notas de la plantilla y sustituye todo su
contenido. Cifras: se leen de los artefactos reales guardados en figuras/datos/ (no se teclean a mano las tablas).
Uso: python construir_articulo.py <plantilla.docx> <salida.docx>
"""
import json, os, re, shutil, sys, zipfile, tempfile, math, csv
from xml.sax.saxutils import escape
from PIL import Image

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, AQUI)
import refs as R

DATOS = os.path.join(RAIZ, "figuras", "datos")
RAW = os.path.join(DATOS, "raw")
NB = " "

# ---------------------------------------------------------------- datos reales
J2 = json.load(open(os.path.join(RAW, "job2_evaluate.json"), encoding="utf8"))
VAL = json.load(open(os.path.join(RAW, "dataset_v3_validation.json"), encoding="utf8"))
TB = VAL["keys"]["time_block"]
M12 = json.load(open(os.path.join(RAW, "runs", "run12_metrics.json"), encoding="utf8"))
HALL = []
_l = [r.rstrip("\n").split("|") for r in open(os.path.join(RAW, "db", "traffic_findings.txt"), encoding="utf8") if "|" in r]
_h = _l[0]
for r in _l[1:]:
    if r[0].isdigit():
        HALL.append(dict(zip(_h, r[:12])))
PRIMERA = [h for h in HALL if h["created_at"].startswith("2026-11-11")]  # primera carga (sin la recarga duplicada)
INFECTADOS = {"147.32.84.165", "147.32.84.191", "147.32.84.192"}
NOMBRE = {"Línea base trivial (Dummy)": "Línea base trivial", "Gradient Boosting de histogramas": "Boosting de histogramas"}
nm = lambda s: NOMBRE.get(s, s)


def fm(x, nd=3):
    if x is None:
        return "n. d."
    s = f"{x:.{nd}f}".replace(".", ",")
    return s.replace("-", "−")


def miles(n):
    return f"{int(n):,}".replace(",", NB)


def wilson(k, n, z=1.959964):
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, c - h), min(1.0, c + h)


# ---------------------------------------------------------------- texto
def nbsp(t):
    t = re.sub(r"(?<=\d) (?=\d{3}(?!\d))", NB, t)           # separador de miles
    t = re.sub(r"(?<=\d) (?=(?:s|min|ms|MB|GB|B|h|%|ppp|Hz)\b)", NB, t)  # número + unidad
    t = re.sub(r"\b(Tabla|Figura|Tablas|Figuras) (?=\d)", lambda m: m.group(1) + NB, t)
    t = re.sub(r"(?<=\b[np]) (?==)", NB, t)                  # n = , p =
    t = re.sub(r"(?<==) (?=[\d−\-])", NB, t)
    return t


def cita(t):
    t = re.sub(r"\{c:(\w+)\}", lambda m: R.cita_parentesis([m.group(1)]), t)
    t = re.sub(r"\{p:([\w,]+)\}", lambda m: R.cita_parentesis(m.group(1).split(",")), t)
    t = re.sub(r"\{n:(\w+)\}", lambda m: R.cita_narrativa(m.group(1)), t)
    return t


def prep(t):
    return nbsp(cita(t))


FUENTE = '<w:rFonts w:ascii="Montserrat" w:hAnsi="Montserrat" w:cs="Arial"/>'


def rpr(sz=20, b=False, i=False, lang=True):
    return (FUENTE + ("<w:b/><w:bCs/>" if b else "") + ("<w:i/><w:iCs/>" if i else "") +
            f'<w:sz w:val="{sz}"/><w:szCs w:val="{sz}"/>' + ('<w:lang w:val="es-PE"/>' if lang else ""))


def run(t, sz=20, b=False, i=False):
    return f'<w:r><w:rPr>{rpr(sz, b, i)}</w:rPr><w:t xml:space="preserve">{escape(t)}</w:t></w:r>'


def runs_md(t, sz=20, b=False):
    """*cursiva* dentro del texto."""
    out = []
    for k, parte in enumerate(re.split(r"\*([^*]+)\*", t)):
        if parte:
            out.append(run(parte, sz, b, i=(k % 2 == 1)))
    return "".join(out)


def p_cuerpo(t, sz=20, jc=None):
    t = prep(t)
    j = f'<w:jc w:val="{jc}"/>' if jc else ""
    return (f'<w:p><w:pPr><w:spacing w:after="120" w:before="120" w:line="360" w:lineRule="auto"/><w:ind/>{j}'
            f'<w:rPr>{rpr(sz)}</w:rPr></w:pPr>{runs_md(t, sz)}</w:p>')


def h1(t):
    return ('<w:p><w:pPr><w:pStyle w:val="771"/><w:keepNext w:val="true"/><w:numPr><w:ilvl w:val="0"/><w:numId w:val="14"/></w:numPr>'
            '<w:spacing w:after="120" w:before="120" w:line="360" w:lineRule="auto"/><w:ind w:hanging="284" w:left="284"/>'
            f'<w:rPr>{rpr(20, True, lang=False)}</w:rPr></w:pPr>{run(t, 20, True)}</w:p>')


def h2(t):
    return ('<w:p><w:pPr><w:pStyle w:val="771"/><w:keepNext w:val="true"/><w:numPr><w:ilvl w:val="1"/><w:numId w:val="14"/></w:numPr>'
            '<w:spacing w:after="120" w:before="120" w:line="360" w:lineRule="auto"/><w:ind w:hanging="431" w:left="425"/>'
            f'<w:rPr>{rpr(20, True, lang=False)}</w:rPr></w:pPr>{run(t, 20, True)}</w:p>')


def h_plano(t):
    return ('<w:p><w:pPr><w:keepNext w:val="true"/><w:spacing w:after="120" w:before="120" w:line="360" w:lineRule="auto"/><w:ind/>'
            f'<w:jc w:val="left"/><w:rPr>{rpr(20)}</w:rPr></w:pPr>{run(t, 20, True)}</w:p>')


def p_vacio(left=False):
    return ('<w:p><w:pPr><w:spacing w:after="0" w:line="240" w:lineRule="auto"/><w:ind/>'
            f'<w:jc w:val="{"left" if left else "center"}"/><w:rPr/></w:pPr></w:p>')


def fld(instr, val, b=True, sz=20):
    r = f'<w:r><w:rPr>{rpr(sz, b)}</w:rPr>'
    return (f'{r}<w:fldChar w:fldCharType="begin"/></w:r>{r}<w:instrText xml:space="preserve"> {instr} </w:instrText></w:r>'
            f'{r}<w:fldChar w:fldCharType="separate"/></w:r>{r}<w:t xml:space="preserve">{val}</w:t></w:r>{r}<w:fldChar w:fldCharType="end"/></w:r>')


CONT = {"Tabla": 0, "Figura": 0}


def leyenda(tipo, titulo):
    CONT[tipo] += 1
    n = CONT[tipo]
    campo = fld("SEQ " + tipo + " \\* ARABIC", n)
    return ('<w:p><w:pPr><w:keepNext w:val="true"/><w:spacing w:after="120" w:before="120" w:line="360" w:lineRule="auto"/><w:ind/>'
            f'<w:jc w:val="left"/><w:rPr>{rpr(20)}</w:rPr></w:pPr>{run(tipo + " ", 20, True)}{campo}'
            f'{run(":", 20, True)}{run(" " + prep(titulo), 20, False, True)}</w:p>')


def nota(t, etiqueta="Nota."):
    t = prep(t)
    return ('<w:p><w:pPr><w:spacing w:after="200" w:before="60" w:line="276" w:lineRule="auto"/><w:ind/><w:jc w:val="left"/>'
            f'<w:rPr>{rpr(18)}</w:rPr></w:pPr>{run(etiqueta, 18, False, True)}{runs_md(" " + t, 18)}</w:p>')


def tabla(anchos, cab, filas, sz=18, alin=None, keep_all=True, negrita_ult=False, margen=None):
    assert sum(anchos) == 9286, sum(anchos)
    alin = alin or ["left"] + ["center"] * (len(anchos) - 1)
    grid = "".join(f'<w:gridCol w:w="{a}"/>' for a in anchos)

    def celda(txt, w, jc, head=False, keep=True, bold=False):
        shd = '<w:shd w:val="clear" w:color="auto" w:fill="f2f2f2"/>' if head else ""
        kn = '<w:keepNext w:val="true"/>' if keep else ""
        return (f'<w:tc><w:tcPr>{shd}<w:tcBorders/><w:tcW w:w="{w}" w:type="dxa"/><w:vAlign w:val="center"/></w:tcPr>'
                f'<w:p><w:pPr>{kn}<w:spacing w:after="60" w:before="60" w:line="276" w:lineRule="auto"/><w:ind/><w:jc w:val="{jc}"/>'
                f'<w:rPr>{rpr(sz, lang=False)}</w:rPr></w:pPr>{runs_md(prep(txt), sz, head or bold)}</w:p></w:tc>')

    x = ('<w:tbl><w:tblPr><w:tblStyle w:val="811"/><w:jc w:val="center"/><w:tblW w:w="9286" w:type="dxa"/><w:tblBorders/>'
         '<w:tblLayout w:type="fixed"/>' + (f'<w:tblCellMar><w:left w:w="{margen}" w:type="dxa"/><w:right w:w="{margen}" w:type="dxa"/></w:tblCellMar>' if margen else '') + '<w:tblLook w:val="04A0" w:firstRow="1" w:lastRow="0" w:firstColumn="1" w:lastColumn="0" w:noHBand="0" w:noVBand="1"/>'
         f'</w:tblPr><w:tblGrid>{grid}</w:tblGrid>')
    x += '<w:tr><w:trPr><w:cantSplit/><w:tblHeader/></w:trPr>' + "".join(celda(c, w, "center", True) for c, w in zip(cab, anchos)) + "</w:tr>"
    for k, f in enumerate(filas):
        keep = keep_all or k < 1
        ult = negrita_ult and k == len(filas) - 1
        x += '<w:tr><w:trPr><w:cantSplit/></w:trPr>' + "".join(
            celda(c, w, a, False, keep, ult) for c, w, a in zip(f, anchos, alin)) + "</w:tr>"
    return x + "</w:tbl>"


FIGS = []


def figura(archivo, alt):
    FIGS.append(archivo)
    n = len(FIGS)
    im = Image.open(os.path.join(RAIZ, "figuras", archivo))
    cx = 5900000
    cy = int(cx * im.height / im.width)
    rid = f"rId{12 + n}"
    return ('<w:p><w:pPr><w:keepNext w:val="true"/><w:spacing w:after="120" w:before="120" w:line="240" w:lineRule="auto"/><w:ind/>'
            f'<w:jc w:val="center"/><w:rPr>{rpr(20)}</w:rPr></w:pPr><w:r><w:rPr>{rpr(20)}</w:rPr><w:drawing>'
            f'<wp:inline distT="0" distB="0" distL="0" distR="0"><wp:extent cx="{cx}" cy="{cy}"/><wp:effectExtent l="0" t="0" r="0" b="0"/>'
            f'<wp:docPr id="{n}" name="Figura {n}" descr="{escape(alt, {chr(34): "&quot;"})}"/>'
            '<wp:cNvGraphicFramePr><a:graphicFrameLocks noChangeAspect="1"/></wp:cNvGraphicFramePr>'
            '<a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
            '<pic:pic xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture">'
            f'<pic:nvPicPr><pic:cNvPr id="{n}" name="{archivo}"/><pic:cNvPicPr><a:picLocks noChangeAspect="1"/></pic:cNvPicPr></pic:nvPicPr>'
            f'<pic:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
            f'<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr>'
            '</pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r></w:p>')


def p_ref(k):
    runs = "".join(run(t, 20, False, it) for t, it in R.referencia(k))
    return ('<w:p><w:pPr><w:pStyle w:val="919"/><w:spacing w:after="120" w:before="120" w:line="360" w:lineRule="auto"/>'
            '<w:ind w:hanging="720" w:left="720"/><w:jc w:val="left"/><w:rPr>' + rpr(20, lang=False) + f'</w:rPr></w:pPr>{runs}</w:p>')


# ---------------------------------------------------------------- contenido
TITULO_ES = "Arquitectura reproducible de bajo costo para analizar registros de cortafuegos con un modelo de lenguaje local: evaluación preliminar"
TITULO_EN = "Reproducible low-cost architecture for analyzing firewall logs with a local language model: a preliminary evaluation"

RESUMEN = (
    "Las pequeñas y medianas empresas carecían de herramientas de bajo costo que analizaran registros de cortafuegos sin enviar datos a "
    "terceros. El objetivo fue diseñar, implementar y evaluar de forma preliminar NetSentinel, una arquitectura que separó el cálculo "
    "determinista de las métricas de su interpretación por un modelo de lenguaje local de 3 000 millones de parámetros. Con un enfoque de ciencia del diseño se "
    "integraron detectores deterministas, una bitácora de auditoría y un laboratorio de aprendizaje automático sin fuga de información. Se procesaron 107 194 flujos del escenario 11 de CTU-13 (16 min); 10 882 tenían etiqueta y se agruparon en bloques temporales de 10 s. Cuatro clasificadores evaluados en "
    "1 525 flujos de prueba produjeron la misma matriz de confusión (21 falsos negativos, ningún falso positivo; "
    "F1 = 0,991; coeficiente de correlación de Matthews = 0,966), explicada casi por completo por los bytes por paquete de la "
    "inundación de mensajes de control de Internet. Los detectores deterministas no identificaron ningún flujo del ataque. Las pruebas "
    "estadísticas carecieron de potencia (p mínimo = 0,0625). El estudio no demuestra una detección efectiva de botnets; aporta una "
    "arquitectura reproducible y un diagnóstico cuantificado de sus límites."
)
ABSTRACT = (
    "Small and medium-sized enterprises lacked low-cost tools to analyze firewall and intrusion detection logs without sending data to "
    "third parties. This study aimed to design, implement, and preliminarily evaluate NetSentinel, an architecture that separated "
    "deterministic metric computation from interpretation by a local language model with 3 billion parameters. Using a design science "
    "approach, we integrated deterministic detectors, an audit log, and a machine learning laboratory with a leakage-safe protocol. We "
    "processed 107,194 flows from CTU-13 scenario 11 (16 min; three infected hosts), of which 10,882 were labeled; flows were grouped into "
    "10-s time blocks, and four classifiers were evaluated on a held-out partition of 1,525 flows. All four models produced the same "
    "confusion matrix (21 false negatives and no false positives; F1 = 0.991; Matthews correlation coefficient = 0.966), explained almost "
    "entirely by the bytes per packet of the Internet Control Message Protocol flood, whereas the deterministic detectors identified none "
    "of the attack flows. The statistical tests lacked power (minimum p = 0.0625). The study does not demonstrate effective botnet "
    "detection; it contributes a reproducible architecture and a quantified diagnosis of its limits."
)
KW_ES = "Aprendizaje automático, Botnet, Detección de intrusiones, Pequeñas y medianas empresas, Seguridad de redes."
KW_EN = "Botnet, Intrusion detection, Machine learning, Network security, Small and medium-sized enterprises."

INTRO = [
    "Las pequeñas y medianas empresas (pymes) sostienen buena parte de la economía, pero suelen carecer del personal, la formación y el "
    "presupuesto necesarios para defender sus redes {p:rombaldo2026,adriko2024}. Sus cortafuegos y sus sistemas de detección de intrusiones "
    "(IDS, por su sigla en inglés) producen registros que crecen cada día y casi nunca se revisan. Esa falta de visibilidad deja sin "
    "vigilancia conductas como la comunicación periódica con un servidor externo (beaconing) o la salida anómala de datos.",

    "Los sistemas de gestión de eventos e información de seguridad (SIEM, por su sigla en inglés) se han analizado sobre todo en "
    "infraestructuras críticas {c:gonzalez2021}, y su operación exige recursos que una pyme rara vez tiene. El volumen de alertas, además, "
    "provoca fatiga en los analistas {c:tariq2025}. El aprendizaje automático sobre datos de SIEM {c:tendikov2024}, la representación del "
    "contexto de los eventos {c:liu2022} y la automatización de la respuesta {c:kinyua2021} buscan aliviar esa carga.",

    "En la detección de botnets, el aprendizaje automático se ha aplicado con selección de variables y árboles de decisión {c:velasco2021}, "
    "en tiempo real {c:velasco2023}, con ensambles híbridos {c:hossain2023} y en redes definidas por software {c:shinan2021}. Otros trabajos "
    "aprovechan la periodicidad del tráfico de comando y control {c:oskera2025}, detectan la exfiltración por túneles del sistema de nombres "
    "de dominio {c:abualghanam2023} o explican las decisiones con valores de Shapley aditivos (SHAP) {p:saied2025,gaspar2024}.",

    "Los modelos de lenguaje de gran tamaño (LLM, por su sigla en inglés) se evalúan para analizar registros y clasificar eventos de "
    "seguridad {p:karlsen2024,palma2025,zhang2025}, y ya existen revisiones sistemáticas {p:xu2026,ma2026,divakaran2025,kheddar2025}. Se han "
    "propuesto marcos explicables para detectar intrusiones {c:houssel2026}, recuperación aumentada de inteligencia de amenazas "
    "{c:alhuzali2025} y reducción de falsos positivos {c:jiang2026}. Los modelos pequeños ofrecen ventajas de privacidad y costo "
    "{c:dikici2026}.",

    "Integrar un LLM en un flujo de seguridad añade riesgos. Los registros de red son datos no confiables que pueden contener "
    "instrucciones, y la inyección indirecta de órdenes compromete las aplicaciones que combinan modelos de lenguaje con datos externos "
    "{p:greshake2023,zhan2025,woesle2026}. Enviar los registros a un tercero plantea, además, problemas de privacidad {c:yao2024}. Un modelo "
    "local reduce esa exposición, a costa de una menor capacidad.",

    "La evaluación con datos de red exige cuidado. La fuga de información entre entrenamiento y prueba infla los resultados {c:kapoor2023}, y "
    "conviene precisar qué estima la validación cruzada {c:bates2023}. En la detección de intrusiones, la generalización entre conjuntos de "
    "datos es limitada {p:cantone2024,verkerken2021,sarhan2022} y usar aprendizaje automático fuera del mundo cerrado de un conjunto resulta "
    "difícil {c:sommer2010}. Con clases desbalanceadas, el coeficiente de correlación de Matthews (MCC, por su sigla en inglés) es más "
    "fiable que la exactitud balanceada {c:chicco2021}.",

    "Aunque la detección de botnets y el análisis de registros con modelos de lenguaje se han estudiado con conjuntos públicos y modelos "
    "grandes, permanece sin resolver cómo combinar, con bajo costo y sin sacar los datos de la organización, detectores deterministas, un "
    "modelo de lenguaje pequeño y una evaluación libre de fuga en una pyme con pocos equipos infectados observables. Esta limitación importa "
    "porque una métrica alta, sin protocolo trazable ni diagnóstico de sus límites, transmite una confianza que los datos no respaldan.",

    "Este estudio aborda la brecha mediante NetSentinel, una arquitectura que separa el cálculo determinista de las métricas de la "
    "interpretación por un modelo de lenguaje local, registra cada acción en una bitácora de auditoría y evalúa clasificadores con un "
    "protocolo contra la fuga de información. El objetivo es diseñar, implementar y evaluar de forma preliminar esa arquitectura con el "
    "escenario 11 del conjunto CTU-13 {c:garcia2014}, siguiendo la ciencia del diseño {c:hevner2004}.",

    "Las contribuciones son cinco: una arquitectura reproducible de bajo costo cuyos datos permanecen en la organización; la separación entre "
    "el cómputo determinista y la interpretación por el modelo de lenguaje; un protocolo de evaluación con salvaguardas contra la fuga; la "
    "trazabilidad mediante una bitácora de auditoría; y un diagnóstico cuantificado de los límites. El alcance es acotado: un escenario de "
    "16 min con tres equipos infectados, de modo que el estudio no pretende demostrar una detección efectiva de botnets.",
]

CONCLUSION = (
    "Se diseñó, implementó y evaluó de forma preliminar NetSentinel, una arquitectura de bajo costo que mantiene los registros dentro de la "
    "organización, separa el cálculo determinista de la interpretación por un modelo de lenguaje local y registra cada acción en una "
    "bitácora de auditoría. Con una captura de 16 min y tres equipos infectados, los detectores deterministas no identificaron ninguno de los "
    "1 118 flujos Botnet de la prueba, porque la inundación fue tráfico interno fuera de su alcance, y el modelo de lenguaje emitió solo "
    "veredictos «incierto». Cuatro clasificadores empataron con la misma matriz de confusión (F1 = 0,991; MCC = 0,966; 21 falsos negativos), "
    "pero ese desempeño se explicó casi por completo por los bytes por paquete de la inundación, se obtuvo con una partición por bloques "
    "temporales que no mide la generalización a equipos nuevos y careció de potencia estadística (p mínimo = 0,0625); ninguno de los 21 flujos "
    "de comando y control se detectó. Por tanto, los resultados no demuestran una detección efectiva de botnets ni permiten extrapolar a "
    "otras redes. Se recomienda evaluar con más escenarios y agrupar por equipo, incorporar un detector de volumen para el tráfico interno, "
    "evaluar el modelo de lenguaje con hallazgos etiquetados y con pruebas adversarias de inyección de órdenes, y priorizar el procesamiento "
    "para que un lote de 30 hallazgos no supere la cadencia de 15 min."
)

AGRADECIMIENTOS = (
    "Declaración sobre el uso de inteligencia artificial generativa: se empleó un asistente de inteligencia artificial generativa (Claude, de "
    "Anthropic) como apoyo para redactar el texto en español, escribir el código de análisis y de las figuras y consolidar las referencias; "
    "los resultados numéricos se extrajeron de los artefactos y de la base de datos del sistema, y las referencias se verificaron en Crossref. "
    "[PARA CONFIRMACIÓN DE LOS AUTORES: que revisaron el contenido y asumen la responsabilidad de la publicación]. El modelo llama3.2:3b "
    "descrito en el estudio es un componente del sistema evaluado y no una herramienta de redacción."
)
CONFLICTO = ("No existe ningún tipo de conflicto de interés relacionado con la materia del trabajo. [PARA CONFIRMACIÓN DE LOS AUTORES: "
             "texto propuesto con la fórmula de la revista]")
CREDIT = ("[A COMPLETAR POR LOS AUTORES: asignar a Roberto Enrique Quezada-Rodríguez y a Melanie Celeste Tello Fuentes los roles de la "
          "taxonomía CRediT (conceptualización, curación de datos, análisis formal, adquisición de financiamiento, investigación, metodología, "
          "administración del proyecto, recursos, software, supervisión, validación, visualización, redacción del borrador original, y "
          "redacción, revisión y edición)]")
FINANCIA = ("Los autores no recibieron ningún patrocinio para llevar a cabo este estudio-artículo. [PARA CONFIRMACIÓN DE LOS AUTORES: texto "
            "propuesto con la fórmula de la revista; si el estudio derivó de un proyecto financiado, indicar la entidad y el número de "
            "contrato, convenio o resolución]")
DATOS_DEP = (
    "Los datos de entrada proceden del conjunto público CTU-13, escenario 11 (captura CTU-Malware-Capture-Botnet-52), del Laboratorio "
    "Stratosphere de la Universidad Técnica Checa: https://mcfp.felk.cvut.cz/publicDatasets/CTU-Malware-Capture-Botnet-52/. El conjunto "
    "no declara una licencia explícita; solicita citar a {n:garcia2014} y se usó citándolo. Las figuras, los scripts que las generan y "
    "los datos derivados de los que proceden (figuras/, con las salidas guardadas de los trabajos de evaluación) se entregan con el "
    "manuscrito. [A COMPLETAR POR LOS AUTORES: depositar el código fuente de NetSentinel y los artefactos en un repositorio con "
    "identificador persistente (p. ej., DOI), indicar su URL y la licencia de uso y distribución, o declarar «No aplica» si no corresponde]"
)


def construir_cuerpo():
    _lista = []
    A = _lista.append
    # ---------------- portada
    A('<w:p><w:pPr><w:pStyle w:val="920"/><w:spacing/><w:ind/><w:rPr/></w:pPr><w:r><w:rPr><w:rFonts w:ascii="Montserrat" w:hAnsi="Montserrat" w:cs="Arial"/>'
      f'<w:b/><w:bCs/><w:sz w:val="30"/><w:szCs w:val="30"/><w:lang w:val="es-PE"/></w:rPr><w:t xml:space="preserve">{escape(TITULO_ES)}</w:t></w:r></w:p>')
    A('<w:p><w:pPr><w:spacing w:after="120" w:before="120" w:line="360" w:lineRule="auto"/><w:ind w:left="142"/><w:jc w:val="center"/><w:rPr/></w:pPr>'
      '<w:r><w:rPr><w:rFonts w:ascii="Montserrat" w:hAnsi="Montserrat" w:cs="Arial"/><w:b/><w:bCs/><w:sz w:val="26"/><w:szCs w:val="26"/>'
      f'<w:lang w:val="es-PE"/></w:rPr><w:t xml:space="preserve">{escape(TITULO_EN)}</w:t></w:r></w:p>')

    def lin(t, sz, bold=False, jc="center", after=0):
        return ('<w:p><w:pPr><w:spacing w:after="0" w:line="240" w:lineRule="auto"/><w:ind/>'
                f'<w:jc w:val="{jc}"/><w:rPr><w:sz w:val="{sz}"/><w:szCs w:val="{sz}"/></w:rPr></w:pPr><w:r><w:rPr>'
                '<w:rFonts w:eastAsia="Times New Roman" w:cs="Times New Roman"/>' + ("<w:b/>" if bold else "") +
                f'<w:sz w:val="{sz}"/><w:szCs w:val="{sz}"/></w:rPr><w:t xml:space="preserve">{escape(t)}</w:t></w:r></w:p>')
    A(lin("Roberto Enrique Quezada-Rodríguez¹,²*  y  Melanie Celeste Tello Fuentes¹,²", 20, True))
    A(p_vacio())
    A(lin("¹ Universidad Nacional de Trujillo, Ciudad Universitaria, Av. Juan Pablo II S/N, Urb. San Andrés, Trujillo, La Libertad, Perú", 18, jc="left"))
    A(lin("² Department of Systems Engineering, Universidad Nacional de Trujillo, Trujillo, La Libertad, Perú", 18, jc="left"))
    A(lin("* Autor de correspondencia: Roberto Enrique Quezada-Rodríguez. [PARA CONFIRMACIÓN DE LOS AUTORES: autor de correspondencia y "
          "asignación de afiliaciones a cada autor]", 18, jc="left"))
    A(p_vacio(True))
    A(lin("Roberto Enrique Quezada-Rodríguez: https://orcid.org/0009-0004-0869-3881; requezadaro@unitru.edu.pe", 18))
    A(lin("Melanie Celeste Tello Fuentes: https://orcid.org/0009-0007-4728-138X; mctellofu@unitru.edu.pe", 18))
    A(p_vacio(True))
    # ---------------- resumen
    A(h_plano("Resumen"))
    A(p_cuerpo(RESUMEN, 18))
    A('<w:p><w:pPr><w:spacing w:after="120" w:before="120" w:line="360" w:lineRule="auto"/><w:ind/><w:jc w:val="left"/><w:rPr>' + rpr(18) + '</w:rPr></w:pPr>'
      + run("Palabras clave:", 18, True) + run(" " + KW_ES, 18, False, True) + "</w:p>")
    A(h_plano("Abstract"))
    A(p_cuerpo(ABSTRACT, 18))
    A('<w:p><w:pPr><w:spacing w:after="120" w:before="120" w:line="360" w:lineRule="auto"/><w:ind/><w:jc w:val="left"/><w:rPr>' + rpr(18) + '</w:rPr></w:pPr>'
      + run("Keywords:", 18, True) + run(" " + KW_EN, 18, False, True) + "</w:p>")

    # ---------------- 1 introducción
    A(h1("Introducción"))
    for t in INTRO:
        A(p_cuerpo(t))

    # ---------------- 2 métodos
    A(h1("Materiales y métodos"))
    A(h2("Diseño del estudio"))
    A(p_cuerpo(
        "Se adoptó la ciencia del diseño {c:hevner2004}: se construyó un artefacto, NetSentinel, y se lo evaluó de forma preliminar con datos "
        "etiquetados y mediciones operativas. No se plantearon hipótesis de superioridad; se formularon tres preguntas: (i) qué hallazgos "
        "producen los detectores deterministas en una captura con tráfico malicioso conocido; (ii) cómo se comportan cuatro clasificadores "
        "bajo un protocolo que evita la fuga de información, y (iii) qué costo de cómputo y qué límites muestran la arquitectura y su "
        "evaluación. Los pasos fueron, en orden, la implementación, la ingesta de la captura, la ejecución de los detectores y del modelo de "
        "lenguaje, la preparación y partición de los datos, el entrenamiento y la evaluación de los clasificadores, el análisis estadístico y la "
        "medición de tiempos."))
    A(h2("Arquitectura de NetSentinel"))
    A(p_cuerpo(
        "NetSentinel se desplegó como un conjunto de contenedores en un único servidor (Docker Compose), de modo que los registros no salieron "
        "de la red de la organización (Figura 1). Un flujo de n8n, una herramienta de automatización de flujos de trabajo, ejecutó la ingesta "
        "cada 15 min mediante una llamada POST al punto final /ingest/run; un segundo flujo evaluó las alertas cada 5 min y un tercero realizó "
        "el mantenimiento. El servicio de aplicación (FastAPI, en Python) normalizó los registros de OPNsense y Suricata o los archivos de "
        "flujos, los almacenó en PostgreSQL 16, ejecutó los detectores y guardó los hallazgos. Una cadena de LangChain invocó el modelo "
        "llama3.2:3b mediante Ollama, en unidad central de procesamiento (CPU)."))
    A(p_cuerpo(
        "El acceso se controló con roles (RBAC, por su sigla en inglés) y toda acción relevante se escribió en una bitácora de auditoría. La "
        "interfaz (React, servida por nginx) mostró el panel de tráfico, los hallazgos y los reportes en PDF, DOCX y XLSX. Un laboratorio de "
        "aprendizaje automático (proceso ml-worker con Optuna, SHAP y predicción conforme) quedó separado del flujo operativo. Las pruebas se "
        "ejecutaron en un equipo con procesador Intel Core i5-12450H (12 hilos) y 16 GB de RAM."))
    A(leyenda("Figura", "Arquitectura de NetSentinel: el cálculo determinista y la evidencia residen en el servicio de aplicación, y el modelo de lenguaje solo interpreta hallazgos ya calculados"))
    A(figura("F1_arquitectura.png", "Diagrama de bloques de la arquitectura de NetSentinel: fuentes de registros, servicio de aplicación con detectores deterministas, cadena LangChain con Ollama, laboratorio de aprendizaje automático, base de datos, interfaz y flujos de n8n"))
    A(nota("n8n: herramienta de automatización de flujos de trabajo; OPNsense: cortafuegos de código abierto; Suricata: sistema de detección de "
           "intrusiones; CTU-13: conjunto público de capturas de la Universidad Técnica Checa usado como demostración; ML: aprendizaje "
           "automático; RBAC: control de acceso basado en roles; SMTP: protocolo simple de transferencia de correo. Azul: entradas; naranja: "
           "cálculo determinista; verde: interpretación; lila: almacenamiento; blanco: orquestación e interfaz. Fuente: elaboración propia."))

    A(h2("Datos y variables"))
    A(p_cuerpo(
        "Se usó el escenario 11 de CTU-13 (captura CTU-Malware-Capture-Botnet-52, archivo capture20110818-2.binetflow), publicado por el "
        "Laboratorio Stratosphere de la Universidad Técnica Checa {c:garcia2014}. Contiene flujos de red bidireccionales de una red de campus y "
        "una inundación de mensajes del protocolo de control de Internet (ICMP, por su sigla en inglés) generada por la botnet Rbot desde tres "
        "equipos infectados (147.32.84.165, 147.32.84.191 y 147.32.84.192) durante 16 min (971 s). Se importaron 107 194 registros de las "
        "107 252 líneas leídas, con 1 error de análisis; el registro de ingesta no desglosa las 57 líneas restantes. La base de datos recibió "
        "la captura dos veces (214 388 filas); todas las cifras de este artículo se calcularon con los 107 194 registros únicos."))
    A(p_cuerpo(
        "Las etiquetas originales se reagruparon en tres clases: Botnet (flujos «From-Botnet»), Normal (flujos «From-Normal» y «To-Normal») y "
        "Background, sin verdad conocida. Solo los 10 882 flujos de las dos primeras clases (8 164 Botnet y 2 718 Normal) se usaron para "
        "entrenar y evaluar; los 96 312 flujos Background (89,8 %) se excluyeron (Tabla 1)."))
    A(p_cuerpo(
        "Cada flujo se describió con 10 variables numéricas (duración, bytes enviados, recibidos y totales, paquetes, bytes por paquete, "
        "proporción de bytes salientes, bytes por segundo, paquetes por segundo y puerto de destino) y 6 categóricas (protocolo, estado de la "
        "conexión, sentido del flujo, dirección de red y clase de puerto de destino y de origen). Se excluyeron por diseño las direcciones IP y "
        "MAC, los identificadores, la marca de tiempo absoluta y las etiquetas. Las variables de magnitud se transformaron con log(1 + x) y se "
        "escalaron en el modelo lineal; los valores faltantes se imputaron con la mediana y las variables categóricas se codificaron como "
        "indicadoras, agrupando las categorías con menos de 20 casos. Todo el preprocesamiento se ajustó dentro de cada pliegue."))
    P = TB["partition"]
    tot = 10882
    A(leyenda("Tabla", "Composición del conjunto de datos y partición por bloques temporales de 10 s"))
    filas = [
        ["Registros importados (únicos)", miles(107194), "—", "—", "—", "Ingesta y detectores"],
        ["Background, sin verdad conocida", miles(96312), "—", "—", "—", "Excluidos de la evaluación"],
        ["Flujos etiquetados", miles(10882), miles(8164), miles(2718), "97 (19)", "Conjunto de modelado"],
    ]
    for nombre, k, uso in (("Desarrollo", "dev", "Validación cruzada anidada 5 × 3 y búsqueda de hiperparámetros"),
                           ("Validación", "val", "Umbral, calibración y predicción conforme"),
                           ("Prueba", "test", "Evaluación única")):
        nb, nn = P[k]["Botnet"]["rows"], P[k]["Normal"]["rows"]
        grupos = {"dev": 66, "val": 8, "test": 23}[k]
        filas.append([f"{nombre} ({fm(100 * (nb + nn) / tot, 1)} %)", miles(nb + nn), miles(nb), miles(nn), f"{grupos} ({P[k]['Botnet']['groups']})", uso])
    A(tabla([2350, 1000, 950, 950, 1350, 2686], ["Conjunto", "Flujos", "Botnet", "Normal", "Bloques (con Botnet)", "Uso"], filas))
    A(nota("Flujos únicos del escenario 11 de CTU-13. Un bloque temporal es un grupo de flujos que comparten una ventana de 10 s; 19 de los 97 "
           "bloques contienen ambas clases. De los 1 118 flujos Botnet de la prueba, 1 097 son del ataque ICMP y 21 son de otros protocolos "
           "(15 UDP y 6 TCP); ninguno de esos 21 flujos estuvo en desarrollo ni en validación. UDP: protocolo de datagramas de usuario; TCP: "
           "protocolo de control de transmisión. Los porcentajes se refieren a los 10 882 flujos etiquetados."))

    A(h2("Detectores deterministas"))
    A(p_cuerpo(
        "Cinco detectores operaron sobre el tráfico saliente de la ventana de análisis (24 h por defecto) con los parámetros por defecto de la "
        "Tabla 2. El detector de beaconing agrupó las conexiones por origen, destino, puerto y protocolo, calculó el coeficiente de variación "
        "(CV = desviación estándar/media) de los intervalos entre conexiones y excluyó los destinos de multidifusión, difusión y enlace local. "
        "El de puertos inusuales agregó el tráfico por puerto y protocolo. El de exfiltración comparó los bytes enviados por equipo con su "
        "historial mediante una puntuación z con piso en la desviación, y el de anomalía de los equipos de mayor tráfico (top talkers) comparó "
        "el número de conexiones y de destinos únicos con el historial propio o con los demás equipos, excluyendo al evaluado. Las alertas "
        "IDS se agruparon por firma y severidad; la captura usada son flujos y no contiene alertas IDS. Cada hallazgo recibió un puntaje de 0 "
        "a 100 y una severidad (crítica ≥ 85; alta ≥ 70; media ≥ 50; baja ≥ 30)."))
    A(leyenda("Tabla", "Detectores deterministas de NetSentinel: condiciones de emisión y puntaje"))
    A(tabla([1500, 3300, 4486], ["Detector", "Condición de emisión (valores por defecto)", "Puntaje (0 a 100)"], [
        ["Beaconing", "≥ 10 conexiones; intervalo medio ≥ 1 s; CV ≤ 0,25; puntaje ≥ 60; se excluyen destinos de grupo",
         "100·(0,5·R + 0,2·S + 0,2·N + 0,1·D); R = 1 − 0,6·CV/0,25; S = 1 − mín(CV de bytes; 1); N = 0,5 + 0,5·log10(n/10); "
         "D = duración/7 200 s; N y D acotados a [0; 1]; × 0,7 si el puerto es 53 o 123"],
        ["Puertos inusuales", "Puerto fuera de la lista común y de la línea base; ≥ 3 conexiones; máximo 25 hallazgos",
         "35 + 25·f(conexiones) + 20·f(orígenes) + 20·f(bytes); f = log10(conexiones/3 + 1)/2; orígenes/5; log10(MB + 1)/2; cada f acotada a [0; 1]"],
        ["Exfiltración", "≥ 52,4 MB (52 428 800 B) enviados; z ≥ 3 frente al historial o, sin historial, relación salida/entrada ≥ 3",
         "30 + 70·(0,35·z/6 + 0,4·V + 0,25·Q); V = log2(bytes/52,4 MB)/4; Q = relación/20; acotados a [0; 1] (sin historial: 0,6·V + 0,4·Q)"],
        ["Anomalía de equipos de mayor tráfico", "≥ 200 conexiones o ≥ 25 destinos únicos; z ≥ 3 frente al historial o a los demás equipos (≥ 5)",
         "40 + 60·acotar((z − 3)/9)"],
        ["Alertas IDS", "Agrupación por firma y severidad del IDS (no aplicable a esta captura)",
         "Base 70, 50 o 30 según la severidad + 20·log10(n)/3 + 5·orígenes/10"],
    ], sz=16, alin=["left", "left", "left"], keep_all=False))
    A(nota("CV: coeficiente de variación de los intervalos; n: número de conexiones; z: puntuación estándar con piso en la desviación "
           "(máx[desviación; 0,1·media; 1]); MB: megabytes. El puntaje de alertas IDS se muestra por completitud; ese detector no produjo "
           "hallazgos en este estudio."))

    A(h2("Interpretación mediante el modelo de lenguaje"))
    A(p_cuerpo(
        "Cada hallazgo se envió a una cadena de LangChain que invocó llama3.2:3b (3 000 millones de parámetros) mediante Ollama, en CPU. El "
        "mensaje de sistema indicó que las métricas ya estaban calculadas y que no debían recalcularse; la evidencia se entregó entre marcas de "
        "datos no confiables, con la instrucción de ignorar cualquier orden contenida en ellos, como defensa frente a la inyección indirecta de "
        "órdenes {p:greshake2023,woesle2026}. La salida debía ser un objeto JSON (notación de objetos de JavaScript) con veredicto (real, ruido o incierto), confianza de 0 a 1, "
        "explicación y recomendación, validado con un esquema; si el modelo no respondía o devolvía una salida inválida, se usó una plantilla "
        "determinista. El modelo podía proponer un ajuste de severidad de un nivel, pero no calculaba ni modificaba puntajes ni métricas. "
        "Los hallazgos de las capturas no tienen etiqueta propia, de modo que los veredictos no se compararon con una verdad de referencia."))

    A(h2("Protocolo de evaluación de los clasificadores"))
    A(p_cuerpo(
        "El flujo operativo y el protocolo se resumieron en la Figura 2. Primero se comprobó qué clave de agrupación permitía separar "
        "desarrollo, validación y prueba sin que un mismo grupo apareciera en dos particiones. Agrupar por equipo de origen no fue viable: solo "
        "3 equipos generaron tráfico Botnet y la partición de prueba habría quedado sin grupos Botnet. Agrupar por par origen-destino tampoco "
        "alcanzó el mínimo de 30 filas Botnet en validación ni en prueba. Se agrupó entonces por bloques temporales de 10 s (97 grupos; los "
        "bloques de 5 s también fueron viables y los de 15 s o más no lo fueron). La partición 70/15/15 por grupos, estratificada por clase y "
        "con semilla 42, produjo 7 694 flujos de desarrollo, 1 663 de validación y 1 525 de prueba (Tabla 1). Se verificó que ningún grupo "
        "estuviera en dos particiones y se contaron los vectores de variables duplicados entre particiones."))
    A(leyenda("Figura", "Flujo operativo de NetSentinel (a) y protocolo de evaluación de los clasificadores (b)"))
    A(figura("F2_flujo_y_protocolo.png", "Diagrama de dos paneles: a, canal operativo de ingesta, detectores, lista de permitidos y denegados, cadena de modelo de lenguaje y alerta con reporte; b, protocolo de evaluación con exclusión de Background, agrupación por bloques temporales y partición en desarrollo, validación y prueba"))
    A(nota("cron: programador de tareas; LLM: modelo de lenguaje de gran tamaño; PDF, DOCX y XLSX: formatos de los reportes; VC: validación "
           "cruzada; TPE: estimador de Parzen estructurado en árbol. n = 10 882 flujos etiquetados; el preprocesamiento se ajustó dentro de cada "
           "pliegue. Fuente: elaboración propia."))
    A(p_cuerpo(
        "Se compararon cuatro clasificadores (regresión logística, Random Forest, boosting de histogramas y XGBoost) con una línea base trivial, "
        "que predice siempre Botnet, y con los detectores deterministas (un flujo fue positivo si pertenecía a un grupo marcado por beaconing "
        "o puertos inusuales, con la configuración por defecto aplicada a toda la captura como una sola ventana). Los hiperparámetros se "
        "optimizaron con Optuna (muestreador TPE, estimador de Parzen estructurado en árbol, con 8 pruebas iniciales aleatorias y poda por mediana), con 20 pruebas por estudio; el objetivo "
        "fue el área bajo la curva de precisión-exhaustividad (PR-AUC) media de 3 pliegues internos. El desempeño se estimó con validación "
        "cruzada anidada de 5 pliegues externos × 3 internos (StratifiedGroupKFold) sobre el desarrollo. El modelo final se reajustó con todo el "
        "desarrollo; el umbral (máximo F1) y la calibración isotónica se ajustaron en validación, y la partición de prueba se evaluó una sola "
        "vez por modelo. Con las probabilidades calibradas se construyó una predicción conforme dividida con cobertura nominal de 90 % y una "
        "alerta de fuera de distribución (≥ 25 % de las variables fuera del rango de los percentiles 1 a 99 del entrenamiento)."))
    A(p_cuerpo(
        "Los espacios de búsqueda (por ejemplo, para XGBoost: tasa de aprendizaje de 0,01 a 0,3 en escala logarítmica; profundidad de 2 a 10; "
        "submuestreo de 0,5 a 1; peso de la clase positiva de 1 a 50) y las versiones de las librerías (Python 3,11; scikit-learn 1,9; "
        "XGBoost 3,2; Optuna 5,0; SHAP 0,51) se guardaron con cada ejecución. La importancia de variables se estimó con SHAP sobre XGBoost y "
        "por permutación (caída del PR-AUC, 5 repeticiones), y se midió su estabilidad entre pliegues con la W de Kendall."))

    A(h2("Métricas y análisis estadístico"))
    A(p_cuerpo(
        "Se calcularon precisión, exhaustividad, F1, MCC {c:chicco2021}, exactitud balanceada, área bajo la curva característica operativa del "
        "receptor (ROC-AUC), PR-AUC (precisión promedio) y puntaje de Brier. Los intervalos de confianza (IC) del 95 % de la validación cruzada se "
        "calcularon con la distribución t de Student (4 grados de libertad) y por bootstrap; los de las proporciones en la prueba, con el método de "
        "Wilson, que supone observaciones independientes e ignora la agrupación en bloques. Las diferencias entre modelos se contrastaron con la "
        "prueba de Friedman (5 modelos y 5 pliegues), pruebas de Wilcoxon exactas por pares con corrección de Holm sobre el PR-AUC por pliegue, d "
        "de Cohen pareada y delta de Cliff como tamaños de efecto, la prueba exacta de McNemar sobre las predicciones de prueba y un bootstrap "
        "de 1 000 remuestreos de grupos con reemplazo para las diferencias de PR-AUC y ROC-AUC. Se reportaron todos los resultados, también los "
        "no significativos. Con 5 pliegues, el menor valor p alcanzable con Wilcoxon bilateral es 0,0625."))
    A(h2("Mediciones operativas y reproducibilidad"))
    A(p_cuerpo(
        "Los tiempos de importación, generación de reportes y entrenamiento se leyeron de las marcas de tiempo de la base de datos; los de los "
        "puntos finales del panel y del modelo de lenguaje, del registro de la prueba de despliegue. Las cifras se extrajeron mediante consultas "
        "de solo lectura a la base de datos y a los artefactos guardados. Las figuras se generaron con scripts de Python (Matplotlib) a 600 ppp "
        "con una paleta apta para daltonismo, y se entregan con los datos de los que proceden."))

    # ---------------- 3 resultados y discusión
    A(h1("Resultados y discusión"))
    A(h2("Perfil de los datos y separabilidad de las clases"))
    A(p_cuerpo(
        "De los 10 882 flujos etiquetados, 8 164 (75,0 %) fueron Botnet; un clasificador que predijera siempre Botnet obtendría una precisión de "
        "0,733 en la prueba (Tabla 1). El 99,7 % de los flujos Botnet (8 143 de 8 164) correspondió a la inundación ICMP de dos equipos (4 144 y "
        "3 999 flujos); los 21 flujos restantes (15 UDP y 6 TCP, 7 por equipo) fueron tráfico de tipo comando y control (C&C). Las clases se "
        "separaron casi de forma trivial: la distancia de Kolmogórov-Smirnov (KS) entre clases fue 0,997 para los bytes por paquete (mediana de "
        "78 B en Normal y de 1 066 B en Botnet) y 0,975 para los bytes enviados. Además, 323 vectores de variables idénticos aparecieron en más de "
        "una partición, lo que afectó al 76,2 % de las filas: aun sin fuga de grupos, el modelo vio ejemplos prácticamente iguales a los de la "
        "prueba. Este perfil coincide con la dificultad de usar aprendizaje automático fuera del mundo cerrado de un conjunto {c:sommer2010} y con "
        "los estudios de generalización entre conjuntos de datos {p:cantone2024,verkerken2021}."))

    A(h2("Hallazgos de los detectores deterministas"))
    n_b = sum(1 for h in PRIMERA if h["finding_type"] == "beaconing")
    assert len(PRIMERA) == 51 and n_b == 23
    A(p_cuerpo(
        "Con la configuración por defecto, el procesamiento de la captura produjo 51 hallazgos: 25 de puertos inusuales, 23 de beaconing y 3 de "
        "anomalía de equipos de mayor tráfico, sin hallazgos de exfiltración ni de alertas IDS (Tabla 3). Hubo 2 hallazgos críticos, 17 altos, "
        "30 medios y 2 bajos. El más regular fue la comunicación de 147.32.84.215 hacia 86.49.87.107:6889 (33 conexiones; intervalo medio de "
        "30,014 s; CV = 0,000). Catorce de los 23 hallazgos de beaconing se dirigieron al puerto 6881, asignado por convención a BitTorrent. "
        "Ninguno de los 51 hallazgos involucró a los tres equipos infectados."))
    A(leyenda("Tabla", "Hallazgos de los detectores deterministas en la primera carga de la captura"))
    tipos = [("beaconing", "Beaconing"), ("unusual_port", "Puertos inusuales"), ("talker_anomaly", "Anomalía de equipos de mayor tráfico"),
             ("exfiltration", "Exfiltración"), ("ids_alert", "Alertas IDS")]
    filas = []
    tot_f = [0, 0, 0, 0, 0, 0, 0]
    for k, nombre in tipos:
        hs = [h for h in PRIMERA if h["finding_type"] == k]
        sev = [sum(1 for h in hs if h["severity"] == s) for s in ("critical", "high", "medium", "low")]
        llm = sum(1 for h in hs if h["llm_verdict"])
        inf = sum(1 for h in hs if h["src_ip"] in INFECTADOS or h["dst_ip"] in INFECTADOS)
        v = [len(hs)] + sev + [llm, inf]
        tot_f = [a + b for a, b in zip(tot_f, v)]
        filas.append([nombre] + [str(x) for x in v])
    filas.append(["Total"] + [str(x) for x in tot_f])
    assert tot_f[0] == 51 and tot_f[6] == 0
    A(tabla([2386, 600, 1000, 750, 850, 750, 1300, 1650], ["Tipo de hallazgo", "n", "Crítica", "Alta", "Media", "Baja", "Con veredicto del LLM", "Con equipos infectados"],
            filas, negrita_ult=True))
    A(nota("n: número de hallazgos creados al importar la captura por primera vez (51 hallazgos; la recarga accidental del mismo archivo creó 4 "
           "hallazgos adicionales que se excluyen de la tabla). Severidad según el puntaje: crítica ≥ 85; alta ≥ 70; media ≥ 50; baja ≥ 30. "
           "Los dos veredictos del LLM (modelo de lenguaje) fueron «incierto». Los equipos infectados son 147.32.84.165, 147.32.84.191 y "
           "147.32.84.192, tomados de las etiquetas de la captura."))
    A(p_cuerpo(
        "De los 246 grupos origen-destino-puerto con al menos 10 conexiones, 211 tuvieron un CV mayor que 0,25, 13 cumplieron el umbral de CV sin "
        "alcanzar el puntaje mínimo o por ser destinos de grupo, y 22 generaron hallazgo (Figura 3). La base de datos conservó 23 hallazgos de "
        "beaconing; el que falta en la reproducción, un anuncio periódico de multidifusión del protocolo de administración de grupos de Internet "
        "(IGMP; 147.32.87.1 hacia 224.0.0.1), no se reproduce con el código actual, que excluye los destinos de grupo."))
    A(leyenda("Figura", "Regularidad temporal de los grupos origen-destino-puerto de la captura frente al umbral de beaconing"))
    A(figura("F3_regularidad_intervalos.png", "Gráfico de dispersión del coeficiente de variación de los intervalos frente al número de conexiones de cada grupo, con el umbral de 0,25 y los 22 hallazgos de beaconing emitidos"))
    A(nota("n = 246 grupos origen-destino-puerto con al menos 10 conexiones en 16 min. CV: coeficiente de variación de los intervalos entre "
           "conexiones (desviación estándar/media); ambos ejes en escala logarítmica. Los rombos (22) son los hallazgos que reproduce el código "
           "actual; la base de datos conservó un hallazgo adicional de multidifusión (IGMP) que el código actual excluye. Ningún hallazgo "
           "involucró a los equipos infectados. Datos: figuras/datos/F3_regularidad_grupos.csv."))
    A(p_cuerpo(
        "Frente a las etiquetas, los detectores no identificaron ninguno de los 1 118 flujos Botnet de la prueba (exhaustividad = 0,000; IC 95 % "
        "de Wilson de 0,000 a 0,003; MCC = −0,798) y marcaron 287 de los 407 flujos Normal (70,5 %) (Tabla 4). La omisión es estructural y no "
        "estadística: los detectores analizan el tráfico saliente, y la inundación ICMP iba de equipos internos a 147.32.96.69, también interno, "
        "por lo que no entró en su análisis. Aun si se hubiera analizado, cada equipo envió 29,7 MB y 29,3 MB, por debajo del mínimo de 52,4 MB "
        "del detector de exfiltración, y solo 3 flujos salientes por equipo infectado (2 TCP y 1 UDP) tuvieron un destino externo, lejos de las 10 "
        "conexiones que exige el detector de beaconing. La periodicidad del tráfico de comando y control {c:oskera2025} solo es utilizable "
        "cuando hay suficientes conexiones por destino en la ventana, condición que esta captura no cumplió."))

    A(h2("Veredictos del modelo de lenguaje"))
    A(p_cuerpo(
        "De los hallazgos de la primera carga, 2 recibieron veredicto del modelo de lenguaje (beaconing hacia 86.49.87.107:6889 y el anuncio "
        "IGMP), y ambos fueron «incierto», con confianza de 0,6 y 0,5. Los 4 hallazgos adicionales de la recarga accidental también fueron "
        "«incierto» (confianza de 0,5). Ningún veredicto fue «real» ni «ruido»: el modelo se comportó de forma conservadora. Como el diseño no "
        "incluyó una verdad de referencia por hallazgo, no pudo calcularse su exactitud, y 6 veredictos no bastan para estimar ninguna tasa. "
        "{n:palma2025} informaron un mejor desempeño de los modelos de lenguaje que el del aprendizaje automático clásico en la clasificación de "
        "registros, con llama3.2:3b entre los modelos evaluados; el comportamiento observado aquí no confirma ni refuta ese resultado, porque la "
        "tarea y los datos difieren."))

    A(h2("Desempeño de los clasificadores"))
    cvrows = {nm(r["model"]): r for r in [x for x in J2["tables"] if x["id"] == "metrics_cv"][0]["rows"]}
    terows = {nm(r["model"]): r for r in [x for x in J2["tables"] if x["id"] == "metrics_test"][0]["rows"]}
    base = {nm(r["name"]): r for r in [x for x in J2["tables"] if x["id"] == "baselines"][0]["rows"]}
    xg = terows["XGBoost"]
    rec_ic = wilson(xg["tp"], xg["tp"] + xg["fn"])
    A(p_cuerpo(
        "En la validación cruzada externa, la regresión logística obtuvo F1 = 1,000 ± 0,000 y Random Forest, boosting de histogramas y XGBoost "
        "0,994 ± 0,014, frente a 0,554 ± 0,394 de la línea base (la desviación de esta última refleja la prevalencia de Botnet entre pliegues, de "
        "0,04 a 0,88). En la partición de prueba, los cuatro modelos produjeron la misma matriz de confusión: 407 verdaderos negativos, 0 falsos "
        "positivos, 21 falsos negativos y 1 097 verdaderos positivos (precisión = 1,000; exhaustividad = 0,981, IC 95 % de Wilson de "
        f"{fm(rec_ic[0])} a {fm(rec_ic[1])}; F1 = 0,991; MCC = 0,966), frente a F1 = 0,846 y MCC = 0,000 de la línea base (Tabla 4; Figura 4). "
        "Las diferencias entre los cuatro modelos aparecieron solo en la cuarta cifra decimal de la PR-AUC (0,995 a 0,996) y del puntaje de Brier "
        "(0,0135 a 0,0138). El IC t del 95 % de varias métricas rebasó 1 (p. ej., precisión de 0,953 a 1,022), lo que muestra que la aproximación "
        "normal con 5 pliegues no es adecuada para métricas acotadas."))
    # Tabla 4
    A(leyenda("Tabla", "Desempeño en validación cruzada externa y en la partición de prueba (evaluación única)"))
    filas = []
    orden = ["Línea base trivial", "Regresión logística", "Random Forest", "Boosting de histogramas", "XGBoost"]
    corto = {"Línea base trivial": "Línea base trivial", "Boosting de histogramas": "Boosting de histogramas"}
    for m in orden:
        c, t = cvrows[m], terows[m]
        ic = wilson(t["tp"], t["tp"] + t["fn"])
        filas.append([m, f"{fm(c['f1'])} ± {fm(c['f1_std'])}", f"{fm(c['pr_auc'])} ± {fm(c['pr_auc_std'])}", fm(t["precision"]),
                      f"{fm(t['recall'])} [{fm(ic[0])}; {fm(ic[1])}]", fm(t["f1"]), fm(t["mcc"]), fm(t["pr_auc"]), fm(t["brier"], 4), f"{t['fp']} / {t['fn']}"])
    d = base["Detectores deterministas de NetSentinel"]
    ic0 = wilson(0, 1118)
    filas.append(["Detectores deterministas", "n. d.", "n. d.", fm(d["precision"]), f"{fm(d['recall'])} [{fm(ic0[0])}; {fm(ic0[1])}]", fm(d["f1"]),
                  fm(d["mcc"]), "n. d.", "n. d.", "287 / 1\u00a0118"])
    A(tabla([1250, 950, 1000, 910, 1450, 700, 700, 760, 800, 766],
            ["Método", "F1 VC (media ± desv.)", "PR-AUC VC (media ± desv.)", "Precisión", "Exhaustividad [IC 95 %]", "F1", "MCC", "PR-AUC", "Brier", "FP / FN"],
            filas, sz=15, alin=["left"] + ["center"] * 9, margen=60))
    A(nota("VC: validación cruzada anidada externa de 5 pliegues (media ± desviación estándar). Prueba: n = 1 525 flujos (1 118 Botnet y 407 Normal), "
           "umbral elegido en validación (0,5 en todos los casos), una sola evaluación por modelo. IC 95 % de Wilson de la exhaustividad: supone "
           "independencia entre flujos e ignora la agrupación en bloques, por lo que es optimista. PR-AUC: precisión promedio. FP / FN: falsos "
           "positivos / falsos negativos. Los detectores se aplicaron a toda la captura como una sola ventana y se mapearon a flujos "
           "(aproximación); n. d.: no disponible. ROC-AUC (calibrada) de la prueba: 0,991 a 0,992 en los cuatro modelos."))
    A(leyenda("Figura", "Desempeño de los clasificadores en la partición de prueba: curvas de precisión-exhaustividad (a) y ROC (b), y matriz de confusión de XGBoost (c)"))
    A(figura("F4_desempeno_prueba.png", "Tres paneles: curvas de precisión-exhaustividad, curvas ROC de los cuatro modelos y la línea base, y matriz de confusión de XGBoost con 407 verdaderos negativos, 21 falsos negativos y 1097 verdaderos positivos"))
    A(nota("n = 1 525 flujos (1 118 Botnet y 407 Normal); evaluación única con umbral 0,5. Las curvas de los cuatro modelos se superponen casi por "
           "completo y la matriz de confusión fue idéntica en los cuatro. Las áreas por regla del trapecio (XGBoost: PR 0,997; ROC 0,991) difieren "
           "ligeramente de la precisión promedio de la Tabla 4 (0,995). ROC: característica operativa del receptor. Datos: figuras/datos/raw/runs/."))
    A(p_cuerpo(
        "La calibración isotónica se aplicó porque la validación tenía al menos 1 000 flujos y 100 por clase; redujo el ROC-AUC de XGBoost de 0,997 "
        "a 0,991 al generar empates en las probabilidades. La predicción conforme alcanzó una cobertura empírica de 0,986 frente a la nominal de "
        "0,90, con conjuntos de ancho medio 0 y ningún caso ambiguo: cumplió el nivel nominal porque los conjuntos fueron casi siempre unitarios "
        "y correctos, no porque cuantificara una incertidumbre útil. No se comparó el desempeño con las cifras de trabajos previos sobre "
        "CTU-13 {p:velasco2021,velasco2023,hossain2023}, porque emplean otros escenarios, particiones y etiquetas; una comparación válida "
        "exigiría repetir la misma partición {c:garcia2014}."))

    A(h2("Qué aprendieron los modelos"))
    A(p_cuerpo(
        "La explicación con SHAP sobre XGBoost mostró que los bytes por paquete concentraron el 84 % del valor absoluto medio de SHAP (5,72 "
        "log-odds, frente a 0,44 del estado de la conexión y 0,43 de los bytes enviados); en la permutación solo esa variable redujo el PR-AUC "
        "(0,052) y las demás tuvieron una caída nula (Figura 5). La estabilidad entre pliegues fue alta (W de Kendall = 0,87; τ medio = 0,77), y "
        "las discrepancias de rango entre SHAP y permutación afectaron a variables de importancia casi nula. El resultado coincide con el perfil "
        "de los datos: los paquetes de la inundación pesan 1 066 B frente a una mediana de 78 B del tráfico Normal. El protocolo por sí solo no "
        "es la causa: 2 089 de los 2 718 flujos Normal (76,9 %) también son ICMP, de modo que el modelo no aprendió «ICMP es Botnet», sino el "
        "tamaño del paquete."))
    A(leyenda("Figura", "Importancia de variables de XGBoost: valores SHAP medios absolutos (a) e importancia por permutación (b)"))
    A(figura("F5_importancia_variables.png", "Dos gráficos de barras horizontales: bytes por paquete domina la importancia con 84 por ciento del valor SHAP absoluto medio y es la única variable con caída de PR-AUC por permutación"))
    A(nota("Se muestran las 9 variables con mayor importancia. SHAP: valores de Shapley aditivos, en log-odds. Permutación: caída del PR-AUC al "
           "permutar la variable (5 repeticiones; media ± desviación estándar). Estabilidad entre pliegues: W de Kendall = 0,87. Datos: "
           "figuras/datos/F5_importancias.json."))
    A(p_cuerpo(
        "Las 21 omisiones fueron exactamente los 21 flujos Botnet no ICMP, todos en la partición de prueba: el modelo no vio tráfico de C&C "
        "durante el entrenamiento ni la validación, de modo que su exhaustividad fue 1,000 (1 097 de 1 097) para la inundación ICMP y 0,000 "
        "(0 de 21) para el resto. En consecuencia, el clasificador detectó una inundación por el tamaño del paquete, no «botnets» en general. "
        "La explicación con SHAP, que otros trabajos usan para auditar la detección de intrusiones {p:saied2025,gaspar2024}, sirvió aquí para "
        "diagnosticar ese atajo y no para justificar el modelo."))

    A(h2("Comparaciones estadísticas"))
    fr = J2["friedman"]
    A(p_cuerpo(
        f"La prueba de Friedman detectó diferencias entre los cinco modelos (χ² = {fm(fr['statistic'], 2)}; 4 grados de libertad; p = {fm(fr['p_value'])}), "
        "pero la señal provino de la línea base, con rango medio 5,0 frente a 2,2 a 3,0 de los demás. Las pruebas de Wilcoxon exactas no pudieron "
        "alcanzar significación: p = 0,0625 en las 4 comparaciones con la línea base (p con Holm = 0,625) y 0 de 10 comparaciones significativas "
        "tras la corrección (Tabla 5). Los tamaños de efecto frente a la línea base fueron grandes (d de Cohen pareada de −1,33 a −1,35; delta de "
        "Cliff = −1,00) y, entre los cuatro modelos, pequeños o moderados (|d| ≤ 0,67; |delta| ≤ 0,40), sin valor inferencial. La prueba de "
        "McNemar exacta dio b = 21, c = 407 y p = 6,6 × 10⁻⁹⁴ entre la línea base y cada modelo, y b = c = 0 y p = 1,00 entre los cuatro modelos, "
        "cuyas predicciones fueron idénticas. El bootstrap por grupos (23 grupos de prueba) dio, para la diferencia de PR-AUC entre la línea base "
        "y XGBoost (−0,262), un IC 95 % de −0,461 a 0,000, que no excluye el cero, y solo 5 de 20 IC excluyeron el cero. La discrepancia con "
        "McNemar ilustra el efecto de ignorar la agrupación: McNemar trata los 1 525 flujos como independientes y el bootstrap, los 23 grupos."))
    A(leyenda("Tabla", "Comparaciones por pares: Wilcoxon exacto con Holm sobre el PR-AUC de los pliegues externos y McNemar exacto sobre la prueba"))
    wil = {(nm(r["a"]), nm(r["b"])): r for r in [x for x in J2["tables"] if x["id"] == "stat_wilcoxon"][0]["rows"]}
    mc = {(nm(r["a"]), nm(r["b"])): r for r in [x for x in J2["tables"] if x["id"] == "stat_mcnemar"][0]["rows"]}
    filas = []
    for (a, b), w in wil.items():
        m = mc[(a, b)]
        pm = m["p"]
        ptxt = "1,000" if pm >= 0.999 else ("6,6 × 10⁻⁹⁴" if pm < 1e-50 else fm(pm))
        filas.append([f"{a} – {b}", fm(w["mean_diff"]), fm(w["cohen_dz"], 2) if w["cohen_dz"] is not None else "n. d.", fm(w["cliffs_delta"], 2),
                      fm(w["p"], 4), fm(w["p_holm"], 3), f"{m['b_count']} / {m['c_count']}", ptxt])
    A(tabla([2386, 900, 800, 800, 1000, 750, 1050, 1600], ["Comparación (A – B)", "Dif. media PR-AUC (A − B)", "d de Cohen", "Delta de Cliff", "p Wilcoxon", "p Holm", "b / c McNemar", "p McNemar"],
            filas, sz=15, alin=["left"] + ["center"] * 7, margen=60))
    A(nota("n = 5 pliegues externos pareados para Wilcoxon (bilateral; el menor p alcanzable es 0,0625) y n = 1 525 flujos para McNemar. b: A "
           "acierta y B falla; c: A falla y B acierta. La d de Cohen no está definida cuando la diferencia es constante (n. d.). Friedman: χ² = 16,00; "
           "p = 0,003. Un resultado no significativo no prueba que los modelos sean equivalentes. McNemar no se corrigió por comparaciones "
           "múltiples."))

    A(h2("Costos y desempeño operativo"))
    A(p_cuerpo(
        "Los puntos finales del panel respondieron en 14 a 472 ms (registro de la prueba de despliegue). La importación de 107 194 registros "
        "tomó 9,66 s (unos 11 100 registros por segundo). El intervalo entre marcas de tiempo de reportes consecutivos fue de 37 a 629 ms "
        "(n = 35), una aproximación del tiempo de generación (Figura 6). El análisis con el modelo de lenguaje fue el cuello de botella: de 28 a "
        "37 s por hallazgo y 74,5 s para una narración bajo demanda (registro de la prueba de despliegue). Un lote de 30 hallazgos requeriría de "
        "14,0 a 18,5 min (30 × 28 s a 30 × 37 s), comparable o superior a la cadencia de ingesta de 15 min, por lo que, sin priorización o "
        "concurrencia, el procesamiento podría acumular retraso. El entrenamiento anidado tomó de 64,1 s (regresión logística) a 1 073,2 s "
        "(Random Forest) por modelo. Son mediciones de una sola ejecución en un equipo, sin repeticiones, y no permiten estimar su variabilidad."))
    A(leyenda("Figura", "Tiempos observados por operación (escala logarítmica)"))
    A(figura("F6_latencias.png", "Gráfico de rangos en escala logarítmica de los tiempos por operación: puntos finales del panel, reportes, importación, análisis con modelo de lenguaje, narración y entrenamiento"))
    A(nota("Azul: valores leídos de la base de datos o de los artefactos (35 intervalos entre reportes; 1 importación; 4 entrenamientos con "
           "validación cruzada anidada). Naranja: valores del registro de la prueba de despliegue, no medidos de nuevo para este estudio. Equipo: "
           "Intel Core i5-12450H y 16 GB de RAM; modelo de lenguaje en CPU. Una sola ejecución por operación. Datos: figuras/datos/F6_tiempos.json."))

    A(h2("Validez y limitaciones"))
    A(p_cuerpo(
        "*Validez interna.* La partición por bloques temporales es menos exigente que la partición por equipo: 5 equipos de origen (2 de ellos "
        "Botnet) y 16 destinos aparecieron en más de una partición, los bloques contiguos son parecidos entre sí {c:kapoor2023} y el 76,2 % de las "
        "filas tuvo un vector idéntico en otra partición. El umbral y la calibración se ajustaron en validación y la prueba se evaluó una sola "
        "vez por modelo, pero los cuatro modelos se compararon sobre la misma prueba."))
    A(p_cuerpo(
        "*Validez externa.* Se usó una captura de 16 min de 2011, con 3 equipos infectados en una red de campus y solo flujos, sin paquetes ni "
        "tráfico cifrado actual. El 89,8 % de los flujos (Background) se excluyó por carecer de verdad conocida, por lo que no se estimó la tasa "
        "de falsos positivos en tráfico real. El modelo de lenguaje fue pequeño y se usó sin ajuste; el desempeño de otros tamaños no se evaluó."))
    A(p_cuerpo(
        "*Validez de constructo.* Las etiquetas Botnet y Normal de CTU-13 provienen de las reglas de captura de sus autores {c:garcia2014}; aquí, "
        "«Botnet» equivale en la práctica a flujos ICMP de gran tamaño, de modo que un F1 alto no mide la capacidad de detectar botnets. La "
        "comparación con los detectores mapeó grupos a flujos, lo que es una aproximación de la operación real por ventanas de 24 h."))
    A(p_cuerpo(
        "*Validez de la conclusión estadística.* Con 5 pliegues, ninguna comparación de Wilcoxon podía ser significativa tras Holm; los IC t "
        "rebasaron el intervalo [0; 1] de las métricas; McNemar ignoró la agrupación en bloques; y el empate de los cuatro modelos no prueba "
        "equivalencia. Estas limitaciones se resumen en la Tabla 6."))
    A(leyenda("Tabla", "Diagnóstico cuantificado de los límites del estudio"))
    A(tabla([2000, 4286, 3000], ["Límite", "Evidencia cuantificada", "Implicación"], [
        ["Un solo escenario corto", "1 captura de 16 min (971 s); 3 equipos infectados; 2011", "No permite extrapolar a otras redes ni épocas"],
        ["Agrupación por bloques temporales", "Por equipo no viable (3 grupos Botnet; prueba sin Botnet); 97 bloques de 10 s; 5 equipos de origen compartidos entre particiones",
         "No mide la generalización a equipos nuevos; estimación optimista"],
        ["Separabilidad casi trivial", "KS = 0,997 en bytes por paquete (78 B frente a 1 066 B); 84 % del |SHAP| en una variable; 4 modelos empatados con los mismos 21 errores",
         "El desempeño refleja un atajo y no la dificultad de la tarea"],
        ["Vectores duplicados", "323 vectores repetidos entre particiones; 76,2 % de las filas", "La prueba se parece al entrenamiento"],
        ["Cobertura de clases", "99,7 % de los flujos Botnet (8 143 de 8 164) son ICMP; 21 flujos de C&C solo en prueba; exhaustividad 0 de 21",
         "No se evaluó la detección de comando y control"],
        ["Potencia estadística", "5 pliegues; p mínimo de Wilcoxon 0,0625; 0 de 10 comparaciones significativas tras Holm; IC t fuera de [0; 1]",
         "Las pruebas no pueden distinguir entre modelos"],
        ["Background excluido", "96 312 de 107 194 flujos (89,8 %) sin verdad conocida", "Falsos positivos en tráfico real no estimados"],
        ["Detectores deterministas", "Exhaustividad 0 de 1 118; 287 de 407 flujos Normal marcados; inundación interna fuera del filtro «saliente»; 29,7 MB y 29,3 MB por equipo, bajo 52,4 MB",
         "No cubren la inundación ICMP; requieren un detector de volumen interno"],
        ["Modelo de lenguaje pequeño", "6 de 6 veredictos «incierto» (confianza de 0,5 a 0,6); 28 a 37 s por hallazgo; lote de 30 de 14,0 a 18,5 min frente a 15 min",
         "Sin evaluación contra verdad; riesgo de retraso en lotes grandes"],
    ], sz=16, alin=["left", "left", "left"], keep_all=False))
    A(nota("KS: distancia de Kolmogórov-Smirnov; SHAP: valores de Shapley aditivos; C&C: comando y control; IC t: intervalo de confianza con la "
           "distribución t de Student. Todas las cifras proceden de las salidas guardadas del sistema y de la base de datos (consultas de solo "
           "lectura)."))
    A(p_cuerpo(
        "Frente a la literatura, el aporte no es una métrica alta, sino el diagnóstico cuantificado que la acompaña: los trabajos sobre botnets "
        "suelen optimizar el desempeño en conjuntos públicos {p:velasco2021,velasco2023,hossain2023,shinan2021}, y la evidencia sobre "
        "generalización {p:cantone2024,sarhan2022} aconseja no tomar esas cifras como prueba de utilidad operativa. Para una pyme, la "
        "arquitectura es viable en un servidor modesto y conserva los datos en la organización, pero su valor de detección sigue sin "
        "demostrarse; las defensas contra la inyección de órdenes, además, deberían someterse a ataques adaptativos {c:zhan2025}."))

    # ---------------- 4 conclusiones
    A(h1("Conclusiones"))
    A(p_cuerpo(CONCLUSION))

    # ---------------- declaraciones y referencias
    for titulo, texto in (("Agradecimientos", AGRADECIMIENTOS), ("Conflicto de intereses", CONFLICTO), ("Contribución de autoría", CREDIT),
                          ("Fuente de financiación", FINANCIA), ("Disponibilidad de datos depositados", DATOS_DEP)):
        A(h_plano(titulo))
        A(p_cuerpo(texto))
    A(h_plano("Referencias bibliográficas"))
    for k in R.claves_citables():
        A(p_ref(k))
    return _lista


def main(plantilla, salida):
    tmp = tempfile.mkdtemp(prefix="docx_")
    with zipfile.ZipFile(plantilla) as z:
        z.extractall(tmp)
    doc = open(os.path.join(tmp, "word", "document.xml"), encoding="utf8").read()
    cabecera = doc[:doc.index("<w:body>") + len("<w:body>")]
    sect = re.search(r"<w:sectPr>.*?</w:sectPr>(?=</w:body>)", doc, re.S).group(0)
    cuerpo = "".join(construir_cuerpo())
    open(os.path.join(tmp, "word", "document.xml"), "w", encoding="utf8").write(cabecera + cuerpo + sect + "</w:body></w:document>")
    # imágenes
    for f in os.listdir(os.path.join(tmp, "word", "media")):
        os.remove(os.path.join(tmp, "word", "media", f))
    for n, f in enumerate(FIGS, 1):
        shutil.copy(os.path.join(RAIZ, "figuras", f), os.path.join(tmp, "word", "media", f"image{n}.png"))
    rels = open(os.path.join(tmp, "word", "_rels", "document.xml.rels"), encoding="utf8").read()
    rels = re.sub(r'<Relationship Id="rId1[3-9]"[^>]*image[^>]*/>', "", rels)
    nuevas = "".join(f'<Relationship Id="rId{12 + n}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/image{n}.png"/>'
                     for n in range(1, len(FIGS) + 1))
    rels = rels.replace("</Relationships>", nuevas + "</Relationships>")
    open(os.path.join(tmp, "word", "_rels", "document.xml.rels"), "w", encoding="utf8").write(rels)
    # partes huérfanas de la plantilla
    if not os.path.exists(os.path.join(tmp, "word", "comments.xml")):
        p = os.path.join(tmp, "word", "_rels", "comments.xml.rels")
        if os.path.exists(p):
            os.remove(p)
    # fuentes bibliográficas de la plantilla (contenido ajeno): se vacían
    open(os.path.join(tmp, "customXml", "item1.xml"), "w", encoding="utf8").write(
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<b:Sources xmlns:b="http://schemas.openxmlformats.org/officeDocument/2006/bibliography" '
        'xmlns="http://schemas.openxmlformats.org/officeDocument/2006/bibliography" SelectedStyle="\\APASeventhEdition.xsl" StyleName="APA" Version="7"></b:Sources>')
    # propiedades
    from datetime import datetime, timezone
    ahora = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    core = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
            'xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:dcmitype="http://purl.org/dc/dcmitype/" '
            'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
            f'<dc:title>{escape(TITULO_ES)}</dc:title><dc:subject>Artículo científico NetSentinel</dc:subject>'
            '<dc:creator>Roberto Enrique Quezada-Rodríguez;Melanie Celeste Tello Fuentes</dc:creator>'
            f'<cp:keywords>{escape(KW_ES.rstrip("."))}</cp:keywords><dc:description></dc:description><cp:revision>1</cp:revision>'
            f'<dcterms:created xsi:type="dcterms:W3CDTF">{ahora}</dcterms:created><dcterms:modified xsi:type="dcterms:W3CDTF">{ahora}</dcterms:modified>'
            '<cp:category></cp:category></cp:coreProperties>')
    open(os.path.join(tmp, "docProps", "core.xml"), "w", encoding="utf8").write(core)
    # empaquetar sin entradas de directorio, [Content_Types].xml primero
    if os.path.exists(salida):
        os.remove(salida)
    with zipfile.ZipFile(salida, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(os.path.join(tmp, "[Content_Types].xml"), "[Content_Types].xml")
        for raiz, _, fs in os.walk(tmp):
            for f in sorted(fs):
                ruta = os.path.join(raiz, f)
                arc = os.path.relpath(ruta, tmp)
                if arc != "[Content_Types].xml":
                    z.write(ruta, arc)
    shutil.rmtree(tmp)
    print("OK", salida, "tablas:", CONT["Tabla"], "figuras:", CONT["Figura"])


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
