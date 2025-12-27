"use client";

import { createGlobalStyle } from "styled-components";
import { weddingConfig } from "@/src/config/wedding-config";

const watermarkId = weddingConfig.meta._jhc_watermark_id || "JHC-NonCommercial";

export const GlobalStyle = createGlobalStyle`
  @font-face {
    font-family: 'MaruBuri';
    src: url('/fonts/MaruBuri-Regular.ttf') format('truetype');
    font-weight: 400;
    font-style: normal;
    font-display: swap;
  }
  @font-face {
    font-family: 'MaruBuri';
    src: url('/fonts/MaruBuri-SemiBold.ttf') format('truetype');
    font-weight: 600;
    font-style: normal;
    font-display: swap;
  }
  @font-face {
    font-family: 'PlayfairDisplay';
    src: url('/fonts/PlayfairDisplay-Italic.ttf') format('truetype');
    font-weight: normal;
    font-style: italic;
    font-display: swap;
  }

  body {
    font-family: 'MaruBuri', 'Apple SD Gothic Neo', 'Noto Sans KR', sans-serif;
    color: var(--text);
    background: var(--bg);
    line-height: 1.65;
  }

  /* 워터마크(최소) */
  body::after {
    content: "${watermarkId}";
    position: fixed;
    bottom: -120px;
    right: -120px;
    opacity: 0.01;
    font-size: 10px;
    transform: rotate(-35deg);
    pointer-events: none;
    user-select: none;
    z-index: -1;
  }

  .wedding-container {
    background-image: radial-gradient(rgba(0,0,0,.03) 1px, transparent 0);
    background-size: 16px 16px;
  }
`;
