"""Entity extraction and dual intelligence engine (offline heuristics + optional AI).

The offline engine produces a fully structured Spanish report with zero cost and
no internet access. When an API key is configured, the report is enriched by an
LLM while keeping the Spanish output.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime, timezone

import httpx

from .config import Settings
from .schemas import (
    AuditFinding,
    AuditReport,
    DataReport,
    DocumentPage,
    Entities,
    ExecutiveSummary,
    KpiItem,
    ParsedDocument,
    ScanReport,
    SummarySection,
    TableRow,
)

_MONTHS = (
    "enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre"
)

_DATE_PATTERNS = [
    re.compile(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b"),
    re.compile(r"\b\d{4}-\d{2}-\d{2}\b"),
    re.compile(rf"\b\d{{1,2}}\s+de\s+(?:{_MONTHS})(?:\s+(?:de|del)\s+\d{{4}})?\b", re.IGNORECASE),
]
_MONEY_PATTERNS = [
    re.compile(r"(?:US\$|\$|S/\.?|€|£)\s?\d[\d.,]*", re.IGNORECASE),
    re.compile(
        r"\b\d[\d.,]*\s?(?:USD|EUR|PEN|soles|d[oó]lares|euros)\b", re.IGNORECASE
    ),
]
_PERCENT_PATTERN = re.compile(r"\b\d+(?:[.,]\d+)?\s?%")
_EMAIL_PATTERN = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")
_URL_PATTERN = re.compile(r"\b(?:https?://|www\.)[^\s<>\"']+", re.IGNORECASE)
_WORD_PATTERN = re.compile(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]{4,}")

_ALERT_KEYWORDS = {
    "confidencial": "Marcado como confidencial: restringir distribución.",
    "urgente": "Contiene lenguaje de urgencia: verificar plazos.",
    "vencido": "Posible vencimiento o mora mencionada.",
    "penalidad": "Se detectan penalidades: revisar cláusulas económicas.",
    "multa": "Se mencionan multas: validar condiciones.",
    "incumplimiento": "Riesgo de incumplimiento referido.",
    "advertencia": "Incluye advertencias que requieren revisión.",
    "riesgo": "El documento referencia riesgos explícitos.",
    "no autorizado": "Referencia a acciones no autorizadas.",
    "prohibido": "Contiene prohibiciones: validar alcance.",
}

_STOPWORDS = {
    "para", "como", "este", "esta", "esto", "estos", "estas", "donde", "cuando",
    "sobre", "entre", "desde", "hasta", "todo", "toda", "todos", "todas", "otro",
    "otra", "otras", "otros", "puede", "debe", "será", "sera", "cada", "tiene",
    "tienen", "hace", "hacer", "según", "segun", "también", "tambien", "pero",
    "porque", "aunque", "mismo", "misma", "ser", "estar", "han", "has", "del",
    "las", "los", "una", "unos", "unas", "por", "con", "sin", "que", "sus", "mas",
    "más", "fue", "son", "era", "esa", "ese", "eso", "este", "dicho", "dicha",
    "parte", "sido", "serán", "seran", "debe", "deberá", "debera", "dentro",
    "sobre", "mediante", "según", "cuenta", "mismo", "través", "traves",
}

_STRUCTURE_PATTERN = re.compile(
    r"^\s*(?:\d+[.)]\s|#{1,6}\s|cap[ií]tulo|secci[oó]n|art[ií]culo|anexo|cl[aá]usula)",
    re.IGNORECASE | re.MULTILINE,
)


def _context(text: str, match: re.Match[str], radius: int = 45) -> str:
    start = max(0, match.start() - radius)
    end = min(len(text), match.end() + radius)
    snippet = text[start:end].replace("\n", " ").strip()
    return re.sub(r"\s+", " ", snippet)


def extract_entities(text: str, top_keywords: int = 8) -> Entities:
    """Extract dates, money, percentages, contacts, keywords and alerts from text."""
    if not text:
        return Entities()

    dates: list[str] = []
    for pattern in _DATE_PATTERNS:
        dates.extend(match.group(0) for match in pattern.finditer(text))

    money: list[str] = []
    for pattern in _MONEY_PATTERNS:
        money.extend(match.group(0) for match in pattern.finditer(text))

    percentages = [m.group(0) for m in _PERCENT_PATTERN.finditer(text)]
    emails = [m.group(0) for m in _EMAIL_PATTERN.finditer(text)]
    urls = [m.group(0).rstrip(".,;)") for m in _URL_PATTERN.finditer(text)]

    words = [
        word.lower()
        for word in _WORD_PATTERN.findall(text)
        if word.lower() not in _STOPWORDS
    ]
    keywords = [word for word, _ in Counter(words).most_common(top_keywords)]

    alerts: list[str] = []
    lowered = text.lower()
    for keyword, message in _ALERT_KEYWORDS.items():
        if keyword in lowered:
            alerts.append(message)

    return Entities(
        dates=_dedupe(dates),
        money=_dedupe(money),
        percentages=_dedupe(percentages),
        emails=_dedupe(emails),
        urls=_dedupe(urls),
        keywords=_dedupe(keywords),
        alerts=_dedupe(alerts),
    )


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        key = item.strip().lower()
        if key and key not in seen:
            seen.add(key)
            result.append(item.strip())
    return result


def merge_entities(bundles: list[Entities]) -> Entities:
    merged = Entities()
    for bundle in bundles:
        merged.dates.extend(bundle.dates)
        merged.money.extend(bundle.money)
        merged.percentages.extend(bundle.percentages)
        merged.emails.extend(bundle.emails)
        merged.urls.extend(bundle.urls)
        merged.keywords.extend(bundle.keywords)
        merged.alerts.extend(bundle.alerts)
    merged.dates = _dedupe(merged.dates)
    merged.money = _dedupe(merged.money)
    merged.percentages = _dedupe(merged.percentages)
    merged.emails = _dedupe(merged.emails)
    merged.urls = _dedupe(merged.urls)
    merged.keywords = _dedupe(merged.keywords)[:20]
    merged.alerts = _dedupe(merged.alerts)
    return merged


def _readability(pages: list[DocumentPage]) -> dict[str, float]:
    text = "\n".join(page.text for page in pages)
    words = text.split()
    sentences = [s for s in re.split(r"[.!?]+", text) if s.strip()]
    word_count = max(1, len(words))
    sentence_count = max(1, len(sentences))
    avg_sentence = word_count / sentence_count
    avg_word = sum(len(word) for word in words) / word_count
    return {
        "words": float(len(words)),
        "sentences": float(sentence_count),
        "avg_sentence": round(avg_sentence, 2),
        "avg_word": round(avg_word, 2),
    }


def _long_paragraphs(pages: list[DocumentPage]) -> list[tuple[int, int]]:
    """Return (page_number, length) for paragraphs longer than 600 chars."""
    offenders: list[tuple[int, int]] = []
    for page in pages:
        for paragraph in re.split(r"\n\s*\n", page.text):
            stripped = paragraph.strip()
            if len(stripped) > 600 and not _STRUCTURE_PATTERN.search(stripped[:80]):
                offenders.append((page.page_number, len(stripped)))
    return offenders


def _document_kind(text: str) -> str:
    lowered = text.lower()
    mapping = [
        (("contrato",), "un contrato"),
        (("informe",), "un informe técnico"),
        (("propuesta",), "una propuesta"),
        (("presupuesto",), "un presupuesto"),
        (("factura",), "una factura"),
        (("póliza", "poliza"), "una póliza"),
        (("acta",), "un acta"),
        (("manual",), "un manual"),
        (("tesis",), "una tesis"),
        (("reporte",), "un reporte"),
    ]
    for keywords, label in mapping:
        if any(keyword in lowered for keyword in keywords):
            return label
    return "un documento general"


def _page_topic(text: str) -> str:
    first_line = next((line.strip() for line in text.splitlines() if line.strip()), "")
    cleaned = re.sub(r"\s+", " ", first_line).strip()
    if not cleaned:
        return "Contenido"
    return cleaned[:70] + "…" if len(cleaned) > 70 else cleaned


def _build_page_sections(
    document: ParsedDocument, per_page: list[Entities]
) -> list[SummarySection]:
    sections: list[SummarySection] = []
    for page, entities in zip(document.pages, per_page, strict=False):
        words = len(page.text.split())
        snippet = re.sub(r"\s+", " ", page.text.strip())[:220]
        entity_count = (
            len(entities.dates)
            + len(entities.money)
            + len(entities.percentages)
            + len(entities.emails)
            + len(entities.urls)
        )

        bullets: list[str] = []
        for date in entities.dates[:3]:
            bullets.append(f"Fecha detectada: {date}")
        for amount in entities.money[:3]:
            bullets.append(f"Monto detectado: {amount}")
        for percent in entities.percentages[:2]:
            bullets.append(f"Porcentaje detectado: {percent}")
        for email in entities.emails[:2]:
            bullets.append(f"Contacto detectado: {email}")
        for alert in entities.alerts[:2]:
            bullets.append(f"Alerta: {alert}")
        if not bullets:
            bullets.append("Sin entidades críticas en esta unidad.")

        metrics = [
            KpiItem(label="Palabras", value=str(words), description="Conteo en la unidad"),
            KpiItem(label="Entidades", value=str(entity_count), description="Datos detectados"),
            KpiItem(label="Alertas", value=str(len(entities.alerts)), description="Señales de riesgo"),
        ]

        content = (
            f"Unidad «{page.label}» con {words} palabras. Se identificaron "
            f"{len(entities.dates)} fechas, {len(entities.money)} montos, "
            f"{len(entities.percentages)} porcentajes y {len(entities.alerts)} alertas. "
            f"Fragmento representativo: «{snippet}»"
        )
        sections.append(
            SummarySection(
                title=f"{page.label} · {_page_topic(page.text)}",
                content=content,
                bullets=bullets,
                metrics=metrics,
            )
        )
        if len(sections) >= 24:
            break
    return sections


def _build_conclusions(
    entities: Entities, entity_total: int, findings: list[AuditFinding], score: int
) -> list[str]:
    conclusions: list[str] = []
    if entity_total:
        conclusions.append(
            f"El documento aporta {entity_total} entidades verificables entre fechas, montos, "
            "porcentajes y contactos que deben validarse antes de su uso."
        )
    if entities.money:
        conclusions.append(
            f"Se identificaron {len(entities.money)} montos económicos; conviene confirmar su moneda, "
            "vigencia y condiciones de pago."
        )
    if entities.dates:
        conclusions.append(
            f"Existen {len(entities.dates)} fechas relevantes que deben contrastarse con los plazos y "
            "vigencias declarados."
        )
    if findings:
        conclusions.append(
            f"La auditoría registra {len(findings)} observaciones; priorizar las de impacto alto para "
            "mejorar la claridad y el cumplimiento."
        )
    conclusions.append(
        f"El puntaje de calidad documental es {score}/100, un indicador "
        f"{'sólido' if score >= 80 else 'aceptable' if score >= 60 else 'que requiere atención'}."
    )
    return conclusions[:5]


def _build_critical_findings(
    findings: list[AuditFinding], entities: Entities
) -> list[str]:
    critical = [f"{finding.title}: {finding.detail}" for finding in findings if finding.impact == "alto"]
    if not critical:
        critical = list(entities.alerts[:4])
    if not critical:
        critical = ["No se detectaron hallazgos críticos; el documento es de bajo riesgo."]
    return critical[:5]


def build_local_report(document: ParsedDocument, per_page: list[Entities]) -> ScanReport:
    """Build the full Spanish report with the offline heuristic engine."""
    total_entities = merge_entities(per_page)
    readability = _readability(document.pages)
    text = "\n".join(page.text for page in document.pages)
    structure_hits = len(_STRUCTURE_PATTERN.findall(text))
    long_paragraphs = _long_paragraphs(document.pages)
    entity_total = (
        len(total_entities.dates)
        + len(total_entities.money)
        + len(total_entities.percentages)
        + len(total_entities.emails)
        + len(total_entities.urls)
    )

    doc_kind = _document_kind(text)
    structure_level = (
        "alto" if structure_hits >= document.total_pages else "moderado" if structure_hits else "bajo"
    )

    sections = _build_page_sections(document, per_page)

    highlights: list[str] = []
    if total_entities.money:
        highlights.append(f"Se detectaron {len(total_entities.money)} montos económicos que conviene validar.")
    if total_entities.dates:
        highlights.append(f"Existen {len(total_entities.dates)} fechas relevantes para plazos y vigencias.")
    if total_entities.alerts:
        highlights.append(f"Hay {len(total_entities.alerts)} señales de alerta que requieren revisión.")
    if structure_hits:
        highlights.append(f"El documento presenta {structure_hits} marcadores estructurales.")
    if not highlights:
        highlights.append("No se detectaron entidades críticas; el documento es de bajo riesgo.")

    kpis = [
        KpiItem(label="Unidades rastreadas", value=str(document.total_pages), description="Páginas, hojas o bloques procesados."),
        KpiItem(label="Palabras totales", value=str(int(readability["words"])), description="Conteo aproximado de palabras."),
        KpiItem(label="Entidades de datos", value=str(entity_total), description="Fechas, montos, porcentajes y contactos."),
        KpiItem(label="Palabras clave", value=str(len(total_entities.keywords)), description="Términos más relevantes del documento."),
        KpiItem(label="Señales de alerta", value=str(len(total_entities.alerts)), description="Indicadores de riesgo detectados."),
    ]

    table: list[TableRow] = []
    for page, entities in zip(document.pages, per_page, strict=False):
        for kind, values in (
            ("fecha", entities.dates),
            ("monto", entities.money),
            ("porcentaje", entities.percentages),
            ("correo", entities.emails),
            ("url", entities.urls),
        ):
            for value in values[:6]:
                table.append(
                    TableRow(
                        page=page.page_number,
                        kind=kind,
                        value=value,
                        context=page.text[:120].replace("\n", " ").strip(),
                    )
                )

    data_report = DataReport(kpis=kpis, entities=total_entities, table=table)

    findings: list[AuditFinding] = []
    score = 100

    if long_paragraphs:
        pages_hit = sorted({page for page, _ in long_paragraphs})
        score -= min(18, 4 * len(long_paragraphs))
        findings.append(
            AuditFinding(
                title="Párrafos demasiado largos",
                impact="medio",
                detail=(
                    f"Se detectaron {len(long_paragraphs)} párrafos de más de 600 caracteres en las "
                    f"unidades {', '.join(map(str, pages_hit[:8]))}. Dificultan la lectura y el escaneo visual."
                ),
                recommendation="Divide los párrafos extensos en bloques de 3-5 oraciones e incorpora subtítulos.",
            )
        )

    if structure_hits < max(1, document.total_pages // 2):
        score -= 14
        findings.append(
            AuditFinding(
                title="Estructura débil o ausente",
                impact="alto",
                detail="El documento carece de capítulos, secciones o listas numeradas suficientes para navegar el contenido.",
                recommendation="Añade títulos, numeración de secciones y viñetas para mejorar la jerarquía del contenido.",
            )
        )

    if entity_total and not structure_hits:
        score -= 10
        findings.append(
            AuditFinding(
                title="Datos numéricos sin contexto",
                impact="medio",
                detail="Aparecen fechas, montos o porcentajes en un documento sin estructura que los contextualice.",
                recommendation="Acompaña cada cifra con su unidad, periodo y fuente para evitar ambigüedad.",
            )
        )

    if readability["avg_sentence"] > 28:
        score -= 12
        findings.append(
            AuditFinding(
                title="Oraciones muy extensas",
                impact="medio",
                detail=f"El promedio es de {readability['avg_sentence']} palabras por oración, por encima de lo recomendado (≤ 25).",
                recommendation="Acorta las oraciones y separa ideas con puntos para mejorar la legibilidad.",
            )
        )

    currencies = set()
    for amount in total_entities.money:
        for symbol in ("$", "S/", "€", "£", "USD", "EUR", "PEN"):
            if symbol.lower() in amount.lower():
                currencies.add(symbol.upper())
    if len(currencies) > 1:
        score -= 6
        findings.append(
            AuditFinding(
                title="Posible inconsistencia de moneda",
                impact="bajo",
                detail=f"Se detectaron múltiples monedas: {', '.join(sorted(currencies))}. Confirma la moneda oficial del documento.",
                recommendation="Unifica la moneda o especifica el tipo de cambio aplicado.",
            )
        )

    if total_entities.alerts:
        score -= min(10, 2 * len(total_entities.alerts))
        findings.append(
            AuditFinding(
                title="Señales de riesgo detectadas",
                impact="alto" if len(total_entities.alerts) >= 3 else "medio",
                detail="El texto incluye términos sensibles: " + "; ".join(total_entities.alerts[:4]),
                recommendation="Revisa las cláusulas asociadas y confirma su vigencia antes de su uso.",
            )
        )

    strengths: list[str] = []
    if structure_hits:
        strengths.append(f"Presenta {structure_hits} marcadores de estructura que facilitan la navegación.")
    if total_entities.dates or total_entities.money:
        strengths.append("Contiene datos cuantitativos y fechas útiles para el análisis.")
    if readability["avg_sentence"] <= 25:
        strengths.append("La longitud media de las oraciones es adecuada para la lectura.")
    if not findings:
        strengths.append("No se detectaron problemas relevantes de estructura o legibilidad.")

    score = max(0, min(100, score))
    audit = AuditReport(score=score, findings=findings, strengths=strengths)

    overview = (
        f"El documento «{document.file_name}» ({document.file_type.upper()}, "
        f"{document.total_pages} unidades) se clasifica como {doc_kind}. El rastreo recorrió "
        f"{int(readability['words'])} palabras y detectó {entity_total} entidades de datos, "
        f"{len(total_entities.keywords)} palabras clave y {len(total_entities.alerts)} señales de alerta. "
        f"El nivel de estructura es {structure_level} y la auditoría otorga {score}/100 con "
        f"{len(findings)} observaciones."
    )
    purpose = (
        f"El propósito del documento es presentar y estructurar el contenido de {doc_kind}, "
        "permitiendo identificar obligaciones, cifras, plazos y riesgos relevantes para la toma de decisiones."
    )
    conclusions = _build_conclusions(total_entities, entity_total, findings, score)
    critical_findings = _build_critical_findings(findings, total_entities)

    executive = ExecutiveSummary(
        overview=overview,
        purpose=purpose,
        sections=sections,
        highlights=highlights,
        conclusions=conclusions,
        critical_findings=critical_findings,
    )

    return ScanReport(
        file_name=document.file_name,
        file_type=document.file_type,
        total_pages=document.total_pages,
        generated_at=datetime.now(timezone.utc),
        provider="local",
        executive_summary=executive,
        data_report=data_report,
        audit=audit,
    )


async def enrich_with_ai(
    report: ScanReport, document: ParsedDocument, settings: Settings
) -> ScanReport:
    """Optionally enrich the report using OpenAI or Gemini (Spanish output)."""
    provider = settings.effective_provider
    if provider == "local":
        return report

    excerpt = "\n".join(page.text for page in document.pages)[:6000]
    prompt = (
        "Eres un auditor documental experto. Analiza el siguiente texto y responde SOLO con un JSON "
        "válido en español con las claves: overview (string), sections (lista de {title, content}), "
        "highlights (lista de strings), findings (lista de {title, impact, detail, recommendation}) y "
        "strengths (lista de strings). No incluyas markdown ni texto adicional.\n\n"
        f"Documento: {document.file_name}\n\n{excerpt}"
    )

    try:
        if provider == "openai":
            payload = await _call_openai(prompt, settings)
        else:
            payload = await _call_gemini(prompt, settings)
        data = json.loads(_extract_json(payload))
    except Exception:  # noqa: BLE001 - enrichment must never break the scan
        return report

    try:
        ai_sections = [
            SummarySection(
                title=str(item["title"]),
                content=str(item["content"]),
                bullets=[str(bullet) for bullet in item.get("bullets", []) if bullet],
            )
            for item in data.get("sections", [])
            if isinstance(item, dict) and item.get("title") and item.get("content")
        ]
        report.executive_summary.overview = str(
            data.get("overview", report.executive_summary.overview)
        )
        if ai_sections:
            report.executive_summary.sections = ai_sections
        ai_highlights = [str(item) for item in data.get("highlights", []) if item]
        if ai_highlights:
            report.executive_summary.highlights = ai_highlights
        ai_findings = [
            AuditFinding(
                title=str(item["title"]),
                impact=item.get("impact", "medio")
                if item.get("impact") in {"alto", "medio", "bajo"}
                else "medio",
                detail=str(item["detail"]),
                recommendation=str(item["recommendation"]),
            )
            for item in data.get("findings", [])
            if isinstance(item, dict)
            and item.get("title")
            and item.get("detail")
            and item.get("recommendation")
        ]
        if ai_findings:
            report.audit.findings = ai_findings
        if data.get("strengths"):
            report.audit.strengths = [str(item) for item in data["strengths"]]
        report.provider = provider
    except Exception:  # noqa: BLE001
        return report

    return report


def _extract_json(raw: str) -> str:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```[a-zA-Z]*", "", raw)
        raw = re.sub(r"```$", "", raw).strip()
    start = raw.find("{")
    end = raw.rfind("}")
    if start != -1 and end != -1:
        return raw[start : end + 1]
    return raw


async def _call_openai(prompt: str, settings: Settings) -> str:
    url = f"{settings.openai_base_url.rstrip('/')}/chat/completions"
    headers = {"Authorization": f"Bearer {settings.openai_api_key}"}
    body = {
        "model": settings.openai_model,
        "messages": [
            {"role": "system", "content": "Respondes únicamente con JSON válido en español."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.3,
        "response_format": {"type": "json_object"},
    }
    async with httpx.AsyncClient(timeout=45) as client:
        response = await client.post(url, headers=headers, json=body)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]


async def _call_gemini(prompt: str, settings: Settings) -> str:
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{settings.gemini_model}:generateContent?key={settings.gemini_api_key}"
    )
    body = {"contents": [{"parts": [{"text": prompt}]}]}
    async with httpx.AsyncClient(timeout=45) as client:
        response = await client.post(url, json=body)
        response.raise_for_status()
        return response.json()["candidates"][0]["content"]["parts"][0]["text"]
