"""Universal multi-format document parsers.

Each parser converts a file into a list of :class:`DocumentPage` units so the
spider engine can crawl the document page by page (PDF pages, Excel sheets,
CSV/rows chunks, DOCX/TXT chunks).
"""

from __future__ import annotations

import csv
import io
import re
from pathlib import Path

from .schemas import DocumentPage, ParsedDocument

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".xlsx", ".csv", ".txt"}

_TXT_CHUNK_SIZE = 2000
_CSV_ROWS_PER_PAGE = 60


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


def _parse_pdf(raw: bytes) -> list[DocumentPage]:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(raw))
    pages: list[DocumentPage] = []
    for index, page in enumerate(reader.pages, start=1):
        try:
            text = page.extract_text() or ""
        except Exception:  # noqa: BLE001 - keep crawling even on broken pages
            text = ""
        pages.append(
            DocumentPage(page_number=index, label=f"Página {index}", text=text.strip())
        )
    return pages or [DocumentPage(page_number=1, label="Página 1", text="")]


def _parse_docx(raw: bytes) -> list[DocumentPage]:
    import docx

    document = docx.Document(io.BytesIO(raw))
    blocks: list[str] = [paragraph.text for paragraph in document.paragraphs]
    for table in document.tables:
        for row in table.rows:
            cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
            if cells:
                blocks.append(" | ".join(cells))
    full_text = "\n".join(block for block in blocks if block.strip())
    chunks = _chunk_text(full_text)
    return [
        DocumentPage(page_number=i, label=f"Bloque {i}", text=chunk)
        for i, chunk in enumerate(chunks, start=1)
    ]


def _parse_xlsx(raw: bytes) -> list[DocumentPage]:
    import openpyxl

    workbook = openpyxl.load_workbook(io.BytesIO(raw), read_only=True, data_only=True)
    pages: list[DocumentPage] = []
    for index, sheet in enumerate(workbook.worksheets, start=1):
        lines: list[str] = []
        for row in sheet.iter_rows(values_only=True):
            cells = [str(cell).strip() for cell in row if cell is not None and str(cell).strip()]
            if cells:
                lines.append(" | ".join(cells))
        pages.append(
            DocumentPage(
                page_number=index,
                label=f"Hoja: {sheet.title}",
                text="\n".join(lines).strip(),
            )
        )
    workbook.close()
    return pages or [DocumentPage(page_number=1, label="Hoja 1", text="")]


def _parse_csv(raw: bytes) -> list[DocumentPage]:
    text = _decode(raw)
    reader = csv.reader(io.StringIO(text))
    rows = [row for row in reader if any(cell.strip() for cell in row)]
    if not rows:
        return [DocumentPage(page_number=1, label="Filas 1", text="")]
    pages: list[DocumentPage] = []
    page_number = 1
    for start in range(0, len(rows), _CSV_ROWS_PER_PAGE):
        block = rows[start : start + _CSV_ROWS_PER_PAGE]
        lines = [" | ".join(cell.strip() for cell in row) for row in block]
        pages.append(
            DocumentPage(
                page_number=page_number,
                label=f"Filas {start + 1}-{start + len(block)}",
                text="\n".join(lines),
            )
        )
        page_number += 1
    return pages


def _parse_txt(raw: bytes) -> list[DocumentPage]:
    text = _decode(raw)
    chunks = _chunk_text(text)
    return [
        DocumentPage(page_number=i, label=f"Página {i}", text=chunk)
        for i, chunk in enumerate(chunks, start=1)
    ]


_PARSERS = {
    ".pdf": _parse_pdf,
    ".docx": _parse_docx,
    ".xlsx": _parse_xlsx,
    ".csv": _parse_csv,
    ".txt": _parse_txt,
}


def parse_document(file_name: str, raw: bytes) -> ParsedDocument:
    """Parse any supported document into crawlable pages."""
    extension = Path(file_name).suffix.lower()
    parser = _PARSERS.get(extension)
    if parser is None:
        supported = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        raise UnsupportedDocumentError(
            f"Formato no soportado '{extension or file_name}'. Use: {supported}."
        )

    pages = parser(raw)
    if not pages:
        pages = [DocumentPage(page_number=1, label="Página 1", text="")]

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
