"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { createSampleScan, createScan, streamUrl } from "@/lib/api";
import type { PageEvent, ScanCreated, ScanReport, StreamEvent } from "@/lib/types";

export type ScanPhase = "idle" | "uploading" | "scanning" | "done" | "error";

export interface ScanState {
  phase: ScanPhase;
  scan: ScanCreated | null;
  currentPage: number;
  totalPages: number;
  progress: number;
  pages: PageEvent[];
  log: string[];
  report: ScanReport | null;
  error: string | null;
}

const INITIAL_STATE: ScanState = {
  phase: "idle",
  scan: null,
  currentPage: 0,
  totalPages: 0,
  progress: 0,
  pages: [],
  log: [],
  report: null,
  error: null,
};

export function useScanStream() {
  const [state, setState] = useState<ScanState>(INITIAL_STATE);
  const sourceRef = useRef<EventSource | null>(null);
  const finishedRef = useRef(false);

  const closeSource = useCallback(() => {
    sourceRef.current?.close();
    sourceRef.current = null;
  }, []);

  useEffect(() => closeSource, [closeSource]);

  const appendLog = useCallback((line: string) => {
    const stamp = new Date().toLocaleTimeString("es-ES", { hour12: false });
    setState((prev) => ({ ...prev, log: [...prev.log.slice(-120), `[${stamp}] ${line}`] }));
  }, []);

  const beginStream = useCallback(
    (scan: ScanCreated) => {
      finishedRef.current = false;
      setState((prev) => ({
        ...prev,
        phase: "scanning",
        scan,
        totalPages: scan.total_pages,
        currentPage: 0,
        progress: 0,
        pages: [],
        report: null,
        error: null,
      }));

      const source = new EventSource(streamUrl(scan.scan_id));
      sourceRef.current = source;

      source.onmessage = (event) => {
        let data: StreamEvent;
        try {
          data = JSON.parse(event.data) as StreamEvent;
        } catch {
          return;
        }

        if (data.type === "status") {
          appendLog(data.message);
        } else if (data.type === "page") {
          setState((prev) => ({
            ...prev,
            currentPage: data.page_number,
            totalPages: data.total_pages,
            progress: data.progress,
            pages: [...prev.pages, data],
          }));
          const found =
            data.entities.dates.length +
            data.entities.money.length +
            data.entities.percentages.length +
            data.entities.emails.length +
            data.entities.urls.length;
          appendLog(
            `${data.label}: ${found} entidades · ${data.entities.alerts.length} alertas (${Math.round(data.progress)}%)`,
          );
        } else if (data.type === "done") {
          finishedRef.current = true;
          closeSource();
          setState((prev) => ({
            ...prev,
            phase: "done",
            report: data.report,
            progress: 100,
            currentPage: data.report.total_pages,
            totalPages: data.report.total_pages,
          }));
          appendLog("Informe de inteligencia generado correctamente.");
        } else if (data.type === "error") {
          finishedRef.current = true;
          closeSource();
          setState((prev) => ({ ...prev, phase: "error", error: data.message }));
          appendLog(`Error: ${data.message}`);
        }
      };

      source.onerror = () => {
        if (finishedRef.current) return;
        closeSource();
        setState((prev) =>
          prev.phase === "done"
            ? prev
            : { ...prev, phase: "error", error: "Se perdió la conexión con el motor de rastreo." },
        );
      };
    },
    [appendLog, closeSource],
  );

  const startFromFile = useCallback(
    async (file: File) => {
      closeSource();
      setState({ ...INITIAL_STATE, phase: "uploading" });
      try {
        appendLog(`Subiendo «${file.name}»...`);
        const scan = await createScan(file);
        appendLog(`Documento aceptado: ${scan.total_pages} unidades detectadas.`);
        beginStream(scan);
      } catch (error) {
        const message = error instanceof Error ? error.message : "Error desconocido.";
        setState((prev) => ({ ...prev, phase: "error", error: message }));
        appendLog(`Error: ${message}`);
      }
    },
    [appendLog, beginStream, closeSource],
  );

  const startSample = useCallback(async () => {
    closeSource();
    setState({ ...INITIAL_STATE, phase: "uploading" });
    try {
      appendLog("Cargando documento de ejemplo...");
      const scan = await createSampleScan();
      appendLog(`Ejemplo listo: ${scan.total_pages} unidades. Iniciando araña...`);
      beginStream(scan);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Error desconocido.";
      setState((prev) => ({ ...prev, phase: "error", error: message }));
      appendLog(`Error: ${message}`);
    }
  }, [appendLog, beginStream, closeSource]);

  const reset = useCallback(() => {
    closeSource();
    finishedRef.current = false;
    setState(INITIAL_STATE);
  }, [closeSource]);

  return { state, startFromFile, startSample, reset };
}
