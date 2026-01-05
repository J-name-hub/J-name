export const runtime = "nodejs";
export const dynamic = "force-dynamic";

import { NextResponse } from "next/server";

const CATEGORY_MAP: Record<string, string> = {
  expo: "/data/expo/quotes.txt",
  hall: "/data/hall/quotes.txt",
  studio: "/data/studio/quotes.txt",
  dress: "/data/dress/quotes.txt",
  makeup: "/data/makeup/quotes.txt",
  dowry: "/data/dowry/quotes.txt",
};

export async function GET(req: Request) {
  try {
    const { searchParams, origin } = new URL(req.url);
    const category = searchParams.get("category");

    if (!category || !(category in CATEGORY_MAP)) {
      return NextResponse.json(
        { ok: false, error: "Invalid category" },
        { status: 400 }
      );
    }

    const url = `${origin}${CATEGORY_MAP[category]}`; // ✅ public 정적 파일
    const res = await fetch(url, { cache: "no-store" });

    if (!res.ok) {
      return NextResponse.json(
        { ok: false, error: `Failed to fetch quotes: ${res.status}` },
        { status: 500 }
      );
    }

    const text = await res.text();

    const lines = text
      .split(/\r?\n/)
      .map((v) => v.trim())
      .filter(Boolean);

    if (lines.length === 0) {
      return NextResponse.json(
        { ok: false, error: "Empty quotes file" },
        { status: 500 }
      );
    }

    const pick = lines[Math.floor(Math.random() * lines.length)];

    return NextResponse.json({ ok: true, pick, count: lines.length });
  } catch (err: any) {
    return NextResponse.json(
      { ok: false, error: err.message },
      { status: 500 }
    );
  }
}
