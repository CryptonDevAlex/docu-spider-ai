"""Professional report exporters: Word (.docx) and PDF."""

from __future__ import annotations

import io

from docx import Document
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Inches, Pt, RGBColor
from fpdf import FPDF

from .schemas import ScanReport

_CYAN = RGBColor(0x0E, 0x74, 0x90)
_DARK = RGBColor(0x0F, 0x17, 0x2A)
_MUTED = RGBColor(0x64, 0x74, 0x8B)
_LIGHT = RGBColor(0xF1, 0xF5, 0xF9)


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
    table.autofit = True
    hdr = table.rows[0].cells
    for i, h in enumerate(headers):
        hdr[i].text = str(h)
        _set_cell_shading(hdr[i], "0E7490")
        for p in hdr[i].paragraphs:
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(2)
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
                p.paragraph_format.space_before = Pt(2)
                p.paragraph_format.space_after = Pt(2)
                for r in p.runs:
                    r.font.size = Pt(9)
                    r.font.color.rgb = _DARK
    document.add_paragraph()


def _docx_kv(document: Document, label: str, value: str) -> None:
    p = document.add_paragraph()
    p.paragraph_format.space_after = Pt(2)
    run = p.add_run(f"{label}: ")
    run.bold = True
    run.font.size = Pt(10)
    run.font.color.rgb = _DARK
    run2 = p.add_run(value)
    run2.font.size = Pt(10)
    run2.font.color.rgb = RGBColor(0x33, 0x41, 0x55)


def _docx_section_title(document: Document, text: str) -> None:
    p = document.add_paragraph()
    p.paragraph_format.space_before = Pt(14)
    p.paragraph_format.space_after = Pt(6)
    run = p.add_run(text)
    run.bold = True
    run.font.size = Pt(16)
    run.font.color.rgb = _CYAN


def _docx_subtitle(document: Document, text: str) -> None:
    p = document.add_paragraph()
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after = Pt(4)
    run = p.add_run(text)
    run.bold = True
    run.font.size = Pt(12)
    run.font.color.rgb = _DARK


def _docx_body(document: Document, text: str, size: int = 10, color: RGBColor = RGBColor(0x33, 0x41, 0x55), italic: bool = False) -> None:
    p = document.add_paragraph()
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.line_spacing = 1.35
    run = p.add_run(text)
    run.font.size = Pt(size)
    run.font.color.rgb = color
    run.italic = italic


def build_docx(report: ScanReport) -> bytes:
    document = Document()
    sec = document.sections[0]
    sec.left_margin = Cm(2.0)
    sec.right_margin = Cm(2.0)
    sec.top_margin = Cm(2.0)
    sec.bottom_margin = Cm(2.0)

    # Cover
    for _ in range(2):
        document.add_paragraph()
    p = document.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    run = p.add_run("INFORME DE ANÁLISIS DOCUMENTAL")
    run.bold = True
    run.font.size = Pt(11)
    run.font.color.rgb = _CYAN

    p = document.add_paragraph()
    p.paragraph_format.space_after = Pt(4)
    run = p.add_run("DocuSpider AI")
    run.bold = True
    run.font.size = Pt(34)
    run.font.color.rgb = _DARK

    p = document.add_paragraph()
    p.paragraph_format.space_after = Pt(18)
    run = p.add_run(report.file_name)
    run.bold = True
    run.font.size = Pt(18)
    run.font.color.rgb = RGBColor(0x33, 0x41, 0x55)

    _docx_kv(document, "Formato", report.file_type.upper())
    _docx_kv(document, "Unidades analizadas", str(report.total_pages))
    _docx_kv(document, "Motor de análisis", report.provider)
    _docx_kv(document, "Fecha de generación", _fmt_date(report))
    _docx_kv(document, "Puntaje de calidad", f"{report.audit.score}/100")

    document.add_paragraph()
    p = document.add_paragraph()
    p.paragraph_format.space_before = Pt(12)
    run = p.add_run("Documento generado automáticamente por DocuSpider AI. El contenido de este informe se basa en análisis heurístico y/o enriquecimiento por IA, manteniendo la salida en español.")
    run.font.size = Pt(9)
    run.font.color.rgb = _MUTED
    run.italic = True

    document.add_page_break()

    # 1. Executive summary
    _docx_section_title(document, "1. Resumen Ejecutivo")
    _docx_subtitle(document, "Visión general")
    _docx_body(document, report.executive_summary.overview)
    if report.executive_summary.purpose:
        _docx_subtitle(document, "Propósito del documento")
        _docx_body(document, report.executive_summary.purpose)

    _docx_subtitle(document, "Desglose estructurado por sección / página")
    for idx, sec in enumerate(report.executive_summary.sections, start=1):
        p = document.add_paragraph()
        p.paragraph_format.space_before = Pt(8)
        p.paragraph_format.space_after = Pt(2)
        run = p.add_run(f"{idx}. {sec.title}")
        run.bold = True
        run.font.size = Pt(11)
        run.font.color.rgb = _DARK
        _docx_body(document, sec.content, size=10)
        if sec.metrics:
            _docx_body(document, "  ·  ".join(f"{m.label}: {m.value}" for m in sec.metrics), size=9, color=_CYAN, italic=True)
        for b in sec.bullets:
            bp = document.add_paragraph(str(b), style="List Bullet")
            bp.paragraph_format.space_after = Pt(1)
            for r in bp.runs:
                r.font.size = Pt(10)

    _docx_subtitle(document, "Conclusiones clave")
    for c in (report.executive_summary.conclusions or ["Sin conclusiones adicionales."]):
        bp = document.add_paragraph(c, style="List Bullet")
        for r in bp.runs:
            r.font.size = Pt(10)

    _docx_subtitle(document, "Hallazgos críticos")
    for c in (report.executive_summary.critical_findings or ["Sin hallazgos críticos."]):
        bp = document.add_paragraph(c, style="List Bullet")
        for r in bp.runs:
            r.font.size = Pt(10)
            r.font.color.rgb = RGBColor(0x99, 0x1B, 0x1B)

    document.add_page_break()

    # 2. Data
    _docx_section_title(document, "2. Datos y Métricas Extraídas")
    _docx_subtitle(document, "Indicadores clave (KPIs)")
    _docx_table(document, ["Indicador", "Valor", "Descripción"], [[k.label, k.value, k.description] for k in report.data_report.kpis])

    _docx_subtitle(document, "Entidades detectadas")
    e = report.data_report.entities
    for label, values in [
        ("Fechas", e.dates),
        ("Montos", e.money),
        ("Porcentajes", e.percentages),
        ("Correos", e.emails),
        ("URLs", e.urls),
        ("Palabras clave", e.keywords),
        ("Alertas", e.alerts),
    ]:
        _docx_body(document, f"{label} ({len(values)}): {', '.join(values) if values else '—'}", size=10)

    if report.data_report.table:
        _docx_subtitle(document, "Detalle de entidades por página")
        rows = [[str(r.page), r.kind, r.value, r.context[:120]] for r in report.data_report.table]
        _docx_table(document, ["Página", "Tipo", "Valor", "Contexto"], rows)

    document.add_page_break()

    # 3. Audit
    _docx_section_title(document, "3. Auditoría y Sugerencias de Mejora")
    _docx_body(document, f"Puntaje de calidad documental: {report.audit.score}/100", size=12, color=_CYAN)

    for f in report.audit.findings:
        impact_color = {"alto": RGBColor(0xDC, 0x26, 0x26), "medio": RGBColor(0xD9, 0x77, 0x06), "bajo": RGBColor(0x05, 0x96, 0x69)}.get(f.impact, _MUTED)
        p = document.add_paragraph()
        p.paragraph_format.space_before = Pt(8)
        p.paragraph_format.space_after = Pt(2)
        run = p.add_run(f"{f.title} ")
        run.bold = True
        run.font.size = Pt(11)
        run.font.color.rgb = _DARK
        run2 = p.add_run(f"[Impacto {f.impact.upper()}]")
        run2.bold = True
        run2.font.size = Pt(9)
        run2.font.color.rgb = impact_color
        _docx_body(document, f.detail, size=10)
        rec = document.add_paragraph()
        rec.paragraph_format.space_after = Pt(6)
        rr = rec.add_run("Recomendación: ")
        rr.bold = True
        rr.font.size = Pt(10)
        rr.font.color.rgb = _CYAN
        rr2 = rec.add_run(f.recommendation)
        rr2.font.size = Pt(10)
        rr2.font.color.rgb = RGBColor(0x33, 0x41, 0x55)

    if report.audit.strengths:
        _docx_subtitle(document, "Fortalezas identificadas")
        for s in report.audit.strengths:
            bp = document.add_paragraph(s, style="List Bullet")
            for r in bp.runs:
                r.font.size = Pt(10)

    buf = io.BytesIO()
    document.save(buf)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# PDF
# ---------------------------------------------------------------------------
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
        self.cell(0, 8, _latin("DocuSpider AI — Informe de análisis documental"), align="L")
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

    # Cover
    pdf.add_page()
    pdf.set_fill_color(14, 116, 144)
    pdf.rect(0, 0, 210, 45, "F")
    pdf.set_y(14)
    pdf.set_font("helvetica", "B", 11)
    pdf.set_text_color(220, 240, 245)
    pdf.cell(0, 6, _latin("INFORME DE ANÁLISIS DOCUMENTAL"), ln=True)
    pdf.set_font("helvetica", "B", 28)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 12, _latin("DocuSpider AI"), ln=True)

    pdf.set_y(58)
    pdf.set_font("helvetica", "B", 20)
    pdf.set_text_color(15, 23, 42)
    pdf.multi_cell(0, 9, _latin(report.file_name))
    pdf.ln(4)
    pdf.set_draw_color(14, 116, 144)
    pdf.set_line_width(0.6)
    pdf.line(15, pdf.get_y(), 195, pdf.get_y())
    pdf.ln(8)

    def cover_kv(label: str, value: str) -> None:
        pdf.set_font("helvetica", "B", 10)
        pdf.set_text_color(100, 116, 139)
        pdf.cell(55, 7, _latin(label), border=0)
        pdf.set_font("helvetica", "", 10)
        pdf.set_text_color(15, 23, 42)
        pdf.cell(0, 7, _latin(value), border=0, ln=True)

    cover_kv("Formato", report.file_type.upper())
    cover_kv("Unidades analizadas", str(report.total_pages))
    cover_kv("Motor de análisis", report.provider)
    cover_kv("Fecha de generación", _fmt_date(report))
    cover_kv("Puntaje de calidad", f"{report.audit.score}/100")

    pdf.ln(10)
    pdf.set_fill_color(248, 250, 252)
    pdf.set_draw_color(226, 232, 240)
    y = pdf.get_y()
    pdf.rect(15, y, 180, 22, "DF")
    pdf.set_xy(20, y + 4)
    pdf.set_font("helvetica", "I", 9)
    pdf.set_text_color(71, 85, 105)
    pdf.multi_cell(170, 5, _latin("Este informe fue generado automáticamente por DocuSpider AI. Incluye resumen ejecutivo, datos extraídos, auditoría y recomendaciones estructuradas en orden por sección y página."))

    def heading(text: str, size: int = 14, color=(14, 116, 144), before: float = 2) -> None:
        pdf.ln(before)
        pdf.set_font("helvetica", "B", size)
        pdf.set_text_color(*color)
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(0, 7, _latin(text))
        y2 = pdf.get_y()
        pdf.set_draw_color(203, 213, 225)
        pdf.set_line_width(0.2)
        pdf.line(pdf.l_margin, y2, 195, y2)
        pdf.ln(2)

    def sub(text: str) -> None:
        pdf.ln(1)
        pdf.set_font("helvetica", "B", 11)
        pdf.set_text_color(15, 23, 42)
        pdf.multi_cell(0, 6, _latin(text))
        pdf.ln(1)

    def body(text: str, size: int = 10, color=(51, 65, 85), italic: bool = False) -> None:
        pdf.set_font("helvetica", "I" if italic else "", size)
        pdf.set_text_color(*color)
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(0, 5.6, _latin(text))
        pdf.ln(1)

    # 1. Summary
    pdf.add_page()
    heading("1. Resumen Ejecutivo")
    sub("Visión general")
    body(report.executive_summary.overview)
    if report.executive_summary.purpose:
        sub("Propósito del documento")
        body(report.executive_summary.purpose)

    sub("Desglose estructurado por sección / página")
    for idx, s in enumerate(report.executive_summary.sections, start=1):
        pdf.set_font("helvetica", "B", 10)
        pdf.set_text_color(15, 23, 42)
        pdf.multi_cell(0, 6, _latin(f"{idx}. {s.title}"))
        body(s.content, size=9)
        if s.metrics:
            body("  ·  ".join(f"{m.label}: {m.value}" for m in s.metrics), size=9, color=(14, 116, 144), italic=True)
        for b in s.bullets:
            body(f"• {b}", size=9)

    sub("Conclusiones clave")
    for c in (report.executive_summary.conclusions or ["Sin conclusiones adicionales."]):
        body(f"• {c}", size=9)
    sub("Hallazgos críticos")
    for c in (report.executive_summary.critical_findings or ["Sin hallazgos críticos."]):
        body(f"• {c}", size=9, color=(153, 27, 27))

    # 2. Data
    pdf.add_page()
    heading("2. Datos y Métricas Extraídas")
    sub("Indicadores clave (KPIs)")
    _pdf_table(pdf, ["Indicador", "Valor", "Descripción"], [[k.label, k.value, k.description] for k in report.data_report.kpis], [45, 25, 110])
    sub("Entidades detectadas")
    e = report.data_report.entities
    for label, values in [
        ("Fechas", e.dates),
        ("Montos", e.money),
        ("Porcentajes", e.percentages),
        ("Correos", e.emails),
        ("URLs", e.urls),
        ("Palabras clave", e.keywords),
        ("Alertas", e.alerts),
    ]:
        body(f"{label} ({len(values)}): {', '.join(values) if values else '—'}", size=9)
    if report.data_report.table:
        sub("Detalle de entidades por página")
        _pdf_table(pdf, ["Página", "Tipo", "Valor"], [[str(r.page), r.kind, r.value] for r in report.data_report.table], [18, 34, 128])

    # 3. Audit
    pdf.add_page()
    heading("3. Auditoría y Sugerencias de Mejora")
    body(f"Puntaje de calidad documental: {report.audit.score}/100", size=11, color=(14, 116, 144))
    for f in report.audit.findings:
        impact_color = {"alto": (220, 38, 38), "medio": (217, 119, 6), "bajo": (5, 150, 105)}.get(f.impact, (100, 116, 139))
        pdf.set_font("helvetica", "B", 10)
        pdf.set_text_color(15, 23, 42)
        pdf.write(6, _latin(f"{f.title} "))
        pdf.set_text_color(*impact_color)
        pdf.write(6, _latin(f"[Impacto {f.impact.upper()}]"))
        pdf.ln(7)
        body(f.detail, size=9)
        body(f"Recomendación: {f.recommendation}", size=9, color=(14, 116, 144))
    if report.audit.strengths:
        sub("Fortalezas identificadas")
        for s in report.audit.strengths:
            body(f"• {s}", size=9)

    return bytes(pdf.output())
