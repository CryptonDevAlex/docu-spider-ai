"""DocuSpider AI — FastAPI entrypoint.

Endpoints:
    GET  /                       -> service metadata
    GET  /api/health             -> health check
    GET  /api/formats            -> supported formats
    POST /api/scan               -> upload a document and create a scan session
    POST /api/scan/sample        -> create a scan session from the built-in demo
    GET  /api/scan/{id}/stream   -> SSE stream crawling the document page by page
"""

from __future__ import annotations

import uuid

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from . import __version__
from .config import get_settings
from .parsers import SUPPORTED_EXTENSIONS, UnsupportedDocumentError, parse_document
from .sample import build_sample_document
from .schemas import ParsedDocument, ScanCreated
from .spider_engine import stream_scan

settings = get_settings()

app = FastAPI(
    title="DocuSpider AI API",
    version=__version__,
    description=(
        "Motor de rastreo documental multiformato con streaming SSE en tiempo real "
        "y auditoría con inteligencia dual (offline + IA opcional)."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin, "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory scan sessions. Each session holds the parsed document until crawled.
SCANS: dict[str, ParsedDocument] = {}


@app.get("/")
async def root() -> dict[str, object]:
    return {
        "name": "DocuSpider AI",
        "version": __version__,
        "provider": settings.effective_provider,
        "docs": "/docs",
        "formats": sorted(ext.lstrip(".") for ext in SUPPORTED_EXTENSIONS),
    }


@app.get("/api/health")
async def health() -> dict[str, object]:
    return {
        "status": "ok",
        "version": __version__,
        "provider": settings.effective_provider,
        "active_sessions": len(SCANS),
    }


@app.get("/api/formats")
async def formats() -> dict[str, list[str]]:
    return {"formats": sorted(ext.lstrip(".") for ext in SUPPORTED_EXTENSIONS)}


@app.post("/api/scan", response_model=ScanCreated)
async def create_scan(file: UploadFile = File(...)) -> ScanCreated:
    if not file.filename:
        raise HTTPException(status_code=400, detail="El archivo no tiene nombre válido.")

    raw = await file.read()
    max_bytes = settings.max_upload_mb * 1024 * 1024
    if len(raw) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"El archivo supera el límite de {settings.max_upload_mb} MB.",
        )
    if not raw:
        raise HTTPException(status_code=400, detail="El archivo está vacío.")

    try:
        document = parse_document(file.filename, raw)
    except UnsupportedDocumentError as exc:
        raise HTTPException(status_code=415, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=422, detail=f"No se pudo leer el documento: {exc}") from exc

    scan_id = uuid.uuid4().hex
    SCANS[scan_id] = document
    return ScanCreated(
        scan_id=scan_id,
        file_name=document.file_name,
        file_type=document.file_type,
        total_pages=document.total_pages,
    )


@app.post("/api/scan/sample", response_model=ScanCreated)
async def create_sample_scan() -> ScanCreated:
    document = build_sample_document()
    scan_id = uuid.uuid4().hex
    SCANS[scan_id] = document
    return ScanCreated(
        scan_id=scan_id,
        file_name=document.file_name,
        file_type=document.file_type,
        total_pages=document.total_pages,
    )


@app.get("/api/scan/{scan_id}/stream")
async def scan_stream(scan_id: str) -> StreamingResponse:
    document = SCANS.get(scan_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Sesión de escaneo no encontrada o expirada.")

    async def event_source():
        try:
            async for frame in stream_scan(document, settings):
                yield frame
        finally:
            SCANS.pop(scan_id, None)

    return StreamingResponse(
        event_source(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
