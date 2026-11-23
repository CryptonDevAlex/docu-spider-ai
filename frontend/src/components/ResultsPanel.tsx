"use client";

import { useMemo, useState } from "react";

import type { AuditFinding, ScanReport } from "@/lib/types";
import { downloadDocx, downloadPdf } from "@/lib/report";

type TabKey = "resumen" | "datos" | "auditoria";

const TABS: { key: TabKey; label: string }[] = [
  { key: "resumen", label: "Resumen Ejecutivo" },
  { key: "datos", label: "Datos Extraídos" },
  { key: "auditoria", label: "Auditoría y Mejoras" },
];

const IMPACT_STYLE: Record<AuditFinding["impact"], string> = {
  alto: "border-spider-rose/40 bg-spider-rose/10 text-spider-rose",
  medio: "border-spider-amber/40 bg-spider-amber/10 text-spider-amber",
  bajo: "border-spider-emerald/40 bg-spider-emerald/10 text-spider-emerald",
};

function ScoreRing({ score }: { score: number }) {
  const color = score >= 80 ? "#34d399" : score >= 60 ? "#fbbf24" : "#fb7185";
  return (
    <div
      className="grid h-24 w-24 place-items-center rounded-full"
      style={{
        background: `conic-gradient(${color} ${score * 3.6}deg, #1c2942 0deg)`,
      }}
    >
      <div className="grid h-[76px] w-[76px] place-items-center rounded-full bg-spider-panel">
        <div className="text-center">
          <p className="text-2xl font-bold" style={{ color }}>
            {score}
          </p>
          <p className="text-[10px] text-spider-muted">/ 100</p>
        </div>
      </div>
    </div>
  );
}

export function ResultsPanel({
  report,
  onReset,
}: {
  report: ScanReport;
  onReset: () => void;
}) {
  const [tab, setTab] = useState<TabKey>("resumen");
  const [query, setQuery] = useState("");
  const [kind, setKind] = useState("todos");
  const [exporting, setExporting] = useState<"docx" | "pdf" | null>(null);
  const [exportError, setExportError] = useState<string | null>(null);

  const kinds = useMemo(() => {
    const set = new Set(report.data_report.table.map((row) => row.kind));
    return ["todos", ...Array.from(set)];
  }, [report]);

  const rows = useMemo(() => {
    return report.data_report.table.filter((row) => {
      const matchesKind = kind === "todos" || row.kind === kind;
      const matchesQuery =
        !query ||
        row.value.toLowerCase().includes(query.toLowerCase()) ||
        row.context.toLowerCase().includes(query.toLowerCase());
      return matchesKind && matchesQuery;
    });
  }, [report, query, kind]);

  const entities = report.data_report.entities;
  const conclusions = report.executive_summary.conclusions ?? [];
  const criticalFindings = report.executive_summary.critical_findings ?? [];

  async function handleExport(target: "docx" | "pdf") {
    setExportError(null);
    setExporting(target);
    try {
      if (target === "docx") {
        await downloadDocx(report);
      } else {
        await downloadPdf(report);
      }
    } catch (error) {
      setExportError(
        error instanceof Error ? error.message : "No se pudo generar el archivo. Inténtalo de nuevo.",
      );
    } finally {
      setExporting(null);
    }
  }

  return (
    <section className="mx-auto max-w-6xl px-5 pb-16 pt-4 animate-fade-up">
      <div className="panel mb-5 flex flex-wrap items-center justify-between gap-4 p-5">
        <div className="flex items-center gap-4">
          <ScoreRing score={report.audit.score} />
          <div>
            <p className="text-xs font-mono uppercase tracking-[0.2em] text-spider-emerald">
              Informe de inteligencia
            </p>
            <h2 className="text-xl font-bold">{report.file_name}</h2>
            <p className="mt-1 text-xs text-spider-muted">
              {report.file_type.toUpperCase()} · {report.total_pages} unidades · Motor: {report.provider} ·{" "}
              {new Date(report.generated_at).toLocaleString("es-ES")}
            </p>
          </div>
        </div>

        <div className="no-print flex flex-col items-end gap-2">
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={() => handleExport("docx")}
              disabled={exporting !== null}
              className="flex items-center gap-2 rounded-lg border border-spider-cyan/40 bg-spider-cyan/10 px-4 py-2.5 text-xs font-semibold text-spider-cyan transition hover:brightness-110 disabled:opacity-50"
            >
              <span aria-hidden="true">📄</span>
              {exporting === "docx" ? "Generando…" : "Descargar Word (.docx)"}
            </button>
            <button
              type="button"
              onClick={() => handleExport("pdf")}
              disabled={exporting !== null}
              className="flex items-center gap-2 rounded-lg border border-spider-rose/40 bg-spider-rose/10 px-4 py-2.5 text-xs font-semibold text-spider-rose transition hover:brightness-110 disabled:opacity-50"
            >
              <span aria-hidden="true">📑</span>
              {exporting === "pdf" ? "Generando…" : "Descargar PDF (.pdf)"}
            </button>
            <button
              type="button"
              onClick={onReset}
              className="rounded-lg bg-gradient-to-r from-spider-cyan to-spider-emerald px-4 py-2.5 text-xs font-bold text-spider-bg transition hover:brightness-110"
            >
              Nuevo análisis
            </button>
          </div>
          {exportError && (
            <p className="text-xs text-spider-rose">{exportError}</p>
          )}
        </div>
      </div>

      <div className="no-print mb-5 flex flex-wrap gap-1 rounded-xl border border-spider-border bg-spider-panel/60 p-1">
        {TABS.map((item) => (
          <button
            key={item.key}
            type="button"
            onClick={() => setTab(item.key)}
            className={`tab-button ${tab === item.key ? "tab-button-active" : ""}`}
          >
            {item.label}
          </button>
        ))}
      </div>

      {tab === "resumen" && (
        <div className="grid gap-5 lg:grid-cols-3">
          <div className="space-y-5 lg:col-span-2">
            <div className="panel p-6">
              <h3 className="mb-3 text-sm font-mono uppercase tracking-[0.2em] text-spider-cyan">
                Visión general y propósito
              </h3>
              <p className="text-sm leading-7 text-spider-text/85">{report.executive_summary.overview}</p>
              {report.executive_summary.purpose && (
                <p className="mt-3 rounded-xl border border-spider-cyan/20 bg-spider-cyan/5 p-3 text-sm leading-6 text-spider-cyan/90">
                  {report.executive_summary.purpose}
                </p>
              )}
            </div>

            <div className="panel p-6">
              <div className="mb-4 flex items-center justify-between">
                <h3 className="text-sm font-mono uppercase tracking-[0.2em] text-spider-cyan">
                  Desglose por secciones y páginas
                </h3>
                <span className="rounded-full border border-spider-border px-2 py-0.5 text-[10px] text-spider-muted">
                  {report.executive_summary.sections.length} secciones
                </span>
              </div>

              <div className="space-y-4">
                {report.executive_summary.sections.map((section, index) => (
                  <div
                    key={`${section.title}-${index}`}
                    className="rounded-xl border border-spider-border bg-spider-bg/50 p-4"
                  >
                    <p className="text-sm font-semibold text-spider-cyan">{section.title}</p>
                    <p className="mt-1 text-sm leading-6 text-spider-text/75">{section.content}</p>

                    {section.metrics && section.metrics.length > 0 && (
                      <div className="mt-3 flex flex-wrap gap-2">
                        {section.metrics.map((metric) => (
                          <span
                            key={metric.label}
                            className="rounded-md border border-spider-emerald/30 bg-spider-emerald/5 px-2 py-1 text-[11px] text-spider-emerald"
                          >
                            {metric.label}: <span className="font-bold">{metric.value}</span>
                          </span>
                        ))}
                      </div>
                    )}

                    {section.bullets && section.bullets.length > 0 && (
                      <ul className="mt-3 space-y-1.5">
                        {section.bullets.map((bullet, bulletIndex) => (
                          <li
                            key={`${bullet}-${bulletIndex}`}
                            className="flex gap-2 text-xs leading-5 text-spider-text/70"
                          >
                            <span className="mt-0.5 text-spider-cyan">▸</span>
                            <span>{bullet}</span>
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="space-y-5">
            <div className="panel p-6">
              <h3 className="mb-3 text-sm font-mono uppercase tracking-[0.2em] text-spider-emerald">
                Conclusiones clave
              </h3>
              <ul className="space-y-3">
                {conclusions.length === 0 ? (
                  <li className="text-sm text-spider-muted">Sin conclusiones adicionales.</li>
                ) : (
                  conclusions.map((conclusion, index) => (
                    <li key={index} className="flex gap-2 text-sm leading-6 text-spider-text/80">
                      <span className="mt-1 text-spider-emerald">◆</span>
                      <span>{conclusion}</span>
                    </li>
                  ))
                )}
              </ul>
            </div>

            <div className="panel border-spider-rose/30 p-6">
              <h3 className="mb-3 text-sm font-mono uppercase tracking-[0.2em] text-spider-rose">
                Hallazgos críticos
              </h3>
              <ul className="space-y-3">
                {criticalFindings.map((finding, index) => (
                  <li
                    key={index}
                    className="rounded-lg border border-spider-rose/25 bg-spider-rose/5 p-3 text-sm leading-6 text-spider-text/85"
                  >
                    {finding}
                  </li>
                ))}
              </ul>
            </div>

            <div className="panel p-6">
              <h3 className="mb-3 text-sm font-mono uppercase tracking-[0.2em] text-spider-amber">
                Puntos clave
              </h3>
              <ul className="space-y-2">
                {report.executive_summary.highlights.map((highlight, index) => (
                  <li key={index} className="flex gap-2 text-xs leading-5 text-spider-text/75">
                    <span className="text-spider-amber">•</span>
                    <span>{highlight}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}

      {tab === "datos" && (
        <div className="space-y-5">
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
            {report.data_report.kpis.map((kpi) => (
              <div key={kpi.label} className="panel p-4">
                <p className="text-xs text-spider-muted">{kpi.label}</p>
                <p className="mt-1 text-2xl font-bold text-spider-cyan">{kpi.value}</p>
                <p className="mt-1 text-[11px] leading-4 text-spider-muted">{kpi.description}</p>
              </div>
            ))}
          </div>

          <div className="panel p-5">
            <h3 className="mb-3 text-sm font-mono uppercase tracking-[0.2em] text-spider-cyan">
              Entidades detectadas
            </h3>
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
              {[
                { label: "Fechas", items: entities.dates, color: "text-spider-cyan" },
                { label: "Montos", items: entities.money, color: "text-spider-emerald" },
                { label: "Porcentajes", items: entities.percentages, color: "text-spider-amber" },
                { label: "Correos", items: entities.emails, color: "text-spider-violet" },
                { label: "URLs", items: entities.urls, color: "text-spider-cyan" },
                { label: "Palabras clave", items: entities.keywords, color: "text-spider-text" },
                { label: "Alertas", items: entities.alerts, color: "text-spider-rose" },
              ].map((group) => (
                <div key={group.label} className="rounded-xl border border-spider-border bg-spider-bg/50 p-3">
                  <p className={`mb-2 text-xs font-semibold ${group.color}`}>
                    {group.label} ({group.items.length})
                  </p>
                  <div className="flex flex-wrap gap-1">
                    {group.items.length === 0 ? (
                      <span className="text-[11px] text-spider-muted">—</span>
                    ) : (
                      group.items.slice(0, 8).map((item, index) => (
                        <span
                          key={`${item}-${index}`}
                          className="rounded bg-spider-border/60 px-1.5 py-0.5 text-[10px] font-mono text-spider-text/80"
                        >
                          {item}
                        </span>
                      ))
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="panel p-5">
            <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
              <h3 className="text-sm font-mono uppercase tracking-[0.2em] text-spider-cyan">
                Tabla de entidades ({rows.length})
              </h3>
              <div className="no-print flex gap-2">
                <input
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
                  placeholder="Buscar valor o contexto…"
                  className="w-56 rounded-lg border border-spider-border bg-spider-bg/70 px-3 py-1.5 text-xs text-spider-text outline-none focus:border-spider-cyan/60"
                />
                <select
                  value={kind}
                  onChange={(event) => setKind(event.target.value)}
                  className="rounded-lg border border-spider-border bg-spider-bg/70 px-2 py-1.5 text-xs text-spider-text outline-none focus:border-spider-cyan/60"
                >
                  {kinds.map((option) => (
                    <option key={option} value={option}>
                      {option}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="max-h-80 overflow-auto rounded-xl border border-spider-border">
              <table className="w-full border-collapse text-left text-xs">
                <thead className="sticky top-0 bg-spider-panelSoft text-spider-muted">
                  <tr>
                    <th className="px-3 py-2 font-semibold">Pág.</th>
                    <th className="px-3 py-2 font-semibold">Tipo</th>
                    <th className="px-3 py-2 font-semibold">Valor</th>
                    <th className="px-3 py-2 font-semibold">Contexto</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.length === 0 ? (
                    <tr>
                      <td colSpan={4} className="px-3 py-6 text-center text-spider-muted">
                        No hay entidades que coincidan con el filtro.
                      </td>
                    </tr>
                  ) : (
                    rows.map((row, index) => (
                      <tr key={index} className="border-t border-spider-border/60 hover:bg-spider-border/20">
                        <td className="px-3 py-2 font-mono text-spider-cyan">{row.page}</td>
                        <td className="px-3 py-2 capitalize text-spider-muted">{row.kind}</td>
                        <td className="px-3 py-2 font-mono text-spider-emerald">{row.value}</td>
                        <td className="max-w-[340px] truncate px-3 py-2 text-spider-muted">{row.context}</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {tab === "auditoria" && (
        <div className="grid gap-5 lg:grid-cols-3">
          <div className="space-y-3">
            {report.audit.findings.map((finding, index) => (
              <div key={index} className="panel p-4">
                <div className="mb-2 flex items-center justify-between gap-2">
                  <p className="text-sm font-semibold text-spider-text">{finding.title}</p>
                  <span className={`rounded-full border px-2 py-0.5 text-[10px] font-bold uppercase ${IMPACT_STYLE[finding.impact]}`}>
                    {finding.impact}
                  </span>
                </div>
                <p className="text-xs leading-5 text-spider-text/75">{finding.detail}</p>
                <p className="mt-2 rounded-lg border border-spider-cyan/20 bg-spider-cyan/5 p-2 text-xs leading-5 text-spider-cyan/90">
                  <span className="font-semibold">Recomendación: </span>
                  {finding.recommendation}
                </p>
              </div>
            ))}
            {report.audit.findings.length === 0 && (
              <div className="panel p-6 text-center text-sm text-spider-emerald">
                No se detectaron problemas relevantes.
              </div>
            )}
          </div>

          <div className="panel p-6 lg:col-span-2">
            <h3 className="mb-3 text-sm font-mono uppercase tracking-[0.2em] text-spider-emerald">
              Fortalezas del documento
            </h3>
            <ul className="space-y-3">
              {report.audit.strengths.map((strength, index) => (
                <li key={index} className="flex gap-2 text-sm leading-6 text-spider-text/80">
                  <span className="mt-0.5 text-spider-emerald">✓</span>
                  <span>{strength}</span>
                </li>
              ))}
            </ul>
            <div className="mt-6 rounded-xl border border-spider-border bg-spider-bg/50 p-4">
              <p className="text-xs text-spider-muted">Puntaje de calidad documental</p>
              <div className="mt-2 h-2 w-full overflow-hidden rounded-full bg-spider-border/60">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-spider-cyan to-spider-emerald"
                  style={{ width: `${report.audit.score}%` }}
                />
              </div>
              <p className="mt-2 text-sm font-semibold text-spider-text">
                {report.audit.score}/100 ·{" "}
                {report.audit.score >= 80
                  ? "Excelente"
                  : report.audit.score >= 60
                    ? "Aceptable con mejoras"
                    : "Requiere atención"}
              </p>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
