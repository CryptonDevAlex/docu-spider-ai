import { API_BASE } from "./api";
import type { ScanReport } from "./types";

function baseName(report: ScanReport): string {
  const dot = report.file_name.lastIndexOf(".");
  const stem = dot > 0 ? report.file_name.slice(0, dot) : report.file_name;
  return `${stem}_informe_docuspider`;
}

function saveBlob(fileName: string, blob: Blob): void {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = fileName;
  document.body.appendChild(anchor);
  anchor.click();
  document.body.removeChild(anchor);
  URL.revokeObjectURL(url);
}

async function postReport(path: string, report: ScanReport): Promise<Blob> {
  const response = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(report),
  });
  if (!response.ok) {
    let detail = `Error ${response.status}`;
    try {
      const data = (await response.json()) as { detail?: string };
      if (data.detail) detail = data.detail;
    } catch {
      // ignore non-JSON error bodies
    }
    throw new Error(detail);
  }
  return response.blob();
}

export async function downloadDocx(report: ScanReport): Promise<void> {
  const blob = await postReport("/api/export/docx", report);
  saveBlob(`${baseName(report)}.docx`, blob);
}

export async function downloadPdf(report: ScanReport): Promise<void> {
  const blob = await postReport("/api/export/pdf", report);
  saveBlob(`${baseName(report)}.pdf`, blob);
}
