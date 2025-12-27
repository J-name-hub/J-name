"use client";

import styled from "styled-components";
import { weddingConfig } from "@/src/config/wedding-config";
import { useToast } from "@/src/components/ui/ToastProvider";
import { Card, SectionShell, Title } from "@/src/components/ui/SectionShell";

export default function AccountSection() {
  const { toast } = useToast();
  const a = weddingConfig.account;

  const copy = async (txt: string) => {
    await navigator.clipboard.writeText(txt);
    toast("계좌번호를 복사했습니다.");
  };

  return (
    <SectionShell>
      <Card>
        <Title>마음 전하실 곳</Title>

        <Item>
          <div>
            <strong>신랑</strong>
            <div>{a.groom.bank} {a.groom.number}</div>
            <div className="muted">{a.groom.holder}</div>
          </div>
          <Btn onClick={() => copy(`${a.groom.bank} ${a.groom.number} (${a.groom.holder})`)}>복사</Btn>
        </Item>

        <Divider />

        <Item>
          <div>
            <strong>신부</strong>
            <div>{a.bride.bank} {a.bride.number}</div>
            <div className="muted">{a.bride.holder}</div>
          </div>
          <Btn onClick={() => copy(`${a.bride.bank} ${a.bride.number} (${a.bride.holder})`)}>복사</Btn>
        </Item>
      </Card>
    </SectionShell>
  );
}

const Item = styled.div`
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;

  .muted{ color: var(--muted); font-size: 13px; }
`;

const Divider = styled.div`
  height: 1px;
  background: var(--border);
  margin: 16px 0;
`;

const Btn = styled.button`
  border: 1px solid var(--border);
  background: #fff;
  border-radius: 999px;
  padding: 10px 12px;
  cursor: pointer;
  white-space: nowrap;
`;
