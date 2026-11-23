export function SpiderMark({ className = "h-9 w-9" }: { className?: string }) {
  return (
    <svg viewBox="0 0 64 64" fill="none" className={className} aria-hidden="true">
      <g stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
        <path d="M32 22v-8M32 22l-9-6M32 22l9-6M32 28l-11-2M32 28l11-2M32 36l-11 2M32 36l11 2M32 40l-8 9M32 40l8 9" />
      </g>
      <ellipse cx="32" cy="30" rx="7" ry="9" fill="currentColor" opacity="0.9" />
      <circle cx="32" cy="18" r="4" fill="currentColor" />
    </svg>
  );
}
