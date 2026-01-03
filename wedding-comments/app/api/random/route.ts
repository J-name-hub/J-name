import { NextResponse } from "next/server";
import { readFile } from "node:fs/promises";
import path from "node:path";

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

  const relPath = CATEGORY_MAP[category];
  if (!relPath) {
    return NextResponse.json({ error: "Invalid category" }, { status: 400 });
  }

  const absPath = path.join(process.cwd(), relPath);
  const text = await readFile(absPath, "utf-8");

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
