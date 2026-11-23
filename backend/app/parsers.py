"""Universal multi-format document parsers.

Each parser converts a file into a list of :class:`DocumentPage` units so the
spider engine can crawl the document page by page. Every page also carries an
ordered list of renderable blocks (headings, paragraphs, tables) so the frontend
can display the real document faithfully.
"""

from __future__ import annotations

import csv
import io
import re
from pathlib import Path

from .schemas import DocBlock, DocumentPage, ParsedDocument

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".xlsx"}

_TXT_CHUNK_SIZE = 2000
_CSV_ROWS_PER_PAGE = 60
_DOCX_PAGE_CHARS = 1800

_HEADING_PREFIXES = (
    "contrato",
    "sección",
    "seccion",
    "anexo",
    "capítulo",
    "capitulo",
    "artículo",
    "articulo",
    "disposiciones",
    "informe",
    "propuesta",
    "resumen",
    "introducción",
    "introduccion",
)


class UnsupportedDocumentError(ValueError):
    """Raised when the uploaded file type is not supported."""


def _decode(raw: bytes) -> str:
    for encoding in ("utf-8", "utf-16", "latin-1"):
        try:
            return raw.decode(encoding)
        except (UnicodeDecodeError, LookupError):
            continue
    return raw.decode("utf-8", errors="ignore")


def _chunk_text(text: str, size: int = _TXT_CHUNK_SIZE) -> list[str]:
    text = text.strip()
    if not text:
        return [""]
    chunks: list[str] = []
    for start in range(0, len(text), size):
        chunk = text[start : start + size].strip()
        if chunk:
            chunks.append(chunk)
    return chunks or [""]


def _split_paragraphs(text: str) -> list[str]:
    text = text.strip()
    if not text:
        return []
    parts = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
    if len(parts) <= 1:
        parts = [part.strip() for part in text.split("\n") if part.strip()]

    expanded: list[str] = []
    for part in parts:
        lines = [line.strip() for line in part.split("\n") if line.strip()]
        if len(lines) > 1 and _looks_like_heading(lines[0]):
            expanded.append(lines[0])
            expanded.append("\n".join(lines[1:]))
        else:
            expanded.append(part)
    return expanded or [text]


def _looks_like_heading(text: str) -> bool:
    if not text or len(text) > 100:
        return False
    letters = [char for char in text if char.isalpha()]
    if not letters:
        return False
    uppercase_ratio = sum(1 for char in letters if char.isupper()) / len(letters)
    lowered = text.lower()
    return (
        uppercase_ratio > 0.6
        or any(lowered.startswith(prefix) for prefix in _HEADING_PREFIXES)
        or bool(re.match(r"^(secci[oó]n|anexo|cap[ií]tulo|art[ií]culo)\b", lowered))
    )


def _structure_from_text(text: str) -> tuple[str, list[str], list[DocBlock]]:
    paragraphs = _split_paragraphs(text)
    title = ""
    if paragraphs and _looks_like_heading(paragraphs[0]):
        title = paragraphs[0]

    blocks: list[DocBlock] = []
    start = 0
    if title:
        blocks.append(DocBlock(type="heading", text=title))
        start = 1
    for paragraph in paragraphs[start:]:
        blocks.append(DocBlock(type="paragraph", text=paragraph))
    return title, paragraphs, blocks


def build_text_page(page_number: int, label: str, text: str) -> DocumentPage:
    """Build a page with heading/paragraph blocks derived from raw text."""
    title, paragraphs, blocks = _structure_from_text(text)
    return DocumentPage(
        page_number=page_number,
        label=label,
        text=text,
        title=title,
        paragraphs=paragraphs,
        tables=[],
        blocks=blocks,
    )


def _iter_docx_blocks(document):  # noqa: ANN001 - python-docx Document
    from docx.oxml.ns import qn
    from docx.table import Table
    from docx.text.paragraph import Paragraph

    body = document.element.body
    for child in body.iterchildren():
        if child.tag == qn("w:p"):
            yield Paragraph(child, document)
        elif child.tag == qn("w:tbl"):
            yield Table(child, document)


def _parse_pdf(raw: bytes) -> list[DocumentPage]:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(raw))
    pages: list[DocumentPage] = []
    for index, page in enumerate(reader.pages, start=1):
        try:
            text = page.extract_text() or ""
        except Exception:  # noqa: BLE001 - keep crawling even on broken pages
            text = ""
        pages.append(build_text_page(index, f"Página {index}", text.strip()))
    return pages or [build_text_page(1, "Página 1", "")]


def _parse_docx(raw: bytes) -> list[DocumentPage]:
    import docx
    from docx.table import Table
    from docx.text.paragraph import Paragraph

    document = docx.Document(io.BytesIO(raw))
    pages: list[DocumentPage] = []
    blocks: list[DocBlock] = []
    paragraphs: list[str] = []
    tables: list[list[list[str]]] = []
    title = ""
    buffer = 0
    page_number = 1

    def flush() -> None:
        nonlocal blocks, paragraphs, tables, title, buffer, page_number
        if not blocks:
            return
        text = "\n\n".join(
            block.text for block in blocks if block.type in ("paragraph", "heading") and block.text
        )
        pages.append(
            DocumentPage(
                page_number=page_number,
                label=f"Página {page_number}",
                text=text,
                title=title,
                paragraphs=list(paragraphs),
                tables=list(tables),
                blocks=list(blocks),
            )
        )
        page_number += 1
        blocks, paragraphs, tables, title, buffer = [], [], [], "", 0

    for item in _iter_docx_blocks(document):
        if isinstance(item, Paragraph):
            content = item.text.strip()
            if not content:
                continue
            style_name = (item.style.name or "").lower() if item.style else ""
            if "heading" in style_name or "título" in style_name or "titulo" in style_name:
                if not title:
                    title = content
                blocks.append(DocBlock(type="heading", text=content))
            else:
                blocks.append(DocBlock(type="paragraph", text=content))
                paragraphs.append(content)
            buffer += len(content)
        elif isinstance(item, Table):
            rows = [
                [cell.text.strip() for cell in row.cells]
                for row in item.rows
            ]
            rows = [row for row in rows if any(cell for cell in row)]
            if rows:
                blocks.append(DocBlock(type="table", rows=rows))
                tables.append(rows)
                buffer += 30 * len(rows)
        if buffer >= _DOCX_PAGE_CHARS:
            flush()

    flush()
    return pages or [build_text_page(1, "Página 1", "")]


def _parse_xlsx(raw: bytes) -> list[DocumentPage]:
    import openpyxl

    workbook = openpyxl.load_workbook(io.BytesIO(raw), read_only=True, data_only=True)
    pages: list[DocumentPage] = []
    for index, sheet in enumerate(workbook.worksheets, start=1):
        rows: list[list[str]] = []
        for row in sheet.iter_rows(values_only=True):
            cells = [str(cell).strip() for cell in row if cell is not None and str(cell).strip()]
            if cells:
                rows.append(cells)
        label = f"Hoja: {sheet.title}"
        text = "\n".join(" | ".join(row) for row in rows)
        blocks = [DocBlock(type="heading", text=label)]
        if rows:
            blocks.append(DocBlock(type="table", rows=rows))
        pages.append(
            DocumentPage(
                page_number=index,
                label=label,
                text=text,
                title=label,
                paragraphs=[],
                tables=[rows] if rows else [],
                blocks=blocks,
            )
        )
    workbook.close()
    return pages or [build_text_page(1, "Hoja 1", "")]


def _parse_csv(raw: bytes) -> list[DocumentPage]:
    text = _decode(raw)
    reader = csv.reader(io.StringIO(text))
    rows = [row for row in reader if any(cell.strip() for cell in row)]
    if not rows:
        return [build_text_page(1, "Filas 1", "")]

    pages: list[DocumentPage] = []
    page_number = 1
    for start in range(0, len(rows), _CSV_ROWS_PER_PAGE):
        block = rows[start : start + _CSV_ROWS_PER_PAGE]
        cells = [[cell.strip() for cell in row] for row in block]
        label = f"Filas {start + 1}-{start + len(block)}"
        page_text = "\n".join(" | ".join(row) for row in cells)
        blocks = [
            DocBlock(type="heading", text=label),
            DocBlock(type="table", rows=cells),
        ]
        pages.append(
            DocumentPage(
                page_number=page_number,
                label=label,
                text=page_text,
                title=label,
                paragraphs=[],
                tables=[cells],
                blocks=blocks,
            )
        )
        page_number += 1
    return pages


def _parse_txt(raw: bytes) -> list[DocumentPage]:
    text = _decode(raw)
    chunks = _chunk_text(text)
    return [
        build_text_page(index, f"Página {index}", chunk)
        for index, chunk in enumerate(chunks, start=1)
    ]


_PARSERS = {
    ".pdf": _parse_pdf,
    ".docx": _parse_docx,
    ".xlsx": _parse_xlsx,
}


def parse_document(file_name: str, raw: bytes) -> ParsedDocument:
    """Parse any supported document into crawlable, renderable pages."""
    extension = Path(file_name).suffix.lower()
    parser = _PARSERS.get(extension)
    if parser is None:
        supported = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        raise UnsupportedDocumentError(
            f"Formato no soportado '{extension or file_name}'. Use: {supported}."
        )

    pages = parser(raw)
    if not pages:
        pages = [build_text_page(1, "Página 1", "")]

    return ParsedDocument(
        file_name=file_name,
        file_type=extension.lstrip("."),
        total_pages=len(pages),
        pages=pages,
        size_bytes=len(raw),
    )


def guess_file_type(file_name: str) -> str:
    extension = Path(file_name).suffix.lower()
    if extension in SUPPORTED_EXTENSIONS:
        return extension.lstrip(".")
    return re.sub(r"[^a-z0-9]+", "", file_name.lower()) or "unknown"
