"""Referencias APA 7 generadas desde los metadatos verificados en Crossref (build/crossref_raw.json).

Los títulos se escriben en la capitalización de oración que exige APA 7; se verifica por código que coincidan
con el título de Crossref ignorando mayúsculas y signos (verificar.py). No se envía información del proyecto a Crossref.
"""
import json, re, html, unicodedata, os

AQUI = os.path.dirname(os.path.abspath(__file__))
RAW = json.load(open(os.path.join(AQUI, "crossref_raw.json"), encoding="utf8"))

# Referencia descartada del texto (no se cita): se mantiene en crossref_raw.json solo como registro de la búsqueda.
EXCLUIDAS = {"chicco2021b"}

TITULOS = {
    "rombaldo2026": "Unaware, unfunded, untrained, and unsupported: A systematic review of cybersecurity in small and medium enterprises",
    "adriko2024": "Cybersecurity, cyber insurance and small-to-medium-sized enterprises: A systematic review",
    "gonzalez2021": "Security information and event management (SIEM): Analysis, trends, and usage in critical infrastructures",
    "tariq2025": "Alert fatigue in security operations centres: Research challenges and opportunities",
    "tendikov2024": "Security information event management data acquisition and analysis methods with machine learning principles",
    "liu2022": "Context2Vector: Accelerating security event triage via context representation learning",
    "velasco2021": "Efficient detection of botnet traffic by features selection and decision trees",
    "velasco2023": "Real-time botnet detection on large network bandwidths using machine learning",
    "hossain2023": "A novel hybrid feature selection and ensemble-based machine learning approach for botnet detection",
    "shinan2021": "Machine learning-based botnet detection in software-defined network: A systematic review",
    "saied2025": "Explainable artificial intelligence for botnet detection in internet of things",
    "abualghanam2023": "Real-time detection system for data exfiltration over DNS tunneling using machine learning",
    "cantone2024": "Machine learning in network intrusion detection: A cross-dataset generalization study",
    "verkerken2021": "Towards model generalization for intrusion detection: Unsupervised machine learning techniques",
    "sarhan2022": "Towards a standard feature set for network intrusion detection system datasets",
    "karlsen2024": "Benchmarking large language models for log analysis, security, and interpretation",
    "palma2025": "Leveraging large language models for scalable and explainable cybersecurity log analysis",
    "zhang2025": "LLM-LADE: Large language model-based log anomaly detection with explanation",
    "xu2026": "Large language models for cyber security: A systematic literature review",
    "ma2026": "LLM4Log: A systematic review of large language model-based log analysis",
    "divakaran2025": "Large language models for cybersecurity: New opportunities",
    "yao2024": "A survey on large language model (LLM) security and privacy: The good, the bad, and the ugly",
    "kheddar2025": "Transformers and large language models for efficient intrusion detection systems: A comprehensive survey",
    "houssel2026": "eX-NIDS: A framework for explainable network intrusion detection leveraging large language models",
    "alhuzali2025": "LLM-powered threat intelligence: A retrieval-augmented generation approach for cyber attack investigation",
    "woesle2026": "A systematic literature review of prompt injection attacks in LLM-integrated systems",
    "dikici2026": "Small language models: A systematic review of computational trade-offs, privacy advantages and deployment in intelligent systems",
    "kapoor2023": "Leakage and the reproducibility crisis in machine-learning-based science",
    "bates2023": "Cross-validation: What does it estimate and how well does it do it?",
    "chicco2021": "The Matthews correlation coefficient (MCC) is more reliable than balanced accuracy, bookmaker informedness, and markedness in two-class confusion matrix evaluation",
    "gaspar2024": "Explainable AI for intrusion detection systems: LIME and SHAP applicability on multi-layer perceptron",
    "kinyua2021": "AI/ML in security orchestration, automation and response: Future research directions",
    "oskera2025": "Botnet detection through periodic patterns in command-and-control network traffic",
    "jiang2026": "LLM-FPR: Large language model-based false positive reduction framework for network intrusion detection",
    "greshake2023": "Not what you've signed up for: Compromising real-world LLM-integrated applications with indirect prompt injection",
    "zhan2025": "Adaptive attacks break defenses against indirect prompt injection attacks on LLM agents",
    "garcia2014": "An empirical comparison of botnet detection methods",
    "hevner2004": "Design science in information systems research",
    "sommer2010": "Outside the closed world: On using machine learning for network intrusion detection",
}

# Correcciones de nombre sobre los metadatos de Crossref (apellido compuesto mal separado)
FIX_AUTOR = {("rombaldo2026", 0): ("Rombaldo Junior", "Carlos")}

EDITORIAL = {"Association for Computing Machinery (ACM)": "Association for Computing Machinery", "ACM": "Association for Computing Machinery",
             "Institute of Electrical and Electronics Engineers (IEEE)": "IEEE"}


def _msg(k):
    return RAW[k]["msg"]


def autores(k):
    out = []
    for i, a in enumerate(_msg(k).get("author", [])):
        fam, giv = FIX_AUTOR.get((k, i), (a.get("family", ""), a.get("given", "")))
        out.append((fam, giv))
    return out


def anio(k):
    m = _msg(k)
    for f in ("published-print", "issued", "published-online"):
        dp = (m.get(f, {}).get("date-parts") or [[None]])[0][0]
        if dp:
            return dp


def iniciales(giv):
    partes = []
    for tok in giv.replace("(", " ").replace(")", " ").split():
        if re.fullmatch(r"(?:[^\W\d_]\.)+", tok):  # R.C.
            partes += re.findall(r"[^\W\d_]\.", tok)
        elif "-" in tok:
            partes.append("-".join(p[0].upper() + "." for p in tok.split("-") if p))
        else:
            partes.append(tok[0].upper() + ".")
    return " ".join(partes)


def sin_acentos(s):
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn").lower()


def etiqueta(k):
    """Texto de la cita en el cuerpo: 'Autor', 'Autor y Autor' o 'Autor et al.'."""
    a = [x[0] for x in autores(k)]
    if len(a) == 1:
        return a[0]
    if len(a) == 2:
        return f"{a[0]} y {a[1]}"
    return f"{a[0]} et al."


def cita_parentesis(claves):
    ordenadas = sorted(claves, key=lambda k: (sin_acentos(autores(k)[0][0]), anio(k)))
    return "(" + "; ".join(f"{etiqueta(k)}, {anio(k)}" for k in ordenadas) + ")"


def cita_narrativa(k):
    return f"{etiqueta(k)} ({anio(k)})"


def _lista_autores(k):
    nombres = [f"{f}, {iniciales(g)}" for f, g in autores(k)]
    if len(nombres) == 1:
        return nombres[0]
    return ", ".join(nombres[:-1]) + ", & " + nombres[-1]


def referencia(k):
    """Devuelve una lista de (texto, cursiva) para construir la referencia."""
    m = _msg(k)
    tipo = m["type"]
    cont = html.unescape((m.get("container-title") or [""])[0])
    pag = m.get("page")
    art = m.get("article-number")
    vol, num = m.get("volume"), m.get("issue")
    doi = "https://doi.org/" + m["DOI"]
    tit = TITULOS[k]
    base = f"{_lista_autores(k)} ({anio(k)}). {tit}{'' if tit[-1] in '?!.' else '.'} "
    runs = [(base, False)]
    if tipo == "journal-article":
        runs.append((cont, True))
        if vol:
            runs.append((", ", False)); runs.append((vol, True))
            if num:
                runs.append((f"({num})", False))
        if not vol:
            runs.append((". Advance online publication", False))
        elif pag and "-" in pag:
            runs.append((", " + pag.replace("-", "–"), False))
        elif pag or art:
            runs.append((f", Article {art or pag}", False))
        runs.append((". " + doi, False))
    else:  # proceedings-article
        editorial = EDITORIAL.get(m.get("publisher", ""), m.get("publisher", ""))
        runs.append(("In ", False)); runs.append((cont, True))
        if pag:
            runs.append((f" (pp. {pag.replace('-', '–')})", False))
        runs.append((f". {editorial}. {doi}", False))
    return runs


def claves_citables():
    return sorted((k for k in TITULOS if k not in EXCLUIDAS), key=lambda k: (sin_acentos(autores(k)[0][0]), sin_acentos(autores(k)[1][0]) if len(autores(k)) > 1 else "", anio(k)))


if __name__ == "__main__":
    for k in claves_citables():
        print("".join(t for t, _ in referencia(k)))
    print(len(claves_citables()))
