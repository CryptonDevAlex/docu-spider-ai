# 🕷️ DocuSpider AI

**Visual multi-format document spider crawler that streams page-by-page scans over SSE and delivers AI-assisted Spanish audit reports — 100% free offline engine with optional OpenAI/Gemini enrichment.**

> Upload a PDF, DOCX, XLSX, CSV or TXT file and watch an animated spider crawl every page in real time while it extracts entities (dates, money, percentages, emails, URLs, keywords, alerts) and generates a structured intelligence report: executive summary, extracted-data report, and a document-quality audit.

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🕷️ **Visual Spider Crawling** | Animated document viewer with a scanning laser and a live spider crawling each page as it is processed |
| ⚡ **Real-Time SSE Streaming** | Server-Sent Events push page number, total pages, text fragment, per-page entities and progress percentage as the crawl advances |
| 📄 **Universal Multi-Format Parsing** | PDF (page-by-page), DOCX (block chunks), XLSX (one unit per sheet), CSV (row chunks) and TXT (page chunks) |
| 🧠 **Dual Intelligence Engine** | Free offline heuristics/statistics by default (`LLM_PROVIDER=local`); optional OpenAI-compatible or Google Gemini enrichment — output always in Spanish |
| 🔎 **Entity Extraction** | Dates, monetary amounts, percentages, emails, URLs, keywords and risk alerts detected per page and aggregated |
| 📊 **3-Tab Report Dashboard** | Executive Summary · Extracted Data (KPIs + filterable table) · Audit & Improvements with impact levels |
| 📈 **Document Audit** | Detects long paragraphs, weak structure, numeric data without context, oversized sentences and currency inconsistencies, then scores quality 0–100 |
| 💾 **Export Everywhere** | Download the full report as a formatted Word document (`.docx`) or a clean white PDF (`.pdf`) |
| 🎯 **One-Click Demo** | Built-in 9-page Spanish contract to try the full crawl instantly |
| 🆓 **Zero-Cost Offline Mode** | No API keys, no internet and no external database required |

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                         FRONTEND · Next.js 16 + Tailwind                      │
│                                                                                │
│   ┌───────────────┐    ┌────────────────────┐    ┌──────────────────────────┐  │
│   │  Upload Zone  │    │  Animated Spider   │    │  3-Tab Results Panel     │  │
│   │  Drag & Drop  │    │  Viewer (SSE live) │    │  Summary / Data / Audit  │  │
│   │  + Sample Doc │    │  laser + node map  │    │  Export Word · PDF       │  │
│   └───────┬───────┘    └─────────┬──────────┘    └────────────┬─────────────┘  │
│           │                      │                            │                │
│           └──────────────┬───────┴────────────────────────────┘                │
│                          │  useScanStream (EventSource)                         │
└──────────────────────────│─────────────────────────────────────────────────────┘
                           │ HTTP · multipart upload + SSE (text/event-stream)
                           ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                          BACKEND · FastAPI + Python                           │
│                                                                                │
│   POST /api/scan ─────────────┐                                                │
│   POST /api/scan/sample ──────┤                                                │
│                               ▼                                                │
│                     ┌───────────────────┐      ┌────────────────────────────┐  │
│                     │    parsers.py     │      │      spider_engine.py      │  │
│                     │  PDF · DOCX ·     │─────▶│  page-by-page SSE emitter  │  │
│                     │  XLSX · CSV · TXT │      │  (controlled pause)        │  │
│                     └───────────────────┘      └──────────────┬─────────────┘  │
│                                                                │                │
│                                                                ▼                │
│                     ┌────────────────────────────────────────────────────────┐ │
│                     │                  analyzer.py                           │ │
│                     │  Entity extraction + dual intelligence engine          │ │
│                     │  ┌──────────────────┐      ┌─────────────────────────┐ │ │
│                     │  │  Local heuristics│      │  Optional AI enrichment │ │ │
│                     │  │  (offline, free) │      │  OpenAI · Gemini        │ │ │
│                     │  └──────────────────┘      └─────────────────────────┘ │ │
│                     └──────────────────────────┬─────────────────────────────┘ │
│                                                ▼                               │
│                     GET /api/scan/{id}/stream → SSE frames:                    │
│                       status → page → page … → done (full report)              │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites
- **Python 3.11+**
- **Node.js 20+**

### 1. Backend (FastAPI)
```bash
cd backend

# Create & activate a virtual environment
py -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS / Linux:
# source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment (defaults to the free offline engine)
cp .env.example .env

# Run the API with hot reload
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
- API docs (Swagger): **http://localhost:8000/docs**
- Health check: **http://localhost:8000/api/health**

### 2. Frontend (Next.js)
```bash
cd frontend

# Install dependencies
npm install

# Start the dev server
npm run dev
```
- Web UI (Spanish): **http://localhost:3000**

> The frontend reads the backend URL from `NEXT_PUBLIC_API_URL` (default `http://localhost:8000`). Copy `frontend/.env.example` to `frontend/.env.local` to override it.

---

## ⚙️ Configuration (`backend/.env`)

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_PROVIDER` | `local` | `local` (offline, free) · `openai` · `gemini` · `auto` |
| `OPENAI_API_KEY` | — | Enable OpenAI-compatible enrichment |
| `OPENAI_BASE_URL` | `https://api.openai.com/v1` | Custom OpenAI-compatible endpoint |
| `OPENAI_MODEL` | `gpt-4o-mini` | Model name for the OpenAI provider |
| `GEMINI_API_KEY` | — | Enable Google Gemini enrichment |
| `GEMINI_MODEL` | `gemini-2.5-flash` | Gemini model name |
| `SPIDER_DELAY_SECONDS` | `0.45` | Controlled pause between pages (visible crawl) |
| `MAX_UPLOAD_MB` | `25` | Maximum upload size in megabytes |
| `FRONTEND_ORIGIN` | `http://localhost:3000` | Allowed CORS origin |

> 💡 **Free by default:** with `LLM_PROVIDER=local` (the default) the engine runs entirely offline using heuristics and statistics — no API keys, no network calls, no cost. Adding a key only enriches the report; the output stays in Spanish and never breaks the scan if the provider fails.

---

## 📸 Screenshots / Demo

> Save your captures in [`docs/images/`](docs/images/) and reference them here.

| View | Preview |
|------|---------|
| Upload Zone (Drag & Drop + Sample) | ![Preview coming soon](https://img.shields.io/badge/Preview-coming_soon-lightgrey?style=flat-square) |
| Animated Spider Viewer + Live Log | ![Preview coming soon](https://img.shields.io/badge/Preview-coming_soon-lightgrey?style=flat-square) |
| Executive Summary Tab | ![Preview coming soon](https://img.shields.io/badge/Preview-coming_soon-lightgrey?style=flat-square) |
| Extracted Data Tab (KPIs + Table) | ![Preview coming soon](https://img.shields.io/badge/Preview-coming_soon-lightgrey?style=flat-square) |
| Audit & Improvements Tab | ![Preview coming soon](https://img.shields.io/badge/Preview-coming_soon-lightgrey?style=flat-square) |

---

## 📁 Repository Structure

```
docu-spider-ai/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── analyzer.py        # Entity extraction + dual intelligence engine
│   │   ├── config.py          # Environment settings
│   │   ├── main.py            # FastAPI routes + SSE endpoint
│   │   ├── parsers.py         # Multi-format parsers (PDF/DOCX/XLSX/CSV/TXT)
│   │   ├── sample.py          # Built-in 9-page Spanish demo document
│   │   ├── schemas.py         # Pydantic contracts
│   │   └── spider_engine.py   # Page-by-page SSE crawl orchestration
│   ├── .env.example
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/               # Next.js App Router (layout, page, globals.css)
│   │   ├── components/        # Header, UploadZone, SpiderViewer, ResultsPanel
│   │   ├── hooks/             # useScanStream (EventSource)
│   │   └── lib/               # API client, types, report exporters
│   ├── next.config.ts
│   ├── package.json
│   ├── tailwind.config.ts
│   └── tsconfig.json
├── docs/
│   └── images/                # Screenshots / demo assets (.gitkeep)
├── LICENSE
├── .gitignore
└── README.md
```

---

## 🧪 Tech Stack

| Layer | Technologies |
|-------|--------------|
| **Backend** | Python 3.11+, FastAPI, Uvicorn, Pydantic v2, pypdf, python-docx, openpyxl, httpx |
| **Streaming** | Server-Sent Events (SSE) with `StreamingResponse` |
| **Intelligence** | Offline heuristic engine + optional OpenAI / Gemini |
| **Frontend** | Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS |
| **Export** | Word (.docx) via python-docx, clean white PDF via fpdf2 |

---

## 🎯 API Reference (summary)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | Service status, version and active provider |
| `GET` | `/api/formats` | Supported document formats |
| `POST` | `/api/scan` | Upload a document (multipart) → returns `scan_id` |
| `POST` | `/api/scan/sample` | Create a scan from the built-in demo document |
| `GET` | `/api/scan/{id}/stream` | SSE stream: `status`, `page`, `done`, `error` events |
| `POST` | `/api/export/docx` | Export a report as a formatted Word (`.docx`) file |
| `POST` | `/api/export/pdf` | Export a report as a clean white PDF (`.pdf`) file |

---

## 📜 License

**MIT License** — see [LICENSE](LICENSE) for details.

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`feat/your-feature`)
3. Follow [Conventional Commits](https://www.conventionalcommits.org/)
4. Ensure `npm run build` (frontend) passes and the backend starts cleanly
5. Open a Pull Request

---

<div align="center">
  <sub>Built with 🕷️ by <a href="https://github.com/CryptonDevAlex">CryptonDevAlex</a> ·
  <a href="https://www.linkedin.com/in/alex-alhuay-uquiche-191570308/">LinkedIn</a> ·
  Open to Work &amp; Freelance 🟢</sub>
</div>
