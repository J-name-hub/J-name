import { NextResponse } from "next/server";

const CATEGORY_MAP: Record<string, string> = {
  expo: "data/expo/quotes.txt",
  hall: "data/hall/quotes.txt",
  studio: "data/studio/quotes.txt",
  dress: "data/dress/quotes.txt",
  makeup: "data/makeup/quotes.txt",
  dowry: "data/dowry/quotes.txt",
};

export async function GET(req: Request) {
  const { searchParams } = new URL(req.url);
  const category = (searchParams.get("category") || "").trim();

  const path = CATEGORY_MAP[category];
  if (!path) {
    return NextResponse.json({ error: "Invalid category" }, { status: 400 });
  }

  const owner = process.env.GH_OWNER!;
  const repo = process.env.GH_REPO!;
  const token = process.env.GH_TOKEN; // private repo면 필요, public이면 없어도 됨
  const branch = process.env.GH_BRANCH || "main";

  // GitHub raw URL (가장 단순)
  const rawUrl = `https://raw.githubusercontent.com/${owner}/${repo}/${branch}/${path}`;

  const res = await fetch(rawUrl, {
    headers: token ? { Authorization: `token ${token}` } : undefined,
    cache: "no-store",
  });

  if (!res.ok) {
    return NextResponse.json(
      { error: "Failed to fetch source file", status: res.status },
      { status: 500 }
    );
  }

  const text = await res.text();

  // 줄바꿈 기준으로 문구 목록화
  const lines = text
    .split(/\r?\n/)
    .map((l) => l.trim())
    .filter(Boolean);

  if (lines.length === 0) {
    return NextResponse.json({ error: "No quotes found" }, { status: 500 });
  }

  const pick = lines[Math.floor(Math.random() * lines.length)];
  return NextResponse.json({ category, pick, count: lines.length });
}
