import type { ScanCreated } from "./types";

export const API_BASE =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ?? "http://localhost:8000";

async function readError(response: Response): Promise<string> {
  try {
    const data = (await response.json()) as { detail?: string };
    return data.detail ?? `Error ${response.status}`;
  } catch {
    return `Error ${response.status}`;
  }
}

export async function createScan(file: File): Promise<ScanCreated> {
  const form = new FormData();
  form.append("file", file);
  const response = await fetch(`${API_BASE}/api/scan`, {
    method: "POST",
    body: form,
  });
  if (!response.ok) {
    throw new Error(await readError(response));
  }
  return (await response.json()) as ScanCreated;
}

export async function createSampleScan(): Promise<ScanCreated> {
  const response = await fetch(`${API_BASE}/api/scan/sample`, { method: "POST" });
  if (!response.ok) {
    throw new Error(await readError(response));
  }
  return (await response.json()) as ScanCreated;
}

export function streamUrl(scanId: string): string {
  return `${API_BASE}/api/scan/${scanId}/stream`;
}
