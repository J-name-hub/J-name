import { NextResponse } from "next/server";
import { getJsonFromGitHub, putJsonToGitHub, checkPassword } from "@/lib/github";
import { paths } from "@/lib/paths";

type TeamItem = { start_date: string; team: "A" | "B" | "C" | "D" };
type TeamFile = { team_history?: TeamItem[]; team?: "A" | "B" | "C" | "D" };

export async function GET() {
  const { team } = paths();
  const file = await getJsonFromGitHub<TeamFile>(team);
  const data = file.data;
  const team_history =
    data?.team_history ??
    (data?.team ? [{ start_date: "2000-01-03", team: data.team }] : [{ start_date: "2000-01-03", team: "A" }]);
  return NextResponse.json({ team_history, sha: file.sha });
}

export async function PUT(req: Request) {
  const body = await req.json().catch(() => null);
  const password = body?.password as string | undefined;
  if (!checkPassword(password)) return NextResponse.json({ error: "unauthorized" }, { status: 401 });

  const team_history = body?.team_history as TeamItem[] | undefined;
  const sha = (body?.sha as string | null | undefined) ?? null;
  if (!Array.isArray(team_history)) return NextResponse.json({ error: "invalid payload" }, { status: 400 });

  const { team } = paths();
  const newSha = await putJsonToGitHub(team, { team_history }, sha, "Update team settings");
  return NextResponse.json({ ok: true, sha: newSha });
}
