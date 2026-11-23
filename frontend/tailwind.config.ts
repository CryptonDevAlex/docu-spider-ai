import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: [
    "./src/app/**/*.{ts,tsx}",
    "./src/components/**/*.{ts,tsx}",
    "./src/hooks/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        spider: {
          bg: "#090d16",
          panel: "#0e1524",
          panelSoft: "#121b2e",
          border: "#1c2942",
          muted: "#64748b",
          text: "#e2e8f0",
          cyan: "#22d3ee",
          emerald: "#34d399",
          amber: "#fbbf24",
          rose: "#fb7185",
          violet: "#a78bfa",
        },
      },
      fontFamily: {
        mono: ["JetBrains Mono", "Consolas", "monospace"],
      },
      keyframes: {
        "scan-sweep": {
          "0%": { transform: "translateY(-10%)", opacity: "0" },
          "10%": { opacity: "1" },
          "90%": { opacity: "1" },
          "100%": { transform: "translateY(1000%)", opacity: "0" },
        },
        float: {
          "0%, 100%": { transform: "translateY(0)" },
          "50%": { transform: "translateY(-6px)" },
        },
        "pulse-ring": {
          "0%": { transform: "scale(0.8)", opacity: "0.7" },
          "100%": { transform: "scale(2.2)", opacity: "0" },
        },
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
        "fade-up": {
          "0%": { opacity: "0", transform: "translateY(12px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
      },
      animation: {
        "scan-sweep": "scan-sweep 2.2s ease-in-out infinite",
        float: "float 3s ease-in-out infinite",
        "pulse-ring": "pulse-ring 1.8s ease-out infinite",
        shimmer: "shimmer 2.5s linear infinite",
        "fade-up": "fade-up 0.5s ease-out both",
      },
    },
  },
  plugins: [],
};

export default config;
