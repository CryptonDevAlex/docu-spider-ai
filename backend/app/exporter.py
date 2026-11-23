"""Report exporters: Word (.docx) via python-docx and clean white PDF via fpdf2."""

from __future__ import annotations

import io

from docx import Document
from docx.shared import Pt, RGBColor
from fpdf import FPDF

from .schemas import ScanReport

_CYAN = RGBColor(0x0E, 0x74, 0x90)
_MUTED = RGBColor(0x64, 0x74, 0x8B)


# --------------------------------------------------------------------------- #
# Word (.docx)
# --------------------------------------------------------------------------- #
def _docx_bullets(document: Document, items: list[str]) -> None:
    for item in items:
        document.add_paragraph(str(item), style="List Bullet")


def _docx_table(document: Document, headers: list[str], rows: list[list[str]]) -> None:
    table = document.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"
    header_cells = table.rows[0].cells
    for index, header in enumerate(headers):
        header_cells[index].text = header
        for run in header_cells[index].paragraphs[0].runs:
            run.bold = True
    for row in rows:
        cells = table.add_row().cells
        for index, value in enumerate(row):
            cells[index].text = str(value)


def _format_date(report: ScanReport) -> str:
    return report.generated_at.strftime("%d/%m/%Y %H:%M")


def build_docx(report: ScanReport) -> bytes:
    document = Document()

    title = document.add_heading("Informe DocuSpider AI", level=0)
    title.alignment = 0

    file_paragraph = document.add_paragraph()
    file_run = file_paragraph.add_run(report.file_name)
    file_run.bold = True
    file_run.font.size = Pt(14)

    meta = document.add_paragraph(
        f"Formato: {report.file_type.upper()}  ·  Unidades: {report.total_pages}  ·  "
        f"Motor: {report.provider}  ·  Generado: {_format_date(report)}"
    )
    meta_run = meta.add_run()
    meta_run.font.size = Pt(9)
    meta_run.font.color.rgb = _MUTED
    meta.runs[0].font.size = Pt(9)
    meta.runs[0].font.color.rgb = _MUTED

    score_paragraph = document.add_paragraph()
    score_run = score_paragraph.add_run(
        f"Puntaje de calidad documental: {report.audit.score}/100"
    )
    score_run.bold = True
    score_run.font.size = Pt(11)
    score_run.font.color.rgb = _CYAN

    # 1. Executive summary
    document.add_heading("1. Resumen Ejecutivo", level=1)
    document.add_heading("Visión general y propósito", level=2)
    document.add_paragraph(report.executive_summary.overview)
    if report.executive_summary.purpose:
        document.add_paragraph(report.executive_summary.purpose)

    document.add_heading("Desglose por secciones y páginas", level=2)
    for section in report.executive_summary.sections:
        document.add_heading(section.title, level=3)
        document.add_paragraph(section.content)
        if section.metrics:
            metrics_text = "  ·  ".join(f"{item.label}: {item.value}" for item in section.metrics)
            metrics_paragraph = document.add_paragraph()
            metrics_run = metrics_paragraph.add_run(metrics_text)
            metrics_run.italic = True
            metrics_run.font.size = Pt(9)
            metrics_run.font.color.rgb = _CYAN
        if section.bullets:
            _docx_bullets(document, section.bullets)

    document.add_heading("Conclusiones clave", level=2)
    _docx_bullets(
        document,
        report.executive_summary.conclusions or ["Sin conclusiones adicionales."],
    )

    document.add_heading("Hallazgos críticos", level=2)
    _docx_bullets(
        document,
        report.executive_summary.critical_findings or ["Sin hallazgos críticos."],
    )

    # 2. Data report
    document.add_heading("2. Reporte de Datos y Métricas Extraídas", level=1)
    document.add_heading("Indicadores clave", level=2)
    _docx_table(
        document,
        ["Indicador", "Valor", "Descripción"],
        [[item.label, item.value, item.description] for item in report.data_report.kpis],
    )

    document.add_heading("Entidades detectadas", level=2)
    entities = report.data_report.entities
    for label, values in (
        ("Fechas", entities.dates),
        ("Montos", entities.money),
        ("Porcentajes", entities.percentages),
        ("Correos", entities.emails),
        ("URLs", entities.urls),
        ("Palabras clave", entities.keywords),
        ("Alertas", entities.alerts),
    ):
        document.add_paragraph(f"{label} ({len(values)}): {', '.join(values) if values else '—'}")

    if report.data_report.table:
        document.add_heading("Tabla de entidades", level=2)
        _docx_table(
            document,
            ["Página", "Tipo", "Valor", "Contexto"],
            [
                [str(row.page), row.kind, row.value, row.context[:140]]
                for row in report.data_report.table
            ],
        )

    # 3. Audit
    document.add_heading("3. Auditoría y Sugerencias de Mejora", level=1)
    audit_score = document.add_paragraph()
    audit_run = audit_score.add_run(
        f"Puntaje de calidad documental: {report.audit.score}/100"
    )
    audit_run.bold = True
    audit_run.font.color.rgb = _CYAN

    for finding in report.audit.findings:
        document.add_heading(f"{finding.title} (impacto {finding.impact})", level=3)
        document.add_paragraph(finding.detail)
        recommendation = document.add_paragraph()
        rec_label = recommendation.add_run("Recomendación: ")
        rec_label.bold = True
        recommendation.add_run(finding.recommendation)

    if report.audit.strengths:
        document.add_heading("Fortalezas", level=2)
        _docx_bullets(document, report.audit.strengths)

    buffer = io.BytesIO()
    document.save(buffer)
    return buffer.getvalue()


# --------------------------------------------------------------------------- #
# PDF (clean white editorial layout)
# --------------------------------------------------------------------------- #
def _latin(text: object) -> str:
    return str(text).encode("latin-1", "replace").decode("latin-1")


def _truncate(text: str, max_chars: int) -> str:
    if max_chars <= 1:
        return ""
    return text if len(text) <= max_chars else text[: max_chars - 1] + "…"


class _ReportPDF(FPDF):
    def footer(self) -> None:  # noqa: D401 - fpdf hook
        self.set_y(-12)
        self.set_font("helvetica", "I", 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 8, _latin(f"DocuSpider AI · Página {self.page_no()}/{{nb}}"), align="C")


def _pdf_table(
    pdf: FPDF, headers: list[str], rows: list[list[str]], widths: list[int]
) -> None:
    def draw_header() -> None:
        pdf.set_font("helvetica", "B", 9)
        pdf.set_text_color(255, 255, 255)
        pdf.set_fill_color(14, 116, 144)
        for header, width in zip(headers, widths, strict=False):
            pdf.cell(width, 7, _latin(_truncate(header, int(width * 1.7))), border=1, fill=True)
        pdf.ln()

    draw_header()
    pdf.set_font("helvetica", "", 8)
    pdf.set_text_color(15, 23, 42)
    shaded = False
    for row in rows:
        if pdf.get_y() + 6 > pdf.page_break_trigger:
            pdf.add_page()
            draw_header()
            pdf.set_font("helvetica", "", 8)
            pdf.set_text_color(15, 23, 42)
        pdf.set_fill_color(245, 247, 250) if shaded else pdf.set_fill_color(255, 255, 255)
        for value, width in zip(row, widths, strict=False):
            pdf.cell(width, 6, _latin(_truncate(str(value), int(width * 1.7))), border=1, fill=True)
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

    pdf.set_font("helvetica", "B", 20)
    pdf.set_text_color(*dark)
    pdf.set_x(pdf.l_margin)
    pdf.multi_cell(0, 10, _latin("Informe DocuSpider AI"))
    pdf.set_font("helvetica", "B", 13)
    pdf.set_x(pdf.l_margin)
    pdf.multi_cell(0, 7, _latin(report.file_name))
    pdf.set_font("helvetica", "", 9)
    pdf.set_text_color(*muted)
    pdf.set_x(pdf.l_margin)
    pdf.multi_cell(
        0,
        5,
        _latin(
            f"Formato: {report.file_type.upper()}  ·  Unidades: {report.total_pages}  ·  "
            f"Motor: {report.provider}  ·  Generado: {_format_date(report)}"
        ),
    )
    pdf.ln(2)
    pdf.set_font("helvetica", "B", 11)
    pdf.set_text_color(*cyan)
    pdf.set_x(pdf.l_margin)
    pdf.multi_cell(0, 7, _latin(f"Puntaje de calidad documental: {report.audit.score}/100"))
    pdf.set_draw_color(*cyan)
    pdf.set_line_width(0.4)
    pdf.line(15, pdf.get_y() + 1, 195, pdf.get_y() + 1)
    pdf.ln(5)

    def heading(text: str, size: int = 13, color: tuple[int, int, int] = cyan, before: float = 3) -> None:
        pdf.ln(before)
        pdf.set_font("helvetica", "B", size)
        pdf.set_text_color(*color)
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(0, 7, _latin(text))
        pdf.ln(1)

    def body(text: str, size: int = 10, color: tuple[int, int, int] = dark) -> None:
        pdf.set_font("helvetica", "", size)
        pdf.set_text_color(*color)
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(0, 5, _latin(text))
        pdf.ln(1)

    def bullet(text: str) -> None:
        pdf.set_font("helvetica", "", 10)
        pdf.set_text_color(*dark)
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(0, 5, _latin(f"• {text}"))

    heading("1. Resumen Ejecutivo")
    heading("Visión general y propósito", size=11)
    body(report.executive_summary.overview)
    if report.executive_summary.purpose:
        body(report.executive_summary.purpose)

    heading("Desglose por secciones y páginas", size=11)
    for section in report.executive_summary.sections:
        heading(section.title, size=10, color=dark, before=2)
        body(section.content, size=9)
        if section.metrics:
            metrics_text = "  ·  ".join(f"{item.label}: {item.value}" for item in section.metrics)
            body(metrics_text, size=9, color=cyan)
        for item in section.bullets:
            bullet(item)

    heading("Conclusiones clave", size=11)
    for conclusion in report.executive_summary.conclusions:
        bullet(conclusion)
    heading("Hallazgos críticos", size=11)
    for finding in report.executive_summary.critical_findings:
        bullet(finding)

    heading("2. Reporte de Datos y Métricas Extraídas")
    heading("Indicadores clave", size=11)
    for kpi in report.data_report.kpis:
        body(f"{kpi.label}: {kpi.value} — {kpi.description}", size=9)

    heading("Entidades detectadas", size=11)
    entities = report.data_report.entities
    for label, values in (
        ("Fechas", entities.dates),
        ("Montos", entities.money),
        ("Porcentajes", entities.percentages),
        ("Correos", entities.emails),
        ("URLs", entities.urls),
        ("Palabras clave", entities.keywords),
        ("Alertas", entities.alerts),
    ):
        body(f"{label} ({len(values)}): {', '.join(values) if values else '—'}", size=9)

    if report.data_report.table:
        heading("Tabla de entidades", size=11)
        _pdf_table(
            pdf,
            ["Página", "Tipo", "Valor"],
            [[str(row.page), row.kind, row.value] for row in report.data_report.table],
            [18, 34, 128],
        )

    heading("3. Auditoría y Sugerencias de Mejora")
    body(f"Puntaje de calidad documental: {report.audit.score}/100", size=10, color=cyan)
    for finding in report.audit.findings:
        heading(f"{finding.title} (impacto {finding.impact})", size=10, color=dark, before=2)
        body(finding.detail, size=9)
        body(f"Recomendación: {finding.recommendation}", size=9, color=cyan)

    if report.audit.strengths:
        heading("Fortalezas", size=11)
        for strength in report.audit.strengths:
            bullet(strength)

    return bytes(pdf.output())
