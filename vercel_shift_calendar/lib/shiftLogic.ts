// lib/shiftLogic.ts

export type ShiftType = '주' | '야' | '비' | '올';
export type TeamType = 'A' | 'B' | 'C' | 'D';

export interface TeamHistory {
  start_date: string;
  team: TeamType;
}

const BASE_DATE = new Date(2000, 0, 3); // 2000-01-03

const SHIFTS: ShiftType[] = ['주', '야', '비', '비'];

export const SHIFT_PATTERNS: Record<TeamType, ShiftType[]> = {
  C: SHIFTS,
  B: [...SHIFTS.slice(-1), ...SHIFTS.slice(0, -1)] as ShiftType[],
  A: [...SHIFTS.slice(-2), ...SHIFTS.slice(0, -2)] as ShiftType[],
  D: [...SHIFTS.slice(-3), ...SHIFTS.slice(0, -3)] as ShiftType[],
};

export const SHIFT_COLORS: Record<ShiftType, { bg: string; color: string }> = {
  주: { bg: 'yellow', color: 'black' },
  야: { bg: 'lightgray', color: 'black' },
  비: { bg: 'white', color: 'black' },
  올: { bg: 'lightblue', color: 'black' },
};

export function getTeamForDate(targetDate: Date, teamHistory: TeamHistory[]): TeamType {
  const sorted = [...teamHistory].sort((a, b) => a.start_date.localeCompare(b.start_date));
  let currentTeam: TeamType = sorted[0]?.team || 'A';
  const targetStr = formatDate(targetDate);
  for (const record of sorted) {
    if (targetStr >= record.start_date) {
      currentTeam = record.team;
    } else {
      break;
    }
  }
  return currentTeam;
}

export function getShift(targetDate: Date, team: TeamType): ShiftType {
  const deltaDays = Math.floor(
    (targetDate.getTime() - BASE_DATE.getTime()) / (1000 * 60 * 60 * 24)
  );
  const pattern = SHIFT_PATTERNS[team];
  return pattern[((deltaDays % pattern.length) + pattern.length) % pattern.length];
}

export function formatDate(date: Date): string {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, '0');
  const d = String(date.getDate()).padStart(2, '0');
  return `${y}-${m}-${d}`;
}

export function getMonthDays(year: number, month: number): number[][] {
  // Returns weeks array, week starts on Sunday (0)
  const firstDay = new Date(year, month - 1, 1).getDay();
  const daysInMonth = new Date(year, month, 0).getDate();
  const weeks: number[][] = [];
  let week: number[] = Array(firstDay).fill(0);

  for (let d = 1; d <= daysInMonth; d++) {
    week.push(d);
    if (week.length === 7) {
      weeks.push(week);
      week = [];
    }
  }
  if (week.length > 0) {
    while (week.length < 7) week.push(0);
    weeks.push(week);
  }
  return weeks;
}

export function isInExamPeriod(dateStr: string, examRanges: { start: string; end: string }[]): boolean {
  return examRanges.some(r => dateStr >= r.start && dateStr <= r.end);
}

export function getExamClass(
  dateStr: string,
  examRanges: { start: string; end: string }[]
): string {
  if (!isInExamPeriod(dateStr, examRanges)) return '';

  const date = new Date(dateStr);
  const prev = formatDate(new Date(date.getTime() - 86400000));
  const next = formatDate(new Date(date.getTime() + 86400000));
  const prevIn = isInExamPeriod(prev, examRanges);
  const nextIn = isInExamPeriod(next, examRanges);

  if (prevIn && nextIn) return 'exam-band exam-mid';
  if (prevIn && !nextIn) return 'exam-band exam-end';
  if (!prevIn && nextIn) return 'exam-band exam-start';
  return 'exam-band exam-single';
}
