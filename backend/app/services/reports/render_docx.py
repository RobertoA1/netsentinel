from __future__ import annotations

import io

from docx import Document
from docx.enum.section import WD_ORIENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

from app.services.reports.charts import render_png
from app.services.reports.model import MAX_TABLE_ROWS_DOC, SYSTEM_NAME, Chart, ReportData, ReportMeta, Table
from app.services.reports.util import cell_text, fmt_dt, period_text


def _shade(cell, hex_color: str) -> None:
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_color)
    tcPr.append(shd)


def render_docx(data: ReportData, meta: ReportMeta) -> bytes:
    doc = Document()
    sec = doc.sections[0]
    sec.orientation = WD_ORIENT.LANDSCAPE
    sec.page_width, sec.page_height = sec.page_height, sec.page_width
    for m in ("left_margin", "right_margin"):
        setattr(sec, m, Cm(1.8))
    doc.styles["Normal"].font.name = "Calibri"
    doc.styles["Normal"].font.size = Pt(10)
    hp = sec.header.paragraphs[0]
    hp.text = f"{SYSTEM_NAME}  |  {data.name}  |  Período: {period_text(data)}"
    hp.runs[0].font.size = Pt(8)
    hp.runs[0].font.color.rgb = RGBColor(0x47, 0x55, 0x69)
    fp = sec.footer.paragraphs[0]
    fp.text = f"Generado por {meta.generated_by} el {fmt_dt(meta.generated_at)}"
    fp.runs[0].font.size = Pt(8)

    doc.add_heading(data.name, level=0)
    p = doc.add_paragraph()
    p.add_run("Período: ").bold = True
    p.add_run(period_text(data) + "    ")
    p.add_run("Generado por: ").bold = True
    p.add_run(meta.generated_by + "    ")
    p.add_run("Fecha: ").bold = True
    p.add_run(fmt_dt(meta.generated_at))
    doc.add_heading("Resumen", level=1)
    doc.add_paragraph(data.summary)
    if data.kpis:
        doc.add_heading("Indicadores clave", level=1)
        t = doc.add_table(rows=1, cols=2)
        t.style = "Light Grid Accent 1"
        t.rows[0].cells[0].text, t.rows[0].cells[1].text = "Indicador", "Valor"
        for k in data.kpis:
            r = t.add_row().cells
            r[0].text, r[1].text = k.label, k.value
    def interp(obj) -> None:
        if obj.note:
            q = doc.add_paragraph()
            r_ = q.add_run("Nota: " + obj.note)
            r_.italic, r_.font.size = True, Pt(8)
        if obj.meaning:
            q = doc.add_paragraph()
            q.add_run("Cómo leerlo / qué significa: ").bold = True
            q.add_run(" ".join(obj.meaning))
        if obj.caution:
            q = doc.add_paragraph()
            r_ = q.add_run("Precaución: ")
            r_.bold = True
            r_.font.color.rgb = RGBColor(0xB4, 0x53, 0x09)
            q.add_run(" ".join(obj.caution))

    def add_chart(ch: Chart) -> None:
        if ch.spec is not None:
            doc.add_heading(ch.title, level=2)
        doc.add_paragraph().add_run().add_picture(io.BytesIO(render_png(ch)), width=Cm(17))
        interp(ch)

    def add_table(tb: Table, page_break: bool) -> None:
        if page_break:
            doc.add_page_break()
        doc.add_heading(tb.title, level=1 if page_break else 2)
        rows = tb.rows[:MAX_TABLE_ROWS_DOC]
        total = tb.total_rows if tb.total_rows is not None else len(tb.rows)
        if not rows:
            doc.add_paragraph("Sin datos en el período seleccionado.")
            return
        t = doc.add_table(rows=1, cols=len(tb.columns))
        t.style = "Table Grid"
        for i, c in enumerate(tb.columns):
            cell = t.rows[0].cells[i]
            cell.text = ""
            run = cell.paragraphs[0].add_run(c)
            run.bold, run.font.size = True, Pt(8)
            run.font.color.rgb = RGBColor(255, 255, 255)
            _shade(cell, "1E3A8A")
        for r in rows:
            cells = t.add_row().cells
            for i, v in enumerate(r):
                cells[i].text = ""
                cells[i].paragraphs[0].add_run(cell_text(v, tb.decimals)).font.size = Pt(7.5)
        if total > len(rows):
            doc.add_paragraph(f"Se muestran {len(rows)} de {total} filas. El archivo Excel incluye el detalle completo.")
        interp(tb)

    if data.blocks:
        for blk in data.blocks:
            add_chart(blk) if isinstance(blk, Chart) else add_table(blk, False)
    else:
        for ch in data.charts:
            add_chart(ch)
        for tb in data.tables:
            add_table(tb, True)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()
