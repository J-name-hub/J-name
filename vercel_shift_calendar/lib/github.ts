// lib/github.ts

const GITHUB_TOKEN = process.env.GITHUB_TOKEN!;
const GITHUB_REPO = process.env.GITHUB_REPO!;

export async function githubGet(path: string) {
  const url = `https://api.github.com/repos/${GITHUB_REPO}/contents/${path}`;
  const res = await fetch(url, {
    headers: { Authorization: `token ${GITHUB_TOKEN}` },
    cache: 'no-store',
  });
  if (!res.ok) {
    if (res.status === 404) return null;
    throw new Error(`GitHub GET failed: ${res.status}`);
  }
  const data = await res.json();
  const content = Buffer.from(data.content, 'base64').toString('utf-8');
  return { data: JSON.parse(content), sha: data.sha };
}

export async function githubPut(path: string, content: unknown, sha: string | null, message: string) {
  const url = `https://api.github.com/repos/${GITHUB_REPO}/contents/${path}`;
  const encoded = Buffer.from(JSON.stringify(content, null, 2)).toString('base64');
  const body: Record<string, string> = { message, content: encoded };
  if (sha) body.sha = sha;

  const res = await fetch(url, {
    method: 'PUT',
    headers: {
      Authorization: `token ${GITHUB_TOKEN}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`GitHub PUT failed: ${res.status}`);
  const result = await res.json();
  return result.content.sha as string;
}
