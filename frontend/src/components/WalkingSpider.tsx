"use client";

import { useEffect, useRef } from "react";
import type { RefObject } from "react";

interface WalkingSpiderProps {
  targetRef: RefObject<HTMLDivElement | null>;
  durationMs?: number;
}

const LEFT_LEGS = [
  [30, 26, 18, 18, 5, 26],
  [30, 28, 15, 22, 2, 34],
  [30, 30, 14, 30, 3, 44],
  [30, 32, 18, 39, 8, 52],
];

const RIGHT_LEGS = [
  [34, 26, 46, 18, 59, 26],
  [34, 28, 49, 22, 62, 34],
  [34, 30, 50, 30, 61, 44],
  [34, 32, 46, 39, 56, 52],
];

export function WalkingSpider({ targetRef, durationMs = 1700 }: WalkingSpiderProps) {
  const outerRef = useRef<HTMLDivElement>(null);
  const innerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let frame = 0;
    let start: number | null = null;
    const rows = 11;

    const animate = (timestamp: number) => {
      if (start === null) start = timestamp;
      const target = targetRef.current;
      const outer = outerRef.current;
      const inner = innerRef.current;

      if (target && outer && inner) {
        const width = target.offsetWidth;
        const height = target.offsetHeight;
        const elapsed = (timestamp - start) % durationMs;
        const progress = elapsed / durationMs;
        const rowFloat = progress * rows;
        const row = Math.min(rows - 1, Math.floor(rowFloat));
        const fraction = rowFloat - row;
        const direction = row % 2 === 0 ? 1 : -1;
        const xRatio = direction === 1 ? 0.08 + fraction * 0.84 : 0.92 - fraction * 0.84;
        const yRatio = 0.07 + (row / (rows - 1)) * 0.86;
        const x = xRatio * width;
        const y = yRatio * height;

        outer.style.transform = `translate3d(${x}px, ${y}px, 0)`;
        inner.style.transform = `translate(-50%, -50%) scaleX(${direction})`;
        target.style.setProperty("--scan-y", `${y}px`);
      }

      frame = requestAnimationFrame(animate);
    };

    frame = requestAnimationFrame(animate);
    return () => {
      cancelAnimationFrame(frame);
      targetRef.current?.style.removeProperty("--scan-y");
    };
  }, [durationMs, targetRef]);

  return (
    <div ref={outerRef} className="walking-spider-outer" aria-hidden="true">
      <div ref={innerRef} className="walking-spider-inner">
        <svg viewBox="0 0 64 62" className="h-[62px] w-[64px] overflow-visible">
          <defs>
            <linearGradient id="spiderBody" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#4b5563" />
              <stop offset="55%" stopColor="#1f2937" />
              <stop offset="100%" stopColor="#020617" />
            </linearGradient>
            <linearGradient id="spiderBeam" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#22d3ee" stopOpacity="0.34" />
              <stop offset="100%" stopColor="#22d3ee" stopOpacity="0" />
            </linearGradient>
            <filter id="spiderSoftShadow" x="-50%" y="-50%" width="200%" height="200%">
              <feGaussianBlur stdDeviation="2.4" />
            </filter>
            <filter id="spiderGlow" x="-50%" y="-50%" width="200%" height="200%">
              <feGaussianBlur stdDeviation="1.3" />
            </filter>
          </defs>

          <polygon points="25,44 39,44 54,92 10,92" fill="url(#spiderBeam)" opacity="0.75" />
          <ellipse
            cx="32"
            cy="55"
            rx="17"
            ry="4"
            fill="rgba(2, 6, 23, 0.42)"
            filter="url(#spiderSoftShadow)"
          />

          {LEFT_LEGS.map((leg, index) => (
            <g
              key={`left-${index}`}
              className={`spider-leg ${index % 2 === 0 ? "spider-leg-a" : "spider-leg-b"}`}
              style={{ transformOrigin: `${leg[0]}px ${leg[1]}px` }}
            >
              <path
                d={`M ${leg[0]} ${leg[1]} L ${leg[2]} ${leg[3]} L ${leg[4]} ${leg[5]}`}
                fill="none"
                stroke="#020617"
                strokeWidth="1.6"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              <circle cx={leg[2]} cy={leg[3]} r="1.2" fill="#111827" />
            </g>
          ))}

          {RIGHT_LEGS.map((leg, index) => (
            <g
              key={`right-${index}`}
              className={`spider-leg ${index % 2 === 0 ? "spider-leg-b" : "spider-leg-a"}`}
              style={{ transformOrigin: `${leg[0]}px ${leg[1]}px` }}
            >
              <path
                d={`M ${leg[0]} ${leg[1]} L ${leg[2]} ${leg[3]} L ${leg[4]} ${leg[5]}`}
                fill="none"
                stroke="#020617"
                strokeWidth="1.6"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              <circle cx={leg[2]} cy={leg[3]} r="1.2" fill="#111827" />
            </g>
          ))}

          <g className="spider-body-bob">
            <ellipse cx="32" cy="38" rx="10" ry="14" fill="url(#spiderBody)" stroke="#020617" strokeWidth="0.8" />
            <ellipse cx="32" cy="37" rx="6" ry="9" fill="#334155" opacity="0.35" />
            <circle cx="32" cy="25" r="7.5" fill="url(#spiderBody)" stroke="#020617" strokeWidth="0.8" />
            <circle cx="29.5" cy="23" r="1.5" fill="#22d3ee" filter="url(#spiderGlow)" />
            <circle cx="34.5" cy="23" r="1.5" fill="#22d3ee" filter="url(#spiderGlow)" />
            <circle cx="29.5" cy="23" r="0.8" fill="#e2e8f0" />
            <circle cx="34.5" cy="23" r="0.8" fill="#e2e8f0" />
            <path d="M 28 31 L 24 34 M 36 31 L 40 34" stroke="#0f172a" strokeWidth="1.1" strokeLinecap="round" />
          </g>
        </svg>
      </div>
    </div>
  );
}
