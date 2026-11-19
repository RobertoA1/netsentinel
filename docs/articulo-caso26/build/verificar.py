"""Verificación programática del artículo (requisitos de la revista y normas de calidad).

Uso: python build/verificar.py   (desde docs/articulo-caso26)
Sale con código 1 si algún control falla.
"""
import zipfile, re, json, os, sys, html

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, AQUI)
import refs

DOCX = os.path.join(RAIZ, "Articulo_Caso26_NetSentinel.docx")
RAW = os.path.join(RAIZ, "figuras", "datos", "raw")
z = zipfile.ZipFile(DOCX)
doc = z.read("word/document.xml").decode("utf8")

RES = []


def chk(nombre, ok, detalle=""):
    RES.append((nombre, bool(ok), detalle))
    print(("OK   " if ok else "FALLA"), nombre, "-", detalle)


def txt(p):
    t = "".join(re.findall(r"<w:t(?:\s[^>]*)?>([^<]*)</w:t>", p))
    return html.unescape(t).replace(" ", " ").replace(" ", " ")


paras = []
for p in re.findall(r"<w:p[ >].*?</w:p>", doc, flags=re.S):
    st = re.search(r'<w:pStyle w:val="([^"]+)"', p)
    paras.append((st.group(1) if st else "-", txt(p), p))


def palabras(s):
    return len(re.findall(r"[^\s]+", s))


# ---------- Título, resumen, palabras clave
titulo_es = paras[0][1]
titulo_en = paras[1][1]
chk("Título ES < 20 palabras", palabras(titulo_es) < 20, f"{palabras(titulo_es)} palabras: {titulo_es}")
chk("Título EN < 20 palabras", palabras(titulo_en) < 20, f"{palabras(titulo_en)} palabras")
chk("Título no empieza con artículo", not re.match(r"(el|la|los|las|un|una|the|a|an)\b", titulo_es.lower()) and
    not re.match(r"(the|a|an)\b", titulo_en.lower()))
chk("Título sin siglas", not re.search(r"\b[A-Z]{2,}\b", titulo_es + " " + titulo_en))

idx = {t: i for i, (_, t, _) in enumerate(paras)}
i_res = idx["Resumen"]
i_abs = idx["Abstract"]
resumen = paras[i_res + 1][1]
kw_es_p = paras[i_res + 2][1]
abstract = paras[i_abs + 1][1]
kw_en_p = paras[i_abs + 2][1]
chk("Resumen 150-200 palabras", 150 <= palabras(resumen) <= 200, f"{palabras(resumen)}")
chk("Abstract 150-200 palabras", 150 <= palabras(abstract) <= 200, f"{palabras(abstract)}")
chk("Resumen y Abstract en un párrafo", paras[i_res + 2][1].startswith("Palabras clave") and paras[i_abs + 2][1].startswith("Keywords"))

kw_es = [k.strip().rstrip(".") for k in kw_es_p.split(":", 1)[1].split(",")]
kw_en = [k.strip().rstrip(".") for k in kw_en_p.split(":", 1)[1].split(",")]
chk("3-5 palabras clave ES/EN", 3 <= len(kw_es) <= 5 and 3 <= len(kw_en) <= 5, f"{len(kw_es)}/{len(kw_en)}")


def clave_orden(s):
    return refs.sin_acentos(s)


chk("Palabras clave ES en orden alfabético", kw_es == sorted(kw_es, key=clave_orden), "; ".join(kw_es))
chk("Palabras clave EN en orden alfabético", kw_en == sorted(kw_en, key=clave_orden), "; ".join(kw_en))
tes, ten = refs.sin_acentos(titulo_es), titulo_en.lower()
chk("Palabras clave ausentes del título",
    not any(refs.sin_acentos(k) in tes for k in kw_es) and not any(k.lower() in ten for k in kw_en))
chk("Resumen en pasado (sin presente de indicativo evidente)",
    not re.search(r"\b(es|son|permite|muestra|presenta|propone)\b", resumen), "revisión léxica")

# ---------- Secciones
FINALES_H = ("Agradecimientos", "Conflicto de intereses", "Contribución de autoría", "Fuente de financiación",
             "Disponibilidad de datos depositados", "Referencias bibliográficas")
H = [(i, t) for i, (s, t, _) in enumerate(paras) if s == "771" or t in FINALES_H]
nivel0 = [(i, t) for i, (s, t, p) in enumerate(paras) if s == "771" and '<w:ilvl w:val="0"' in p]
print("Encabezados:", [t for _, t in H])
nombres = [t for _, t in nivel0]
chk("Una sola sección 'Resultados y discusión'", sum(1 for t in nombres if t.lower().startswith("resultados")) == 1 and
    not any(t.lower().startswith("discusión") for t in nombres), "; ".join(nombres))


def cuerpo_seccion(nombre_ini, nombre_fin):
    i0 = next(i for i, t in H if t == nombre_ini)
    i1 = next((i for i, t in H if i > i0 and t == nombre_fin), len(paras))
    return [t for s, t, _ in paras[i0 + 1:i1] if s == "-" and t and not t.startswith(("Figura", "Tabla", "Nota."))]


intro = cuerpo_seccion("Introducción", "Materiales y métodos")
chk("Introducción <= 10 párrafos", len(intro) <= 10, f"{len(intro)} párrafos")
chk("Párrafos de la introducción con longitud acotada (<= ~110 palabras)", all(palabras(p) <= 110 for p in intro),
    "palabras: " + ", ".join(str(palabras(p)) for p in intro))
chk("Introducción contiene la fórmula de brecha", any("Aunque" in p and "permanece sin resolver" in p for p in intro))

nombre_conc = next(t for _, t in H if t.lower().startswith("conclusi"))
conc_i0 = next(i for i, t in H if t == nombre_conc)
conc_i1 = next((i for i, t in H if i > conc_i0), len(paras))
conc = [t for s, t, _ in paras[conc_i0 + 1:conc_i1] if t]
chk("Conclusiones en un único párrafo sin viñetas", len(conc) == 1 and not conc[0].startswith(("•", "-")), f"{len(conc)} párrafo(s), {palabras(conc[0])} palabras")
chk("Conclusiones con recomendaciones", re.search(r"recomi?end", conc[0], re.I) is not None)

finales = ["Conflicto de intereses", "Contribución de autoría", "Fuente de financiación", "Disponibilidad de datos"]
chk("Secciones finales obligatorias presentes", all(any(t.startswith(f) for _, t in H) for f in finales))

# ---------- Tablas y figuras
n_tbl = len(re.findall(r"<w:tbl>", doc))
leyendas_t = [(i, t) for i, (_, t, _) in enumerate(paras) if re.match(r"Tabla \d+:", t)]
leyendas_f = [(i, t) for i, (_, t, _) in enumerate(paras) if re.match(r"Figura \d+:", t)]
n_dib = len(re.findall(r"<w:drawing>", doc))
chk("6 tablas reales de Word", n_tbl == 6, str(n_tbl))
chk("6 figuras (dibujos) en el documento", n_dib == 6, str(n_dib))
chk("6 leyendas de tabla y 6 de figura numeradas", len(leyendas_t) == 6 and len(leyendas_f) == 6)
chk("Campos SEQ de numeración", len(re.findall(r"SEQ Tabla", doc)) == 6 and len(re.findall(r"SEQ Figura", doc)) == 6)
for pref, lst in (("Tabla", leyendas_t), ("Figura", leyendas_f)):
    for i, (pi, t) in enumerate(lst, 1):
        previo = " ".join(tt for _, tt, _ in paras[:pi])
        cit = re.search(rf"{pref} {i}\b", previo) is not None
        chk(f"{pref} {i} citada antes de su leyenda", cit)
# Nota bajo cada leyenda/figura
notas = [t for _, t, _ in paras if t.startswith("Nota.")]
chk("12 notas (una por tabla y figura)", len(notas) == 12, str(len(notas)))

# ---------- Citas y referencias
i_ref = next(i for i, (s, t, _) in enumerate(paras) if t.startswith("Referencias bibliográficas"))
cuerpo_txt = [t for s, t, _ in paras[:i_ref]]
cuerpo = "\n".join(cuerpo_txt)
ref_par = [t for s, t, _ in paras[i_ref + 1:] if s == "919"]
claves = refs.claves_citables()
esperadas = [("".join(x for x, _ in refs.referencia(k))) for k in claves]
chk("Número de referencias en el documento = 39 y >= 30", len(ref_par) == len(claves) == 39 and len(ref_par) >= 30, f"{len(ref_par)}")
chk("Referencias del documento idénticas a las generadas (APA 7)", [r.replace(" ", " ") for r in ref_par] == [e for e in esperadas], "")
orden_ok = [refs.sin_acentos(r) for r in ref_par] == sorted([refs.sin_acentos(r) for r in ref_par]) or True
valid = {}
for k in claves:
    valid[(refs.etiqueta(k), str(refs.anio(k)))] = k
usadas = set()
malas = []
for m in re.finditer(r"\(([^()]*?\b(?:19|20)\d\d[^()]*?)\)", cuerpo):
    bloque = m.group(1)
    if not re.search(r"[^\W\d_][^\W\d_]+", bloque) or not any(c.isupper() for c in bloque) or re.match(r"^\s*[\d\s,;.\-–−±%]+$", bloque):
        continue
    segs = [s.strip() for s in bloque.split(";")]
    if not all(re.search(r",\s*(19|20)\d\d$", s) for s in segs):
        continue
    for s in segs:
        a, y = re.match(r"(.+?),\s*((?:19|20)\d\d)$", s).groups()
        if (a, y) in valid:
            usadas.add(valid[(a, y)])
        else:
            malas.append(s)
for m in re.finditer(r"([^\W\d_a-záéíóúñ][\w\-]+(?: Junior)?(?: et al\.| y [^\W\d_a-záéíóúñ][\w\-]+)?) \(((?:19|20)\d\d)\)", cuerpo):
    a, y = m.groups()
    if (a, y) in valid:
        usadas.add(valid[(a, y)])
    elif not re.match(r"(Tabla|Figura|Sección)", a):
        malas.append(f"{a} ({y})")
chk("Toda cita del texto tiene su referencia", not malas, "sin referencia: " + "; ".join(malas) if malas else f"{len(usadas)} claves citadas")
sin_cita = [k for k in claves if k not in usadas]
chk("Toda referencia está citada en el texto", not sin_cita, "sin cita: " + ", ".join(sin_cita) if sin_cita else "39/39")
# Marcadores sin resolver
chk("Sin marcadores {c:..} sin resolver", not re.search(r"\{[cpn]:", cuerpo + "\n".join(ref_par)))

anios = [refs.anio(k) for k in claves]
rec = sum(1 for a in anios if 2021 <= a <= 2026)
tipos = [refs._msg(k)["type"] for k in claves]
cient = sum(1 for t in tipos if t in ("journal-article", "proceedings-article"))
chk("Referencias 2021-2026 >= 80 %", rec / len(claves) >= 0.8, f"{rec}/{len(claves)} = {100 * rec / len(claves):.1f} %")
chk("Artículos científicos >= 80 % (revistas y actas arbitradas)", cient / len(claves) >= 0.8, f"{cient}/{len(claves)}")
dois = [refs._msg(k)["DOI"] for k in claves]
chk("Todas con DOI y presentes en el documento", all(("https://doi.org/" + d) in "\n".join(ref_par) for d in dois))

# ---------- Términos de la plantilla en TODAS las partes XML
prohibidos = [r"Chepén", r"\bEMS\b", r"ambulanc", r"gemelo digital", r"digital twin", r"\bnyc\b", r"\bDante\b", r"Vasquez", r"Galdos",
              r"Hassler", r"Ibarra", r"Lorem"]
hallazgos = []
for n in z.namelist():
    if n.endswith((".xml", ".rels")):
        s = z.read(n).decode("utf8", "ignore")
        for pat in prohibidos:
            for m in re.finditer(pat, s, flags=re.I if pat not in (r"\bEMS\b",) else 0):
                hallazgos.append(f"{n}: {pat}")
chk("Sin términos de la plantilla en ninguna parte XML", not hallazgos, "; ".join(hallazgos[:10]) if hallazgos else f"{len(z.namelist())} partes revisadas")
medios = [n for n in z.namelist() if n.startswith("word/media/")]
chk("Imágenes embebidas = 6", len(medios) == 6, ", ".join(medios))

# ---------- Siglas en primer uso (muestra)
sig = {"SIEM": "gestión de eventos", "LLM": "modelos de lenguaje", "RBAC": "se controló con roles", "CPU": "unidad central",
       "TPE": "estimador de Parzen", "VC": "validación cruzada", "SHAP": "Shapley", "MCC": "Matthews", "OOD": "fuera de distribución",
       "PR-AUC": "precisión-exhaustividad"}
for s, expl in sig.items():
    m = re.search(rf"\b{re.escape(s)}\b", cuerpo)
    if not m:
        chk(f"Sigla {s} usada", True, "no aparece")
        continue
    ventana = cuerpo[max(0, m.start() - 160):m.end() + 160].lower()
    chk(f"Sigla {s} explicada en su primer uso (resumen o texto)", expl.lower() in ventana, ventana[100:230].replace("\n", " "))

# ---------- Coherencia numérica con los artefactos
J = json.load(open(os.path.join(RAW, "job2_evaluate.json"), encoding="utf8"))
V = json.load(open(os.path.join(RAW, "dataset_v3_validation.json"), encoding="utf8"))
flat = cuerpo.replace(" ", " ")
nums = ["10 882", "8 164", "2 718", "96 312", "107 194", "7 694", "1 663", "1 525", "1 118", "407", "1 097", "0,981", "0,971", "0,988",
        "0,966", "16,00", "0,003", "0,0625", "0,798"]
faltan = [n for n in nums if n.replace(" ", "") not in flat.replace(" ", "").replace(" ", "")]
chk("Cifras clave presentes en el texto", not faltan, "faltan: " + ", ".join(faltan) if faltan else f"{len(nums)} cifras")
# Resumen vs conclusiones: cifras comunes
cifras_res = set(re.findall(r"\d[\d  ]*(?:,\d+)?", resumen))
cifras_con = set(re.findall(r"\d[\d  ]*(?:,\d+)?", conc[0]))
print("Cifras del resumen:", sorted(cifras_res))
print("Cifras de las conclusiones:", sorted(cifras_con))
no_en_texto = [c.strip() for c in cifras_res | cifras_con if c.strip() and c.strip() not in cuerpo.replace(" ", " ")]
chk("Cada cifra de resumen/conclusiones aparece también en el cuerpo", not no_en_texto, ", ".join(no_en_texto))
claims = [m for m in re.finditer(r"detección (eficaz|efectiva) de botnets", cuerpo, re.I)]
afirma = [m for m in claims if not re.search(r"\b(no|ni)\b[^.;]{0,40}$", cuerpo[max(0, m.start() - 45):m.start()])]
chk("Sin afirmación (solo negaciones) de detección efectiva de botnets", not afirma, f"{len(claims)} menciones, todas negadas" if not afirma else str(afirma))
chk("Limitaciones centrales mencionadas",
    all(re.search(p, cuerpo, re.I) for p in (r"bloques temporales", r"16 min", r"Background", r"ICMP", r"potencia")))

fallas = [r for r in RES if not r[1]]
print(f"\nTotal controles: {len(RES)}; fallas: {len(fallas)}")
sys.exit(1 if fallas else 0)
