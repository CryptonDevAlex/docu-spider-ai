import type { ScanReport } from "./types";

function baseName(report: ScanReport): string {
  const dot = report.file_name.lastIndexOf(".");
  const stem = dot > 0 ? report.file_name.slice(0, dot) : report.file_name;
  return `${stem}_informe_docuspider`;
}

export function reportToMarkdown(report: ScanReport): string {
  const lines: string[] = [];
  lines.push(`# Informe DocuSpider AI — ${report.file_name}`);
  lines.push("");
  lines.push(
    `**Formato:** ${report.file_type.toUpperCase()} · **Unidades:** ${report.total_pages} · **Motor:** ${report.provider}`,
  );
  lines.push(`**Generado:** ${new Date(report.generated_at).toLocaleString("es-ES")}`);
  lines.push("");
  lines.push("## 1. Resumen Ejecutivo");
  lines.push("");
  lines.push(report.executive_summary.overview);
  lines.push("");
  for (const section of report.executive_summary.sections) {
    lines.push(`### ${section.title}`);
    lines.push("");
    lines.push(section.content);
    lines.push("");
  }
  if (report.executive_summary.highlights.length) {
    lines.push("**Puntos clave:**");
    for (const highlight of report.executive_summary.highlights) {
      lines.push(`- ${highlight}`);
    }
    lines.push("");
  }

  lines.push("## 2. Reporte de Datos y Métricas Extraídas");
  lines.push("");
  lines.push("| Indicador | Valor | Descripción |");
  lines.push("| --- | --- | --- |");
  for (const kpi of report.data_report.kpis) {
    lines.push(`| ${kpi.label} | ${kpi.value} | ${kpi.description} |`);
  }
  lines.push("");
  lines.push("### Entidades detectadas");
  lines.push("");
  const entities = report.data_report.entities;
  lines.push(`- Fechas (${entities.dates.length}): ${entities.dates.join(", ") || "—"}`);
  lines.push(`- Montos (${entities.money.length}): ${entities.money.join(", ") || "—"}`);
  lines.push(`- Porcentajes (${entities.percentages.length}): ${entities.percentages.join(", ") || "—"}`);
  lines.push(`- Correos (${entities.emails.length}): ${entities.emails.join(", ") || "—"}`);
  lines.push(`- URLs (${entities.urls.length}): ${entities.urls.join(", ") || "—"}`);
  lines.push(`- Palabras clave: ${entities.keywords.join(", ") || "—"}`);
  lines.push("");
  if (report.data_report.table.length) {
    lines.push("### Tabla de entidades");
    lines.push("");
    lines.push("| Página | Tipo | Valor |");
    lines.push("| --- | --- | --- |");
    for (const row of report.data_report.table) {
      lines.push(`| ${row.page} | ${row.kind} | ${row.value} |`);
    }
    lines.push("");
  }

  lines.push("## 3. Auditoría y Sugerencias de Mejora");
  lines.push("");
  lines.push(`**Puntaje de calidad documental:** ${report.audit.score}/100`);
  lines.push("");
  for (const finding of report.audit.findings) {
    lines.push(`### ${finding.title} (impacto ${finding.impact})`);
    lines.push("");
    lines.push(finding.detail);
    lines.push("");
    lines.push(`**Recomendación:** ${finding.recommendation}`);
    lines.push("");
  }
  if (report.audit.strengths.length) {
    lines.push("### Fortalezas");
    for (const strength of report.audit.strengths) {
      lines.push(`- ${strength}`);
    }
    lines.push("");
  }

  lines.push("---");
  lines.push("_Informe generado automáticamente por DocuSpider AI._");
  return lines.join("\n");
}

function downloadText(fileName: string, content: string, mime: string): void {
  const blob = new Blob([content], { type: mime });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = fileName;
  document.body.appendChild(anchor);
  anchor.click();
  document.body.removeChild(anchor);
  URL.revokeObjectURL(url);
}

export function downloadMarkdown(report: ScanReport): void {
  downloadText(`${baseName(report)}.md`, reportToMarkdown(report), "text/markdown;charset=utf-8");
}

export function downloadJson(report: ScanReport): void {
  downloadText(
    `${baseName(report)}.json`,
    JSON.stringify(report, null, 2),
    "application/json;charset=utf-8",
  );
}
