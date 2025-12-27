"use client";

import styled from "styled-components";
import { weddingConfig } from "@/src/config/wedding-config";
import { Body, Card, SectionShell, Title } from "@/src/components/ui/SectionShell";

export default function VenueSection() {
  const v = weddingConfig.venue;

  return (
    <SectionShell>
      <Card>
        <Title>오시는 길</Title>
        <Body>
          {v.name}
          {"\n"}
          {v.address}
          {"\n\n"}
          지하철: {v.transportation.subway}
          {"\n"}
          버스: {v.transportation.bus}
          {"\n\n"}
          주차: {v.parking}
        </Body>

        {/* 지도는 개인용이면 “구글 링크”만으로도 충분합니다.
            기존처럼 카카오맵을 붙이려면 여기에서 ssr:false + SDK 로드로 확장하시면 됩니다. */}
        <MapNote>필요 시 “길찾기” 버튼을 이용해 주세요.</MapNote>
      </Card>
    </SectionShell>
  );
}

const MapNote = styled.div`
  margin-top: 14px;
  color: var(--muted);
  font-size: 13px;
`;
