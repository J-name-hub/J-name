"use client";

import styled from "styled-components";
import { buildVersion } from "@/src/config/version";

export default function Footer() {
  return (
    <Wrap>
      <div>감사합니다.</div>
      <small>build: {buildVersion}</small>
    </Wrap>
  );
}

const Wrap = styled.footer`
  padding: 56px 16px 120px;
  text-align: center;
  color: var(--muted);
  display: grid;
  gap: 6px;
`;
