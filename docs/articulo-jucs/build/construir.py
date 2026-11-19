"""Construye el articulo en .docx sobre la plantilla J.UCS (JUCSWordTemplateV5.docx) editando su XML.
Uso: python -I construir.py <plantilla_desempaquetada> <salida.docx>"""
import sys, os, re, json, shutil, zipfile, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from xml.sax.saxutils import escape
from lxml import etree
from PIL import Image
import texto as T

TPL, OUT = sys.argv[1], sys.argv[2]
HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(HERE, "..", "figuras")
WORK = os.path.join(HERE, "docx_tmp")
LANG = '<w:lang w:val="es-ES"/>'
W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
CM = 567  # twips por cm

# ------------------------------------------------------------------ utilidades XML
def rpr(b=False, i=False, sz=None, sup=False, extra=""):
    s = ("<w:b/><w:bCs/>" if b else "") + ("<w:i/><w:iCs/>" if i else "")
    if sz: s += f'<w:sz w:val="{sz}"/><w:szCs w:val="{sz}"/>'
    if sup: s += '<w:vertAlign w:val="superscript"/>'
    return f"<w:rPr>{extra}{s}{LANG}</w:rPr>"

def run(t, **k): return f'<w:r>{rpr(**k)}<w:t xml:space="preserve">{escape(t)}</w:t></w:r>'

def multicita(t):
    return re.sub(r"\[([^\[\]]*?\d\d(?:; [^\[\]]*?\d\d)+)\]", lambda m: "[" + m.group(1).replace("; ", "], [") + "]", t)

def runs(text, sz=None, b=False, i=False):
    text = multicita(text); out = []
    for tok in re.split(r"(\*\*.+?\*\*|\*[^*]+?\*|\^[^^]+?\^)", text):
        if not tok: continue
        if tok.startswith("**"): out.append(run(tok[2:-2], b=True, i=i, sz=sz))
        elif tok.startswith("*"): out.append(run(tok[1:-1], b=b, i=not i, sz=sz))
        elif tok.startswith("^"): out.append(run(tok[1:-1], b=b, i=i, sz=sz, sup=True))
        else: out.append(run(tok, b=b, i=i, sz=sz))
    return "".join(out)

def para(style, text="", ppr="", sz=None, b=False, i=False):
    return f'<w:p><w:pPr><w:pStyle w:val="{style}"/>{ppr}</w:pPr>{runs(text, sz=sz, b=b, i=i) if text else ""}</w:p>'

# ------------------------------------------------------------------ figuras, tablas
rels_extra, media_extra, _id = [], [], [200]
def nid(): _id[0] += 1; return _id[0]

def figura(archivo, ancho_cm, leyenda):
    src = os.path.join(FIG, archivo); w, h = Image.open(src).size
    cx = int(ancho_cm * 360000); cy = int(cx * h / w); n = nid(); rid = f"rId{n}"
    destino = f"media/{archivo}"; rels_extra.append(f'<Relationship Id="{rid}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="{destino}"/>')
    media_extra.append((src, "word/" + destino))
    alt = escape(re.sub(r"^Figura \d+: ", "", leyenda)[:200], {'"': "&quot;"})
    dr = (f'<w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0"><wp:extent cx="{cx}" cy="{cy}"/><wp:effectExtent l="0" t="0" r="0" b="0"/>'
          f'<wp:docPr id="{n}" name="Figura {n}" descr="{alt}"/><wp:cNvGraphicFramePr><a:graphicFrameLocks noChangeAspect="1"/></wp:cNvGraphicFramePr>'
          f'<a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture"><pic:pic><pic:nvPicPr><pic:cNvPr id="{n}" name="{archivo}" descr="{alt}"/><pic:cNvPicPr/></pic:nvPicPr>'
          f'<pic:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill><pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>'
          f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr></pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing>')
    return (f'<w:p><w:pPr><w:pStyle w:val="JUCSFigure"/><w:keepNext/></w:pPr><w:r><w:rPr><w:noProof/></w:rPr>{dr}</w:r></w:p>'
            + para("JUCSFigureTitle", leyenda, ppr='<w:spacing w:before="120" w:after="240"/>'))

def num(celda):
    m = re.match(r"\s*([-+]?\d+[.,]?\d*)", celda); return float(m.group(1).replace(",", ".")) if m else None

JC = {"l": "left", "c": "center", "r": "right", "j": "left"}
def tabla(t):
    _, leyenda, enc, filas, anchos, o = t
    nc = len(enc); al = (o.get("al", "l" + "c" * (nc - 1)) + "c" * nc)[:nc]
    sz = 18 if nc <= 4 else (17 if nc <= 6 else 16)
    tw = [int(round(a * CM)) for a in anchos]; assert len(tw) == nc and sum(tw) <= int(12.25 * CM), (leyenda[:20], sum(tw))
    bd = lambda s=4: "".join(f'<w:{x} w:val="single" w:sz="{s if x == "top" else 4}" w:space="0" w:color="auto"/>' for x in ("top", "left", "bottom", "right"))
    def celda(txt, ancho, jc, b=False, span=1, top=4, hdr=False, mejor=False, keep=True):
        sp = f'<w:gridSpan w:val="{span}"/>' if span > 1 else ""
        return (f'<w:tc><w:tcPr><w:tcW w:w="{ancho}" w:type="dxa"/>{sp}<w:tcBorders>{bd(top)}</w:tcBorders><w:vAlign w:val="{"bottom" if hdr else "center"}"/></w:tcPr>'
                f'<w:p><w:pPr><w:pStyle w:val="{"JUCSTableHeading" if hdr else "JUCSTable"}"/>{"<w:keepNext/>" if keep else ""}<w:jc w:val="{jc}"/></w:pPr>{runs(txt, sz=sz, b=(b or mejor)) if txt else ""}</w:p></w:tc>')
    fl = []
    if "grupos" in o:
        cs = []; k = 0
        for lab, span in o["grupos"]:
            cs.append(celda(lab, sum(tw[k:k + span]), "center", span=span, hdr=True)); k += span
        fl.append(f'<w:tr><w:trPr><w:cantSplit/><w:tblHeader/></w:trPr>{"".join(cs)}</w:tr>')
    fl.append('<w:tr><w:trPr><w:cantSplit/><w:tblHeader/></w:trPr>' + "".join(celda(h, tw[j], "left" if al[j] == "l" else "center", hdr=True) for j, h in enumerate(enc)) + "</w:tr>")
    for r_i, fila in enumerate(filas):
        ult = o.get("negrita_ultima") and r_i == len(filas) - 1
        mejor = None
        if o.get("mejor_fila"):
            v = {j: num(c) for j, c in enumerate(fila) if j >= 3 and num(c) is not None}; mejor = max(v, key=v.get) if v else None
        top = 12 if r_i in o.get("separador_antes", []) else 4
        keep = not o.get("dividir") or r_i < 1 or r_i >= len(filas) - 2
        fl.append("<w:tr><w:trPr><w:cantSplit/></w:trPr>" + "".join(celda(c, tw[j], JC[al[j]], b=ult, top=top, mejor=(j == mejor), keep=keep) for j, c in enumerate(fila)) + "</w:tr>")
    tbl = (f'<w:tbl><w:tblPr><w:tblW w:w="{sum(tw)}" w:type="dxa"/><w:jc w:val="center"/><w:tblBorders>' + "".join(f'<w:{x} w:val="single" w:sz="4" w:space="0" w:color="auto"/>' for x in ("top", "left", "bottom", "right", "insideH", "insideV"))
           + '</w:tblBorders><w:tblLayout w:type="fixed"/><w:tblCellMar><w:left w:w="57" w:type="dxa"/><w:right w:w="57" w:type="dxa"/></w:tblCellMar><w:tblLook w:val="04A0" w:firstRow="1" w:lastRow="0" w:firstColumn="1" w:lastColumn="0" w:noHBand="0" w:noVBand="1"/></w:tblPr>'
           + "<w:tblGrid>" + "".join(f'<w:gridCol w:w="{x}"/>' for x in tw) + "</w:tblGrid>" + "".join(fl) + "</w:tbl>")
    return tbl + para("JUCSFigureTitle", leyenda, ppr='<w:spacing w:before="120" w:after="240"/>')

# ------------------------------------------------------------------ portada
AUTORES = [("Roberto Enrique Quezada-Rodríguez", "School of Systems Engineering", "0009-0004-0869-3881", "requezadaro@unitru.edu.pe"),
           ("Melanie Celeste Tello Fuentes", "School of Systems Engineering", "0009-0007-4728-138X", "mctellofu@unitru.edu.pe"),
           ("Juan Pedro Santos Fernández", "Department of Systems Engineering", "0000-0002-8882-9256", "jsantos@unitru.edu.pe"),
           ("Robert Jerry Sanchez Ticona", "Department of Systems Engineering", "0000-0001-9387-1945", "rsanchezt@unitru.edu.pe")]
UNI = "Universidad Nacional de Trujillo, Trujillo, La Libertad, Peru"

def orcid_icon(n, largo):
    x = 408509 + int((66 - largo) / 2 * 50000); pid = nid()
    return (f'<w:r><w:rPr><w:noProof/></w:rPr><w:drawing><wp:anchor distT="0" distB="0" distL="114300" distR="114300" simplePos="0" relativeHeight="{251659264 + 2048 * n}" behindDoc="0" locked="0" layoutInCell="1" allowOverlap="1">'
            f'<wp:simplePos x="0" y="0"/><wp:positionH relativeFrom="column"><wp:posOffset>{x}</wp:posOffset></wp:positionH><wp:positionV relativeFrom="paragraph"><wp:posOffset>128558</wp:posOffset></wp:positionV>'
            f'<wp:extent cx="129540" cy="129540"/><wp:effectExtent l="0" t="0" r="0" b="0"/><wp:wrapNone/><wp:docPr id="{pid}" name="ORCID {n}" descr="Icono de ORCID"/><wp:cNvGraphicFramePr><a:graphicFrameLocks noChangeAspect="1"/></wp:cNvGraphicFramePr>'
            f'<a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture"><pic:pic><pic:nvPicPr><pic:cNvPr id="{pid}" name="ORCID {n}"/><pic:cNvPicPr/></pic:nvPicPr><pic:blipFill>'
            f'<a:blip r:embed="rId8" cstate="print"><a:extLst><a:ext uri="{{28A0092B-C50C-407E-A947-70E740481C1C}}"><a14:useLocalDpi val="0"/></a:ext><a:ext uri="{{96DAC541-7B7A-43D3-8B79-37D633B846F1}}"><asvg:svgBlip r:embed="rId9"/></a:ext></a:extLst></a:blip>'
            f'<a:stretch><a:fillRect/></a:stretch></pic:blipFill><pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="129540" cy="129540"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr></pic:pic></a:graphicData></a:graphic></wp:anchor></w:drawing></w:r>')

def portada():
    o = [f'<w:p><w:pPr><w:pStyle w:val="JUCSTitle"/><w:spacing w:after="0"/></w:pPr>{run(T.TITULO)}</w:p>']
    o.append('<w:p><w:pPr><w:pStyle w:val="JUCSAuthor"/><w:spacing w:before="0"/></w:pPr></w:p>')
    for k, (nom, dep, orc, mail) in enumerate(AUTORES, 1):
        rid = f"rId{100 + k}"; rels_extra.append(f'<Relationship Id="{rid}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink" Target="https://orcid.org/{orc}" TargetMode="External"/>')
        o.append(f'<w:p><w:pPr><w:pStyle w:val="JUCSAuthor"/><w:spacing w:before="{0 if k == 1 else 0}"/></w:pPr>{run(nom, b=True)}</w:p>')
        o.append(f'<w:p><w:pPr><w:pStyle w:val="JUCSAffilitation"/></w:pPr>{run("(" + dep + ",")}</w:p>')
        o.append(f'<w:p><w:pPr><w:pStyle w:val="JUCSAffilitation"/></w:pPr>{orcid_icon(k, 37 + 2 + len(mail) + 1)}{run(UNI)}</w:p>')
        o.append(f'<w:p><w:pPr><w:pStyle w:val="JUCSOrcid"/><w:rPr><w:sz w:val="18"/><w:szCs w:val="18"/></w:rPr></w:pPr><w:hyperlink r:id="{rid}" w:history="1">{run("https://orcid.org/" + orc, extra="<w:rStyle w:val=" + chr(34) + "Hyperlink" + chr(34) + "/>", sz=18)}</w:hyperlink>{run(", " + mail + ")", sz=18)}</w:p>')
        o.append('<w:p><w:pPr><w:pStyle w:val="JUCSAffilitation"/></w:pPr></w:p>')
    o.append('<w:p><w:pPr><w:pStyle w:val="JUCSAffilitation"/></w:pPr></w:p>')
    f = '<w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:cs="Times New Roman"/>'
    o.append(f'<w:p><w:pPr><w:pStyle w:val="JUCSAbstract"/><w:spacing w:before="0"/></w:pPr>{run("Resumen:", b=True, extra=f)}{run(" " + T.RESUMEN, extra=f)}</w:p>')
    o.append('<w:p><w:pPr><w:pStyle w:val="JUCSAbstract"/><w:spacing w:before="0"/></w:pPr></w:p>')
    fk = '<w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/>'
    o.append(f'<w:p><w:pPr><w:pStyle w:val="JUCSKeywords"/><w:spacing w:before="0"/></w:pPr>{run("Palabras clave:", b=True, extra=fk)}{run(T.PALABRAS, extra=fk)}<w:r><w:cr/></w:r>{run("Categorías:", b=True, extra=fk)}{run(T.CATEGORIAS, extra=fk)}</w:p>')
    o.append(f'<w:p><w:pPr><w:pStyle w:val="JUCSKeywords"/><w:spacing w:before="0"/></w:pPr>{run("DOI:", b=True, extra=fk)}{run(" 10.3897/jucs.<SubmissionNumber>", extra=fk)}</w:p>')
    return o

# ------------------------------------------------------------------ cuerpo
def cuerpo():
    o = []; B = T.B
    for k, b in enumerate(B):
        t = b[0]; sig = B[k + 1][0] if k + 1 < len(B) else None
        if t == "h1":
            o.append(para("JUCSHeading1", b[1], ppr=f'<w:spacing w:after="{120 if sig == "h2" else 240}"/>'))
        elif t == "h2":
            o.append(para("JUCSHeading2", b[1], ppr='<w:spacing w:before="{}"/><w:ind w:left="578" w:hanging="578"/>'.format(0 if B[k - 1][0] == "h1" else 200)))
        elif t == "agr":
            o.append(para("JUCSReferenceHeading", b[1], ppr='<w:spacing w:before="360" w:after="120"/>'))
        elif t == "p1": o.append(para("JUCSParagraphFirst", b[1]))
        elif t == "p": o.append(para("JUCSParagraph", b[1]))
        elif t == "fig": o.append(figura(b[1], b[2], b[3]))
        elif t == "tabla_ref":
            o.append('<w:p><w:pPr><w:pStyle w:val="JUCSParagraphFirst"/><w:keepNext/><w:spacing w:before="0" w:after="0" w:line="140" w:lineRule="exact"/></w:pPr></w:p>')
            o.append(tabla(b[1]))
        else: raise ValueError(t)
    o.append(para("JUCSReferenceHeading", "Referencias", ppr='<w:spacing w:before="360" w:after="240"/>'))
    for r in json.load(open(os.path.join(HERE, "refs.json"), encoding="utf-8")):
        m = re.match(r"(\[[^\]]+\])\s*(.*)", r, re.S)
        o.append(f'<w:p><w:pPr><w:pStyle w:val="JUCSReferences"/><w:spacing w:before="0" w:after="120"/><w:jc w:val="left"/></w:pPr>{run(m.group(1) + " ")}{run(m.group(2))}</w:p>')
    return o

# ------------------------------------------------------------------ ensamblado
if os.path.exists(WORK): shutil.rmtree(WORK)
shutil.copytree(TPL, WORK)
docp = os.path.join(WORK, "word/document.xml"); raw = open(docp, encoding="utf-8").read()
cab = raw[:raw.index("<w:body>") + len("<w:body>")]
NS_EXTRA = ('xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture" '
            'xmlns:a14="http://schemas.microsoft.com/office/drawing/2010/main" xmlns:asvg="http://schemas.microsoft.com/office/drawing/2016/SVG/main"')
cab = cab.replace("<w:document ", "<w:document " + NS_EXTRA + " ", 1)
sect = re.search(r"<w:sectPr\b.*?</w:sectPr>", raw, re.S).group(0)
body = "".join(portada() + cuerpo())
open(docp, "w", encoding="utf-8").write(cab + body + sect + "</w:body></w:document>")

# relaciones: quitar muestra (imagen, hipervinculos) y anadir las nuevas
relp = os.path.join(WORK, "word/_rels/document.xml.rels"); rels = open(relp, encoding="utf-8").read()
for rid in ("rId10", "rId11", "rId12", "rId13"): rels = re.sub(rf'<Relationship Id="{rid}"[^>]*/>', "", rels)
rels = rels.replace("</Relationships>", "".join(rels_extra) + "</Relationships>"); open(relp, "w", encoding="utf-8").write(rels)
os.remove(os.path.join(WORK, "word/media/image3.jpeg"))
for src, dst in media_extra: shutil.copy(src, os.path.join(WORK, dst))
ct = os.path.join(WORK, "[Content_Types].xml"); s = open(ct, encoding="utf-8").read(); s = s.replace('<Default Extension="jpeg" ContentType="image/jpeg"/>', ""); open(ct, "w", encoding="utf-8").write(s)

# encabezados: texto en cache de los campos TITLE
CORTO_ENC = "Quezada-Rodríguez R.E., Tello Fuentes M.C., et al.: Validación entre escenarios…"
for h in ("header1.xml", "header2.xml"):
    hp = os.path.join(WORK, "word", h); tree = etree.parse(hp); ns = {"w": W}
    for it in tree.iter("{%s}instrText" % W):
        if "TITLE" not in (it.text or ""): continue
        r_it = it.getparent(); p = r_it.getparent(); hijos = list(p); i0 = hijos.index(r_it)
        sep = next(x for x in hijos[i0:] if x.find("w:fldChar", ns) is not None and x.find("w:fldChar", ns).get("{%s}fldCharType" % W) == "separate")
        fin = next(x for x in hijos[hijos.index(sep) + 1:] if x.find("w:fldChar", ns) is not None and x.find("w:fldChar", ns).get("{%s}fldCharType" % W) == "end")
        ini, fn = hijos.index(sep), hijos.index(fin)
        modelo = etree.fromstring(etree.tostring(sep));
        for x in modelo.findall("w:fldChar", ns): modelo.remove(x)
        tt = etree.SubElement(modelo, "{%s}t" % W); tt.text = CORTO_ENC
        for x in hijos[ini + 1:fn]: p.remove(x)
        p.insert(ini + 1, modelo)
    tree.write(hp, xml_declaration=True, encoding="UTF-8", standalone=True)

# propiedades del documento
ahora = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
core = os.path.join(WORK, "docProps/core.xml"); s = open(core, encoding="utf-8").read()
s = re.sub(r"<dc:title>.*?</dc:title>", f"<dc:title>{escape(CORTO_ENC)}</dc:title>", s)
s = re.sub(r"<dc:creator>.*?</dc:creator>", "<dc:creator>Quezada-Rodríguez R.E.; Tello Fuentes M.C.; Santos Fernández J.P.; Sanchez Ticona R.J.</dc:creator>", s)
s = re.sub(r"<cp:lastModifiedBy>.*?</cp:lastModifiedBy>", "<cp:lastModifiedBy>Quezada-Rodríguez R.E.</cp:lastModifiedBy>", s)
s = re.sub(r"<cp:lastPrinted>.*?</cp:lastPrinted>", "", s)
s = re.sub(r"(<dcterms:(?:created|modified)[^>]*>).*?(</dcterms:\w+>)", lambda m: m.group(1) + ahora + m.group(2), s)
s = s.replace("<cp:keywords></cp:keywords>", f"<cp:keywords>{escape(T.PALABRAS.strip())}</cp:keywords>"); open(core, "w", encoding="utf-8").write(s)
app = os.path.join(WORK, "docProps/app.xml")
open(app, "w", encoding="utf-8").write('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes"><Template>Normal.dotm</Template><Application>Microsoft Office Word</Application><DocSecurity>0</DocSecurity><ScaleCrop>false</ScaleCrop><Company>Journal of Universal Computer Science</Company><LinksUpToDate>false</LinksUpToDate><SharedDoc>false</SharedDoc><HyperlinksChanged>false</HyperlinksChanged><AppVersion>16.0000</AppVersion></Properties>')

# empaquetado (sin entradas de directorio; [Content_Types].xml primero)
if os.path.exists(OUT): os.remove(OUT)
with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
    z.write(os.path.join(WORK, "[Content_Types].xml"), "[Content_Types].xml")
    for d, _, fs in os.walk(WORK):
        for f in sorted(fs):
            full = os.path.join(d, f); arc = os.path.relpath(full, WORK)
            if arc != "[Content_Types].xml": z.write(full, arc)
shutil.rmtree(WORK)
print("escrito", OUT, os.path.getsize(OUT), "bytes")
