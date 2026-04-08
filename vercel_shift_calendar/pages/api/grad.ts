// pages/api/grad.ts
import type { NextApiRequest, NextApiResponse } from 'next';
import { githubGet, githubPut } from '../../lib/github';

const FILE = 'vercel_shift_calendar/grad_days.json';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method === 'GET') {
    try {
      const result = await githubGet(FILE);
      if (!result) return res.json({ dates: [], sha: null });
      return res.json({ dates: result.data.dates || [], sha: result.sha });
    } catch (e) {
      return res.status(500).json({ error: String(e) });
    }
  }

  if (req.method === 'POST') {
    const { password, dates, sha } = req.body;
    if (password !== process.env.SCHEDULE_PASSWORD) {
      return res.status(403).json({ error: '암호가 일치하지 않습니다.' });
    }
    try {
      const current = await githubGet(FILE);
      const sorted = [...new Set(dates as string[])].sort();
      const newSha = await githubPut(FILE, { dates: sorted }, sha || current?.sha || null, 'Update grad days');
      return res.json({ ok: true, sha: newSha });
    } catch (e) {
      return res.status(500).json({ error: String(e) });
    }
  }

  res.status(405).end();
}
