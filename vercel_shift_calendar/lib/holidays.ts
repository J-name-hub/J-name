export type HolidaysMap = Record<string, string[]>;

export async function fetchKoreanHolidays(year: number): Promise<HolidaysMap> {
  const key = process.env.HOLIDAY_API_KEY;
  if (!key) return {};

  const url = `http://apis.data.go.kr/B090041/openapi/service/SpcdeInfoService/getRestDeInfo?ServiceKey=${encodeURIComponent(
    key
  )}&solYear=${year}&numOfRows=100&_type=json`;

  const r = await fetch(url, { cache: "no-store" });
  if (!r.ok) return {};

  const data = await r.json().catch(() => null);
  if (!data?.response?.body?.items) return {};

  const items = data.response.body.items.item;
  const list = Array.isArray(items) ? items : items ? [items] : [];

  const out: HolidaysMap = {};
  for (const it of list) {
    const loc = String(it.locdate); // YYYYMMDD
    const y = loc.slice(0, 4);
    const m = loc.slice(4, 6);
    const d = loc.slice(6, 8);
    const dateStr = `${y}-${m}-${d}`;
    if (!out[dateStr]) out[dateStr] = [];
    out[dateStr].push(String(it.dateName));
  }
  return out;
}
