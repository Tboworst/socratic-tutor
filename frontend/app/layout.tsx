import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Rung",
  description:
    "A tutor that never answers. It diagnoses your bug in silence, then walks you down five questions until you find it — and checks you found it for the right reason.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          rel="stylesheet"
          href="https://fonts.googleapis.com/css2?family=Archivo:wght@600;700;800&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap"
        />
      </head>
      <body className="min-h-screen bg-ink text-paper antialiased">{children}</body>
    </html>
  );
}
