from __future__ import annotations

import io
import re
from datetime import datetime

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from app.services.reports.model import SYSTEM_NAME, Chart, ReportData, ReportMeta, Table
from app.services.reports.util import fmt_dt, period_text

HEAD_FILL = PatternFill("solid", fgColor="1E3A8A")
HEAD_FONT = Font(bold=True, color="FFFFFF")
THIN = Side(style="thin", color="CBD5E1")
MAX_XLSX_ROWS = 200_000


def _sheet_name(title: str, used: set[str]) -> str:
    base = re.sub(r"[\[\]\*\?/\\:]", " ", title).strip()[:28] or "Hoja"
    name, i = base, 2
    while name.lower() in used:
        name = f"{base[:25]} {i}"
        i += 1
    used.add(name.lower())
    return name


def _autowidth(ws, max_w: int = 60) -> None:
    for col in ws.columns:
        letter = get_column_letter(col[0].column)
        longest = max((len(str(c.value)) if c.value is not None else 0) for c in col[:500])
        ws.column_dimensions[letter].width = min(max(10, longest + 2), max_w)


def render_xlsx(data: ReportData, meta: ReportMeta) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "Resumen"
    used = {"resumen"}
    ws["A1"] = f"{SYSTEM_NAME} - {data.name}"
    ws["A1"].font = Font(bold=True, size=14)
    for i, (k, v) in enumerate((("Período", period_text(data)), ("Generado por", meta.generated_by),
                                ("Fecha de generación", fmt_dt(meta.generated_at))), start=2):
        ws.cell(i, 1, k).font = Font(bold=True)
        ws.cell(i, 2, v)
    ws.cell(6, 1, "Resumen").font = Font(bold=True)
    ws.cell(6, 2, data.summary).alignment = Alignment(wrap_text=True, vertical="top")
    ws.merge_cells(start_row=6, start_column=2, end_row=6, end_column=6)
    ws.row_dimensions[6].height = 75
    r = 8
    if data.kpis:
        for j, h in enumerate(("Indicador", "Valor"), start=1):
            c = ws.cell(r, j, h)
            c.fill, c.font = HEAD_FILL, HEAD_FONT
        for k in data.kpis:
            r += 1
            ws.cell(r, 1, k.label)
            ws.cell(r, 2, k.value)
    ws.column_dimensions["A"].width = 34
    for col in "BCDEF":
        ws.column_dimensions[col].width = 26
    items = data.blocks or (list(data.charts) + list(data.tables))
    for it in items:
        if isinstance(it, Chart):  # datos del gráfico como tabla (auditable) + imagen 600 DPI en reportes ML
            s = wb.create_sheet(_sheet_name("Gráfico " + it.title, used))
            _chart_sheet(s, it)
        else:
            s = wb.create_sheet(_sheet_name(it.title, used))
            s.append(it.columns)
            for row in it.rows[:MAX_XLSX_ROWS]:
                s.append([_xl(v) for v in row])
            _style_table(s)
            _notes(s, it, s.max_row + 2)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _notes(s, obj, row: int) -> None:
    for lab, txt in (("Nota", obj.note), ("Cómo leerlo / qué significa", " ".join(obj.meaning)),
                     ("Precaución", " ".join(obj.caution))):
        if txt:
            s.cell(row, 1, lab).font = Font(bold=True)
            c = s.cell(row, 2, txt)
            c.alignment = Alignment(wrap_text=True, vertical="top")
            s.merge_cells(start_row=row, start_column=2, end_row=row, end_column=8)
            s.row_dimensions[row].height = max(30, 15 * (len(txt) // 90 + 1))
            row += 1


def _chart_sheet(s, ch: Chart) -> None:
    if ch.spec is None:
        s.append(["Etiqueta"] + list(ch.series.keys()))
        for i, lab in enumerate(ch.labels):
            s.append([lab] + [vals[i] if i < len(vals) else None for vals in ch.series.values()])
        _style_table(s)
        _add_png(s, ch, f"A{s.max_row + 3}")  # la figura a 600 DPI acompaña a sus datos (auditables)
        _notes(s, ch, s.max_row + 2)
        return
    from openpyxl.drawing.image import Image as XImage

    from app.services.reports.charts import png_size, render_png

    png = render_png(ch)
    pw, ph = png_size(png)
    img = XImage(io.BytesIO(png))
    img.width, img.height = 720, int(720 * ph / pw)  # tamaño en pantalla; el PNG conserva 600 DPI
    s["A1"] = ch.title
    s["A1"].font = Font(bold=True, size=12)
    s.add_image(img, "A3")
    _notes(s, ch, 3 + int(img.height / 20) + 2)
    s.column_dimensions["A"].width = 30


def _add_png(s, ch: Chart, anchor: str) -> None:
    from openpyxl.drawing.image import Image as XImage

    from app.services.reports.charts import png_size, render_png

    png = render_png(ch)
    pw, ph = png_size(png)
    img = XImage(io.BytesIO(png))
    img.width, img.height = 720, int(720 * ph / pw)
    s.add_image(img, anchor)
    s.cell(s.max_row + 1, 1)  # reserva visual aproximada de las filas que ocupa la imagen
    for _ in range(int(img.height / 20) + 1):
        s.cell(s.max_row + 1, 1)


def _xl(v):
    if isinstance(v, datetime) and v.tzinfo is not None:
        return v.replace(tzinfo=None)
    return v


def _style_table(s) -> None:
    for c in s[1]:
        c.fill, c.font = HEAD_FILL, HEAD_FONT
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        c.border = Border(top=THIN, bottom=THIN, left=THIN, right=THIN)
    s.freeze_panes = "A2"
    if s.max_row >= 1 and s.max_column >= 1:
        s.auto_filter.ref = s.dimensions
    for row in s.iter_rows(min_row=2):
        for c in row:
            if isinstance(c.value, datetime):
                c.number_format = "yyyy-mm-dd hh:mm:ss"
    _autowidth(s)
