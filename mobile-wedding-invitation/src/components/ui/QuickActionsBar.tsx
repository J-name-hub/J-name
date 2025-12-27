'use client';

import styled from 'styled-components';
import { weddingConfig } from '../../config/wedding-config';
import { useToast } from './ToastProvider';

const QuickActionsBar = () => {
  const { toast } = useToast();

  const shareOrCopy = async () => {
    const url = window.location.href;

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const nav = navigator as any;
    if (nav.share) {
      try {
        await nav.share({ title: weddingConfig.meta.title, text: weddingConfig.meta.description, url });
        return;
      } catch {
        // 사용자 취소 등은 무시
      }
    }

    await navigator.clipboard.writeText(url);
    toast('링크를 복사했습니다.');
  };

  const copyAddress = async () => {
    const txt = `${weddingConfig.venue.name}\n${weddingConfig.venue.address}`;
    await navigator.clipboard.writeText(txt);
    toast('주소를 복사했습니다.');
  };

  const openMap = () => {
    const { latitude, longitude } = weddingConfig.venue.coordinates;
    const url = `https://www.google.com/maps/search/?api=1&query=${latitude},${longitude}`;
    window.open(url, '_blank', 'noopener,noreferrer');
  };

  const callVenue = () => {
    if (!weddingConfig.venue.tel) return;
    window.location.href = `tel:${weddingConfig.venue.tel}`;
  };

  return (
    <Bar>
      <Inner>
        <Action type="button" onClick={shareOrCopy}>공유/복사</Action>
        <Action type="button" onClick={copyAddress}>주소복사</Action>
        <Action type="button" onClick={openMap}>길찾기</Action>
        <Action type="button" onClick={callVenue}>전화</Action>
      </Inner>
    </Bar>
  );
};

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
  width: min(520px, calc(100vw - 24px));
  background: rgba(255,255,255,.92);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(0,0,0,.08);
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

export default QuickActionsBar;
