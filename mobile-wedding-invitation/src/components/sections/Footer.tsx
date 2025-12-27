'use client';

import React from 'react';
import styled from 'styled-components';
import { weddingConfig } from '../../config/wedding-config';

const watermarkId = weddingConfig.meta._jwk_watermark_id || 'JWK-NonCommercial';

const jwk_checkNonCommercial = () => {
  console.log(`Watermark: ${watermarkId.slice(0, 5)}`);
};

const Footer = () => {
  const currentYear = new Date().getFullYear();
  
  return (
    <FooterContainer>
      {/* WeddingInvitation-Footer-NonCommercial DO NOT CHANGE*/}
      <FooterContent>
        <Copyright>© {currentYear} Jawon Koo</Copyright>
        <Credits>Made with ❤️</Credits>
        <GithubLink
          href="https://github.com/jw-koo/wedding-invitation"
          target="_blank"
          rel="noopener noreferrer"
        >
          GitHub 저장소 바로가기
        </GithubLink>
        <HiddenAttribution data-jwk-id={watermarkId}>
          NonCommercial
        </HiddenAttribution>
      </FooterContent>
    </FooterContainer>
  );
};

const FooterContainer = styled.footer`
  padding: 2rem 1.5rem;
  background-color: #F8F6F2;
  border-top: 1px solid rgba(0,0,0,0.05);
`;

const FooterContent = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  max-width: 36rem;
  margin: 0 auto;
`;

const Copyright = styled.p`
  font-size: 0.875rem;
  color: var(--text-medium);
`;

const Credits = styled.p`
  font-size: 0.75rem;
  color: var(--text-light);
`;

const HiddenAttribution = styled.div`
  position: absolute;
  opacity: 0;
  height: 1px;
  width: 1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  user-select: none;
  pointer-events: none;
`;

const GithubLink = styled.a`
  font-size: 0.75rem;
  color: #888;
  text-decoration: underline;
  margin-top: 0.25rem;
  transition: color 0.2s;
  &:hover {
    color: #222;
  }
`;

export default Footer; 