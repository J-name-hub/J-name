"use client";

import styled from "styled-components";
import { buildGoogleCalendarUrl, buildIcs } from "@/src/lib/calendar";
import { useToast } from "@/src/components/ui/ToastProvider";

export default function CalendarButtons() {
  const { toast } = useToast();

  const downloadIcs = () => {
    const ics = buildIcs();
    const blob = new Blob([ics], { type: "text/calendar;charset=utf-8" });
    const url = URL.createObjectURL(blob);

    const a = document.createElement("a");
    a.href = url;
    a.download = "wedding.ics";
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);

    toast("캘린더 파일(ICS)을 다운로드했습니다.");
  };

  const openGoogle = () => {
    window.open(buildGoogleCalendarUrl(), "_blank", "noopener,noreferrer");
  };

  return (
    <Row>
      <Btn type="button" onClick={openGoogle}>구글 캘린더</Btn>
      <Btn type="button" onClick={downloadIcs}>ICS 다운로드</Btn>
    </Row>
  );
}

const Row = styled.div`
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  margin-top: 14px;
`;

const Btn = styled.button`
  border: 1px solid var(--border);
  background: #fff;
  border-radius: 999px;
  padding: 10px 14px;
  cursor: pointer;
  font-size: 14px;
  transition: transform .06s ease, background .15s ease;

  &:active { transform: scale(0.98); }
  &:hover { background: rgba(0,0,0,.03); }
`;
