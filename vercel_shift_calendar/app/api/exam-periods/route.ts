import { NextResponse } from "next/server";
import { getJsonFromGitHub, putJsonToGitHub, checkPassword } from "@/lib/github";
import { paths } from "@/lib/paths";

type ExamRange = { start: string; end: string };
type ExamFile = { ranges?: ExamRange[] };

export async function GET() {
  const { exam } = paths();
  const file = await getJsonFromGitHub<ExamFile>(exam);
  return NextResponse.json({ ranges: file.data?.ranges ?? [], sha: file.sha });
}

export async function PUT(req: Request) {
  const body = await req.json().catch(() => null);
  const password = body?.password as string | undefined;
  if (!checkPassword(password)) return NextResponse.json({ error: "unauthorized" }, { status: 401 });

  const ranges = body?.ranges as ExamRange[] | undefined;
  const sha = (body?.sha as string | null | undefined) ?? null;
  if (!Array.isArray(ranges)) return NextResponse.json({ error: "invalid payload" }, { status: 400 });

  const { exam } = paths();
  const newSha = await putJsonToGitHub(exam, { ranges }, sha, "Update exam periods");
  return NextResponse.json({ ok: true, sha: newSha });
}
