import type { Metadata } from "next";
import StyledComponentsRegistry from "@/src/lib/registry";
import { weddingConfig } from "@/src/config/wedding-config";
import "./globals.css";

export const metadata: Metadata = {
  title: weddingConfig.meta.title,
  description: weddingConfig.meta.description,
  openGraph: {
    title: weddingConfig.meta.title,
    description: weddingConfig.meta.description,
    images: [weddingConfig.meta.ogImage]
  },
  robots: weddingConfig.meta.noIndex ? { index: false, follow: false } : undefined
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko">
      <body>
        <StyledComponentsRegistry>{children}</StyledComponentsRegistry>
      </body>
    </html>
  );
}
