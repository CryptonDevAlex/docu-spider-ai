"use client";

import { Header } from "@/components/Header";
import { ResultsPanel } from "@/components/ResultsPanel";
import { SpiderViewer } from "@/components/SpiderViewer";
import { UploadZone } from "@/components/UploadZone";
import { useScanStream } from "@/hooks/useScanStream";

export default function Home() {
  const { state, startFromFile, startSample, reset } = useScanStream();

  const showUpload = state.phase === "idle" || state.phase === "error";
  const showViewer = state.phase === "uploading" || state.phase === "scanning" || state.phase === "done";

  return (
    <div className="min-h-screen">
      <Header provider={state.report?.provider ?? state.scan?.file_type ?? null} />

      {state.phase === "error" && state.error && (
        <div className="mx-auto mt-6 max-w-3xl px-5">
          <div className="rounded-xl border border-spider-rose/40 bg-spider-rose/10 px-4 py-3 text-sm text-spider-rose">
            <span className="font-semibold">No se pudo completar el rastreo: </span>
            {state.error}
          </div>
        </div>
      )}

      {showUpload && (
        <UploadZone
          onFile={startFromFile}
          onSample={startSample}
          busy={state.phase === "uploading"}
        />
      )}

      {showViewer && <SpiderViewer state={state} />}

      {state.phase === "done" && state.report && (
        <ResultsPanel report={state.report} onReset={reset} />
      )}

      {showUpload && (
        <footer className="mx-auto max-w-3xl px-5 pb-10 text-center text-xs text-spider-muted">
          DocuSpider AI · Motor offline gratuito (LLM_PROVIDER=local) · Soporta PDF, DOCX, XLSX, CSV y TXT
        </footer>
      )}
    </div>
  );
}
