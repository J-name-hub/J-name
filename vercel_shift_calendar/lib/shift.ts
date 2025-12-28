import { addDays, ymd } from "./date";

export type Team = "A" | "B" | "C" | "D";
export type Shift = "주" | "야" | "비" | "올";

export type TeamHistoryItem = { start_date: string; team: Team };
export type ScheduleMap = Record<string, Shift>;

const shifts: Shift[] = ["주", "야", "비", "비"];
const shiftPatterns: Record<Team, Shift[]> = {
  C: shifts,
  B: [shifts[3], shifts[0], shifts[1], shifts[2]],
  A: [shifts[2], shifts[3], shifts[0], shifts[1]],
  D: [shifts[1], shifts[2], shifts[3], shifts[0]],
};

export function getTeamForDate(dateObj: Date, history: TeamHistoryItem[]): Team {
  const sorted = [...history].sort((a, b) => a.start_date.localeCompare(b.start_date));
  let current: Team = (sorted[0]?.team ?? "A") as Team;
  for (const rec of sorted) {
    if (ymd(dateObj) >= rec.start_date) current = rec.team;
    else break;
  }
  return current;
}

export function getShiftByPattern(dateObj: Date, history: TeamHistoryItem[]): Shift {
  const team = getTeamForDate(dateObj, history);
  const base = new Date(2000, 0, 3); // 2000-01-03
  const diffDays = Math.floor((dateObj.getTime() - base.getTime()) / 86400000);
  const pattern = shiftPatterns[team];
  return pattern[((diffDays % pattern.length) + pattern.length) % pattern.length];
}

export function resolveShift(dateObj: Date, history: TeamHistoryItem[], schedule: ScheduleMap): Shift {
  const key = ymd(dateObj);
  return schedule[key] ?? getShiftByPattern(dateObj, history);
}

export function expandExamDates(ranges: Array<{ start: string; end: string }>): Set<string> {
  const set = new Set<string>();
  for (const r of ranges) {
    const sd = new Date(r.start);
    const ed = new Date(r.end);
    for (let d = new Date(sd); d <= ed; d = addDays(d, 1)) {
      set.add(ymd(d));
    }
  }
  return set;
}
