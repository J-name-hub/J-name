'use client';

import { weddingConfig } from "../src/config/wedding-config";
import StyledComponentsRegistry from "../src/lib/registry";
import { GlobalStyle } from "../src/styles/globalStyles";
import "./globals.css";

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ko">
      <head>
        <title>{weddingConfig.meta.title}</title>
        <meta name="description" content={weddingConfig.meta.description} />
        <meta property="og:title" content={weddingConfig.meta.title} />
        <meta property="og:description" content={weddingConfig.meta.description} />
        <meta property="og:image" content={weddingConfig.meta.ogImage} />
        <meta property="og:image:width" content="1200" />
        <meta property="og:image:height" content="630" />
        <meta property="og:image:alt" content="웨딩 청첩장" />
        <meta name="robots" content="noindex, nofollow" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=0" />
      </head>
      <body>
        <StyledComponentsRegistry>
          <GlobalStyle />
        {children}
        </StyledComponentsRegistry>
      </body>
    </html>
  );
}
