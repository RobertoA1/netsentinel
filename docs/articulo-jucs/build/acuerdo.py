"""Rellena el acuerdo de publicacion de J.UCS (V6 2026): autor de correspondencia, titulo y demas autores. Fecha y firma quedan en blanco.
Uso: python -I acuerdo.py <acuerdo_desempaquetado> <salida.docx>"""
import sys, os, shutil, zipfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lxml import etree
import texto as T
SRC, OUT = sys.argv[1], sys.argv[2]
WORK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "agr_tmp")
if os.path.exists(WORK): shutil.rmtree(WORK)
shutil.copytree(SRC, WORK)
Wn = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"; W = "{%s}" % Wn
p = os.path.join(WORK, "word/document.xml"); tree = etree.parse(p); body = tree.getroot().find(W + "body")
def poner(i, texto, esperado):
    par = body[i]; ts = list(par.iter(W + "t")); actual = "".join(x.text or "" for x in ts)
    assert esperado in actual, (i, actual[:60])
    ts[0].text = texto; ts[0].set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    for x in ts[1:]: x.text = ""
poner(5, "Roberto Enrique Quezada-Rodríguez, School of Systems Engineering, Universidad Nacional de Trujillo, Trujillo, La Libertad, Peru (requezadaro@unitru.edu.pe)", "………")
poner(35, T.TITLE_EN, "………")
poner(39, "Melanie Celeste Tello Fuentes, Juan Pedro Santos Fernández,", "………")
poner(41, "Robert Jerry Sanchez Ticona", "………")
poner(91, "Roberto Enrique Quezada-Rodríguez, Universidad Nacional de Trujillo", "____")
tree.write(p, xml_declaration=True, encoding="UTF-8", standalone=True)
if os.path.exists(OUT): os.remove(OUT)
with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
    z.write(os.path.join(WORK, "[Content_Types].xml"), "[Content_Types].xml")
    for d, _, fs in os.walk(WORK):
        for f in sorted(fs):
            full = os.path.join(d, f); arc = os.path.relpath(full, WORK)
            if arc != "[Content_Types].xml": z.write(full, arc)
shutil.rmtree(WORK); print("escrito", OUT)
