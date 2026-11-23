"use client";

import { useRef, useState } from "react";

import { SpiderMark } from "./SpiderMark";

const ACCEPTED = ".pdf,.docx,.xlsx,.csv,.txt";
const FORMATS = [
  { ext: "PDF", color: "text-spider-rose" },
  { ext: "DOCX", color: "text-spider-cyan" },
  { ext: "XLSX", color: "text-spider-emerald" },
  { ext: "CSV", color: "text-spider-amber" },
  { ext: "TXT", color: "text-spider-violet" },
];

interface UploadZoneProps {
  onFile: (file: File) => void;
  onSample: () => void;
  busy: boolean;
}

export function UploadZone({ onFile, onSample, busy }: UploadZoneProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);

  const handleDrop = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setDragging(false);
    if (busy) return;
    const file = event.dataTransfer.files?.[0];
    if (file) onFile(file);
  };

  const handleSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) onFile(file);
    event.target.value = "";
  };

  return (
    <section className="mx-auto max-w-3xl px-5 py-14 animate-fade-up">
      <div className="mb-8 text-center">
        <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
          Rastrea cualquier documento con una <span className="text-spider-cyan">araña visual</span>
        </h2>
        <p className="mx-auto mt-3 max-w-xl text-sm text-spider-muted">
          Sube un PDF, DOCX, XLSX, CSV o TXT y observa en tiempo real cómo la araña recorre cada hoja,
          extrae entidades y genera un informe de auditoría en español.
        </p>
      </div>

      <div
        onDragOver={(event) => {
          event.preventDefault();
          if (!busy) setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
        onClick={() => !busy && inputRef.current?.click()}
        role="button"
        tabIndex={0}
        onKeyDown={(event) => {
          if ((event.key === "Enter" || event.key === " ") && !busy) inputRef.current?.click();
        }}
        className={`group relative cursor-pointer rounded-3xl border-2 border-dashed p-10 text-center transition ${
          dragging
            ? "border-spider-cyan bg-spider-cyan/5 glow-cyan"
            : "border-spider-border bg-spider-panel/60 hover:border-spider-cyan/50 hover:bg-spider-panel"
        } ${busy ? "pointer-events-none opacity-60" : ""}`}
      >
        <input
          ref={inputRef}
          type="file"
          accept={ACCEPTED}
          onChange={handleSelect}
          className="hidden"
        />
        <div className="mx-auto mb-5 grid h-16 w-16 place-items-center rounded-2xl border border-spider-cyan/30 bg-spider-cyan/10 text-spider-cyan animate-float">
          <SpiderMark className="h-9 w-9" />
        </div>
        <p className="text-base font-semibold">
          Arrastra y suelta tu documento aquí
        </p>
        <p className="mt-1 text-sm text-spider-muted">
          o haz clic para seleccionar un archivo
        </p>

        <div className="mt-6 flex flex-wrap items-center justify-center gap-2">
          {FORMATS.map((format) => (
            <span
              key={format.ext}
              className={`rounded-md border border-spider-border bg-spider-bg/60 px-2.5 py-1 text-xs font-mono font-semibold ${format.color}`}
            >
              {format.ext}
            </span>
          ))}
        </div>
      </div>

      <div className="mt-6 flex flex-col items-center gap-3">
        <button
          type="button"
          onClick={onSample}
          disabled={busy}
          className="rounded-xl bg-gradient-to-r from-spider-cyan to-spider-emerald px-6 py-3 text-sm font-bold text-spider-bg transition hover:brightness-110 disabled:opacity-60"
        >
          Probar con Documento de Ejemplo
        </button>
        <p className="text-xs text-spider-muted">
          Carga un contrato técnico de 9 páginas en español y ejecuta el escaneo completo al instante.
        </p>
      </div>
    </section>
  );
}
