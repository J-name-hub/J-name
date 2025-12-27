"use client";

import { weddingConfig } from "@/src/config/wedding-config";
import { Body, Card, SectionShell, Title } from "@/src/components/ui/SectionShell";
import CalendarButtons from "@/src/components/ui/CalendarButtons";

export default function InvitationSection() {
  return (
    <SectionShell>
      <Card>
        <Title>{weddingConfig.intro.heading}</Title>
        <Body>{weddingConfig.intro.text}</Body>

        {/* 캘린더 추가 버튼(요즘 청첩장에 거의 필수) */}
        <CalendarButtons />
      </Card>
    </SectionShell>
  );
}
