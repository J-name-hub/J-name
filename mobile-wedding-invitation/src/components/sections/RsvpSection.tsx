"use client";

import { useState } from "react";
import styled from "styled-components";
import { weddingConfig } from "@/src/config/wedding-config";
import { useToast } from "@/src/components/ui/ToastProvider";
import { Card, SectionShell, Title } from "@/src/components/ui/SectionShell";

export default function RsvpSection() {
  const { toast } = useToast();

  const [name, setName] = useState("");
  const [attending, setAttending] = useState<"yes" | "no">("yes");
  const [phone, setPhone] = useState("");
  const [headcount, setHeadcount] = useState(1);
  const [message, setMessage] = useState("");

  const submit = async () => {
    if (!name.trim()) {
      toast("이름을 입력해 주세요.");
      return;
    }

    const res = await fetch("/api/rsvp", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        name,
        phone: phone || undefined,
        attending,
        headcount: attending === "yes" ? headcount : undefined,
        message: message || undefined,
        meal: weddingConfig.rsvp.showMealOption ? "yes" : undefined
      })
    });

    if (res.ok) {
      toast("전송되었습니다. 감사합니다.");
      setMessage("");
    } else {
      toast("전송에 실패했습니다. 다시 시도해 주세요.");
    }
  };

  return (
    <SectionShell>
      <Card>
        <Title>참석 의사 전달</Title>
        <Form>
          <label>
            이름
            <input value={name} onChange={(e) => setName(e.target.value)} />
          </label>

          <label>
            연락처(선택)
            <input value={phone} onChange={(e) => setPhone(e.target.value)} />
          </label>

          <Row>
            <Pill onClick={() => setAttending("yes")} data-on={attending === "yes"}>참석</Pill>
            <Pill onClick={() => setAttending("no")} data-on={attending === "no"}>불참</Pill>
          </Row>

          {attending === "yes" && (
            <label>
              참석 인원
              <input
                type="number"
                min={1}
                max={20}
                value={headcount}
                onChange={(e) => setHeadcount(Number(e.target.value))}
              />
            </label>
          )}

          <label>
            메모(선택)
            <textarea value={message} onChange={(e) => setMessage(e.target.value)} />
          </label>

          <Submit type="button" onClick={submit}>전송</Submit>
        </Form>
      </Card>
    </SectionShell>
  );
}

const Form = styled.div`
  display: grid;
  gap: 12px;

  label{
    display: grid;
    gap: 6px;
    font-size: 13px;
    color: var(--muted);
  }

  input, textarea{
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 10px 12px;
    font-size: 14px;
    outline: none;
    background: #fff;
  }

  textarea{
    min-height: 88px;
    resize: vertical;
  }
`;

const Row = styled.div`
  display: flex;
  gap: 10px;
`;

const Pill = styled.button`
  flex: 1;
  border: 1px solid var(--border);
  background: #fff;
  border-radius: 999px;
  padding: 10px 12px;
  cursor: pointer;
  font-size: 14px;

  &[data-on="true"]{
    border-color: rgba(201,178,139,.65);
    background: rgba(201,178,139,.14);
    color: var(--accent-2);
  }
`;

const Submit = styled.button`
  border: 0;
  background: var(--accent);
  color: #1a1a1a;
  border-radius: 999px;
  padding: 12px 14px;
  cursor: pointer;
  font-weight: 600;
`;
