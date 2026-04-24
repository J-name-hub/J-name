// lib/github.ts

const GITHUB_TOKEN = process.env.GITHUB_TOKEN!;
const GITHUB_REPO = process.env.GITHUB_REPO!;

// eslint-disable-next-line @typescript-eslint/no-explicit-any
async function fetchFromGitHub(path: string): Promise<{ data: any; sha: string } | null> {
  const url = `https://api.github.com/repos/${GITHUB_REPO}/contents/${path}`;
  const res = await fetch(url, {
    headers: { Authorization: `token ${GITHUB_TOKEN}` },
    cache: 'no-store',
  });
  if (!res.ok) {
    if (res.status === 404) return null;
    throw new Error(`GitHub GET failed: ${res.status}`);
  }
  const raw = await res.json();
  const content = Buffer.from(raw.content, 'base64').toString('utf-8');
  return { data: JSON.parse(content), sha: raw.sha };
}

// 캐시 없이 항상 최신 데이터를 반환
// (Vercel 서버리스는 인스턴스별 메모리가 분리돼 인스턴스 간 캐시 불일치 발생 → 제거)
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export async function githubGet(path: string): Promise<{ data: any; sha: string } | null> {
  return fetchFromGitHub(path);
}

export async function githubPut(
  path: string,
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  content: any,
  sha: string | null,
  message: string
): Promise<string> {
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
