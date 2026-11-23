"""Professional report exporters: Word (.docx) and PDF."""

from __future__ import annotations

import io

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from fpdf import FPDF

from .schemas import ScanReport

_CYAN = RGBColor(0x0E, 0x74, 0x90)
_DARK = RGBColor(0x0F, 0x17, 0x2A)
_MUTED = RGBColor(0x64, 0x74, 0x8B)


def _fmt_date(report: ScanReport) -> str:
    return report.generated_at.strftime("%d/%m/%Y %H:%M")


def _set_cell_shading(cell, hex_color: str) -> None:
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_color)
    tcPr.append(shd)


def _docx_table(document: Document, headers: list[str], rows: list[list[str]]) -> None:
    table = document.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"
    hdr = table.rows[0].cells
    for i, h in enumerate(headers):
        hdr[i].text = str(h)
        _set_cell_shading(hdr[i], "0E7490")
        for p in hdr[i].paragraphs:
            for r in p.runs:
                r.bold = True
                r.font.size = Pt(9)
                r.font.color.rgb = RGBColor(255, 255, 255)
    for ri, row in enumerate(rows):
        cells = table.add_row().cells
        bg = "F8FAFC" if ri % 2 == 0 else "FFFFFF"
        for i, value in enumerate(row):
            cells[i].text = str(value)
            _set_cell_shading(cells[i], bg)
            for p in cells[i].paragraphs:
                for r in p.runs:
                    r.font.size = Pt(9)
                    r.font.color.rgb = _DARK
    document.add_paragraph()


def _docx_title(document: Document, text: str, size: int = 14, color=_CYAN, space_before=10, space_after=4) -> None:
    p = document.add_paragraph()
    p.paragraph_format.space_before = Pt(space_before)
    p.paragraph_format.space_after = Pt(space_after)
    run = p.add_run(text)
    run.bold = True
    run.font.size = Pt(size)
    run.font.color.rgb = color


def _docx_body(document: Document, text: str, size: int = 10, color=RGBColor(0x33, 0x41, 0x55), bold=False, italic=False) -> None:
    p = document.add_paragraph()
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.line_spacing = 1.35
    run = p.add_run(text)
    run.font.size = Pt(size)
    run.font.color.rgb = color
    run.bold = bold
    run.italic = italic


def build_docx(report: ScanReport) -> bytes:
    doc = Document()
    sec = doc.sections[0]
    sec.left_margin = Cm(2.2)
    sec.right_margin = Cm(2.2)
    sec.top_margin = Cm(2.0)
    sec.bottom_margin = Cm(2.0)

    for _ in range(2):
        doc.add_paragraph()
    p = doc.add_paragraph()
    run = p.add_run("INFORME PROFESIONAL DE ANÁLISIS DOCUMENTAL")
    run.bold = True
    run.font.size = Pt(11)
    run.font.color.rgb = _CYAN

    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(2)
    run = p.add_run(report.file_name)
    run.bold = True
    run.font.size = Pt(26)
    run.font.color.rgb = _DARK

    p = doc.add_paragraph()
    run = p.add_run("Resumen ejecutivo, extracción de datos, auditoría y recomendaciones")
    run.font.size = Pt(12)
    run.font.color.rgb = _MUTED

    doc.add_paragraph()
    _docx_table(doc, ["Campo", "Detalle"], [
        ["Archivo", report.file_name],
        ["Formato", report.file_type.upper()],
        ["Unidades analizadas", str(report.total_pages)],
        ["Motor de análisis", report.provider],
        ["Fecha de generación", _fmt_date(report)],
        ["Puntaje de calidad", f"{report.audit.score}/100"],
    ])

    _docx_title(doc, "¿De qué trata este documento?", 13, _DARK, 8, 4)
    _docx_body(doc, report.executive_summary.overview)
    if report.executive_summary.purpose:
        _docx_body(doc, report.executive_summary.purpose, bold=True)

    doc.add_page_break()

    _docx_title(doc, "1. Resumen Ejecutivo Detallado", 18, _CYAN, 0, 6)
    _docx_title(doc, "1.1 Desglose completo por sección/página", 13, _DARK, 6, 4)
    for idx, s in enumerate(report.executive_summary.sections, start=1):
        _docx_title(doc, f"{idx}. {s.title}", 11, _DARK, 8, 2)
        _docx_body(doc, s.content)
        if s.metrics:
            _docx_body(doc, "Métricas: " + "  ·  ".join(f"{m.label}: {m.value}" for m in s.metrics), 9, _CYAN, italic=True)
        for b in s.bullets:
            bp = doc.add_paragraph(str(b), style="List Bullet")
            for r in bp.runs:
                r.font.size = Pt(10)

    _docx_title(doc, "1.2 Conclusiones clave", 13, _DARK, 10, 4)
    for c in (report.executive_summary.conclusions or ["Sin conclusiones adicionales."]):
        bp = doc.add_paragraph(c, style="List Bullet")
        for r in bp.runs:
            r.font.size = Pt(10)

    _docx_title(doc, "1.3 Hallazgos críticos", 13, _DARK, 10, 4)
    for c in (report.executive_summary.critical_findings or ["Sin hallazgos críticos."]):
        bp = doc.add_paragraph(c, style="List Bullet")
        for r in bp.runs:
            r.font.size = Pt(10)
            r.font.color.rgb = RGBColor(0x99, 0x1B, 0x1B)

    doc.add_page_break()

    _docx_title(doc, "2. Datos y Métricas Extraídas", 18, _CYAN, 0, 6)
    _docx_title(doc, "2.1 Indicadores clave (KPIs)", 13, _DARK, 6, 4)
    _docx_table(doc, ["Indicador", "Valor", "Descripción"], [[k.label, k.value, k.description] for k in report.data_report.kpis])

    e = report.data_report.entities
    _docx_title(doc, "2.2 Entidades detectadas", 13, _DARK, 6, 4)
    for label, values in [("Fechas", e.dates), ("Montos", e.money), ("Porcentajes", e.percentages), ("Correos", e.emails), ("URLs", e.urls), ("Palabras clave", e.keywords), ("Alertas", e.alerts)]:
        _docx_body(doc, f"{label} ({len(values)}): {', '.join(values) if values else '—'}")

    if report.data_report.table:
        _docx_title(doc, "2.3 Detalle de entidades por página", 13, _DARK, 6, 4)
        _docx_table(doc, ["Página", "Tipo", "Valor", "Contexto"], [[str(r.page), r.kind, r.value, r.context[:120]] for r in report.data_report.table])

    doc.add_page_break()

    _docx_title(doc, "3. Auditoría y Recomendaciones", 18, _CYAN, 0, 6)
    _docx_body(doc, f"Puntaje de calidad documental: {report.audit.score}/100", 12, _CYAN, bold=True)
    for f in report.audit.findings:
        impact_color = {"alto": RGBColor(0xDC, 0x26, 0x26), "medio": RGBColor(0xD9, 0x77, 0x06), "bajo": RGBColor(0x05, 0x96, 0x69)}.get(f.impact, _MUTED)
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(8)
        run = p.add_run(f"{f.title} ")
        run.bold = True
        run.font.size = Pt(11)
        run.font.color.rgb = _DARK
        run2 = p.add_run(f"[Impacto {f.impact.upper()}]")
        run2.bold = True
        run2.font.size = Pt(9)
        run2.font.color.rgb = impact_color
        _docx_body(doc, f.detail)
        rec = doc.add_paragraph()
        rr = rec.add_run("Recomendación: ")
        rr.bold = True
        rr.font.size = Pt(10)
        rr.font.color.rgb = _CYAN
        rec.add_run(f.recommendation).font.size = Pt(10)

    if report.audit.strengths:
        _docx_title(doc, "Fortalezas identificadas", 13, _DARK, 10, 4)
        for s in report.audit.strengths:
            bp = doc.add_paragraph(s, style="List Bullet")
            for r in bp.runs:
                r.font.size = Pt(10)

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def _latin(text: object) -> str:
    return str(text).encode("latin-1", "replace").decode("latin-1")


def _truncate(text: str, max_chars: int) -> str:
    if max_chars <= 1:
        return ""
    return text if len(text) <= max_chars else text[: max_chars - 1] + "…"


class _ReportPDF(FPDF):
    def header(self) -> None:
        if self.page_no() == 1:
            return
        self.set_font("helvetica", "I", 8)
        self.set_text_color(100, 116, 139)
        self.cell(0, 8, _latin("DocuSpider AI — Informe profesional"), align="L")
        self.ln(10)

    def footer(self) -> None:
        self.set_y(-12)
        self.set_font("helvetica", "I", 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 8, _latin(f"Página {self.page_no()}/{{nb}}"), align="C")


def _pdf_table(pdf: FPDF, headers: list[str], rows: list[list[str]], widths: list[int]) -> None:
    def draw_header() -> None:
        pdf.set_font("helvetica", "B", 8)
        pdf.set_fill_color(14, 116, 144)
        pdf.set_text_color(255, 255, 255)
        for h, w in zip(headers, widths, strict=False):
            pdf.cell(w, 7, _latin(_truncate(h, int(w * 1.8))), border=1, fill=True)
        pdf.ln()

    draw_header()
    pdf.set_font("helvetica", "", 8)
    pdf.set_text_color(15, 23, 42)
    shaded = False
    for row in rows:
        if pdf.get_y() + 8 > pdf.page_break_trigger:
            pdf.add_page()
            draw_header()
            pdf.set_font("helvetica", "", 8)
            pdf.set_text_color(15, 23, 42)
        pdf.set_fill_color(248, 250, 252) if shaded else pdf.set_fill_color(255, 255, 255)
        for value, w in zip(row, widths, strict=False):
            pdf.cell(w, 6, _latin(_truncate(str(value), int(w * 1.8))), border=1, fill=True)
        pdf.ln()
        shaded = not shaded
    pdf.ln(3)


def build_pdf(report: ScanReport) -> bytes:
    pdf = _ReportPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.alias_nb_pages()
    pdf.set_margins(15, 15, 15)

    pdf.add_page()
    pdf.set_fill_color(14, 116, 144)
    pdf.rect(0, 0, 210, 48, "F")
    pdf.set_y(15)
    pdf.set_font("helvetica", "B", 11)
    pdf.set_text_color(220, 240, 245)
    pdf.cell(0, 6, _latin("INFORME PROFESIONAL DE ANÁLISIS DOCUMENTAL"), ln=True)
    pdf.set_font("helvetica", "B", 28)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 12, _latin("DocuSpider AI"), ln=True)

    pdf.set_y(62)
    pdf.set_x(pdf.l_margin)
    pdf.set_font("helvetica", "B", 20)
    pdf.set_text_color(15, 23, 42)
    pdf.multi_cell(0, 9, _latin(report.file_name))
    pdf.set_x(pdf.l_margin)
    pdf.set_font("helvetica", "", 11)
    pdf.set_text_color(100, 116, 139)
    pdf.multi_cell(0, 6, _latin("Resumen ejecutivo, extraccion de datos, auditoria y recomendaciones"))
    pdf.ln(4)
    pdf.set_draw_color(14, 116, 144)
    pdf.line(15, pdf.get_y(), 195, pdf.get_y())
    pdf.ln(6)
    _pdf_table(pdf, ["Campo", "Detalle"], [
        ["Formato", report.file_type.upper()],
        ["Unidades analizadas", str(report.total_pages)],
        ["Motor", report.provider],
        ["Generado", _fmt_date(report)],
        ["Puntaje", f"{report.audit.score}/100"],
    ], [55, 125])

    def heading(text: str, size: int = 14, color=(14, 116, 144)) -> None:
        pdf.ln(2)
        pdf.set_x(pdf.l_margin)
        pdf.set_font("helvetica", "B", size)
        pdf.set_text_color(*color)
        pdf.multi_cell(0, 7, _latin(text))
        pdf.set_draw_color(203, 213, 225)
        pdf.line(pdf.l_margin, pdf.get_y(), 195, pdf.get_y())
        pdf.ln(2)

    def sub(text: str) -> None:
        pdf.set_x(pdf.l_margin)
        pdf.set_font("helvetica", "B", 11)
        pdf.set_text_color(15, 23, 42)
        pdf.multi_cell(0, 6, _latin(text))
        pdf.ln(1)

    def body(text: str, size: int = 9, color=(51, 65, 85), italic=False) -> None:
        pdf.set_x(pdf.l_margin)
        pdf.set_font("helvetica", "I" if italic else "", size)
        pdf.set_text_color(*color)
        pdf.multi_cell(0, 5.5, _latin(text))
        pdf.ln(1)

    heading("¿De qué trata este documento?", 13, (15, 23, 42))
    body(report.executive_summary.overview, 10)
    if report.executive_summary.purpose:
        body(report.executive_summary.purpose, 10, italic=True)

    pdf.add_page()
    heading("1. Resumen Ejecutivo Detallado")
    sub("1.1 Desglose completo por sección/página")
    for idx, s in enumerate(report.executive_summary.sections, start=1):
        pdf.set_font("helvetica", "B", 10)
        pdf.set_text_color(15, 23, 42)
        pdf.multi_cell(0, 6, _latin(f"{idx}. {s.title}"))
        body(s.content)
        if s.metrics:
            body("Métricas: " + "  ·  ".join(f"{m.label}: {m.value}" for m in s.metrics), 8, (14, 116, 144), True)
        for b in s.bullets:
            body(f"• {b}")
    sub("1.2 Conclusiones clave")
    for c in (report.executive_summary.conclusions or ["Sin conclusiones adicionales."]):
        body(f"• {c}")
    sub("1.3 Hallazgos críticos")
    for c in (report.executive_summary.critical_findings or ["Sin hallazgos críticos."]):
        body(f"• {c}", 9, (153, 27, 27))

    pdf.add_page()
    heading("2. Datos y Métricas Extraídas")
    sub("2.1 Indicadores clave (KPIs)")
    _pdf_table(pdf, ["Indicador", "Valor", "Descripción"], [[k.label, k.value, k.description] for k in report.data_report.kpis], [45, 25, 110])
    sub("2.2 Entidades detectadas")
    e = report.data_report.entities
    for label, values in [("Fechas", e.dates), ("Montos", e.money), ("Porcentajes", e.percentages), ("Correos", e.emails), ("URLs", e.urls), ("Palabras clave", e.keywords), ("Alertas", e.alerts)]:
        body(f"{label} ({len(values)}): {', '.join(values) if values else '—'}")
    if report.data_report.table:
        sub("2.3 Detalle de entidades por página")
        _pdf_table(pdf, ["Página", "Tipo", "Valor"], [[str(r.page), r.kind, r.value] for r in report.data_report.table], [18, 34, 128])

    pdf.add_page()
    heading("3. Auditoría y Recomendaciones")
    body(f"Puntaje de calidad documental: {report.audit.score}/100", 11, (14, 116, 144))
    for f in report.audit.findings:
        impact_color = {"alto": (220, 38, 38), "medio": (217, 119, 6), "bajo": (5, 150, 105)}.get(f.impact, (100, 116, 139))
        pdf.set_font("helvetica", "B", 10)
        pdf.set_text_color(15, 23, 42)
        pdf.write(6, _latin(f"{f.title} "))
        pdf.set_text_color(*impact_color)
        pdf.write(6, _latin(f"[Impacto {f.impact.upper()}]"))
        pdf.ln(7)
        body(f.detail)
        body(f"Recomendación: {f.recommendation}", 9, (14, 116, 144))
    if report.audit.strengths:
        sub("Fortalezas identificadas")
        for s in report.audit.strengths:
            body(f"• {s}")

    return bytes(pdf.output())
