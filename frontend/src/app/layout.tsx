import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "OmniAgent",
  description: "Multimodal agentic AI system",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
