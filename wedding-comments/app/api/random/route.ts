export const runtime = "nodejs";
export const dynamic = "force-dynamic";

import { NextResponse } from "next/server";
import { readFile, access } from "fs/promises";
import path from "path";

const CATEGORY_MAP: Record<string, string> = {
  dowry: "data/dowry/quotes.txt",
  // 나머지 동일
};

export async function GET(req: Request) {
  const { searchParams } = new URL(req.url);
  const category = searchParams.get("category") ?? "dowry";

  const rel = CATEGORY_MAP[category];
  const filePath = path.join(process.cwd(), rel);

  console.log("cwd=", process.cwd());
  console.log("filePath=", filePath);

  try {
    await access(filePath); // 여기서도 바로 ENOENT면 "파일이 배포에 없음"
    const text = await readFile(filePath, "utf-8");
    return NextResponse.json({ ok: true, sample: text.slice(0, 50), filePath });
  } catch (e: any) {
    return NextResponse.json(
      { ok: false, error: e.message, cwd: process.cwd(), filePath },
      { status: 500 }
    );
  }
}