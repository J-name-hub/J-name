"use client";

import styled from "styled-components";
import { weddingConfig } from "@/src/config/wedding-config";
import { useToast } from "@/src/components/ui/ToastProvider";

export default function QuickActionsBar() {
  const { toast } = useToast();

  const share = async () => {
    const url = window.location.href;

    // Web Share 지원
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const nav = navigator as any;
    if (nav.share) {
      try {
        await nav.share({ title: weddingConfig.meta.title, text: weddingConfig.meta.description, url });
        return;
      } catch {
        // 취소 등은 무시
      }
    }

    await navigator.clipboard.writeText(url);
    toast("링크를 복사했습니다.");
  };

  const copyAddress = async () => {
    const txt = `${weddingConfig.venue.name}\n${weddingConfig.venue.address}`;
    await navigator.clipboard.writeText(txt);
    toast("주소를 복사했습니다.");
  };

  const callVenue = () => {
    if (!weddingConfig.venue.tel) return;
    window.location.href = `tel:${weddingConfig.venue.tel}`;
  };

  const openMap = () => {
    const { latitude, longitude } = weddingConfig.venue.coordinates;
    // 범용: 카카오/네이버/구글 중 아무거나 사용 가능하나, 개인용이면 구글 맵 링크가 가장 무난
    const url = `https://www.google.com/maps/search/?api=1&query=${latitude},${longitude}`;
    window.open(url, "_blank", "noopener,noreferrer");
  };

  return (
    <Bar>
      <Inner>
        <Action type="button" onClick={share}>공유/복사</Action>
        **<Action type="button" onClick={copyAddress}>주소복사</Action>**
        <Action type="button" onClick={openMap}>길찾기</Action>
        <Action type="button" onClick={callVenue}>전화</Action>
      </Inner>
    </Bar>
  );
}

const Bar = styled.div`
  position: fixed;
  left: 0;
  right: 0;
  bottom: 10px;
  z-index: 9998;
  display: flex;
  justify-content: center;
  pointer-events: none;
`;

const Inner = styled.div`
  width: min(var(--maxw), calc(100vw - 24px));
  background: rgba(255,255,255,.92);
  backdrop-filter: blur(10px);
  border: 1px solid var(--border);
  border-radius: 999px;
  box-shadow: 0 14px 40px rgba(0,0,0,.16);
  padding: 8px;
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 6px;
  pointer-events: auto;
`;

const Action = styled.button`
  border: 0;
  background: transparent;
  border-radius: 999px;
  padding: 10px 8px;
  cursor: pointer;
  font-size: 13px;

  &:hover { background: rgba(0,0,0,.04); }
  &:active { transform: scale(0.99); }
`;
