// pages/api/holidays.ts
import type { NextApiRequest, NextApiResponse } from 'next';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  const { year } = req.query;
  const apiKey = process.env.HOLIDAY_API_KEY;
  const url = `http://apis.data.go.kr/B090041/openapi/service/SpcdeInfoService/getRestDeInfo?ServiceKey=${apiKey}&solYear=${year}&numOfRows=100&_type=json`;

  try {
    const response = await fetch(url);
    const data = await response.json();
    const body = data?.response?.body;
    if (!body?.items) return res.json({});

    let items = body.items.item || [];
    if (!Array.isArray(items)) items = [items];

    const holidays: Record<string, string[]> = {};
    for (const item of items) {
      const dateStr = String(item.locdate);
      const key = `${dateStr.slice(0, 4)}-${dateStr.slice(4, 6)}-${dateStr.slice(6, 8)}`;
      if (!holidays[key]) holidays[key] = [];
      holidays[key].push(item.dateName);
    }
    res.setHeader('Cache-Control', 's-maxage=86400');
    return res.json(holidays);
  } catch (e) {
    return res.status(500).json({ error: String(e) });
  }
}
