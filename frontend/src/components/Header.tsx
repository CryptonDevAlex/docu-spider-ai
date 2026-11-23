import { SpiderMark } from "./SpiderMark";

export function Header({ provider }: { provider?: string | null }) {
  return (
    <header className="border-b border-spider-border/70 bg-spider-bg/70 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-5 py-4">
        <div className="flex items-center gap-3">
          <span className="grid h-11 w-11 place-items-center rounded-xl border border-spider-cyan/40 bg-spider-cyan/10 text-spider-cyan glow-cyan">
            <SpiderMark className="h-6 w-6" />
          </span>
          <div>
            <h1 className="text-lg font-bold tracking-tight">
              DocuSpider <span className="text-spider-cyan">AI</span>
            </h1>
            <p className="text-xs text-spider-muted">
              Rastreador visual multiformato &amp; motor de auditoría documental
            </p>
          </div>
        </div>

        <div className="hidden items-center gap-3 sm:flex">
          <span className="rounded-full border border-spider-emerald/40 bg-spider-emerald/10 px-3 py-1 text-xs font-medium text-spider-emerald">
            Motor: {provider ?? "local"}
          </span>
          <a
            href="https://github.com/CryptonDevAlex/docu-spider-ai"
            target="_blank"
            rel="noreferrer"
            className="rounded-full border border-spider-border px-3 py-1 text-xs font-medium text-spider-muted transition hover:border-spider-cyan/50 hover:text-spider-cyan"
          >
            GitHub
          </a>
        </div>
      </div>
    </header>
  );
}
