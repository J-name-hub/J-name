'use client';

import { createGlobalStyle } from 'styled-components';
import { weddingConfig } from '../config/wedding-config';

const watermarkId = weddingConfig.meta._jwk_watermark_id || 'JWK-NonCommercial';

/**
 * @license
 * 웨딩 청첩장 템플릿
 * Copyright (c) 2025 Jawon Koo
 * 라이선스: CC BY-NC-ND 4.0
 * 저작자표시-비영리-변경금지
 * https://creativecommons.org/licenses/by-nc-nd/4.0/deed.ko
 * 
 * 이 코드는 비상업적 용도로만 사용 가능합니다.
 * 상업적 용도로 사용 시 법적 조치가 취해질 수 있습니다.
 * ID: ${watermarkId}
 */

export const GlobalStyle = createGlobalStyle`
  /* 폰트 로딩 전에 적용될 스타일 */
  @font-face {
    font-family: 'MaruBuri';
    src: url('/fonts/MaruBuri-ExtraLight.ttf') format('truetype');
    font-weight: 200;
    font-style: normal;
    font-display: block; /* 폰트 로딩될 때까지 텍스트를 보이지 않게 함 */
  }
  
  @font-face {
    font-family: 'MaruBuri';
    src: url('/fonts/MaruBuri-Light.ttf') format('truetype');
    font-weight: 300;
    font-style: normal;
    font-display: block;
  }
  
  @font-face {
    font-family: 'MaruBuri';
    src: url('/fonts/MaruBuri-Regular.ttf') format('truetype');
    font-weight: 400;
    font-style: normal;
    font-display: block;
  }
  
  @font-face {
    font-family: 'MaruBuri';
    src: url('/fonts/MaruBuri-SemiBold.ttf') format('truetype');
    font-weight: 600;
    font-style: normal;
    font-display: block;
  }
  
  @font-face {
    font-family: 'MaruBuri';
    src: url('/fonts/MaruBuri-Bold.ttf') format('truetype');
    font-weight: 700;
    font-style: normal;
    font-display: block;
  }

  @font-face {
    font-family: 'PlayfairDisplay';
    src: url('/fonts/PlayfairDisplay-Italic.ttf') format('truetype');
    font-weight: normal;
    font-style: italic;
    font-display: block;
  }
  
  /* 컨텐츠가 바로 보이지만 폰트가 로드되면 레이아웃이 바뀌는 것을 방지 */
  html, body {
    visibility: visible;
    opacity: 1;
    font-size: 16px;
  }
  
  body {
    font-family: 'MaruBuri', 'Apple SD Gothic Neo', 'Noto Sans KR', sans-serif;
    color: #333333;
    margin: 0;
    padding: 0;
    line-height: 1.6;
  }

  body::after {
    content: "${watermarkId}";
    position: fixed;
    bottom: -100px;
    right: -100px;
    opacity: 0.01;
    font-size: 8px;
    transform: rotate(-45deg);
    pointer-events: none;
    z-index: -1000;
    color: rgba(0, 0, 0, 0.02);
    user-select: none;
  }
  
  .jwk-watermark {
    position: absolute;
    opacity: 0.01;
    font-size: 1px;
    color: rgba(255, 255, 255, 0.01);
    pointer-events: none;
    user-select: none;
    z-index: -9999;
  }
  
  .wedding-container {
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='200' height='200' opacity='0.01'%3E%3Ctext x='0' y='20' fill='rgba(0,0,0,0.03)'%3EJWK-TEMPLATE%3C/text%3E%3C/svg%3E");
  }

  :root {
    --primary-color: #F8F6F2;
    --secondary-color: #D4B996; 
    --text-dark: #333333;
    --text-medium: #666666;
    --text-light: #999999;
    --jwk-id: "${watermarkId}";
  }
`; 