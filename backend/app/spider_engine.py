"""Real-time spider engine that crawls a document page by page over SSE."""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator

from .analyzer import build_local_report, enrich_with_ai, extract_entities
from .config import Settings
from .schemas import DoneEvent, ErrorEvent, PageEvent, ParsedDocument, StatusEvent

_PREVIEW_CHARS = 320


def _sse(payload: dict) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


async def stream_scan(document: ParsedDocument, settings: Settings) -> AsyncIterator[str]:
    """Yield SSE frames while the spider crawls each page of the document."""
    try:
        yield _sse(
            StatusEvent(
                message="Iniciando rastreo del documento...",
                provider=settings.effective_provider,
                total_pages=document.total_pages,
            ).model_dump(mode="json")
        )
        await asyncio.sleep(min(0.2, settings.spider_delay_seconds))

        per_page_entities = []
        total = max(1, document.total_pages)

        for page in document.pages:
            entities = extract_entities(page.text)
            per_page_entities.append(entities)
            progress = round((page.page_number / total) * 100, 2)

            yield _sse(
                PageEvent(
                    page_number=page.page_number,
                    total_pages=document.total_pages,
                    label=page.label,
                    text_preview=page.text[:_PREVIEW_CHARS],
                    full_text=page.text,
                    title=page.title,
                    paragraphs=page.paragraphs,
                    tables=page.tables,
                    blocks=page.blocks,
                    entities=entities,
                    progress=progress,
                ).model_dump(mode="json")
            )
            await asyncio.sleep(settings.spider_delay_seconds)

        yield _sse(
            StatusEvent(
                message="Rastreo completado. Generando informe de inteligencia...",
                provider=settings.effective_provider,
                total_pages=document.total_pages,
            ).model_dump(mode="json")
        )

        report = build_local_report(document, per_page_entities)
        report = await enrich_with_ai(report, document, settings)

        yield _sse(DoneEvent(report=report).model_dump(mode="json"))
    except Exception as exc:  # noqa: BLE001 - surface errors as SSE events
        yield _sse(ErrorEvent(message=f"Error durante el rastreo: {exc}").model_dump(mode="json"))
