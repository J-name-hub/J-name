// lib/github.ts

const GITHUB_TOKEN = process.env.GITHUB_TOKEN!;
const GITHUB_REPO = process.env.GITHUB_REPO!;

// ── 인메모리 캐시 ──────────────────────────────────────────────────
// 같은 서버 인스턴스 내에서 60초간 캐시 유지 (stale-while-revalidate)
const CACHE_TTL_MS = 60_000;

interface CacheEntry {
  value: { data: unknown; sha: string } | null;
  fetchedAt: number;
  revalidating: boolean;
}

const cache = new Map<string, CacheEntry>();

async function fetchFromGitHub(path: string): Promise<{ data: unknown; sha: string } | null> {
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

export async function githubGet(path: string): Promise<{ data: unknown; sha: string } | null> {
  const now = Date.now();
  const entry = cache.get(path);

  if (entry) {
    const age = now - entry.fetchedAt;

    if (age < CACHE_TTL_MS) {
      // 캐시가 신선함 → 즉시 반환
      return entry.value;
    }

    // 캐시가 낡았지만 재검증 중이 아니면 백그라운드에서 갱신 (stale-while-revalidate)
    if (!entry.revalidating) {
      entry.revalidating = true;
      fetchFromGitHub(path)
        .then(fresh => {
          cache.set(path, { value: fresh, fetchedAt: Date.now(), revalidating: false });
        })
        .catch(() => {
          if (cache.has(path)) cache.get(path)!.revalidating = false;
        });
    }
    // 낡은 캐시라도 즉시 반환 (깜빡임 방지)
    return entry.value;
  }

  // 캐시 없음 → 최초 fetch
  const value = await fetchFromGitHub(path);
  cache.set(path, { value, fetchedAt: now, revalidating: false });
  return value;
}

/** 쓰기 후 캐시를 즉시 갱신 */
export async function githubPut(
  path: string,
  content: unknown,
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
  const newSha = result.content.sha as string;

  // 쓰기 성공 → 해당 파일 캐시 즉시 갱신
  cache.set(path, {
    value: { data: content, sha: newSha },
    fetchedAt: Date.now(),
    revalidating: false,
  });

  return newSha;
}
