import { NextResponse } from "next/server";
import { fetchKoreanHolidays } from "@/lib/holidays";

export async function GET(req: Request) {
  const { searchParams } = new URL(req.url);
  const year = Number(searchParams.get("year") || "");
  if (!year || year < 1900 || year > 2200) {
    return NextResponse.json({ error: "invalid year" }, { status: 400 });
  }
  const holidays = await fetchKoreanHolidays(year);
  return NextResponse.json({ holidays });
}
