// pages/api/schedule.ts
import type { NextApiRequest, NextApiResponse } from 'next';
import { githubGet, githubPut } from '../../lib/github';

const FILE = process.env.GITHUB_SCHEDULE_PATH || 'shift_schedule.json';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method === 'GET') {
    try {
      const result = await githubGet(FILE);
      if (!result) return res.json({ data: {}, sha: null });
      return res.json(result);
    } catch (e) {
      return res.status(500).json({ error: String(e) });
    }
  }

  if (req.method === 'POST') {
    const { password, date, shift, sha } = req.body;
    if (password !== process.env.SCHEDULE_PASSWORD) {
      return res.status(403).json({ error: '암호가 일치하지 않습니다.' });
    }
    try {
      const current = await githubGet(FILE);
      const data = current?.data || {};
      data[date] = shift;
      const newSha = await githubPut(FILE, data, sha || current?.sha || null, 'Update schedule');
      return res.json({ ok: true, sha: newSha });
    } catch (e) {
      return res.status(500).json({ error: String(e) });
    }
  }

  res.status(405).end();
}
