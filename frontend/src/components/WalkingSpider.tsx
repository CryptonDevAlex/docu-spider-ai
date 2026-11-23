"use client";

import { useEffect, useRef } from "react";
import type { RefObject } from "react";

interface WalkingSpiderProps {
  targetRef: RefObject<HTMLDivElement | null>;
  durationMs?: number;
}

type Leg = {
  hip: [number, number];
  k1: [number, number];
  k2: [number, number];
  tip: [number, number];
  group: "a" | "b";
};

const LEGS: Leg[] = [
  { hip: [62, 43], k1: [46, 28], k2: [24, 18], tip: [6, 12], group: "a" },
  { hip: [65, 44], k1: [52, 24], k2: [38, 8], tip: [28, -2], group: "b" },
  { hip: [69, 44], k1: [76, 24], k2: [90, 8], tip: [102, -2], group: "a" },
  { hip: [72, 43], k1: [88, 28], k2: [110, 18], tip: [128, 12], group: "b" },
  { hip: [62, 57], k1: [46, 72], k2: [24, 84], tip: [6, 92], group: "b" },
  { hip: [65, 58], k1: [52, 78], k2: [38, 96], tip: [28, 106], group: "a" },
  { hip: [69, 58], k1: [76, 78], k2: [90, 96], tip: [102, 106], group: "b" },
  { hip: [72, 57], k1: [88, 72], k2: [110, 84], tip: [128, 92], group: "a" },
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
        <svg viewBox="-10 -10 154 124" className="h-[124px] w-[154px] overflow-visible">
          <defs>
            <filter id="cyber-glow" x="-120%" y="-120%" width="340%" height="340%">
              <feGaussianBlur stdDeviation="2.8" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
            <filter id="cyber-shadow" x="-40%" y="-40%" width="180%" height="180%">
              <feGaussianBlur stdDeviation="4" />
            </filter>
            <linearGradient id="cyber-beam" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#ff5a5a" stopOpacity="0.28" />
              <stop offset="100%" stopColor="#ff5a5a" stopOpacity="0" />
            </linearGradient>
          </defs>

          <polygon points="56,60 78,60 102,120 32,120" fill="url(#cyber-beam)" opacity="0.85" />
          <ellipse cx="67" cy="70" rx="34" ry="8" fill="rgba(2,6,23,0.38)" filter="url(#cyber-shadow)" />

          {LEGS.map((leg, index) => (
            <g
              key={index}
              className={`cyber-leg ${leg.group === "a" ? "cyber-leg-a" : "cyber-leg-b"}`}
              style={{ transformOrigin: `${leg.hip[0]}px ${leg.hip[1]}px` }}
            >
              <polyline
                points={`${leg.hip[0]},${leg.hip[1]} ${leg.k1[0]},${leg.k1[1]}`}
                fill="none"
                stroke="#1e1b4b"
                strokeWidth="2.2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              <g
                className={`cyber-leg-inner ${leg.group === "a" ? "cyber-leg-inner-a" : "cyber-leg-inner-b"}`}
                style={{ transformOrigin: `${leg.k1[0]}px ${leg.k1[1]}px` }}
              >
                <polyline
                  points={`${leg.k1[0]},${leg.k1[1]} ${leg.k2[0]},${leg.k2[1]} ${leg.tip[0]},${leg.tip[1]}`}
                  fill="none"
                  stroke="#1e1b4b"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
                <circle cx={leg.k2[0]} cy={leg.k2[1]} r="2.2" fill="#fff" filter="url(#cyber-glow)" />
                <circle cx={leg.k2[0]} cy={leg.k2[1]} r="1.2" fill="#fff" />
                <circle cx={leg.tip[0]} cy={leg.tip[1]} r="2.8" fill="#fff" filter="url(#cyber-glow)" />
                <circle cx={leg.tip[0]} cy={leg.tip[1]} r="1.4" fill="#fff" />
              </g>
              <circle cx={leg.k1[0]} cy={leg.k1[1]} r="2.4" fill="#fff" filter="url(#cyber-glow)" />
              <circle cx={leg.k1[0]} cy={leg.k1[1]} r="1.3" fill="#fff" />
            </g>
          ))}

          <g className="spider-body-bob">
            <rect x="34" y="38" width="30" height="24" rx="6" fill="#18181b" stroke="#27272a" strokeWidth="1" />
            <g stroke="#f8fafc" strokeWidth="0.9" opacity="0.9">
              <path d="M 38 43 H 46 V 48 H 38 Z" fill="none" />
              <path d="M 50 43 H 60 V 48 H 50 Z" fill="none" />
              <path d="M 42 52 H 52 V 58 H 42 Z" fill="none" />
              <path d="M 46 43 V 38 M 55 48 V 52 M 47 58 V 62" fill="none" />
            </g>
            <g fill="#fff">
              <circle cx="40" cy="45" r="1.1" />
              <circle cx="44" cy="46" r="1" />
              <circle cx="53" cy="45" r="1.1" />
              <circle cx="58" cy="46" r="1" />
              <circle cx="47" cy="55" r="1.1" />
            </g>

            <ellipse cx="74" cy="50" rx="10" ry="8.5" fill="#dc2626" stroke="#7f1d1d" strokeWidth="0.8" />
            <g fill="#fff" opacity="0.85">
              <circle cx="71" cy="47" r="0.8" />
              <circle cx="74" cy="45" r="0.7" />
              <circle cx="77" cy="47" r="0.8" />
              <circle cx="72" cy="52" r="0.7" />
              <circle cx="76" cy="52" r="0.7" />
            </g>
            <path d="M 82 47 C 86 45, 88 46, 90 48" fill="none" stroke="#111827" strokeWidth="1.8" strokeLinecap="round" />
            <path d="M 82 53 C 86 55, 88 54, 90 52" fill="none" stroke="#111827" strokeWidth="1.8" strokeLinecap="round" />
          </g>
        </svg>
      </div>
    </div>
  );
}