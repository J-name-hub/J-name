import { NextResponse } from "next/server";
import { getJsonFromGitHub, putJsonToGitHub, checkPassword } from "../../../lib/github";
import { paths } from "../../../lib/paths";

export async function GET() {
  const { schedule } = paths();
  const file = await getJsonFromGitHub<Record<string, string>>(schedule);
  return NextResponse.json({ schedule: file.data ?? {}, sha: file.sha });
}

export async function PUT(req: Request) {
  const body = await req.json().catch(() => null);
  const password = body?.password as string | undefined;
  if (!checkPassword(password)) return NextResponse.json({ error: "unauthorized" }, { status: 401 });

  const schedule = body?.schedule as Record<string, string> | undefined;
  const sha = (body?.sha as string | null | undefined) ?? null;
  if (!schedule || typeof schedule !== "object") return NextResponse.json({ error: "invalid payload" }, { status: 400 });

  const { schedule: schedulePath } = paths();
  const newSha = await putJsonToGitHub(schedulePath, schedule, sha, "Update schedule");
  return NextResponse.json({ ok: true, sha: newSha });
}
