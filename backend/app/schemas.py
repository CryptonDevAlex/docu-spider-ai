"""Pydantic contracts shared by the parser, spider engine and analyzer."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class DocBlock(BaseModel):
    """An ordered content block used to render a page faithfully."""

    type: Literal["heading", "paragraph", "table"] = "paragraph"
    text: str = ""
    rows: list[list[str]] = Field(default_factory=list)


class DocumentPage(BaseModel):
    """A single crawlable unit of a document (PDF page, sheet, chunk...)."""

    page_number: int
    label: str
    text: str
    title: str = ""
    paragraphs: list[str] = Field(default_factory=list)
    tables: list[list[list[str]]] = Field(default_factory=list)
    blocks: list[DocBlock] = Field(default_factory=list)


class ParsedDocument(BaseModel):
    """Result of parsing an uploaded file into pages."""

    file_name: str
    file_type: str
    total_pages: int
    pages: list[DocumentPage]
    size_bytes: int = 0


class Entities(BaseModel):
    """Entities detected on a single page or across the whole document."""

    dates: list[str] = Field(default_factory=list)
    money: list[str] = Field(default_factory=list)
    percentages: list[str] = Field(default_factory=list)
    emails: list[str] = Field(default_factory=list)
    urls: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    alerts: list[str] = Field(default_factory=list)


class ScanCreated(BaseModel):
    """Response returned when a scan session is created."""

    scan_id: str
    file_name: str
    file_type: str
    total_pages: int


class PageEvent(BaseModel):
    """SSE event emitted for every page crawled by the spider."""

    type: Literal["page"] = "page"
    page_number: int
    total_pages: int
    label: str
    text_preview: str
    full_text: str
    title: str = ""
    paragraphs: list[str] = Field(default_factory=list)
    tables: list[list[list[str]]] = Field(default_factory=list)
    blocks: list[DocBlock] = Field(default_factory=list)
    entities: Entities
    progress: float


class StatusEvent(BaseModel):
    """SSE event describing the lifecycle of the scan."""

    type: Literal["status"] = "status"
    message: str
    provider: str
    total_pages: int


class TableRow(BaseModel):
    page: int
    kind: str
    value: str
    context: str


class KpiItem(BaseModel):
    label: str
    value: str
    description: str


class DataReport(BaseModel):
    kpis: list[KpiItem]
    entities: Entities
    table: list[TableRow]


class SummarySection(BaseModel):
    title: str
    content: str
    bullets: list[str] = Field(default_factory=list)
    metrics: list[KpiItem] = Field(default_factory=list)


class ExecutiveSummary(BaseModel):
    overview: str
    purpose: str = ""
    sections: list[SummarySection]
    highlights: list[str] = Field(default_factory=list)
    conclusions: list[str] = Field(default_factory=list)
    critical_findings: list[str] = Field(default_factory=list)


class AuditFinding(BaseModel):
    title: str
    impact: Literal["alto", "medio", "bajo"]
    detail: str
    recommendation: str


class AuditReport(BaseModel):
    score: int
    findings: list[AuditFinding]
    strengths: list[str]


class ScanReport(BaseModel):
    file_name: str
    file_type: str
    total_pages: int
    generated_at: datetime
    provider: str
    executive_summary: ExecutiveSummary
    data_report: DataReport
    audit: AuditReport


class DoneEvent(BaseModel):
    """SSE event carrying the final report."""

    type: Literal["done"] = "done"
    report: ScanReport


class ErrorEvent(BaseModel):
    type: Literal["error"] = "error"
    message: str
