from __future__ import annotations

import io
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Image, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table as RLTable, TableStyle

from app.services.reports.charts import png_size, render_png
from app.services.reports.model import MAX_TABLE_ROWS_DOC, SYSTEM_NAME, Chart, ReportData, ReportMeta, Table
from app.services.reports.util import cell_text, fmt_dt, period_text


def render_pdf(data: ReportData, meta: ReportMeta) -> bytes:
    buf = io.BytesIO()
    page = landscape(A4)
    doc = SimpleDocTemplate(buf, pagesize=page, leftMargin=1.5 * cm, rightMargin=1.5 * cm, topMargin=2.4 * cm,
                            bottomMargin=1.6 * cm, title=f"{SYSTEM_NAME} - {data.name}", author=meta.generated_by)
    ss = getSampleStyleSheet()
    h1 = ParagraphStyle("h1", parent=ss["Heading1"], fontSize=18, textColor=colors.HexColor("#0f172a"))
    h2 = ParagraphStyle("h2", parent=ss["Heading2"], fontSize=12, textColor=colors.HexColor("#1e3a8a"))
    body = ParagraphStyle("b", parent=ss["BodyText"], fontSize=9.5, leading=13)
    small = ParagraphStyle("s", parent=ss["BodyText"], fontSize=7, leading=8.5)
    smallb = ParagraphStyle("sb", parent=small, fontName="Helvetica-Bold", textColor=colors.white)

    def header_footer(c, d):
        c.saveState()
        w, h = page
        c.setFillColor(colors.HexColor("#0f172a"))
        c.rect(0, h - 1.5 * cm, w, 1.5 * cm, stroke=0, fill=1)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(1.5 * cm, h - 0.95 * cm, f"{SYSTEM_NAME}  |  {data.name}")
        c.setFont("Helvetica", 8)
        c.drawRightString(w - 1.5 * cm, h - 0.95 * cm, f"Período: {period_text(data)}")
        c.setFillColor(colors.HexColor("#475569"))
        c.setFont("Helvetica", 7.5)
        c.drawString(1.5 * cm, 0.8 * cm, f"Generado por {meta.generated_by} el {fmt_dt(meta.generated_at)}")
        c.drawRightString(w - 1.5 * cm, 0.8 * cm, f"Página {d.page}")
        c.restoreState()

    el: list = [Paragraph(escape(data.name), h1),
                Paragraph(f"<b>Período:</b> {escape(period_text(data))} &nbsp;&nbsp; <b>Generado por:</b> "
                          f"{escape(meta.generated_by)} &nbsp;&nbsp; <b>Fecha:</b> {fmt_dt(meta.generated_at)}", body),
                Spacer(1, 8), Paragraph("Resumen", h2), Paragraph(escape(data.summary), body), Spacer(1, 8)]
    if data.kpis:
        cells = [[Paragraph(f"<font size=7 color='#64748b'>{escape(k.label)}</font><br/><b><font size=12>"
                            f"{escape(k.value)}</font></b>", body) for k in data.kpis[i:i + 4]]
                 for i in range(0, len(data.kpis), 4)]
        for r in cells:
            r += [""] * (4 - len(r))
        t = RLTable(cells, colWidths=[(page[0] - 3 * cm) / 4] * 4)
        t.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
                               ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#e2e8f0")),
                               ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                               ("VALIGN", (0, 0), (-1, -1), "TOP"), ("TOPPADDING", (0, 0), (-1, -1), 5),
                               ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]))
        el += [Paragraph("Indicadores clave", h2), t, Spacer(1, 10)]
    def interp_paras(obj) -> list:
        out = []
        if obj.note:
            out.append(Paragraph("<i>Nota: " + escape(obj.note) + "</i>", small))
        if obj.meaning:
            out.append(Paragraph("<b>Cómo leerlo / qué significa:</b> " + escape(" ".join(obj.meaning)), body))
        if obj.caution:
            out.append(Paragraph("<font color='#b45309'><b>Precaución:</b> " + escape(" ".join(obj.caution)) + "</font>", body))
        if out:
            out.append(Spacer(1, 8))
        return out

    def chart_els(ch: Chart) -> list:
        png = render_png(ch)
        pw, ph = png_size(png)
        w = 17 * cm
        els = []
        if ch.spec is not None:
            els.append(Paragraph(escape(ch.title), h2))
        els.append(KeepTogether([Image(io.BytesIO(png), width=w, height=w * ph / pw)]))
        return els + [Spacer(1, 4)] + interp_paras(ch)

    def table_els(tb: Table, page_break: bool) -> list:
        el_: list = ([PageBreak()] if page_break else []) + [Paragraph(escape(tb.title), h2)]
        rows = tb.rows[:MAX_TABLE_ROWS_DOC]
        total = tb.total_rows if tb.total_rows is not None else len(tb.rows)
        if not rows:
            return el_ + [Paragraph("Sin datos en el período seleccionado.", body)]
        ncol = len(tb.columns)
        data_rows = [[Paragraph(escape(c), smallb) for c in tb.columns]] + \
                    [[Paragraph(escape(cell_text(v, tb.decimals)), small) for v in r] for r in rows]
        t = RLTable(data_rows, colWidths=[(page[0] - 3 * cm) / ncol] * ncol, repeatRows=1)
        t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e3a8a")),
                               ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f1f5f9")]),
                               ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#cbd5e1")),
                               ("VALIGN", (0, 0), (-1, -1), "TOP")]))
        el_.append(t)
        if total > len(rows):
            el_.append(Paragraph(f"Se muestran {len(rows)} de {total} filas. El archivo Excel incluye el detalle completo.",
                                 small))
        return el_ + [Spacer(1, 4)] + interp_paras(tb)

    if data.blocks:  # reportes ML: figuras y tablas intercaladas con su interpretación
        for blk in data.blocks:
            el += chart_els(blk) if isinstance(blk, Chart) else table_els(blk, False)
    else:
        for ch in data.charts:
            el += chart_els(ch)
        for tb in data.tables:
            el += table_els(tb, True)
    doc.build(el, onFirstPage=header_footer, onLaterPages=header_footer)
    return buf.getvalue()
