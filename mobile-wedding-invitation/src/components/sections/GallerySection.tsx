"use client";

import Image from "next/image";
import styled from "styled-components";
import { weddingConfig } from "@/src/config/wedding-config";
import { Card, SectionShell, Title } from "@/src/components/ui/SectionShell";

export default function GallerySection() {
  const imgs = weddingConfig.gallery.images || [];
  if (!imgs.length) return null;

  return (
    <SectionShell>
      <Card>
        <Title>갤러리</Title>
        <Grid>
          {imgs.map((src, i) => (
            <Thumb key={src + i}>
              <Image
                src={src}
                alt={`gallery-${i + 1}`}
                fill
                sizes="(max-width: 520px) 33vw, 170px"
                style={{ objectFit: "cover" }}
              />
            </Thumb>
          ))}
        </Grid>
      </Card>
    </SectionShell>
  );
}

const Grid = styled.div`
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
`;

const Thumb = styled.div`
  position: relative;
  width: 100%;
  aspect-ratio: 1 / 1;
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid var(--border);
`;
