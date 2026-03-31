// pages/api/team.ts
import type { NextApiRequest, NextApiResponse } from 'next';
import { githubGet, githubPut } from '../../lib/github';

const FILE = 'team_settings.json';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method === 'GET') {
    try {
      const result = await githubGet(FILE);
      if (!result) return res.json({ team_history: [{ start_date: '2000-01-03', team: 'A' }], sha: null });
      return res.json({ team_history: result.data.team_history, sha: result.sha });
    } catch (e) {
      return res.status(500).json({ error: String(e) });
    }
  }

  if (req.method === 'POST') {
    const { password, team_history } = req.body;
    if (password !== process.env.SCHEDULE_PASSWORD) {
      return res.status(403).json({ error: '암호가 일치하지 않습니다.' });
    }
    try {
      const current = await githubGet(FILE);
      const newSha = await githubPut(FILE, { team_history }, current?.sha || null, 'Update team settings');
      return res.json({ ok: true, sha: newSha });
    } catch (e) {
      return res.status(500).json({ error: String(e) });
    }
  }

  res.status(405).end();
}
