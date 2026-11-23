import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "DocuSpider AI — Rastreo Documental Inteligente",
  description:
    "Rastreador visual multiformato de documentos con streaming en tiempo real e informes de auditoría con inteligencia artificial.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es" className="dark">
      <body className="min-h-screen bg-spider-bg text-spider-text antialiased">
        <div className="pointer-events-none fixed inset-0 -z-10 bg-[radial-gradient(ellipse_at_top,rgba(34,211,238,0.12),transparent_55%),radial-gradient(ellipse_at_bottom_right,rgba(52,211,153,0.10),transparent_50%)]" />
        {children}
      </body>
    </html>
  );
}
