import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "UAE Legal Agent",
  description: "Local RAG assistant for UAE legal research.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-Hans">
      <body>{children}</body>
    </html>
  );
}
