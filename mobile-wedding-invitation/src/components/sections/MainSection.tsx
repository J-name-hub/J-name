"use client";

import Image from "next/image";
import styled from "styled-components";
import { weddingConfig } from "@/src/config/wedding-config";

export default function MainSection() {
  return (
    <Wrap className="wedding-container">
      <Bg
        src={weddingConfig.main.image}
        alt="메인 이미지"
        fill
        priority
        sizes="100vw"
        style={{ objectFit: "cover", objectPosition: "center 20%" }}
      />
      <Overlay />
      <Content>
        <Kicker>We’re getting married</Kicker>
        <Title>{weddingConfig.main.title}</Title>
        <Sub>{weddingConfig.main.dateText}</Sub>
        <Sub>{weddingConfig.main.venueText}</Sub>
      </Content>
      <Hint>아래로 스크롤</Hint>
    </Wrap>
  );
}

const Wrap = styled.section`
  position: relative;
  height: 100vh;
  width: 100%;
  overflow: hidden;
  display: flex;
  justify-content: center;

  @media (min-width: 768px) and (min-height: 780px) {
    width: min(calc(100vh * 9 / 16), 520px);
    margin: 18px auto 0;
    border-radius: 24px;
    box-shadow: 0 18px 60px rgba(0,0,0,.14);
  }
`;

const Bg = styled(Image)`
  z-index: 0;
`;

const Overlay = styled.div`
  position: absolute;
  inset: 0;
  background:
    linear-gradient(to bottom, rgba(0,0,0,.55), rgba(0,0,0,.15) 42%, rgba(0,0,0,.55));
  z-index: 1;
`;

const Content = styled.div`
  z-index: 2;
  width: min(var(--maxw), calc(100vw - 24px));
  padding-top: 10vh;
  text-align: center;
  color: #fff;
`;

const Kicker = styled.div`
  font-size: 13px;
  letter-spacing: 0.22em;
  text-transform: uppercase;
  opacity: .9;
`;

const Title = styled.h1`
  margin: 10px 0 10px;
  font-family: 'PlayfairDisplay', serif;
  font-style: italic;
  font-weight: 400;
  letter-spacing: 0.06em;
  font-size: clamp(34px, 6vw, 52px);
  line-height: 1.1;
`;

const Sub = styled.div`
  font-size: clamp(14px, 2.8vw, 18px);
  opacity: .95;
`;

const Hint = styled.div`
  position: absolute;
  z-index: 2;
  bottom: 18px;
  left: 50%;
  transform: translateX(-50%);
  color: rgba(255,255,255,.9);
  font-size: 12px;
  letter-spacing: 0.08em;
`;
