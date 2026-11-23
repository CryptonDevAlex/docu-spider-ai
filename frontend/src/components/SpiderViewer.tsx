"use client";

import { useEffect, useRef } from "react";

import type { ScanState } from "@/hooks/useScanStream";
import type { PageEvent } from "@/lib/types";
import { SpiderMark } from "./SpiderMark";

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

export function SpiderViewer({ state }: { state: ScanState }) {
  const logRef = useRef<HTMLDivElement>(null);
  const current = state.pages[state.pages.length - 1];
  const scanning = state.phase === "scanning";
  const done = state.phase === "done";

  useEffect(() => {
    if (logRef.current) {
      logRef.current.scrollTop = logRef.current.scrollHeight;
    }
  }, [state.log]);

  return (
    <section className="mx-auto max-w-6xl px-5 py-8 animate-fade-up">
      <div className="mb-5 flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="text-xs font-mono uppercase tracking-[0.2em] text-spider-cyan/80">
            {scanning ? "Rastreo en curso" : done ? "Rastreo completado" : "Preparando"}
          </p>
          <h2 className="mt-1 text-2xl font-bold">
            {state.scan?.file_name ?? "Documento"}
          </h2>
          <p className="mt-1 text-sm text-spider-muted">
            {done
              ? `Se rastrearon ${state.totalPages} unidades correctamente.`
              : `Escaneando Página ${Math.max(1, state.currentPage)} de ${state.totalPages || "…"}…`}
          </p>
        </div>
        <div className="text-right">
          <p className="text-3xl font-bold text-spider-cyan">{Math.round(state.progress)}%</p>
          <p className="text-xs text-spider-muted">
            {countEntities(current)} entidades en la última hoja
          </p>
        </div>
      </div>

      <div className="mb-6 h-2 w-full overflow-hidden rounded-full bg-spider-border/60">
        <div
          className="h-full rounded-full bg-gradient-to-r from-spider-cyan to-spider-emerald transition-all duration-500"
          style={{ width: `${Math.min(100, Math.max(2, state.progress))}%` }}
        />
      </div>

      <div className="grid gap-5 lg:grid-cols-[1.6fr_1fr]">
        {/* Animated document */}
        <div className="panel relative overflow-hidden p-5">
          <div className="mb-3 flex items-center justify-between">
            <span className="text-xs font-mono text-spider-muted">
              {current?.label ?? "Esperando primera hoja…"}
            </span>
            <span className="flex items-center gap-2 text-xs text-spider-emerald">
              <span className="relative flex h-2 w-2">
                <span className="absolute inline-flex h-full w-full rounded-full bg-spider-emerald opacity-75 animate-pulse-ring" />
                <span className="relative inline-flex h-2 w-2 rounded-full bg-spider-emerald" />
              </span>
              {scanning ? "EN VIVO" : "LISTO"}
            </span>
          </div>

          <div className="relative h-64 overflow-hidden rounded-xl border border-spider-border bg-spider-bg/80 grid-paper">
            <div className="absolute left-3 top-3 z-10 text-spider-cyan animate-float">
              <SpiderMark className="h-7 w-7" />
            </div>
            <div className="scanline top-0 animate-scan-sweep" />
            <div className="h-full overflow-hidden px-5 py-10 font-mono text-[11px] leading-6 text-spider-text/70">
              {current?.text_preview ? (
                <p className="whitespace-pre-wrap break-words">{current.text_preview}</p>
              ) : (
                <p className="text-spider-muted">
                  La araña está posicionándose sobre la primera hoja…
                </p>
              )}
            </div>
          </div>

          {/* Node map */}
          <div className="mt-4">
            <p className="mb-2 text-xs text-spider-muted">Mapa de nodos de hallazgos</p>
            <div className="flex flex-wrap gap-1.5">
              {Array.from({ length: state.totalPages || 0 }).map((_, index) => {
                const pageNumber = index + 1;
                const isScanned = pageNumber <= state.currentPage;
                const isCurrent = pageNumber === state.currentPage && scanning;
                return (
                  <span
                    key={pageNumber}
                    title={`Página ${pageNumber}`}
                    className={`h-3 w-3 rounded-sm transition ${
                      isCurrent
                        ? "bg-spider-cyan shadow-[0_0_10px_2px_rgba(34,211,238,0.7)]"
                        : isScanned
                          ? "bg-spider-emerald/70"
                          : "bg-spider-border"
                    }`}
                  />
                );
              })}
            </div>
          </div>
        </div>

        {/* Live log */}
        <div className="panel flex flex-col p-5">
          <p className="mb-3 text-xs font-mono uppercase tracking-[0.2em] text-spider-cyan/80">
            Log en tiempo real
          </p>
          <div
            ref={logRef}
            className="h-64 overflow-y-auto rounded-xl border border-spider-border bg-spider-bg/80 p-3 font-mono text-[11px] leading-5 text-spider-muted"
          >
            {state.log.length === 0 ? (
              <p className="text-spider-muted/70">Iniciando consola de rastreo…</p>
            ) : (
              state.log.map((line, index) => (
                <p key={index} className="whitespace-pre-wrap break-words">
                  <span className="text-spider-cyan/70">›</span> {line}
                </p>
              ))
            )}
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
              <p className="text-lg font-bold text-spider-amber">
                {current?.entities.alerts.length ?? 0}
              </p>
              <p className="text-[10px] text-spider-muted">Alertas</p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
