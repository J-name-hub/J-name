"use client";

import styled from "styled-components";

export const SectionShell = styled.section`
  padding: 56px 16px;
  display: flex;
  justify-content: center;
`;

export const Card = styled.div`
  width: min(var(--maxw), 100%);
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow);
  padding: 22px 18px;
`;

export const Title = styled.h2`
  margin: 0 0 14px;
  font-size: clamp(18px, 3.6vw, 22px);
  letter-spacing: -0.2px;
`;

export const Body = styled.div`
  color: var(--muted);
  font-size: 15px;
  white-space: pre-line;
`;
