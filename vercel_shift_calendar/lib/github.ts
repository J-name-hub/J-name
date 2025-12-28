import { Buffer } from "node:buffer";

type GithubContentResponse = {
  sha: string;
  content: string;
  encoding: string;
};

export type GitHubFile<T> = { data: T; sha: string | null };

function mustEnv(name: string): string {
  const v = process.env[name];
  if (!v) throw new Error(`Missing env: ${name}`);
  return v;
}

export function getGitHubRepo(): string {
  return mustEnv("GITHUB_REPO");
}
export function getGitHubToken(): string {
  return mustEnv("GITHUB_TOKEN");
}

export async function getJsonFromGitHub<T>(path: string): Promise<GitHubFile<T>> {
  const repo = getGitHubRepo();
  const token = getGitHubToken();
  const url = `https://api.github.com/repos/${repo}/contents/${path}`;
  const r = await fetch(url, {
    headers: {
      Authorization: `token ${token}`,
      "User-Agent": "shift-calendar-vercel",
      Accept: "application/vnd.github.v3+json",
    },
    cache: "no-store",
  });

  if (r.status === 404) return { data: (undefined as unknown) as T, sha: null };
  if (!r.ok) throw new Error(`GitHub GET failed: ${r.status} ${await r.text()}`);

  const body = (await r.json()) as GithubContentResponse;
  const decoded = Buffer.from(body.content, "base64").toString("utf-8");
  const data = JSON.parse(decoded) as T;
  return { data, sha: body.sha };
}

export async function putJsonToGitHub<T>(path: string, data: T, sha: string | null, message: string): Promise<string> {
  const repo = getGitHubRepo();
  const token = getGitHubToken();
  const url = `https://api.github.com/repos/${repo}/contents/${path}`;

  const content = Buffer.from(JSON.stringify(data, null, 2), "utf-8").toString("base64");
  const payload: any = { message, content };
  if (sha) payload.sha = sha;

  const r = await fetch(url, {
    method: "PUT",
    headers: {
      Authorization: `token ${token}`,
      "User-Agent": "shift-calendar-vercel",
      Accept: "application/vnd.github.v3+json",
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!r.ok) throw new Error(`GitHub PUT failed: ${r.status} ${await r.text()}`);
  const out = await r.json();
  return out?.content?.sha ?? sha ?? "";
}

export function checkPassword(pw: string | null | undefined): boolean {
  const expected = process.env.SCHEDULE_CHANGE_PASSWORD;
  return Boolean(expected && pw && pw === expected);
}
