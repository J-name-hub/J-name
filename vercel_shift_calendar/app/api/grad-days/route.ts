import { NextResponse } from "next/server";
import { getJsonFromGitHub, putJsonToGitHub, checkPassword } from "../../../lib/github";
import { paths } from "../../../lib/paths";

type GradFile = { dates?: string[] };

export async function GET() {
  const { grad } = paths();
  const file = await getJsonFromGitHub<GradFile>(grad);
  return NextResponse.json({ dates: file.data?.dates ?? [], sha: file.sha });
}

export async function PUT(req: Request) {
  const body = await req.json().catch(() => null);
  const password = body?.password as string | undefined;
  if (!checkPassword(password)) return NextResponse.json({ error: "unauthorized" }, { status: 401 });

  const dates = body?.dates as string[] | undefined;
  const sha = (body?.sha as string | null | undefined) ?? null;
  if (!Array.isArray(dates)) return NextResponse.json({ error: "invalid payload" }, { status: 400 });

  const { grad } = paths();
  const newSha = await putJsonToGitHub(grad, { dates }, sha, "Update grad days");
  return NextResponse.json({ ok: true, sha: newSha });
}
