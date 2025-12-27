"use client";

import { weddingConfig } from "@/src/config/wedding-config";
import { formatKoreanDateTime } from "@/src/lib/format";
import { Body, Card, SectionShell, Title } from "@/src/components/ui/SectionShell";

export default function DateSection() {
  const d = weddingConfig.date;
  return (
    <SectionShell>
      <Card>
        <Title>일정</Title>
        <Body>
          {formatKoreanDateTime(d.year, d.month, d.day, d.hour, d.minute)}
          {"\n"}
          {weddingConfig.date.displayDate}
        </Body>
      </Card>
    </SectionShell>
  );
}
