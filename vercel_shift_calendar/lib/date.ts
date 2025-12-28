export const TZ = "Asia/Seoul";

export function ymd(d: Date): string {
  const yyyy = d.getFullYear();
  const mm = String(d.getMonth() + 1).padStart(2, "0");
  const dd = String(d.getDate()).padStart(2, "0");
  return `${yyyy}-${mm}-${dd}`;
}

export function parseYmd(s: string): Date {
  // s = YYYY-MM-DD
  const [y, m, d] = s.split("-").map((x) => Number(x));
  return new Date(y, m - 1, d);
}

export function addDays(d: Date, days: number): Date {
  const nd = new Date(d);
  nd.setDate(nd.getDate() + days);
  return nd;
}

export function monthMatrix(year: number, month1: number): (number | null)[] {
  // month1 = 1..12
  const first = new Date(year, month1 - 1, 1);
  const last = new Date(year, month1, 0);
  const daysInMonth = last.getDate();

  // Sunday=0 .. Saturday=6, and we want Sunday-first like original streamlit
  const startW = first.getDay();
  const cells: (number | null)[] = [];
  for (let i = 0; i < startW; i++) cells.push(null);
  for (let d = 1; d <= daysInMonth; d++) cells.push(d);
  while (cells.length % 7 !== 0) cells.push(null);
  return cells;
}
