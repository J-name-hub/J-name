export const runtime = "nodejs";
export const dynamic = "force-dynamic";

import { NextResponse } from "next/server";
import path from "path";

export async function GET() {
  return NextResponse.json({
    cwd: process.cwd(),
    dirname: __dirname,
    resolved_data_path: path.resolve("data"),
    resolved_dowry: path.resolve("data/dowry/quotes.txt"),
  });
}
