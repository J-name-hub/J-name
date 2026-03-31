// pages/api/exam.ts
import type { NextApiRequest, NextApiResponse } from 'next';
import { githubGet, githubPut } from '../../lib/github';

const FILE = 'exam_periods.json';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method === 'GET') {
    try {
      const result = await githubGet(FILE);
      if (!result) return res.json({ ranges: [], sha: null });
      return res.json({ ranges: result.data.ranges || [], sha: result.sha });
    } catch (e) {
      return res.status(500).json({ error: String(e) });
    }
  }

  if (req.method === 'POST') {
    const { password, ranges, sha } = req.body;
    if (password !== process.env.SCHEDULE_PASSWORD) {
      return res.status(403).json({ error: '암호가 일치하지 않습니다.' });
    }
    try {
      const current = await githubGet(FILE);
      const sorted = (ranges as { start: string; end: string }[])
        .sort((a, b) => a.start.localeCompare(b.start));
      const newSha = await githubPut(FILE, { ranges: sorted }, sha || current?.sha || null, 'Update exam periods');
      return res.json({ ok: true, sha: newSha });
    } catch (e) {
      return res.status(500).json({ error: String(e) });
    }
  }

  res.status(405).end();
}
