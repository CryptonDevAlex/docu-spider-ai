"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import type { ReactNode } from "react";

import type { ScanState } from "@/hooks/useScanStream";
import type { DocBlock, Entities, PageEvent } from "@/lib/types";
import { WalkingSpider } from "./WalkingSpider";

type TermClassMap = Map<string, string>;

const CLAUSE_TERMS = [
  "cláusula",
  "clausula",
  "penalidad",
  "multa",
  "confidencial",
  "vencido",
  "incumplimiento",
  "advertencia",
  "prohibido",
  "garantía",
  "obligación",
  "vigencia",
  "plazo",
  "resolución",
];

const NAME_HINTS = [
  "Innovatech Solutions S.A.C.",
  "Corporación Andina de Logística S.A.",
  "Alex Jhon Alhuay Uquiche",
  "María Fernanda Rojas Campos",
];

function escapeRegExp(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function addTerms(map: TermClassMap, values: string[] | undefined, className: string): void {
  for (const value of values ?? []) {
    const clean = value.trim().toLowerCase();
    if (clean.length > 2 && !map.has(clean)) {
      map.set(clean, className);
    }
  }
}

function buildTermMap(page: PageEvent): TermClassMap {
  const map: TermClassMap = new Map();
  addTerms(map, page.entities.dates, "entity-date");
  addTerms(map, page.entities.money, "entity-money");
  addTerms(map, page.entities.percentages, "entity-number");
  addTerms(map, page.entities.emails, "entity-contact");
  addTerms(map, page.entities.urls, "entity-contact");
  addTerms(map, page.entities.alerts, "entity-alert");
  addTerms(map, page.entities.keywords, "entity-keyword");
  addTerms(map, CLAUSE_TERMS, "entity-clause");
  addTerms(map, NAME_HINTS, "entity-name");
  return map;
}

function termClass(value: string, map: TermClassMap): string {
  const direct = map.get(value.trim().toLowerCase());
  if (direct) return direct;
  if (/^[A-ZÁÉÍÓÚÜÑ]/.test(value.trim()) && /[a-záéíóúüñ]/.test(value)) {
    return "entity-name";
  }
  return "entity-keyword";
}

function HighlightedText({ text, map }: { text: string; map: TermClassMap }) {
  const pattern = useMemo(() => {
    const terms = Array.from(map.keys())
      .sort((a, b) => b.length - a.length)
      .map(escapeRegExp);
    return terms.length ? new RegExp(`(${terms.join("|")})`, "gi") : null;
  }, [map]);

  if (!pattern) return <>{text}</>;

  const parts = text.split(pattern);
  return (
    <>
      {parts.map((part, index) => {
        if (index % 2 === 1) {
          return (
            <mark key={`${part}-${index}`} className={`entity-token ${termClass(part, map)}`}>
              {part}
            </mark>
          );
        }
        return <span key={`${part}-${index}`}>{part}</span>;
      })}
    </>
  );
}

function TableBlock({ rows, map }: { rows: string[][]; map: TermClassMap }) {
  if (!rows.length) return null;
  const [header, ...body] = rows;
  return (
    <div className="my-4 overflow-hidden rounded-md border border-slate-300">
      <table className="w-full border-collapse text-[12.5px]">
        <thead className="bg-slate-100">
          <tr>
            {header.map((cell, index) => (
              <th
                key={`${cell}-${index}`}
                className="border-b border-slate-300 px-2.5 py-2 text-left font-semibold text-slate-700"
              >
                <HighlightedText text={cell} map={map} />
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {body.map((row, rowIndex) => (
            <tr key={`row-${rowIndex}`} className="odd:bg-white even:bg-slate-50/70">
              {row.map((cell, cellIndex) => (
                <td
                  key={`${cell}-${cellIndex}`}
                  className="border-t border-slate-200 px-2.5 py-1.5 align-top text-slate-700"
                >
                  <HighlightedText text={cell} map={map} />
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function PaperBlock({ block, map, primary }: { block: DocBlock; map: TermClassMap; primary: boolean }) {
  if (block.type === "heading") {
    return (
      <h2
        className={`paper-block ${primary ? "paper-title" : "paper-heading"} ${
          primary ? "mb-5" : "mb-3 mt-6"
        }`}
      >
        <HighlightedText text={block.text} map={map} />
      </h2>
    );
  }

  if (block.type === "table") {
    return (
      <div className="paper-block">
        <TableBlock rows={block.rows} map={map} />
      </div>
    );
  }

  return (
    <p className="paper-block paper-paragraph">
      <HighlightedText text={block.text} map={map} />
    </p>
  );
}

function PaperSheet({
  page,
  isCurrent,
  showSpider,
  registerRef,
}: {
  page: PageEvent;
  isCurrent: boolean;
  showSpider: boolean;
  registerRef: (pageNumber: number, element: HTMLDivElement | null) => void;
}) {
  const sheetRef = useRef<HTMLDivElement>(null);
  const map = useMemo(() => buildTermMap(page), [page]);

  const fallbackParagraphs = useMemo(() => {
    if (page.blocks.length) return [];
    if (page.paragraphs.length) return page.paragraphs;
    return page.full_text
      .split(/\n\s*\n+/)
      .map((paragraph) => paragraph.trim())
      .filter(Boolean);
  }, [page]);

  return (
    <div
      ref={(element) => {
        sheetRef.current = element;
        registerRef(page.page_number, element);
      }}
      data-sheet={page.page_number}
      className={`paper-sheet relative mx-auto w-full max-w-[760px] ${isCurrent ? "is-current" : ""}`}
    >
      <div className="paper-watermark" aria-hidden="true">
        DOS
      </div>

      <div className="relative z-10">
        <div className="mb-7 flex items-center justify-between border-b border-slate-200 pb-3 font-sans text-[10px] uppercase tracking-[0.22em] text-slate-400">
          <span>{page.label}</span>
          <span>
            {page.page_number} / {page.total_pages}
          </span>
        </div>

        {page.blocks.length ? (
          page.blocks.map((block, index) => (
            <PaperBlock
              key={`${block.type}-${index}`}
              block={block}
              map={map}
              primary={index === 0 && block.type === "heading"}
            />
          ))
        ) : (
          fallbackParagraphs.map((paragraph, index) => (
            <p key={`fallback-${index}`} className="paper-block paper-paragraph">
              <HighlightedText text={paragraph} map={map} />
            </p>
          ))
        )}

        <div className="mt-10 flex items-center justify-between border-t border-slate-200 pt-3 font-sans text-[10px] text-slate-400">
          <span>DocuSpider AI · Rastreo documental</span>
          <span>{new Date().toLocaleDateString("es-ES")}</span>
        </div>
      </div>

      {isCurrent && <div className="sheet-scan-band" aria-hidden="true" />}
      {isCurrent && showSpider && <WalkingSpider targetRef={sheetRef} />}
    </div>
  );
}

function countEntities(page: PageEvent | undefined): number {
  if (!page) return 0;
  return (
    page.entities.dates.length +
    page.entities.money.length +
    page.entities.percentages.length +
    page.entities.emails.length +
    page.entities.urls.length
  );
}

function buildDraft(page: PageEvent | undefined): string {
  if (!page) return "Esperando la primera hoja para comenzar la redacción del resumen…";
  const paragraphs = page.blocks.filter((block) => block.type === "paragraph").length;
  const entities = countEntities(page);
  const title = page.title || page.label;
  const clues: string[] = [];
  if (page.entities.dates.length) clues.push(`${page.entities.dates.length} fechas`);
  if (page.entities.money.length) clues.push(`${page.entities.money.length} montos`);
  if (page.entities.percentages.length) clues.push(`${page.entities.percentages.length} porcentajes`);
  if (page.entities.alerts.length) clues.push(`${page.entities.alerts.length} alertas`);
  const clueText = clues.length ? ` He localizado ${clues.join(", ")}.` : " No se han localizado datos críticos.";
  return `Página ${page.page_number}. ${title}. He recorrido ${paragraphs} párrafos y extraído ${entities} entidades.${clueText}`;
}

function TypewriterDraft({ text }: { text: string }) {
  const [shown, setShown] = useState("");

  useEffect(() => {
    setShown("");
    let index = 0;
    const timer = window.setInterval(() => {
      index = Math.min(text.length, index + 3);
      setShown(text.slice(0, index));
      if (index >= text.length) window.clearInterval(timer);
    }, 18);
    return () => window.clearInterval(timer);
  }, [text]);

  return (
    <p className="text-sm leading-6 text-spider-text/85">
      {shown}
      <span className="draft-caret" aria-hidden="true" />
    </p>
  );
}

function LiveChip({
  label,
  value,
  tone,
  index,
}: {
  label: string;
  value: string;
  tone: string;
  index: number;
}) {
  return (
    <span
      className={`live-chip ${tone}`}
      style={{ animationDelay: `${Math.min(index * 90, 600)}ms` }}
      title={value}
    >
      <span className="opacity-60">{label}</span> {value}
    </span>
  );
}

function entityChips(entities: Entities | undefined) {
  if (!entities) return [];
  return [
    ...entities.dates.slice(0, 4).map((value) => ({ label: "FECHA", value, tone: "tone-date" })),
    ...entities.money.slice(0, 4).map((value) => ({ label: "MONTO", value, tone: "tone-money" })),
    ...entities.percentages.slice(0, 3).map((value) => ({ label: "%", value, tone: "tone-number" })),
    ...entities.emails.slice(0, 2).map((value) => ({ label: "CORREO", value, tone: "tone-contact" })),
    ...entities.alerts.slice(0, 3).map((value) => ({ label: "ALERTA", value, tone: "tone-alert" })),
  ];
}

function OriginalViewer({
  fileUrl,
  fileType,
  fileName,
  currentPage,
}: {
  fileUrl: string;
  fileType: string;
  fileName: string;
  currentPage: number;
}) {
  const sheetRef = useRef<HTMLDivElement>(null);
  const type = (fileType || "").toLowerCase();
  const isText = type === "txt" || type === "csv";
  const isPdf = type === "pdf";
  const isImage = ["png", "jpg", "jpeg", "webp", "gif", "bmp", "svg"].includes(type);

  return (
    <div
      ref={sheetRef}
      className="relative mx-auto w-full max-w-[920px] overflow-hidden rounded-md bg-white shadow-[0_28px_70px_-28px_rgba(0,0,0,0.85)]"
      style={{ minHeight: 920 }}
    >
      {isPdf && (
        <iframe
          src={`${fileUrl}#page=${Math.max(1, currentPage)}&view=FitH`}
          title={fileName}
          className="h-[920px] w-full bg-white"
        />
      )}
      {isImage && (
        <div className="grid min-h-[920px] place-items-center bg-white p-4">
          <img src={fileUrl} alt={fileName} className="max-h-[880px] w-auto max-w-full object-contain" />
        </div>
      )}
      {isText && (
        <iframe src={fileUrl} title={fileName} className="h-[920px] w-full bg-white" />
      )}
      {!isPdf && !isImage && !isText && (
        <div className="grid min-h-[920px] place-items-center bg-slate-50 p-10 text-center text-slate-600">
          <div>
            <p className="text-lg font-semibold text-slate-800">Vista original no disponible en el navegador</p>
            <p className="mt-2 text-sm">
              Los archivos DOCX/XLSX conservan su formato para auditoría; aquí se muestra el rastreo y el informe generado.
            </p>
            <a href={fileUrl} download={fileName} className="mt-4 inline-block rounded-lg bg-cyan-600 px-4 py-2 text-sm font-medium text-white">
              Descargar archivo original
            </a>
          </div>
        </div>
      )}
      <div className="sheet-scan-band" aria-hidden="true" />
      <WalkingSpider targetRef={sheetRef} />
    </div>
  );
}

export function SpiderViewer({ state }: { state: ScanState }) {
  const logRef = useRef<HTMLDivElement>(null);
  const sheetRefs = useRef<Record<number, HTMLDivElement | null>>({});
  const current = state.pages[state.pages.length - 1];
  const scanning = state.phase === "scanning";
  const done = state.phase === "done";
  const chips = entityChips(current?.entities);
  const showOriginal = Boolean(state.fileUrl) && Boolean(state.scan?.file_type);

  useEffect(() => {
    const sheet = sheetRefs.current[state.currentPage];
    if (sheet && !showOriginal) {
      sheet.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }, [state.currentPage, state.pages.length, showOriginal]);

  useEffect(() => {
    if (logRef.current) {
      logRef.current.scrollTop = logRef.current.scrollHeight;
    }
  }, [state.log]);

  return (
    <section className="mx-auto max-w-[1280px] px-5 py-8 animate-fade-up">
      <div className="mb-5 flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="text-xs font-mono uppercase tracking-[0.2em] text-spider-cyan/80">
            {scanning ? "Rastreo en curso" : done ? "Rastreo completado" : "Preparando"}
          </p>
          <h2 className="mt-1 text-2xl font-bold">{state.scan?.file_name ?? "Documento"}</h2>
          <p className="mt-1 text-sm text-spider-muted">
            {done
              ? `Se rastrearon ${state.totalPages} hojas correctamente.`
              : `Escaneando Página ${Math.max(1, state.currentPage)} de ${state.totalPages || "…"}…`}
          </p>
        </div>
        <div className="text-right">
          <p className="text-3xl font-bold text-spider-cyan">{Math.round(state.progress)}%</p>
          <p className="text-xs text-spider-muted">{countEntities(current)} entidades en la hoja actual</p>
        </div>
      </div>

      <div className="mb-5 h-2 w-full overflow-hidden rounded-full bg-spider-border/60">
        <div
          className="h-full rounded-full bg-gradient-to-r from-spider-cyan to-spider-emerald transition-all duration-500"
          style={{ width: `${Math.min(100, Math.max(2, state.progress))}%` }}
        />
      </div>

      <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_360px]">
        <div className="viewer-scroll relative h-[74vh] overflow-y-auto rounded-2xl border border-spider-border bg-[#070b13] p-5 sm:p-8">
          <div className="space-y-8 pb-8">
            {showOriginal && state.fileUrl && state.scan ? (
              <OriginalViewer
                fileUrl={state.fileUrl}
                fileType={state.scan.file_type}
                fileName={state.scan.file_name}
                currentPage={state.currentPage || 1}
              />
            ) : (
              state.pages.map((page) => (
                <PaperSheet
                  key={page.page_number}
                  page={page}
                  isCurrent={page.page_number === state.currentPage}
                  showSpider={scanning}
                  registerRef={(pageNumber, element) => {
                    sheetRefs.current[pageNumber] = element;
                  }}
                />
              ))
            )}

            {!showOriginal && state.pages.length === 0 && (
              <div className="grid h-full place-items-center text-center">
                <div>
                  <p className="text-sm text-spider-muted">
                    La araña está posicionándose sobre la primera hoja…
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>

        <aside className="space-y-4">
          <div className="panel p-4">
            <div className="mb-3 flex items-center justify-between">
              <p className="text-xs font-mono uppercase tracking-[0.2em] text-spider-emerald">
                Redacción en vivo
              </p>
              <span className="flex items-center gap-2 text-[10px] uppercase tracking-widest text-spider-emerald">
                <span className="relative flex h-2 w-2">
                  <span className="absolute inline-flex h-full w-full rounded-full bg-spider-emerald opacity-70 animate-pulse-ring" />
                  <span className="relative inline-flex h-2 w-2 rounded-full bg-spider-emerald" />
                </span>
                {scanning ? "escribiendo" : "listo"}
              </span>
            </div>
            <div className="mb-3 rounded-lg border border-spider-border bg-spider-bg/70 px-3 py-2">
              <p className="font-mono text-xs text-spider-cyan">
                {current ? current.label : "Sin hoja activa"}
              </p>
            </div>
            <div key={current?.page_number ?? "empty"}>
              <TypewriterDraft text={buildDraft(current)} />
            </div>
          </div>

          <div className="panel p-4">
            <p className="mb-3 text-xs font-mono uppercase tracking-[0.2em] text-spider-cyan/80">
              Hallazgos de esta hoja
            </p>
            <div className="flex flex-wrap gap-1.5">
              {chips.length ? (
                chips.map((chip, index) => (
                  <LiveChip key={`${chip.label}-${chip.value}-${index}`} {...chip} index={index} />
                ))
              ) : (
                <span className="text-xs text-spider-muted">Aún no hay entidades resaltadas.</span>
              )}
            </div>
          </div>

          <div className="panel p-4">
            <p className="mb-3 text-xs font-mono uppercase tracking-[0.2em] text-spider-amber">
              Recorrido de la araña
            </p>
            <div className="flex flex-wrap gap-1.5">
              {Array.from({ length: state.totalPages || 0 }).map((_, index) => {
                const pageNumber = index + 1;
                const scanned = pageNumber <= state.currentPage;
                const active = pageNumber === state.currentPage && scanning;
                return (
                  <span
                    key={pageNumber}
                    title={`Página ${pageNumber}`}
                    className={`h-3 w-3 rounded-sm transition ${
                      active
                        ? "bg-spider-cyan shadow-[0_0_10px_2px_rgba(34,211,238,0.7)]"
                        : scanned
                          ? "bg-spider-emerald/70"
                          : "bg-spider-border"
                    }`}
                  />
                );
              })}
            </div>

            <div className="mt-4 grid grid-cols-3 gap-2 text-center">
              <div className="rounded-lg border border-spider-border bg-spider-bg/60 py-2">
                <p className="text-lg font-bold text-spider-cyan">{state.pages.length}</p>
                <p className="text-[10px] text-spider-muted">Hojas</p>
              </div>
              <div className="rounded-lg border border-spider-border bg-spider-bg/60 py-2">
                <p className="text-lg font-bold text-spider-emerald">{countEntities(current)}</p>
                <p className="text-[10px] text-spider-muted">Entidades</p>
              </div>
              <div className="rounded-lg border border-spider-border bg-spider-bg/60 py-2">
                <p className="text-lg font-bold text-spider-rose">{current?.entities.alerts.length ?? 0}</p>
                <p className="text-[10px] text-spider-muted">Alertas</p>
              </div>
            </div>
          </div>

          <div className="panel flex flex-col p-4">
            <p className="mb-3 text-xs font-mono uppercase tracking-[0.2em] text-spider-cyan/80">
              Log en tiempo real
            </p>
            <div
              ref={logRef}
              className="h-32 overflow-y-auto rounded-lg border border-spider-border bg-spider-bg/80 p-2 font-mono text-[10px] leading-4 text-spider-muted"
            >
              {state.log.length ? (
                state.log.map((line, index) => (
                  <p key={index} className="whitespace-pre-wrap break-words">
                    <span className="text-spider-cyan/70">›</span> {line}
                  </p>
                ))
              ) : (
                <p>Iniciando consola de rastreo…</p>
              )}
            </div>
          </div>
        </aside>
      </div>
    </section>
  );
}