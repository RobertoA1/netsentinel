import re, json, html, os, sys
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_COLOR_INDEX, WD_TAB_ALIGNMENT, WD_BREAK
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.section import WD_ORIENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import supuestos as S, tablas, c1, c2, c3, c4
from fmt import *
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, '..'); FIG = os.path.join(OUT, 'figuras')
R = S.calcula(); REAL = S.REAL; DS = S.DS
T, F = tablas.definiciones(R, REAL, DS)
FONT = 'Times New Roman'
doc = Document()
sec = doc.sections[0]; sec.page_width = Cm(21); sec.page_height = Cm(29.7)
for a in ('left_margin', 'right_margin'): setattr(sec, a, Cm(2.0))
sec.top_margin = Cm(2.2); sec.bottom_margin = Cm(2.0)
def setfont(style, size, bold=None, italic=None, color=RGBColor(0, 0, 0)):
    style.font.name = FONT; style.font.size = Pt(size)
    style.element.rPr.rFonts.set(qn('w:eastAsia'), FONT)
    if bold is not None: style.font.bold = bold
    if italic is not None: style.font.italic = italic
    style.font.color.rgb = color
st = doc.styles
setfont(st['Normal'], 10.5); pf = st['Normal'].paragraph_format; pf.space_after = Pt(5); pf.line_spacing = 1.12; pf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
setfont(st['Heading 1'], 13, True); st['Heading 1'].paragraph_format.space_before = Pt(14); st['Heading 1'].paragraph_format.space_after = Pt(5); st['Heading 1'].paragraph_format.keep_with_next = True; st['Heading 1'].paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
setfont(st['Heading 2'], 11, True, True); st['Heading 2'].paragraph_format.space_before = Pt(9); st['Heading 2'].paragraph_format.space_after = Pt(3); st['Heading 2'].paragraph_format.keep_with_next = True; st['Heading 2'].paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
setfont(st['Title'], 17, True); st['Title'].paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER; st['Title'].paragraph_format.space_after = Pt(8)
# quitar borde inferior del Title
for nm in ('Title','Heading 1','Heading 2'):
    rf = st[nm].element.rPr.rFonts
    for a in ('w:asciiTheme','w:hAnsiTheme','w:eastAsiaTheme','w:cstheme'):
        if rf.get(qn(a)) is not None: del rf.attrib[qn(a)]
    rf.set(qn('w:cs'), FONT)
pPr = st['Title'].element.get_or_add_pPr()
for b in pPr.findall(qn('w:pBdr')): pPr.remove(b)

# ---------- referencias / citas ----------
RAW = json.load(open(os.path.join(HERE, 'refs_raw.json')))['meta']
DOCS = {
 'suricata': ('Open Information Security Foundation, "Suricata User Guide," Suricata documentation. [Online]. Available: https://docs.suricata.io/en/latest/ (accessed Nov. 11, 2026).', None),
 'opnsense': ('OPNsense, "Firewall rules," OPNsense documentation. [Online]. Available: https://docs.opnsense.org/manual/firewall.html (accessed Nov. 11, 2026).', None),
 'n8n': ('n8n GmbH, "n8n Docs," n8n documentation. [Online]. Available: https://docs.n8n.io/ (accessed Nov. 11, 2026).', None),
 'langchain': ('LangChain, "ChatOllama integration," LangChain documentation. [Online]. Available: https://python.langchain.com/docs/integrations/chat/ollama/ (accessed Nov. 11, 2026).', None),
 'ollama': ('Ollama, "Ollama API documentation," GitHub repository ollama/ollama. [Online]. Available: https://github.com/ollama/ollama/blob/main/docs/api.md (accessed Nov. 11, 2026).', None),
 'owasp': ('OWASP Gen AI Security Project, "LLM01:2025 Prompt injection." [Online]. Available: https://genai.owasp.org/llmrisk/llm01-prompt-injection/ (accessed Nov. 11, 2026).', None),
 'mcfp': ('S. García, "Malware Capture Facility Project: The CTU-13 dataset. A labeled dataset with botnet, normal and background traffic," Stratosphere Laboratory, CTU in Prague. [Online]. Available: https://www.stratosphereips.org/datasets-ctu13 (accessed Nov. 11, 2026).', None),
 'llama3': ('A. Grattafiori et al., "The Llama 3 herd of models," arXiv:2407.21783, Jul. 2024. [Online]. Available: https://arxiv.org/abs/2407.21783 (accessed Nov. 11, 2026).', None),
}
def initials(given):
    parts = re.split(r'[\s]+', given.strip()); out = []
    for p in parts:
        for q in p.split('-'):
            q = q.strip('.')
            if q: out.append(q[0].upper() + '.')
    return ' '.join(out)
def fmt_ref(k):
    if k in DOCS: return [(DOCS[k][0], False)]
    m = RAW[k]; au = m.get('author', [])
    names = [f"{initials(a.get('given',''))} {a.get('family','')}".strip() for a in au]
    if len(names) > 6: s = names[0] + ' et al.'
    elif len(names) > 2: s = ', '.join(names[:-1]) + ', and ' + names[-1]
    elif len(names) == 2: s = names[0] + ' and ' + names[1]
    else: s = names[0]
    title = html.unescape(m['title'][0])
    if k == 'hevner2004': title = 'Design science in information systems research'
    title = re.sub(r'\s+', ' ', title)
    if m.get('subtitle'):
        sub = html.unescape(m['subtitle'][0]); title = title.rstrip(':') + ': ' + sub[0].upper() + sub[1:] if k == 'bilge2012' else title
    cont = html.unescape(m['container-title'][0]) if m.get('container-title') else ''
    if k == 'pietraszek2004': cont = 'Recent Advances in Intrusion Detection'
    dp = (m.get('published-print') or m.get('issued'))['date-parts'][0]; year = dp[0]
    pages = (m.get('page') or '').replace('-', '–')
    doi = m['DOI']
    segs = [(s + ', "' + title + ',"', False)]
    if m['type'] == 'journal-article':
        segs.append((' ', False)); segs.append((cont, True))
        extra = ''
        if m.get('volume'): extra += f", vol. {m['volume']}"
        if m.get('issue'): extra += f", no. {m['issue']}"
        if pages and m.get('page') and '–' in pages: extra += f", pp. {pages}"
        elif m.get('page'): extra += f", Art. no. {m['page']}"
        elif m.get('article-number'): extra += f", Art. no. {m['article-number']}"
        extra += f", {year}, doi: {doi}."
        segs.append((extra, False))
    else:
        segs.append((' in ', False)); segs.append((cont, True))
        extra = f", {year}"
        if pages: extra += f", pp. {pages}"
        extra += f", doi: {doi}."
        segs.append((extra, False))
    return segs
ORDER = []
def cite(keys):
    nums = []
    for k in keys:
        if k not in ORDER: ORDER.append(k)
        nums.append(ORDER.index(k) + 1)
    nums = sorted(set(nums)); out = []; i = 0
    while i < len(nums):
        j = i
        while j + 1 < len(nums) and nums[j+1] == nums[j] + 1: j += 1
        out.append(f"[{nums[i]}]–[{nums[j]}]" if j - i >= 2 else ', '.join(f"[{x}]" for x in nums[i:j+1])); i = j + 1
    return ', '.join(out)

# ---------- parser inline ----------
TOK = re.compile(r'(⟦|⟧|@@[^@]+@@|\*\*|\*|_<[^>]*>|\^<[^>]*>)')
def add_runs(par, text, size=None, bold=False, italic=False, hl=False, font=None):
    # estado de formato
    st_ = dict(b=bold, i=italic, h=hl)
    for piece in TOK.split(text):
        if piece == '': continue
        if piece == '⟦': st_['h'] = True; continue
        if piece == '⟧': st_['h'] = hl; continue
        if piece == '**': st_['b'] = not st_['b']; continue
        if piece == '*': st_['i'] = not st_['i']; continue
        sub = sup = False
        if piece.startswith('@@'): txt = cite(piece[2:-2].split(','))
        elif piece.startswith('_<'): txt = piece[2:-1]; sub = True
        elif piece.startswith('^<'): txt = piece[2:-1]; sup = True
        else: txt = piece
        r = par.add_run(txt); r.bold = st_['b']; r.italic = st_['i']
        if sub: r.font.subscript = True
        if sup: r.font.superscript = True
        if st_['h']: r.font.highlight_color = WD_COLOR_INDEX.YELLOW
        if size: r.font.size = Pt(size)
        if font: r.font.name = font; r._element.rPr.rFonts.set(qn('w:eastAsia'), font); r._element.rPr.rFonts.set(qn('w:cs'), font)
    return par
def para(text, style=None, align=None, size=None, bold=False, italic=False, after=None, before=None, keep=False, left=None):
    p = doc.add_paragraph(style=style); add_runs(p, text, size=size, bold=bold, italic=italic)
    if align is not None: p.alignment = align
    if after is not None: p.paragraph_format.space_after = Pt(after)
    if before is not None: p.paragraph_format.space_before = Pt(before)
    if keep: p.paragraph_format.keep_with_next = True
    if left is not None: p.paragraph_format.left_indent = Cm(left)
    return p
def shade(el_pPr, fill, border=True):
    shd = OxmlElement('w:shd'); shd.set(qn('w:val'), 'clear'); shd.set(qn('w:color'), 'auto'); shd.set(qn('w:fill'), fill); el_pPr.append(shd)
def box_para(text, fill='FFF2CC', border_color='B8860B', size=9.5, bold_first=None):
    p = doc.add_paragraph(); add_runs(p, text, size=size); p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    pPr = p._p.get_or_add_pPr(); bd = OxmlElement('w:pBdr')
    for s in ('top', 'left', 'bottom', 'right'):
        e = OxmlElement(f'w:{s}'); e.set(qn('w:val'), 'single'); e.set(qn('w:sz'), '10'); e.set(qn('w:space'), '4'); e.set(qn('w:color'), border_color); bd.append(e)
    pPr.append(bd); shade(pPr, fill)
    p.paragraph_format.left_indent = Cm(0.2); p.paragraph_format.right_indent = Cm(0.2); p.paragraph_format.space_after = Pt(8)
    return p
def eq_par(formula, num):
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.tab_stops.add_tab_stop(Cm(8.5), WD_TAB_ALIGNMENT.CENTER); p.paragraph_format.tab_stops.add_tab_stop(Cm(17.0), WD_TAB_ALIGNMENT.RIGHT)
    p.paragraph_format.space_before = Pt(3); p.paragraph_format.space_after = Pt(5); p.paragraph_format.keep_together = True
    p.add_run('\t'); add_runs(p, formula, italic=True, size=10.5); p.add_run('\t(%d)' % num)
    return p
def set_cell_borders(cell, **kw):
    tcPr = cell._tc.get_or_add_tcPr(); b = tcPr.find(qn('w:tcBorders'))
    if b is None: b = OxmlElement('w:tcBorders'); tcPr.append(b)
    for edge, val in kw.items():
        e = OxmlElement(f'w:{edge}'); e.set(qn('w:val'), val[0]); e.set(qn('w:sz'), str(val[1])); e.set(qn('w:space'), '0'); e.set(qn('w:color'), '000000'); b.append(e)
def cell_shade(cell, fill):
    tcPr = cell._tc.get_or_add_tcPr(); shd = OxmlElement('w:shd'); shd.set(qn('w:val'), 'clear'); shd.set(qn('w:color'), 'auto'); shd.set(qn('w:fill'), fill); tcPr.append(shd)
def render_table(tid):
    t = T[tid]
    cap = para('', align=WD_ALIGN_PARAGRAPH.LEFT, keep=True, before=8, after=3)
    num, rest = t['caption'].split('. ', 1)
    add_runs(cap, f"**{num}.** {rest}", size=9.5)
    ncols = len(t['header']); tb = doc.add_table(rows=1, cols=ncols); tb.alignment = WD_TABLE_ALIGNMENT.CENTER; tb.autofit = False
    tblPr = tb._tbl.tblPr; lay = OxmlElement('w:tblLayout'); lay.set(qn('w:type'), 'fixed'); tblPr.append(lay)
    mar = OxmlElement('w:tblCellMar')
    for s, w in (('top', 30), ('left', 60), ('bottom', 30), ('right', 60)):
        e = OxmlElement(f'w:{s}'); e.set(qn('w:w'), str(w)); e.set(qn('w:type'), 'dxa'); mar.append(e)
    tblPr.append(mar)
    widths = [Cm(w) for w in t['widths']]
    def fill(row, vals, hdr=False):
        for i, v in enumerate(vals):
            c = row.cells[i]; c.width = widths[i]; c.text = ''
            p = c.paragraphs[0]; p.paragraph_format.space_after = Pt(0); p.paragraph_format.line_spacing = 1.0; p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            add_runs(p, v, size=t['fs'], bold=hdr)
            if hdr: cell_shade(c, 'E7E6E6')
    fill(tb.rows[0], t['header'], True)
    trPr = tb.rows[0]._tr.get_or_add_trPr(); th = OxmlElement('w:tblHeader'); th.set(qn('w:val'), 'true'); trPr.append(th)
    for rw in t['rows']:
        r = tb.add_row(); fill(r, rw)
        cs = OxmlElement('w:cantSplit'); r._tr.get_or_add_trPr().append(cs)
    for i, c in enumerate(tb.rows[0].cells): set_cell_borders(c, top=('single', 12), bottom=('single', 6))
    for c in tb.rows[-1].cells: set_cell_borders(c, bottom=('single', 12))
    n = para(t['notes'], align=WD_ALIGN_PARAGRAPH.JUSTIFY, size=8, before=3, after=9)
def render_fig(fid):
    f = F[fid]
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.keep_with_next = True; p.paragraph_format.space_before = Pt(6); p.paragraph_format.space_after = Pt(2)
    p.add_run().add_picture(os.path.join(FIG, f['file']), width=Cm(f['w']))
    cap = para('', align=WD_ALIGN_PARAGRAPH.LEFT, keep=True, after=1)
    num, rest = f['caption'].split('. ', 1); add_runs(cap, f"**{num}.** {rest}", size=9.5)
    para(f['notes'], align=WD_ALIGN_PARAGRAPH.JUSTIFY, size=8, after=9)

# ---------- cabecera / pie ----------
hp = sec.header.paragraphs[0]; hp.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = hp.add_run('Borrador para revisión de los autores · contiene valores supuestos (†) · no enviar sin sustituirlos'); r.font.size = Pt(8); r.font.name = FONT; r.italic = True
fp = sec.footer.paragraphs[0]; fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
def fld(par, instr):
    r = par.add_run(); r.font.size = Pt(9)
    for t_, txt in (('begin', None), (None, instr), ('end', None)):
        if t_: e = OxmlElement('w:fldChar'); e.set(qn('w:fldCharType'), t_)
        else: e = OxmlElement('w:instrText'); e.set(qn('xml:space'), 'preserve'); e.text = txt
        r._r.append(e)
fld(fp, 'PAGE')

# ---------- portada ----------
TITLE = "Detección determinista de beaconing y puertos inusuales en logs de firewall de pequeñas y medianas empresas con filtrado de ruido mediante un modelo de lenguaje local: diseño y evaluación experimental"
doc.add_paragraph(TITLE, style='Title')
para("Roberto Enrique Quezada-Rodríguez^<1> (ORCID: 0009-0004-0869-3881) y Melanie Celeste Tello Fuentes^<1> (ORCID: 0009-0007-4728-138X)", align=WD_ALIGN_PARAGRAPH.CENTER, size=11, after=2)
para("^<1> Universidad Nacional de Trujillo, Trujillo, La Libertad, Perú", align=WD_ALIGN_PARAGRAPH.CENTER, size=10, after=2)
para("Correspondencia: (correo electrónico a completar por los autores)", align=WD_ALIGN_PARAGRAPH.CENTER, size=10, after=8)
box_para("**Nota para los autores (eliminar antes del envío).** Este manuscrito mezcla dos tipos de valores. Los valores **reales** proceden de mediciones del despliegue de NetSentinel y del archivo del dataset CTU-13 (107 252 líneas leídas, 107 194 registros, 51 hallazgos, latencias, reportes, 114 pruebas, tamaño del modelo). Todo lo demás —adjudicación por analistas, comparación con Suricata y con un umbral fijo, beacons inyectados, modelos qwen2.5:7b, llama3.1:8b y mistral:7b, estudio de usabilidad con 12 administradores, consumo de recursos y costos— son valores **supuestos, ilustrativos**, generados con un protocolo reproducible y semilla fija. Están resaltados en amarillo en el texto, las tablas y las notas, y las tablas y figuras que los contienen llevan el símbolo †. Antes de someter el artículo a una revista deben sustituirse por mediciones reales (ver el archivo VALORES_SUPUESTOS.md, que indica qué experimento ejecutar para cada dato). El texto que describe esos experimentos (Sección 3.6 y siguientes) se redactó como si se hubieran realizado y debe revisarse en consecuencia.")

# ---------- resumen ----------
def rsum(): 
    det = {r['nombre']: r for r in R['t4']}; dd = det['NetSentinel determinista (unión)']; fx = det['Umbral fijo (≥100 conexiones/destino)']; su = det['Suricata 7 (reglas por defecto)']
    t5 = {m['m']: m for m in R['t5']}; q3 = t5['llama3.2:3b']; q8 = t5['llama3.1:8b']; ut = R['us_time']; sus = R['sus']
    es = [
     ("Contexto/problema", "Las pequeñas y medianas empresas rara vez cuentan con un analista o un SIEM para interpretar los logs de su firewall, y las alertas sin filtrar producen fatiga y amenazas sin atender."),
     ("Objetivo", "Diseñar y evaluar NetSentinel, un analista de logs que combina detección determinista de beaconing y de puertos inusuales con un filtro de ruido basado en un modelo de lenguaje local, y determinar en qué condiciones el filtro aporta valor."),
     ("Método", "Design Science Research con evaluación experimental cuantitativa sobre el escenario 11 de CTU-13 (107 194 registros normalizados; 51 hallazgos), " + A("200 beacons inyectados, adjudicación por dos analistas, cuatro modelos locales y un estudio de usabilidad con 12 administradores") + "; se compararon un umbral fijo y Suricata con reglas por defecto, con IC 95 %, pruebas de McNemar y de Wilcoxon y κ de Cohen."),
     ("Resultados", f"La detección determinista alcanzó F1 = " + A(f"{d(dd['f1'])} {ci(*dd['f1_ci'])}") + f", frente a " + A(d(fx['f1'])) + " del umbral fijo y " + A(d(su['f1'])) + " de Suricata (McNemar " + A(pv(R['mc_fix']['p'])) + "). llama3.2:3b, único modelo medido en el despliegue, respondió «incierto» (confianza de 0,5 a 0,6 en 2 de 2 hallazgos reanalizados) con 28–37 s por hallazgo en CPU" + A(f" y redujo {pc(q3['red'],0)} de las alertas") + "; llama3.1:8b redujo " + A(pc(q8['red'])) + " con " + A(f"{q8['rl']} hallazgo real descartado (κ = {d(q8['kappa'])})") + ". Las explicaciones redujeron " + A(pc(ut['red'],0)) + " la mediana del tiempo de decisión (" + A(pv(ut['p'])) + "; SUS " + A(d(sus['mean'],1)) + ")."),
     ("Conclusión", "En el escenario evaluado, un modelo local de 3 mil millones de parámetros resulta demasiado conservador para filtrar ruido, mientras que modelos de 7–8 mil millones reducen alertas a costa de latencia y de algún falso negativo; los resultados no se extrapolan más allá de un escenario corto, de tres hosts infectados y de modelos ejecutados en CPU."),
    ]
    return es
ES = rsum()
doc.add_paragraph('Resumen', style='Heading 1')
for k, v in ES:
    para(f"**{k}.** {v}", after=3)
para("**Palabras clave:** beaconing; comunicaciones de mando y control; análisis de logs de firewall; modelos de lenguaje locales; fatiga de alertas; pequeñas y medianas empresas; Design Science Research.", before=4, after=6)
def abstract_en():
    det = {r['nombre']: r for r in R['t4']}; dd = det['NetSentinel determinista (unión)']; fx = det['Umbral fijo (≥100 conexiones/destino)']; su = det['Suricata 7 (reglas por defecto)']
    t5 = {m['m']: m for m in R['t5']}; q3 = t5['llama3.2:3b']; q8 = t5['llama3.1:8b']; ut = R['us_time']; sus = R['sus']
    dn = lambda x, k=2: f"{x:.{k}f}"
    return [
     ("Context/problem", "Small and medium-sized enterprises rarely have an analyst or a SIEM to interpret their firewall logs, and unfiltered alerts cause alert fatigue and unattended threats."),
     ("Objective", "To design and evaluate NetSentinel, a log analyst that combines deterministic detection of beaconing and unusual ports with a noise filter based on a local language model, and to determine under which conditions the filter adds value."),
     ("Method", "Design Science Research with quantitative experimental evaluation on CTU-13 scenario 11 (107,194 normalized records; 51 findings), " + A("200 injected beacons, adjudication by two analysts, four local models and a usability study with 12 administrators") + "; a fixed threshold and Suricata with default rules were used as baselines, with 95% CIs, McNemar and Wilcoxon tests and Cohen's κ."),
     ("Results", f"Deterministic detection reached F1 = " + A(f"{dn(dd['f1'])} [{dn(dd['f1_ci'][0])}, {dn(dd['f1_ci'][1])}]") + " versus " + A(dn(fx['f1'])) + " for the fixed threshold and " + A(dn(su['f1'])) + " for Suricata (McNemar " + A(f"p = {dn(R['mc_fix']['p'],3)}") + "). llama3.2:3b, the only model measured in the deployment, answered “uncertain” (confidence 0.5–0.6 in 2 of 2 re-analyzed findings) at 28–37 s per finding on CPU" + A(f" and reduced alerts by {q3['red']*100:.0f}%") + "; llama3.1:8b reduced them by " + A(f"{q8['red']*100:.1f}%") + " with " + A(f"{q8['rl']} real finding discarded (κ = {dn(q8['kappa'])})") + ". Explanations reduced median decision time by " + A(f"{ut['red']*100:.0f}%") + " (" + A("p < 0.001") + "; SUS " + A(f"{sus['mean']:.1f}") + ")."),
     ("Conclusion", "In the evaluated scenario, a 3-billion-parameter local model is too conservative to filter noise, whereas 7–8-billion-parameter models reduce alerts at the cost of latency and some false negatives; results should not be extrapolated beyond a short scenario, three infected hosts and CPU-only models."),
    ]
doc.add_paragraph('Abstract', style='Heading 1')
for k, v in abstract_en(): para(f"**{k}.** {v}", after=3)
para("**Keywords:** beaconing; command-and-control communications; firewall log analysis; local language models; alert fatigue; small and medium-sized enterprises; Design Science Research.", before=4, after=6)

# ---------- cuerpo ----------
blocks = c1.bloques(R, REAL, DS) + c2.bloques(R, REAL, DS) + c3.bloques(R, REAL, DS) + c4.bloques(R, REAL, DS)
WORDS = 0; first = True
def count(t):
    t = re.sub(r'@@[^@]+@@', '[1]', t); t = re.sub(r'[⟦⟧*]|_<|\^<|>', '', t); return len(t.split())
for b in blocks:
    k = b[0]
    if k == 'h1': doc.add_paragraph(b[1], style='Heading 1'); WORDS += count(b[1])
    elif k == 'h2': doc.add_paragraph(b[1], style='Heading 2'); WORDS += count(b[1])
    elif k == 'p': para(b[1]); WORDS += count(b[1])
    elif k == 'bullets':
        for it in b[1]:
            p = doc.add_paragraph(style='List Bullet'); add_runs(p, it); p.paragraph_format.space_after = Pt(2); p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY; WORDS += count(it)
    elif k == 'eq': eq_par(b[1], b[2])
    elif k == 'tbl': render_table(b[1])
    elif k == 'fig': render_fig(b[1])

# ---------- declaraciones ----------
decl = [
 ("Declaración de disponibilidad de datos y código", "El conjunto de datos CTU-13 es público (Stratosphere Laboratory) y se descarga con el script del proyecto. El código de NetSentinel (backend, frontend, flujos de n8n y flujo de LangFlow), las migraciones y las 114 pruebas están en el repositorio del proyecto (enlace público a completar por los autores). Los scripts que generan las figuras, los estadísticos supuestos y este documento se entregan en la carpeta docs/articulo, con semilla fija. Los valores supuestos no corresponden a datos reales y no se publican como tales."),
 ("Consideraciones éticas", "El dataset utilizado es público y anonimizado; el sistema procesa los logs localmente y no los envía a servicios externos. " + A("El estudio de usabilidad con 12 administradores se realizó con consentimiento informado, sin recolección de datos personales identificables y con aprobación del comité de ética institucional (código a completar)") + "."),
 ("Contribuciones de autoría (CRediT)", "(A completar por los autores.) Roles sugeridos para asignar: conceptualización, metodología, software, validación, análisis formal, investigación, curación de datos, redacción del borrador original, redacción (revisión y edición), visualización, supervisión y administración del proyecto."),
 ("Conflicto de intereses", "Los autores declararán cualquier conflicto de intereses (a confirmar por los autores; en este borrador no se ha identificado ninguno)."),
 ("Financiamiento", "(A completar por los autores.)"),
 ("Declaración de uso de inteligencia artificial generativa", "Este borrador fue redactado con la asistencia de un modelo de inteligencia artificial generativa (Claude, de Anthropic), que se utilizó para estructurar y redactar el texto, programar los scripts de figuras y de estadística y consultar la API de Crossref para verificar las referencias. Los valores supuestos se generaron a petición de los autores como marcadores ilustrativos y no son resultados experimentales. El contenido debe ser revisado, verificado y asumido por los autores, quienes son responsables de su exactitud; la IA no figura como autora."),
]
for t_, x in decl:
    doc.add_paragraph(t_, style='Heading 2'); para(x); WORDS += count(t_) + count(x)

# ---------- referencias ----------
doc.add_paragraph('Referencias', style='Heading 1')
for i, k in enumerate(ORDER, 1):
    p = doc.add_paragraph(); p.paragraph_format.left_indent = Cm(0.9); p.paragraph_format.first_line_indent = Cm(-0.9); p.paragraph_format.space_after = Pt(3); p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    r = p.add_run(f"[{i}]\t"); r.font.size = Pt(9)
    p.paragraph_format.tab_stops.add_tab_stop(Cm(0.9))
    for txt, it in fmt_ref(k):
        r = p.add_run(txt); r.italic = it; r.font.size = Pt(9)
doc.core_properties.title = TITLE; doc.core_properties.author = 'Roberto Enrique Quezada-Rodríguez; Melanie Celeste Tello Fuentes'
doc.core_properties.keywords = 'beaconing; command and control; firewall logs; local LLM; SMEs'
path = os.path.join(OUT, 'Articulo_NetSentinel.docx'); doc.save(path)
json.dump(dict(order=ORDER, words=WORDS, title=TITLE), open(os.path.join(HERE, 'build_info.json'), 'w'), ensure_ascii=False)
print('guardado', path, 'palabras cuerpo', WORDS, 'refs', len(ORDER))
