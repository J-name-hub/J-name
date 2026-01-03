import { NextResponse } from "next/server";
import { readFile } from "fs/promises";
import path from "path";

const BASE_DIR = "wedding-comments";

const CATEGORY_MAP: Record<string, string> = {
  expo: "data/expo/quotes.txt",
  hall: "data/hall/quotes.txt",
  studio: "data/studio/quotes.txt",
  dress: "data/dress/quotes.txt",
  makeup: "data/makeup/quotes.txt",
  dowry: "data/dowry/quotes.txt",
};

export async function GET(req: Request) {
  try {
    const { searchParams } = new URL(req.url);
    const category = searchParams.get("category");

    if (!category || !(category in CATEGORY_MAP)) {
      return NextResponse.json(
        { ok: false, error: "Invalid category" },
        { status: 400 }
      );
    }

    // ✅ 핵심: wedding-comments 기준으로 파일 찾기
    const filePath = path.join(
      process.cwd(),
      BASE_DIR,
      CATEGORY_MAP[category]
    );

    const text = await readFile(filePath, "utf-8");

    const lines = text
      .split(/\r?\n/)
      .map(v => v.trim())
      .filter(Boolean);

    if (lines.length === 0) {
      return NextResponse.json(
        { ok: false, error: "Empty quotes file" },
        { status: 500 }
      );
    }

    const pick = lines[Math.floor(Math.random() * lines.length)];

    return NextResponse.json({
      ok: true,
      pick,
      count: lines.length,
    });

  } catch (err: any) {
    return NextResponse.json(
      { ok: false, error: err.message },
      { status: 500 }
    );
  }
}
