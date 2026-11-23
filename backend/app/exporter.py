"""Report exporters: Word (.docx) via python-docx and clean white PDF via fpdf2."""

from __future__ import annotations

import io

from docx import Document
from docx.shared import Inches, Pt, RGBColor
from fpdf import FPDF

from .schemas import ScanReport

_CYAN = RGBColor(0x0E, 0x74, 0x90)
_MUTED = RGBColor(0x64, 0x74, 0x8B)
_DARK = RGBColor(0x0F, 0x17, 0x2A)


def _format_date(report: ScanReport) -> str:
    return report.generated_at.strftime("%d/%m/%Y %H:%M")


def _docx_table(document: Document, headers: list[str], rows: list[list[str]]) -> None:
    table = document.add_table(rows=1, cols=len(headers))
    table.style = "Light List Accent 1"
    for i, h in enumerate(headers):
        cell = table.rows[0].cells[i]
        cell.text = h
        for p in cell.paragraphs:
            for r in p.runs:
                r.bold = True
                r.font.size = Pt(9)
    for row in rows:
        cells = table.add_row().cells
        for i, value in enumerate(row):
            cells[i].text = str(value)
            for p in cells[i].paragraphs:
                for r in p.runs:
                    r.font.size = Pt(9)


def build_docx(report: ScanReport) -> bytes:
    document = Document()
    section = document.sections[0]
    section.left_margin = Inches(0.8)
    section.right_margin = Inches(0.8)

    p = document.add_paragraph()
    r = p.add_run("INFORME DOCUSPIDER AI")
    r.bold = True
    r.font.size = Pt(24)
    r.font.color.rgb = _CYAN

    p = document.add_paragraph()
    r = p.add_run(report.file_name)
    r.bold = True
    r.font.size = Pt(14)
    r.font.color.rgb = _DARK

    p = document.add_paragraph()
    p.add_run(f"Formato: {report.file_type.upper()}  ·  Unidades: {report.total_pages}  ·  Motor: {report.provider}  ·  Generado: {_format_date(report)}").font.size = Pt(9)
    p.runs[0].font.color.rgb = _MUTED

    p = document.add_paragraph()
    r = p.add_run(f"Puntaje de calidad documental: {report.audit.score}/100")
    r.bold = True
    r.font.size = Pt(12)
    r.font.color.rgb = _CYAN

    document.add_page_break()
    document.add_heading("1. Resumen Ejecutivo", level=1)
    document.add_paragraph(report.executive_summary.overview)
    if report.executive_summary.purpose:
        document.add_paragraph(report.executive_summary.purpose)

    document.add_heading("Desglose por secciones y páginas", level=2)
    for idx, sec in enumerate(report.executive_summary.sections, start=1):
        document.add_heading(f"{idx}. {sec.title}", level=3)
        document.add_paragraph(sec.content)
        if sec.metrics:
            p = document.add_paragraph()
            r = p.add_run("  ·  ".join(f"{m.label}: {m.value}" for m in sec.metrics))
            r.italic = True
            r.font.size = Pt(9)
            r.font.color.rgb = _CYAN
        for b in sec.bullets:
            document.add_paragraph(str(b), style="List Bullet")

    document.add_heading("Conclusiones clave", level=2)
    for c in (report.executive_summary.conclusions or ["Sin conclusiones adicionales."]):
        document.add_paragraph(c, style="List Bullet")
    document.add_heading("Hallazgos críticos", level=2)
    for c in (report.executive_summary.critical_findings or ["Sin hallazgos críticos."]):
        document.add_paragraph(c, style="List Bullet")

    document.add_page_break()
    document.add_heading("2. Reporte de Datos y Métricas Extraídas", level=1)
    document.add_heading("Indicadores clave", level=2)
    _docx_table(document, ["Indicador", "Valor", "Descripción"], [[k.label, k.value, k.description] for k in report.data_report.kpis])
    document.add_heading("Entidades detectadas", level=2)
    e = report.data_report.entities
    for label, values in (("Fechas", e.dates), ("Montos", e.money), ("Porcentajes", e.percentages), ("Correos", e.emails), ("URLs", e.urls), ("Palabras clave", e.keywords), ("Alertas", e.alerts)):
        document.add_paragraph(f"{label} ({len(values)}): {', '.join(values) if values else '—'}")
    if report.data_report.table:
        document.add_heading("Tabla de entidades", level=2)
        _docx_table(document, ["Página", "Tipo", "Valor", "Contexto"], [[str(r.page), r.kind, r.value, r.context[:140]] for r in report.data_report.table])

    document.add_page_break()
    document.add_heading("3. Auditoría y Sugerencias de Mejora", level=1)
    p = document.add_paragraph()
    r = p.add_run(f"Puntaje: {report.audit.score}/100")
    r.bold = True
    r.font.color.rgb = _CYAN
    for f in report.audit.findings:
        document.add_heading(f"{f.title} (impacto {f.impact})", level=3)
        document.add_paragraph(f.detail)
        rec = document.add_paragraph()
        rec.add_run("Recomendación: ").bold = True
        rec.add_run(f.recommendation)
    if report.audit.strengths:
        document.add_heading("Fortalezas", level=2)
        for s in report.audit.strengths:
            document.add_paragraph(s, style="List Bullet")

    buffer = io.BytesIO()
    document.save(buffer)
    return buffer.getvalue()


def _latin(text: object) -> str:
    return str(text).encode("latin-1", "replace").decode("latin-1")


def _truncate(text: str, max_chars: int) -> str:
    if max_chars <= 1:
        return ""
    return text if len(text) <= max_chars else text[: max_chars - 1] + "…"


class _ReportPDF(FPDF):
    def footer(self) -> None:
        self.set_y(-12)
        self.set_font("helvetica", "I", 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 8, _latin(f"DocuSpider AI · Página {self.page_no()}/{{nb}}"), align="C")


def _pdf_table(pdf: FPDF, headers: list[str], rows: list[list[str]], widths: list[int]) -> None:
    def draw_header() -> None:
        pdf.set_font("helvetica", "B", 9)
        pdf.set_fill_color(14, 116, 144)
        pdf.set_text_color(255, 255, 255)
        for h, w in zip(headers, widths, strict=False):
            pdf.cell(w, 7, _latin(_truncate(h, int(w * 1.7))), border=1, fill=True)
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
        pdf.set_fill_color(245, 247, 250) if shaded else pdf.set_fill_color(255, 255, 255)
        for value, w in zip(row, widths, strict=False):
            pdf.cell(w, 6, _latin(_truncate(str(value), int(w * 1.7))), border=1, fill=True)
        pdf.ln()
        shaded = not shaded
    pdf.ln(2)


def build_pdf(report: ScanReport) -> bytes:
    pdf = _ReportPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.alias_nb_pages()
    pdf.add_page()
    dark = (15, 23, 42)
    cyan = (14, 116, 144)
    muted = (100, 116, 139)

    pdf.set_font("helvetica", "B", 22)
    pdf.set_text_color(*cyan)
    pdf.multi_cell(0, 10, _latin("INFORME DOCUSPIDER AI"))
    pdf.set_font("helvetica", "B", 14)
    pdf.set_text_color(*dark)
    pdf.multi_cell(0, 8, _latin(report.file_name))
    pdf.set_font("helvetica", "", 10)
    pdf.set_text_color(*muted)
    pdf.multi_cell(0, 6, _latin(f"Formato: {report.file_type.upper()}  ·  Unidades: {report.total_pages}  ·  Motor: {report.provider}  ·  Generado: {_format_date(report)}"))
    pdf.ln(3)
    pdf.set_font("helvetica", "B", 12)
    pdf.set_text_color(*cyan)
    pdf.multi_cell(0, 8, _latin(f"Puntaje de calidad documental: {report.audit.score}/100"))

    def heading(text: str, size: int = 13, color=cyan, before: float = 2) -> None:
        pdf.ln(before)
        pdf.set_font("helvetica", "B", size)
        pdf.set_text_color(*color)
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(0, 7, _latin(text))
        pdf.ln(1)

    def body(text: str, size: int = 10, color=dark) -> None:
        pdf.set_font("helvetica", "", size)
        pdf.set_text_color(*color)
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(0, 5.5, _latin(text))
        pdf.ln(1)

    pdf.add_page()
    heading("1. Resumen Ejecutivo")
    body(report.executive_summary.overview)
    if report.executive_summary.purpose:
        body(report.executive_summary.purpose)
    heading("Desglose por secciones y páginas", size=11)
    for idx, sec in enumerate(report.executive_summary.sections, start=1):
        heading(f"{idx}. {sec.title}", size=10, color=dark, before=1)
        body(sec.content, size=9)
        if sec.metrics:
            body("  ·  ".join(f"{m.label}: {m.value}" for m in sec.metrics), size=9, color=cyan)
        for b in sec.bullets:
            body(f"• {b}", size=9)
    heading("Conclusiones clave", size=11)
    for c in report.executive_summary.conclusions:
        body(f"• {c}", size=9)
    heading("Hallazgos críticos", size=11)
    for c in report.executive_summary.critical_findings:
        body(f"• {c}", size=9)

    pdf.add_page()
    heading("2. Reporte de Datos y Métricas Extraídas")
    heading("Indicadores clave", size=11)
    _pdf_table(pdf, ["Indicador", "Valor", "Descripción"], [[k.label, k.value, k.description] for k in report.data_report.kpis], [45, 25, 110])
    heading("Entidades detectadas", size=11)
    e = report.data_report.entities
    for label, values in (("Fechas", e.dates), ("Montos", e.money), ("Porcentajes", e.percentages), ("Correos", e.emails), ("URLs", e.urls), ("Palabras clave", e.keywords), ("Alertas", e.alerts)):
        body(f"{label} ({len(values)}): {', '.join(values) if values else '—'}", size=9)
    if report.data_report.table:
        heading("Tabla de entidades", size=11)
        _pdf_table(pdf, ["Página", "Tipo", "Valor"], [[str(r.page), r.kind, r.value] for r in report.data_report.table], [18, 34, 128])

    pdf.add_page()
    heading("3. Auditoría y Sugerencias de Mejora")
    body(f"Puntaje: {report.audit.score}/100", size=10, color=cyan)
    for f in report.audit.findings:
        heading(f"{f.title} (impacto {f.impact})", size=10, color=dark, before=1)
        body(f.detail, size=9)
        body(f"Recomendación: {f.recommendation}", size=9, color=cyan)
    if report.audit.strengths:
        heading("Fortalezas", size=11)
        for s in report.audit.strengths:
            body(f"• {s}", size=9)

    return bytes(pdf.output())
