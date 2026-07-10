// pages/index.tsx
import { useEffect, useState, useCallback, useMemo, useRef } from 'react';
import Head from 'next/head';
import {
  getTeamForDate, getShift, getMonthDays, getExamClass, formatDate, parseYMD, isInExamPeriod,
  SHIFT_COLORS, TeamHistory, ShiftType
} from '../lib/shiftLogic';
import { APP_VERSION } from '../lib/version';

const GRAD_COLOR = '#0066CC';
const EXAM_COLOR = '#FF6F00';
const HIGHLIGHTED_MONTH_DAYS = ['01-27', '03-01', '04-06'];
const AVAILABLE_TEAMS = ['A', 'B', 'C', 'D'];

// ── 스와이프 페이징 설정 ──────────────────────────────────────────
const SWIPE_DURATION = 300;                          // 스냅 애니메이션 시간(ms)
const SWIPE_EASING = 'cubic-bezier(0.22, 1, 0.36, 1)'; // iOS 느낌의 쫀쫀한(감속형) 곡선
const DISTANCE_RATIO = 0.25;                         // 화면 폭의 25% 이상 밀면 넘김
const FLICK_VELOCITY = 0.35;                         // 빠르게 튕기면(px/ms) 거리와 무관하게 넘김

type ExamRange = { start: string; end: string };
type SettleTarget = 'center' | 'next' | 'prev';

interface InitialData {
  scheduleData: Record<string, ShiftType>;
  scheduleSha: string | null;
  teamHistory: TeamHistory[];
  teamSha: string | null;
  gradDays: string[];
  gradSha: string | null;
  examRanges: ExamRange[];
  examSha: string | null;
  holidays: Record<string, string[]>;
}

function pad2(n: number) { return String(n).padStart(2, '0'); }

function getTodayKST(): Date {
  const now = new Date();
  const kst = new Date(now.toLocaleString('en-US', { timeZone: 'Asia/Seoul' }));
  return new Date(kst.getFullYear(), kst.getMonth(), kst.getDate());
}

// 캐시(Cache Storage / Service Worker)를 비우고 새로고침.
async function clearCachesAndReload() {
  try {
    if (typeof caches !== 'undefined') {
      const keys = await caches.keys();
      await Promise.all(keys.map(k => caches.delete(k)));
    }
    if ('serviceWorker' in navigator) {
      const regs = await navigator.serviceWorker.getRegistrations();
      await Promise.all(regs.map(r => r.unregister()));
    }
  } finally {
    const url = new URL(window.location.href);
    url.searchParams.set('v', Date.now().toString());
    window.location.replace(url.toString());
  }
}

function isValidMD(m: number, d: number): boolean {
  return Number.isInteger(m) && Number.isInteger(d) && m >= 1 && m <= 12 && d >= 1 && d <= 31;
}

function parseRangesText(text: string, year: number): { ranges: ExamRange[]; errors: string[] } {
  const tokens = text.replace(/\n/g, ',').split(',').map(t => t.trim()).filter(Boolean);
  const ranges: ExamRange[] = [];
  const errors: string[] = [];
  for (const t of tokens) {
    if (t.includes('~')) {
      const [l, r] = t.split('~').map(s => s.trim());
      const [lm, ld] = (l ?? '').split('/').map(Number);
      const [rm, rd] = (r ?? '').split('/').map(Number);
      if (!isValidMD(lm, ld) || !isValidMD(rm, rd)) { errors.push(t); continue; }
      const sd = `${year}-${pad2(lm)}-${pad2(ld)}`;
      const ed = `${year}-${pad2(rm)}-${pad2(rd)}`;
      ranges.push({ start: sd <= ed ? sd : ed, end: sd <= ed ? ed : sd });
    } else {
      const [m, d] = t.split('/').map(Number);
      if (!isValidMD(m, d)) { errors.push(t); continue; }
      const sd = `${year}-${pad2(m)}-${pad2(d)}`;
      ranges.push({ start: sd, end: sd });
    }
  }
  return { ranges, errors };
}

function parseDatesText(text: string, year: number): { dates: string[]; errors: string[] } {
  const tokens = text.replace(/\n/g, ',').split(',').map(t => t.trim()).filter(Boolean);
  const dates: string[] = [];
  const errors: string[] = [];
  for (const t of tokens) {
    const [m, d] = t.split('/').map(Number);
    if (!isValidMD(m, d)) { errors.push(t); continue; }
    dates.push(`${year}-${pad2(m)}-${pad2(d)}`);
  }
  return { dates, errors };
}

// 두 날짜 사이(포함)의 모든 날짜 문자열
function datesInRange(a: string, b: string): string[] {
  const [start, end] = a <= b ? [a, b] : [b, a];
  const out: string[] = [];
  let cur = parseYMD(start);
  const last = parseYMD(end);
  while (cur <= last) { out.push(formatDate(cur)); cur = new Date(cur.getTime() + 86400000); }
  return out;
}
function addExamRange(ranges: ExamRange[], start: string, end: string): ExamRange[] {
  const [s, e] = start <= end ? [start, end] : [end, start];
  return [...ranges, { start: s, end: e }].sort((a, b) => a.start.localeCompare(b.start));
}
// 지정한 날짜들을 시험기간에서 제거(겹치는 구간은 앞/뒤로 분할)
function removeDatesFromExamRanges(ranges: ExamRange[], dates: string[]): ExamRange[] {
  let result = ranges;
  for (const date of dates) {
    const next: ExamRange[] = [];
    for (const r of result) {
      if (date < r.start || date > r.end) { next.push(r); continue; }
      const d = parseYMD(date);
      const prev = formatDate(new Date(d.getTime() - 86400000));
      const nxt = formatDate(new Date(d.getTime() + 86400000));
      if (r.start <= prev) next.push({ start: r.start, end: prev });
      if (nxt <= r.end) next.push({ start: nxt, end: r.end });
    }
    result = next;
  }
  return result;
}

export default function Home({ initialData }: { initialData: InitialData }) {
  const [today] = useState(() => getTodayKST());
  const [year, setYear] = useState(today.getFullYear());
  const [month, setMonth] = useState(today.getMonth() + 1);
  const [view, setView] = useState<'month' | 'year'>('month');
  const [yearViewYear, setYearViewYear] = useState(today.getFullYear());
  const [scheduleData, setScheduleData] = useState<Record<string, ShiftType>>(initialData.scheduleData);
  const [scheduleSha, setScheduleSha] = useState<string | null>(initialData.scheduleSha);
  const [teamHistory, setTeamHistory] = useState<TeamHistory[]>(initialData.teamHistory);
  const [gradDays, setGradDays] = useState<string[]>(initialData.gradDays);
  const [gradSha, setGradSha] = useState<string | null>(initialData.gradSha);
  const [examRanges, setExamRanges] = useState<ExamRange[]>(initialData.examRanges);
  const [examSha, setExamSha] = useState<string | null>(initialData.examSha);
  const [holidays, setHolidays] = useState<Record<string, string[]>>(initialData.holidays);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [activeSection, setActiveSection] = useState<string | null>(null);
  const [msg, setMsg] = useState('');
  const [capturing, setCapturing] = useState(false);
  // 날짜 클릭 → 근무/대학원/시험 변경 팝업
  const [editTarget, setEditTarget] = useState<{ dateStr: string; shift: ShiftType; grad: boolean; exam: boolean } | null>(null);
  const [editShift, setEditShift] = useState<ShiftType>('주');
  const [editGrad, setEditGrad] = useState(false);
  const [editExam, setEditExam] = useState(false);
  const [schedPassword, setSchedPassword] = useState(''); // 세션 동안 암호 기억(메모리에만)
  const [saving, setSaving] = useState(false);
  const flashTimerRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  // 길게 눌러 드래그 → 연속 날짜 범위 선택 팝업
  const [rangeSel, setRangeSel] = useState<{ start: string; end: string } | null>(null);

  const calendarRef = useRef<HTMLDivElement>(null);
  const gradFormRef = useRef<HTMLFormElement>(null);
  const examFormRef = useRef<HTMLFormElement>(null);

  // ── 버전 체크(캐시 초기화) ────────────────────────────────────────
  // 청첩장 CacheManager와 동일한 방식:
  //  - 접속 시 + 5분마다 저장된 버전과 현재 버전을 비교
  //  - 첫 방문이면 버전만 기록
  //  - 버전이 바뀌었으면 캐시/스토리지/서비스워커를 정리 (강제 새로고침은 하지 않음)
  //    HTML은 항상 최신으로 받고 정적파일은 해시 파일명, 일정 데이터는 매번 새로 받아오므로
  //    강제 새로고침은 화면 깜빡임만 유발함. (수동 새로고침 버튼은 그대로 제공)
  useEffect(() => {
    const KEY = 'shiftcal_app_version';
    const checkVersion = () => {
      try {
        const stored = localStorage.getItem(KEY);
        const current = APP_VERSION.version;
        if (!stored) { localStorage.setItem(KEY, current); return; }
        if (stored !== current) {
          try { localStorage.clear(); sessionStorage.clear(); } catch { /* noop */ }
          if ('serviceWorker' in navigator) {
            navigator.serviceWorker.getRegistrations().then(rs => rs.forEach(r => r.unregister())).catch(() => {});
          }
          if ('caches' in window) {
            caches.keys().then(ns => ns.forEach(n => caches.delete(n))).catch(() => {});
          }
          localStorage.setItem(KEY, current);
        }
      } catch (e) { console.error('Version check failed:', e); }
    };
    checkVersion();
    const id = setInterval(checkVersion, 5 * 60 * 1000);
    return () => clearInterval(id);
  }, []);

  const loadHolidays = useCallback(async (y: number) => {
    try {
      const hol = await fetch(`/api/holidays?year=${y}`).then(r => r.json());
      if (hol && typeof hol === 'object') setHolidays(prev => ({ ...prev, ...hol }));
    } catch { /* 네트워크 오류 시 기존 값 유지 */ }
  }, []);

  const loadAll = useCallback(async () => {
    try {
      const [sch, team, grad, exam] = await Promise.all([
        fetch('/api/schedule').then(r => r.json()),
        fetch('/api/team').then(r => r.json()),
        fetch('/api/grad').then(r => r.json()),
        fetch('/api/exam').then(r => r.json()),
      ]);
      setScheduleData(sch.data || {});
      setScheduleSha(sch.sha);
      setTeamHistory(team.team_history || []);
      setGradDays(grad.dates || []);
      setGradSha(grad.sha);
      setExamRanges(exam.ranges || []);
      setExamSha(exam.sha);
    } catch { /* 오류 시 SSR 초기 데이터 유지 */ }
  }, []);

  useEffect(() => { loadAll(); }, [loadAll]);
  useEffect(() => { loadHolidays(year); }, [year, loadHolidays]);
  useEffect(() => { if (view === 'year') loadHolidays(yearViewYear); }, [view, yearViewYear, loadHolidays]);

  const getShiftForDate = useCallback((dateStr: string, dateObj: Date): ShiftType => {
    if (scheduleData[dateStr]) return scheduleData[dateStr];
    const team = getTeamForDate(dateObj, teamHistory);
    return getShift(dateObj, team);
  }, [scheduleData, teamHistory]);

  const todayStr = formatDate(today);

  function calculateWorkdays(y: number, m: number) {
    let count = 0;
    const days = getMonthDays(y, m);
    for (const week of days) {
      for (const d of week) {
        if (!d) continue;
        const dateStr = `${y}-${pad2(m)}-${pad2(d)}`;
        const dateObj = new Date(y, m - 1, d);
        const shift = getShiftForDate(dateStr, dateObj);
        if (['주', '야', '올'].includes(shift)) count++;
      }
    }
    return count;
  }

  function calculateWorkdaysUntil(y: number, m: number, until: Date) {
    let count = 0;
    const days = getMonthDays(y, m);
    for (const week of days) {
      for (const d of week) {
        if (!d) continue;
        const dateObj = new Date(y, m - 1, d);
        if (dateObj > until) return count;
        const dateStr = formatDate(dateObj);
        const shift = getShiftForDate(dateStr, dateObj);
        if (['주', '야', '올'].includes(shift)) count++;
      }
    }
    return count;
  }

  const totalWorkdays = calculateWorkdays(year, month);
  const firstDate = new Date(year, month - 1, 1);
  const lastDate = new Date(year, month, 0);
  let remainingWorkdays = totalWorkdays;
  if (lastDate < today) remainingWorkdays = 0;
  else if (firstDate <= today) remainingWorkdays = totalWorkdays - calculateWorkdaysUntil(year, month, today);

  const currentTeam = teamHistory.length ? getTeamForDate(today, teamHistory) : '미설정';

  // 상단 'Today' 버튼: 이번 달로 이동
  function goToday() { setYear(today.getFullYear()); setMonth(today.getMonth() + 1); }

  function navigateMonth(delta: number) {
    const d = new Date(year, month - 1 + delta, 1);
    setYear(d.getFullYear());
    setMonth(d.getMonth() + 1);
  }

  // ── 좌우 스와이프(3장 페이징, iOS 느낌) ──────────────────────────
  const viewportRef = useRef<HTMLDivElement>(null);
  const [phase, setPhase] = useState<'idle' | 'drag' | 'settle'>('idle');
  const [dragX, setDragX] = useState(0);
  const [settle, setSettle] = useState<SettleTarget>('center');
  const startRef = useRef({ x: 0, y: 0, w: 1 });
  const axisRef = useRef<null | 'h' | 'v'>(null);
  const lastMoveRef = useRef({ x: 0, t: 0 });
  const timerRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  const draggingRef = useRef(false);   // 실제 드래그 진행 여부(스테일 클로저 방지용 ref)
  const capturedRef = useRef<number | null>(null); // 가로 드래그 확정 후에만 포인터 캡처
  // 길게 눌러 드래그 → 범위 선택
  const longPressRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const rangeActiveRef = useRef(false);
  const rangeStartDateRef = useRef<string | null>(null);
  const rangeEndDateRef = useRef<string | null>(null);

  useEffect(() => () => {
    if (timerRef.current) clearTimeout(timerRef.current);
    if (longPressRef.current) clearTimeout(longPressRef.current);
    if (flashTimerRef.current) clearTimeout(flashTimerRef.current);
  }, []);

  const finalize = useCallback((target: SettleTarget) => {
    if (timerRef.current) clearTimeout(timerRef.current);
    setSettle(target);
    setPhase('settle');
    timerRef.current = setTimeout(() => {
      if (target === 'next') navigateMonth(1);
      else if (target === 'prev') navigateMonth(-1);
      setPhase('idle');
      setDragX(0);
      setSettle('center');
    }, SWIPE_DURATION + 20);
  }, [year, month]); // navigateMonth는 year/month 클로저에 의존

  function onSwipeDown(e: React.PointerEvent) {
    if (sidebarOpen || phase === 'settle') return;
    startRef.current = { x: e.clientX, y: e.clientY, w: calendarRef.current?.clientWidth || 1 };
    axisRef.current = null;
    lastMoveRef.current = { x: e.clientX, t: performance.now() };
    draggingRef.current = true;
    // 여기서는 캡처하지 않는다 → 자식 버튼/제목 클릭이 삼켜지지 않음(특히 PC 마우스)
    setPhase('drag');
    setDragX(0);
  }
  function onSwipeMove(e: React.PointerEvent) {
    if (!draggingRef.current) return;
    const dx = e.clientX - startRef.current.x;
    const dy = e.clientY - startRef.current.y;
    // 움직이면 롱프레스(범위선택) 후보 취소 → 스와이프/스크롤로 처리
    if (longPressRef.current && (Math.abs(dx) > 10 || Math.abs(dy) > 10)) {
      clearTimeout(longPressRef.current); longPressRef.current = null;
    }
    if (axisRef.current === null && (Math.abs(dx) > 8 || Math.abs(dy) > 8)) {
      axisRef.current = Math.abs(dx) > Math.abs(dy) ? 'h' : 'v';
      // 가로 드래그가 확정된 순간에만 포인터 캡처(클릭은 이 지점 전에 끝나므로 영향 없음)
      if (axisRef.current === 'h') {
        try { (e.currentTarget as HTMLElement).setPointerCapture(e.pointerId); capturedRef.current = e.pointerId; } catch { /* noop */ }
      }
    }
    if (axisRef.current === 'h') {
      // 한 화면 폭을 넘어가면 저항감(고무줄) 적용. dragX는 "페이지 비율"로 저장(제목/그리드 트랙 동기화용)
      const w = startRef.current.w;
      let v = dx;
      if (Math.abs(dx) > w) v = Math.sign(dx) * (w + (Math.abs(dx) - w) * 0.3);
      setDragX(v / w);
      lastMoveRef.current = { x: e.clientX, t: performance.now() };
    }
  }
  function onSwipeUp(e: React.PointerEvent) {
    if (!draggingRef.current) return;
    draggingRef.current = false;
    if (capturedRef.current !== null) {
      try { (e.currentTarget as HTMLElement).releasePointerCapture(capturedRef.current); } catch { /* noop */ }
      capturedRef.current = null;
    }
    const isH = axisRef.current === 'h';
    const dx = e.clientX - startRef.current.x;
    axisRef.current = null;
    if (!isH) { setPhase('idle'); setDragX(0); return; } // 탭/세로 스크롤 → 클릭은 정상 발생
    const w = startRef.current.w;
    const now = performance.now();
    const vel = (e.clientX - lastMoveRef.current.x) / Math.max(1, now - lastMoveRef.current.t);
    const far = Math.abs(dx) > w * DISTANCE_RATIO;
    const flick = Math.abs(vel) > FLICK_VELOCITY;
    let target: SettleTarget = 'center';
    if (dx < 0 && (far || flick)) target = 'next';       // 왼쪽으로 밀면 다음 달
    else if (dx > 0 && (far || flick)) target = 'prev';  // 오른쪽으로 밀면 이전 달
    finalize(target);
  }
  // 헤더 ‹ › 버튼도 같은 슬라이드 애니메이션 사용
  function pageBy(dir: 1 | -1) {
    if (phase === 'settle') return;
    finalize(dir === 1 ? 'next' : 'prev');
  }

  // ── 핀치 줌으로 월↔연 뷰 전환 ────────────────────────────────────
  const pointersRef = useRef<Map<number, { x: number; y: number }>>(new Map());
  const pinchStartRef = useRef(1);
  const pinchRatioRef = useRef(1);
  const pinchActiveRef = useRef(false);
  const [pinchScale, setPinchScale] = useState(1);
  const [pinchAnim, setPinchAnim] = useState(false);

  const distOf = (a: { x: number; y: number }, b: { x: number; y: number }) => Math.hypot(a.x - b.x, a.y - b.y);

  function openYear() { setYearViewYear(year); setPinchAnim(true); setPinchScale(1); setView('year'); }
  function closeYear() { setPinchAnim(true); setPinchScale(1); setView('month'); }
  function selectMonth(y: number, m: number) { setYear(y); setMonth(m); setPinchAnim(true); setPinchScale(1); setView('month'); }

  const dateAtPoint = (x: number, y: number): string | null => {
    const el = document.elementFromPoint(x, y);
    return (el?.closest?.('[data-date]') as HTMLElement | null)?.getAttribute('data-date') || null;
  };

  function onCalPointerDown(e: React.PointerEvent) {
    pointersRef.current.set(e.pointerId, { x: e.clientX, y: e.clientY });
    if (pointersRef.current.size === 2) {
      pinchActiveRef.current = true;
      // 진행 중이던 스와이프/롱프레스 취소
      draggingRef.current = false;
      if (longPressRef.current) { clearTimeout(longPressRef.current); longPressRef.current = null; }
      if (rangeActiveRef.current) { rangeActiveRef.current = false; clearRangeHighlight(); }
      if (capturedRef.current !== null) {
        try { (e.currentTarget as HTMLElement).releasePointerCapture(capturedRef.current); } catch { /* noop */ }
        capturedRef.current = null;
      }
      setPhase('idle'); setDragX(0); axisRef.current = null;
      const [p1, p2] = [...pointersRef.current.values()];
      pinchStartRef.current = distOf(p1, p2) || 1;
      pinchRatioRef.current = 1;
      setPinchAnim(false);
    } else if (pointersRef.current.size === 1 && !pinchActiveRef.current && view === 'month') {
      onSwipeDown(e); // 캡처는 가로 드래그 확정 후 onSwipeMove에서만
      // 길게 누르면(제자리로 400ms) 범위 선택 모드 진입
      const startDate = (e.target as HTMLElement)?.closest?.('[data-date]')?.getAttribute('data-date') || null;
      if (startDate) {
        const el = e.currentTarget as HTMLElement;
        const pid = e.pointerId;
        rangeStartDateRef.current = startDate;
        rangeEndDateRef.current = startDate;
        if (longPressRef.current) clearTimeout(longPressRef.current);
        longPressRef.current = setTimeout(() => {
          longPressRef.current = null;
          rangeActiveRef.current = true;
          draggingRef.current = false;              // 스와이프 취소
          setPhase('idle'); setDragX(0); axisRef.current = null;
          try { el.setPointerCapture(pid); capturedRef.current = pid; } catch { /* noop */ }
          if (typeof navigator !== 'undefined' && navigator.vibrate) { try { navigator.vibrate(15); } catch { /* noop */ } }
          highlightRange(startDate, startDate);
        }, 400);
      }
    }
  }
  function onCalPointerMove(e: React.PointerEvent) {
    if (pointersRef.current.has(e.pointerId)) pointersRef.current.set(e.pointerId, { x: e.clientX, y: e.clientY });
    // 범위 선택 중: 포인터 아래 날짜까지 하이라이트
    if (rangeActiveRef.current) {
      const d = dateAtPoint(e.clientX, e.clientY);
      if (d) { rangeEndDateRef.current = d; highlightRange(rangeStartDateRef.current, d); }
      return;
    }
    if (pinchActiveRef.current && pointersRef.current.size >= 2) {
      const [p1, p2] = [...pointersRef.current.values()];
      const r = distOf(p1, p2) / pinchStartRef.current;
      pinchRatioRef.current = r;
      const s = view === 'month' ? Math.min(1, Math.max(0.72, r)) : Math.min(1.4, Math.max(1, r));
      setPinchScale(s);
      return;
    }
    if (!pinchActiveRef.current) onSwipeMove(e);
  }
  function onCalPointerUp(e: React.PointerEvent) {
    if (longPressRef.current) { clearTimeout(longPressRef.current); longPressRef.current = null; }
    // 범위 선택 종료 → 팝업 열기
    if (rangeActiveRef.current) {
      rangeActiveRef.current = false;
      pointersRef.current.delete(e.pointerId);
      if (capturedRef.current !== null) {
        try { (e.currentTarget as HTMLElement).releasePointerCapture(capturedRef.current); } catch { /* noop */ }
        capturedRef.current = null;
      }
      clearRangeHighlight();
      const s = rangeStartDateRef.current || '';
      const en = rangeEndDateRef.current || s;
      const [start, end] = s <= en ? [s, en] : [en, s];
      if (start && end && start !== end) {
        setRangeSel({ start, end });
      } else if (start) {
        // 한 칸만 선택됨 → 단일 편집 팝업
        openScheduleEditor(start, getShiftForDate(start, parseYMD(start)));
      }
      return;
    }
    const wasPinch = pinchActiveRef.current;
    pointersRef.current.delete(e.pointerId);
    try { (e.currentTarget as HTMLElement).releasePointerCapture(e.pointerId); } catch { /* noop */ }
    if (wasPinch) {
      if (pointersRef.current.size < 2) {
        const r = pinchRatioRef.current;
        setPinchAnim(true);
        setPinchScale(1);
        if (view === 'month' && r < 0.8) openYear();
        else if (view === 'year' && r > 1.2) closeYear();
        if (pointersRef.current.size === 0) pinchActiveRef.current = false;
      }
      return;
    }
    onSwipeUp(e);
    if (pointersRef.current.size === 0) pinchActiveRef.current = false;
  }

  const zoomStyle: React.CSSProperties = { transform: `scale(${pinchScale})` };

  const trackStyle: React.CSSProperties =
    phase === 'drag'
      ? { transform: `translate3d(${(dragX * 100).toFixed(3)}%,0,0)`, transition: 'none' }
      : phase === 'settle'
        ? {
            transform: settle === 'next' ? 'translate3d(-100%,0,0)' : settle === 'prev' ? 'translate3d(100%,0,0)' : 'translate3d(0,0,0)',
            transition: `transform ${SWIPE_DURATION}ms ${SWIPE_EASING}`,
          }
        : { transform: 'translate3d(0,0,0)', transition: 'none' };

  // ── 이미지 다운로드/공유 ─────────────────────────────────────────
  async function handleDownloadImage() {
    if (!calendarRef.current) return;
    setCapturing(true);
    try {
      const html2canvas = (await import('html2canvas')).default;
      const canvas = await html2canvas(calendarRef.current, {
        backgroundColor: '#ffffff',
        scale: 2,
        useCORS: true,
        logging: false,
      });
      const filename = `근무달력_${year}년${month}월.png`;
      if (typeof navigator.share === 'function' && typeof navigator.canShare === 'function') {
        canvas.toBlob(async (blob) => {
          if (!blob) { triggerDownload(canvas, filename); return; }
          const file = new File([blob], filename, { type: 'image/png' });
          if (navigator.canShare({ files: [file] })) {
            await navigator.share({ files: [file], title: `${year}년 ${month}월 근무달력` });
          } else {
            triggerDownload(canvas, filename);
          }
        }, 'image/png');
      } else {
        triggerDownload(canvas, filename);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setCapturing(false);
    }
  }

  function triggerDownload(canvas: HTMLCanvasElement, filename: string) {
    const link = document.createElement('a');
    link.download = filename;
    link.href = canvas.toDataURL('image/png');
    link.click();
  }

  async function handleScheduleChange(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    const password = fd.get('password') as string;
    const date = fd.get('date') as string;
    const shift = fd.get('shift') as string;
    const res = await fetch('/api/schedule', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ password, date, shift, sha: scheduleSha }),
    });
    const data = await res.json();
    if (data.ok) {
      setMsg('✅ 스케줄이 저장되었습니다.');
      setScheduleData(prev => ({ ...prev, [date]: shift as ShiftType }));
      setScheduleSha(data.sha);
    } else {
      setMsg(`❌ ${data.error}`);
    }
    setTimeout(() => setMsg(''), 3000);
  }

  async function handleTeamChange(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    const password = fd.get('password') as string;
    const team = fd.get('team') as string;
    const startDate = fd.get('start_date') as string;
    const map: Record<string, string> = {};
    for (const h of teamHistory) map[h.start_date] = h.team;
    map[startDate] = team;
    const newHistory = Object.entries(map)
      .sort((a, b) => a[0].localeCompare(b[0]))
      .map(([start_date, team]) => ({ start_date, team: team as TeamHistory['team'] }));
    const res = await fetch('/api/team', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ password, team_history: newHistory }),
    });
    const data = await res.json();
    if (data.ok) {
      setMsg('✅ 조 설정이 저장되었습니다.');
      setTeamHistory(newHistory);
    } else {
      setMsg(`❌ ${data.error}`);
    }
    setTimeout(() => setMsg(''), 3000);
  }

  async function handleGradSave(formEl: HTMLFormElement, isDelete: boolean) {
    const fd = new FormData(formEl);
    const password = fd.get('password') as string;
    const textRaw = fd.get('dates') as string;
    const targetYear = parseInt(fd.get('year') as string);
    if (!Number.isInteger(targetYear)) { setMsg('❌ 연도를 확인해주세요.'); setTimeout(() => setMsg(''), 3000); return; }
    const { dates, errors } = parseDatesText(textRaw, targetYear);
    if (errors.length) setMsg(`⚠️ 무시된 항목: ${errors.join(', ')}`);
    const current = new Set(gradDays);
    if (isDelete) dates.forEach(d => current.delete(d));
    else dates.forEach(d => current.add(d));
    const sorted = [...current].sort();
    const res = await fetch('/api/grad', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ password, dates: sorted, sha: gradSha }),
    });
    const data = await res.json();
    if (data.ok) {
      setMsg(isDelete ? '✅ 날짜가 삭제되었습니다.' : '✅ 날짜가 저장되었습니다.');
      setGradDays(sorted);
      setGradSha(data.sha);
    } else {
      setMsg(`❌ ${data.error}`);
    }
    setTimeout(() => setMsg(''), 3000);
  }

  async function handleExamSave(formEl: HTMLFormElement, isDelete: boolean) {
    const fd = new FormData(formEl);
    const password = fd.get('password') as string;
    const textRaw = fd.get('ranges') as string;
    const targetYear = parseInt(fd.get('year') as string);
    if (!Number.isInteger(targetYear)) { setMsg('❌ 연도를 확인해주세요.'); setTimeout(() => setMsg(''), 3000); return; }
    const { ranges, errors } = parseRangesText(textRaw, targetYear);
    if (errors.length) setMsg(`⚠️ 무시된 항목: ${errors.join(', ')}`);
    const currentSet = new Set(examRanges.map(r => `${r.start}|${r.end}`));
    if (isDelete) ranges.forEach(r => currentSet.delete(`${r.start}|${r.end}`));
    else ranges.forEach(r => currentSet.add(`${r.start}|${r.end}`));
    const merged = [...currentSet].map(s => { const [start, end] = s.split('|'); return { start, end }; }).sort((a, b) => a.start.localeCompare(b.start));
    const res = await fetch('/api/exam', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ password, ranges: merged, sha: examSha }),
    });
    const data = await res.json();
    if (data.ok) {
      setMsg(isDelete ? '✅ 기간이 삭제되었습니다.' : '✅ 기간이 저장되었습니다.');
      setExamRanges(merged);
      setExamSha(data.sha);
    } else {
      setMsg(`❌ ${data.error}`);
    }
    setTimeout(() => setMsg(''), 3000);
  }

  // ── 특정 달의 한 페이지(주 행 + 하단 요약) 렌더 ────────────────────
  // ── 날짜 클릭 → 근무/대학원/시험 변경 ────────────────────────────
  const flashCell = useCallback((dateStr: string) => {
    const el = calendarRef.current?.querySelector(`.cal-page-cur [data-date="${dateStr}"]`) as HTMLElement | null;
    if (!el) return;
    el.classList.remove('flash');
    void el.offsetWidth;            // 리플로우로 애니메이션 재시작
    el.classList.add('flash');
    if (flashTimerRef.current) clearTimeout(flashTimerRef.current);
    flashTimerRef.current = setTimeout(() => el.classList.remove('flash'), 1400);
  }, []);

  const openScheduleEditor = useCallback((dateStr: string, currentShift: ShiftType) => {
    const grad = gradDays.includes(dateStr);
    const exam = isInExamPeriod(dateStr, examRanges);
    setEditTarget({ dateStr, shift: currentShift, grad, exam });
    setEditShift(currentShift);
    setEditGrad(grad);
    setEditExam(exam);
    flashCell(dateStr);
  }, [gradDays, examRanges, flashCell]);

  function closeEditor() { setEditTarget(null); }

  // 공통 저장 헬퍼 (실패 시 msg 설정 후 false 반환)
  async function saveShiftDate(date: string, shift: ShiftType): Promise<boolean> {
    const res = await fetch('/api/schedule', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ password: schedPassword, date, shift, sha: scheduleSha }),
    });
    const data = await res.json();
    if (data.ok) { setScheduleData(prev => ({ ...prev, [date]: shift })); setScheduleSha(data.sha); return true; }
    setMsg(`❌ ${data.error}`); return false;
  }
  async function saveGradDates(newDates: string[]): Promise<boolean> {
    const sorted = [...new Set(newDates)].sort();
    const res = await fetch('/api/grad', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ password: schedPassword, dates: sorted, sha: gradSha }),
    });
    const data = await res.json();
    if (data.ok) { setGradDays(sorted); setGradSha(data.sha); return true; }
    setMsg(`❌ ${data.error}`); return false;
  }
  async function saveExamRanges(newRanges: ExamRange[]): Promise<boolean> {
    const sorted = [...newRanges].sort((a, b) => a.start.localeCompare(b.start));
    const res = await fetch('/api/exam', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ password: schedPassword, ranges: sorted, sha: examSha }),
    });
    const data = await res.json();
    if (data.ok) { setExamRanges(sorted); setExamSha(data.sha); return true; }
    setMsg(`❌ ${data.error}`); return false;
  }

  async function saveEditor() {
    if (!editTarget || saving) return;
    const { dateStr } = editTarget;
    setSaving(true);
    let ok = true;
    try {
      if (editShift !== editTarget.shift) ok = (await saveShiftDate(dateStr, editShift)) && ok;
      if (ok && editGrad !== editTarget.grad) {
        const nd = editGrad ? [...gradDays, dateStr] : gradDays.filter(d => d !== dateStr);
        ok = (await saveGradDates(nd)) && ok;
      }
      if (ok && editExam !== editTarget.exam) {
        const nr = editExam ? addExamRange(examRanges, dateStr, dateStr) : removeDatesFromExamRanges(examRanges, [dateStr]);
        ok = (await saveExamRanges(nr)) && ok;
      }
      if (ok) { setMsg('✅ 저장되었습니다.'); setEditTarget(null); }
    } catch {
      setMsg('❌ 저장에 실패했습니다.');
    } finally {
      setSaving(false);
      setTimeout(() => setMsg(''), 3000);
    }
  }
  function editorDateLabel(dateStr: string) {
    const [y, m, d] = dateStr.split('-').map(Number);
    const wd = ['일', '월', '화', '수', '목', '금', '토'][new Date(y, m - 1, d).getDay()];
    return `${m}월 ${d}일 (${wd})`;
  }

  // ── 범위(길게 눌러 드래그) 선택 후 일괄 적용 ──────────────────────
  function rangeLabel(r: { start: string; end: string }) {
    const [, sm, sd] = r.start.split('-').map(Number);
    const [, em, ed] = r.end.split('-').map(Number);
    const n = datesInRange(r.start, r.end).length;
    if (r.start === r.end) return `${sm}/${sd} (1일)`;
    return `${sm}/${sd} ~ ${em}/${ed} (${n}일)`;
  }
  async function applyRangeGrad(on: boolean) {
    if (!rangeSel || saving) return;
    setSaving(true);
    try {
      const ds = datesInRange(rangeSel.start, rangeSel.end);
      const nd = on ? [...gradDays, ...ds] : gradDays.filter(d => !ds.includes(d));
      if (await saveGradDates(nd)) { setMsg(on ? '✅ 대학원으로 지정했습니다.' : '✅ 대학원을 해제했습니다.'); setRangeSel(null); }
    } finally { setSaving(false); setTimeout(() => setMsg(''), 3000); }
  }
  async function applyRangeExam(on: boolean) {
    if (!rangeSel || saving) return;
    setSaving(true);
    try {
      const nr = on ? addExamRange(examRanges, rangeSel.start, rangeSel.end)
                    : removeDatesFromExamRanges(examRanges, datesInRange(rangeSel.start, rangeSel.end));
      if (await saveExamRanges(nr)) { setMsg(on ? '✅ 시험기간으로 지정했습니다.' : '✅ 시험기간을 해제했습니다.'); setRangeSel(null); }
    } finally { setSaving(false); setTimeout(() => setMsg(''), 3000); }
  }
  async function applyRangeShift(shift: ShiftType) {
    if (!rangeSel || saving) return;
    setSaving(true);
    try {
      const ds = datesInRange(rangeSel.start, rangeSel.end);
      let ok = true;
      for (const d of ds) { ok = (await saveShiftDate(d, shift)) && ok; if (!ok) break; } // 파일 충돌 방지 위해 순차 저장
      if (ok) { setMsg(`✅ ${ds.length}일 근무를 '${shift}'(으)로 변경했습니다.`); setRangeSel(null); }
    } finally { setSaving(false); setTimeout(() => setMsg(''), 3000); }
  }

  // 범위 선택 중 하이라이트(리렌더 없이 DOM에 직접 표시)
  function highlightRange(a: string | null, b: string | null) {
    const root = calendarRef.current?.querySelector('.cal-page-cur');
    if (!root || !a || !b) return;
    const [mn, mx] = a <= b ? [a, b] : [b, a];
    root.querySelectorAll('[data-date]').forEach(el => {
      const d = (el as HTMLElement).getAttribute('data-date') || '';
      (el as HTMLElement).classList.toggle('range-sel', d >= mn && d <= mx);
    });
  }
  function clearRangeHighlight() {
    calendarRef.current?.querySelectorAll('.range-sel').forEach(el => el.classList.remove('range-sel'));
  }

  const renderMonthBody = useCallback((y: number, m: number) => {
    const weeks = getMonthDays(y, m);
    const mm = pad2(m);
    const first = `${y}-${mm}-01`;
    const last = `${y}-${mm}-${pad2(new Date(y, m, 0).getDate())}`;
    const mGrad = gradDays.filter(d => d.startsWith(`${y}-${mm}-`));
    const mExam = examRanges.filter(r => !(r.end < first || r.start > last));

    // 공휴일 요약(해당 달)
    const monthHols: Record<string, string[]> = {};
    for (const [k, v] of Object.entries(holidays)) {
      if (parseInt(k.split('-')[1]) === m && parseInt(k.split('-')[0]) === y) monthHols[k] = v;
    }
    const holKeys = Object.keys(monthHols).sort();
    const holParts: string[] = [];
    for (let i = 0; i < holKeys.length;) {
      const start = holKeys[i];
      const startDay = parseInt(start.split('-')[2]);
      const names = monthHols[start];
      let endDay = startDay;
      let j = i + 1;
      while (j < holKeys.length) {
        const nextDay = parseInt(holKeys[j].split('-')[2]);
        if (nextDay - endDay === 1 && monthHols[holKeys[j]].some(n => names.includes(n))) { endDay = nextDay; j++; }
        else break;
      }
      if (startDay === endDay) holParts.push(`${startDay}일: ${names.join(', ')}`);
      else holParts.push(`${startDay}일~${endDay}일: ${names.join(', ')}`);
      i = j;
    }
    const holDesc = holParts.join(' / ');

    return (
      <>
        {weeks.map((week, wi) => (
          <div key={`week-${wi}`} className="cal-row">
            {week.map((day, di) => {
              if (!day) return <div key={`empty-${wi}-${di}`} className="cal-cell" />;
              const dateStr = `${y}-${mm}-${pad2(day)}`;
              const monthDay = `${mm}-${pad2(day)}`;
              const dateObj = new Date(y, m - 1, day);
              const isWeekend = di === 0 || di === 6;
              const isHoliday = !!holidays[dateStr];
              const isGrad = gradDays.includes(dateStr);
              const isHighlighted = HIGHLIGHTED_MONTH_DAYS.includes(monthDay);
              const examClass = getExamClass(dateStr, examRanges);
              const isToday = dateStr === todayStr;
              const shift = getShiftForDate(dateStr, dateObj);
              const { bg, color } = SHIFT_COLORS[shift];
              const dayColor = isGrad ? GRAD_COLOR : (isWeekend || isHoliday ? 'red' : 'black');
              return (
                <div key={dateStr} className="cal-cell">
                  <div
                    className={`cal-cell-inner clickable ${isToday ? 'today' : ''} ${examClass}`}
                    data-date={dateStr}
                    onClick={() => openScheduleEditor(dateStr, shift)}
                    title="탭: 근무/대학원/시험 변경 · 길게 눌러 드래그: 범위 선택"
                  >
                    <div className="cal-day" style={{ color: dayColor, backgroundColor: isHighlighted ? '#FFB6C1' : 'transparent' }}>
                      {day}
                    </div>
                    <div className="cal-shift" style={shift !== '비' ? { backgroundColor: bg, color } : { color: 'transparent' }}>
                      {shift !== '비' ? shift : '비'}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        ))}

        <div className="cal-footer">
          {mGrad.length > 0 && <span style={{ color: GRAD_COLOR, fontWeight: 700 }}>대학원</span>}
          {mGrad.length > 0 && mExam.length > 0 && ' | '}
          {mExam.length > 0 && (
            <span style={{ color: EXAM_COLOR, fontWeight: 700 }}>
              시험기간: {mExam.map(r => {
                const [, sm, sd] = r.start.split('-').map(Number);
                const [, em, ed] = r.end.split('-').map(Number);
                if (r.start === r.end) return `${sm}/${sd}`;
                return `${sm}/${sd}~${em}/${ed}`;
              }).join(', ')}
            </span>
          )}
          {(mGrad.length > 0 || mExam.length > 0) && holDesc && ' | '}
          {holDesc}
        </div>
      </>
    );
  }, [gradDays, examRanges, holidays, todayStr, getShiftForDate, openScheduleEditor]);

  // 이전/현재/다음 달 좌표
  const prevD = new Date(year, month - 2, 1);
  const nextD = new Date(year, month, 1);
  const prevY = prevD.getFullYear(), prevM = prevD.getMonth() + 1;
  const nextY = nextD.getFullYear(), nextM = nextD.getMonth() + 1;

  // 드래그 중에는 매 프레임 리렌더되므로 세 페이지 그리드는 메모이즈해 성능 확보
  const prevBody = useMemo(() => renderMonthBody(prevY, prevM), [renderMonthBody, prevY, prevM]);
  const curBody = useMemo(() => renderMonthBody(year, month), [renderMonthBody, year, month]);
  const nextBody = useMemo(() => renderMonthBody(nextY, nextM), [renderMonthBody, nextY, nextM]);

  // 상단 제목(연·월)도 그리드와 함께 슬라이드
  const renderTitle = (y: number, m: number) => (
    <div className="cal-title tappable" onClick={openYear} title="연 보기">
      <span className="cal-year">{y}.</span>
      <span className="cal-month">{m}</span>
      <span className="cal-year">월</span>
      <span className="caret">▾</span>
    </div>
  );

  // ── 연 뷰용 미니 달력 ────────────────────────────────────────────
  const renderMiniMonth = useCallback((y: number, m: number) => {
    const weeks = getMonthDays(y, m);
    const mm = pad2(m);
    return (
      <button type="button" key={m} className="mini-month" onClick={() => selectMonth(y, m)}>
        <div className="mini-title">{m}월</div>
        <div className="mini-grid">
          {['일', '월', '화', '수', '목', '금', '토'].map((d, i) => (
            <span key={`h${i}`} className="mini-wday" style={{ color: i === 0 || i === 6 ? '#e03131' : '#adb5bd' }}>{d}</span>
          ))}
          {weeks.flat().map((day, idx) => {
            if (!day) return <span key={idx} className="mini-cell" />;
            const dateStr = `${y}-${mm}-${pad2(day)}`;
            const dateObj = new Date(y, m - 1, day);
            const shift = getShiftForDate(dateStr, dateObj);
            const { bg } = SHIFT_COLORS[shift];
            const work = shift === '주' || shift === '야' || shift === '올';
            const di = idx % 7;
            const isWeekend = di === 0 || di === 6;
            const isHoliday = !!holidays[dateStr];
            const isToday = dateStr === todayStr;
            return (
              <span
                key={idx}
                className={`mini-cell ${isToday ? 'mini-today' : ''}`}
                style={{ background: work ? bg : 'transparent', color: isWeekend || isHoliday ? '#e03131' : '#495057' }}
              >
                {day}
              </span>
            );
          })}
        </div>
      </button>
    );
  }, [getShiftForDate, holidays, todayStr]); // eslint-disable-line react-hooks/exhaustive-deps

  const yearGrid = useMemo(
    () => Array.from({ length: 12 }, (_, i) => renderMiniMonth(yearViewYear, i + 1)),
    [renderMiniMonth, yearViewYear]
  );


  const monthOptions: { year: number; month: number }[] = [];
  for (let i = -5; i <= 5; i++) {
    const d = new Date(year, month - 1 + i, 1);
    monthOptions.push({ year: d.getFullYear(), month: d.getMonth() + 1 });
  }
  const MONTH_NAMES = ['1월', '2월', '3월', '4월', '5월', '6월', '7월', '8월', '9월', '10월', '11월', '12월'];

  return (
    <>
      <Head>
        <title>교대근무 달력</title>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700&display=swap" rel="stylesheet" />
      </Head>

      <div className="app">
        {sidebarOpen && <div className="overlay" onClick={() => setSidebarOpen(false)} />}

        <aside className={`sidebar ${sidebarOpen ? 'open' : ''}`}>
          <div className="sidebar-header">
            <span>⚙️ 설정</span>
            <button onClick={() => setSidebarOpen(false)}>✕</button>
          </div>
          <div className="sidebar-content">
            <div className="sidebar-stat">👥 현재 근무조: <strong>{currentTeam}조</strong></div>
            <div className="sidebar-stat">📋 {month}월 근무일수: <strong>{totalWorkdays}일</strong></div>
            <div className="sidebar-stat-sub">오늘 제외 남은 일수: <strong>{remainingWorkdays}일</strong></div>
            <div className="sidebar-stat">🔁 AB → DA → CD → BC</div>
            {msg && <div className="msg">{msg}</div>}

            <div className="section">
              <label className="section-label">📅 월 이동</label>
              <select className="select" value={`${year}-${month}`} onChange={e => {
                const [y, m] = e.target.value.split('-').map(Number);
                setYear(y); setMonth(m);
              }}>
                {monthOptions.map(o => (
                  <option key={`${o.year}-${o.month}`} value={`${o.year}-${o.month}`}>
                    {o.year}년 {MONTH_NAMES[o.month - 1]}
                  </option>
                ))}
              </select>
            </div>

            <div className="section">
              <button className="section-toggle" onClick={() => setActiveSection(activeSection === 'team' ? null : 'team')}>
                👥 조 설정 {activeSection === 'team' ? '▲' : '▼'}
              </button>
              {activeSection === 'team' && (
                <form onSubmit={handleTeamChange} className="form">
                  <select name="team" className="select">
                    {AVAILABLE_TEAMS.map(t => <option key={t} value={t}>{t}조</option>)}
                  </select>
                  <input type="date" name="start_date" defaultValue={formatDate(today)} className="input" />
                  <input type="password" name="password" placeholder="암호 입력" className="input" />
                  <button type="submit" className="btn">조 설정 저장</button>
                </form>
              )}
            </div>

            <div className="section">
              <button className="section-toggle" onClick={() => setActiveSection(activeSection === 'schedule' ? null : 'schedule')}>
                📝 스케줄 변경 {activeSection === 'schedule' ? '▲' : '▼'}
              </button>
              {activeSection === 'schedule' && (
                <form onSubmit={handleScheduleChange} className="form">
                  <input type="date" name="date" defaultValue={formatDate(today)} className="input" />
                  <select name="shift" className="select">
                    {['주', '야', '비', '올'].map(s => <option key={s} value={s}>{s}</option>)}
                  </select>
                  <input type="password" name="password" placeholder="암호 입력" className="input" />
                  <button type="submit" className="btn">스케줄 변경 저장</button>
                </form>
              )}
            </div>

            <div className="section">
              <button className="section-toggle" onClick={() => setActiveSection(activeSection === 'grad' ? null : 'grad')}>
                🎓 대학원 날짜 편집 {activeSection === 'grad' ? '▲' : '▼'}
              </button>
              {activeSection === 'grad' && (
                <form ref={gradFormRef} onSubmit={e => e.preventDefault()} className="form">
                  <input type="number" name="year" defaultValue={today.getFullYear()} className="input" placeholder="연도" />
                  <textarea name="dates" placeholder="8/15, 8/17, 12/3" className="textarea" rows={3} />
                  <input type="password" name="password" placeholder="암호 입력" className="input" />
                  <div className="btn-row">
                    <button type="button" className="btn" onClick={() => gradFormRef.current && handleGradSave(gradFormRef.current, false)}>저장</button>
                    <button type="button" className="btn btn-del" onClick={() => gradFormRef.current && handleGradSave(gradFormRef.current, true)}>삭제</button>
                  </div>
                </form>
              )}
            </div>

            <div className="section">
              <button className="section-toggle" onClick={() => setActiveSection(activeSection === 'exam' ? null : 'exam')}>
                📚 시험기간 편집 {activeSection === 'exam' ? '▲' : '▼'}
              </button>
              {activeSection === 'exam' && (
                <form ref={examFormRef} onSubmit={e => e.preventDefault()} className="form">
                  <input type="number" name="year" defaultValue={today.getFullYear()} className="input" placeholder="연도" />
                  <textarea name="ranges" placeholder="9/15~9/19, 12/2~12/3, 9/20" className="textarea" rows={3} />
                  <input type="password" name="password" placeholder="암호 입력" className="input" />
                  <div className="btn-row">
                    <button type="button" className="btn" onClick={() => examFormRef.current && handleExamSave(examFormRef.current, false)}>저장</button>
                    <button type="button" className="btn btn-del" onClick={() => examFormRef.current && handleExamSave(examFormRef.current, true)}>삭제</button>
                  </div>
                </form>
              )}
            </div>

            <div className="section">
              <button className="section-toggle" onClick={clearCachesAndReload}>
                🔄 캐시 비우고 새로고침
              </button>
              <div className="version-tag">버전 {APP_VERSION.version} · {APP_VERSION.buildTime.slice(0, 10)}</div>
            </div>
          </div>
        </aside>

        <main className="main">
          <div className="top-bar">
            <button className="menu-btn" onClick={() => setSidebarOpen(true)}>☰</button>
            <span className="top-title">교대근무 달력</span>
            <div className="top-actions">
              <button className="today-btn" onClick={goToday}>Today</button>
              <button
                className="download-btn"
                onClick={handleDownloadImage}
                disabled={capturing}
                title="이미지로 저장"
              >
                {capturing ? '⏳' : '📷'}
              </button>
            </div>
          </div>

          {/* 캡처 대상 영역 — 핀치 줌으로 월↔연 뷰 전환 */}
          <div
            ref={calendarRef}
            className="calendar-container"
            style={{ touchAction: 'pan-y' }}
            onPointerDown={onCalPointerDown}
            onPointerMove={onCalPointerMove}
            onPointerUp={onCalPointerUp}
            onPointerCancel={onCalPointerUp}
          >
            <div key={view} className={`zoomable view-enter ${pinchAnim ? 'zoom-anim' : ''}`} style={zoomStyle}>
              {view === 'month' ? (
                <>
                  <div className="cal-header">
                    <button className="nav-btn" onClick={() => pageBy(-1)}>‹</button>
                    <div className="cal-title-viewport">
                      <div className="cal-title-track" style={trackStyle}>
                        <div className="cal-tpage cal-tpage-prev">{renderTitle(prevY, prevM)}</div>
                        <div className="cal-tpage cal-tpage-cur">{renderTitle(year, month)}</div>
                        <div className="cal-tpage cal-tpage-next">{renderTitle(nextY, nextM)}</div>
                      </div>
                    </div>
                    <button className="nav-btn" onClick={() => pageBy(1)}>›</button>
                  </div>

                  {/* 요일 헤더는 고정, 그리드만 좌우로 슬라이드 */}
                  <div className="cal-weekdays">
                    {['일', '월', '화', '수', '목', '금', '토'].map((d, i) => (
                      <div key={d} className="cal-wday" style={{ color: i === 0 || i === 6 ? 'red' : '#495057' }}>{d}</div>
                    ))}
                  </div>

                  <div
                    ref={viewportRef}
                    className={`cal-viewport ${phase === 'drag' ? 'dragging' : ''}`}
                  >
                    <div className="cal-track" style={trackStyle}>
                      <div className="cal-page cal-page-prev">{prevBody}</div>
                      <div className="cal-page cal-page-cur">{curBody}</div>
                      <div className="cal-page cal-page-next">{nextBody}</div>
                    </div>
                  </div>
                </>
              ) : (
                <>
                  <div className="cal-header">
                    <button className="nav-btn" onClick={() => setYearViewYear(y => y - 1)}>‹</button>
                    <div className="cal-title tappable" onClick={closeYear} title="월 보기로 돌아가기">
                      <span className="cal-month">{yearViewYear}</span>
                      <span className="cal-year"> 년</span>
                    </div>
                    <button className="nav-btn" onClick={() => setYearViewYear(y => y + 1)}>›</button>
                  </div>
                  <div className="year-grid">{yearGrid}</div>
                </>
              )}
            </div>
          </div>

        </main>

        {/* 날짜 클릭 → 근무/대학원/시험 변경 팝업 */}
        {editTarget && (
          <div className="edit-overlay" onClick={closeEditor}>
            <div className="edit-card" onClick={e => e.stopPropagation()}>
              <div className="edit-title">{editorDateLabel(editTarget.dateStr)}</div>
              <div className="edit-label">근무</div>
              <div className="edit-shifts">
                {(['주', '야', '비', '올'] as ShiftType[]).map(s => {
                  const { bg, color } = SHIFT_COLORS[s];
                  const sel = editShift === s;
                  return (
                    <button
                      key={s}
                      type="button"
                      className={`edit-shift ${sel ? 'sel' : ''}`}
                      style={{ backgroundColor: bg, color }}
                      onClick={() => setEditShift(s)}
                    >
                      {s}
                    </button>
                  );
                })}
              </div>
              <div className="edit-toggles">
                <button type="button" className={`edit-toggle ${editGrad ? 'on' : ''}`} onClick={() => setEditGrad(v => !v)}>
                  🎓 대학원 {editGrad ? 'ON' : 'OFF'}
                </button>
                <button type="button" className={`edit-toggle ${editExam ? 'on' : ''}`} onClick={() => setEditExam(v => !v)}>
                  📚 시험기간 {editExam ? 'ON' : 'OFF'}
                </button>
              </div>
              <input
                type="password"
                placeholder="암호 입력"
                value={schedPassword}
                onChange={e => setSchedPassword(e.target.value)}
                className="edit-input"
                onKeyDown={e => { if (e.key === 'Enter') saveEditor(); }}
              />
              <div className="edit-actions">
                <button type="button" className="edit-btn edit-cancel" onClick={closeEditor}>취소</button>
                <button type="button" className="edit-btn edit-save" onClick={saveEditor} disabled={saving}>
                  {saving ? '저장 중…' : '저장'}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* 길게 눌러 드래그 → 범위 일괄 설정 팝업 */}
        {rangeSel && (
          <div className="edit-overlay" onClick={() => !saving && setRangeSel(null)}>
            <div className="edit-card" onClick={e => e.stopPropagation()}>
              <div className="edit-title">{rangeLabel(rangeSel)} 일괄 설정</div>
              <input
                type="password"
                placeholder="암호 입력"
                value={schedPassword}
                onChange={e => setSchedPassword(e.target.value)}
                className="edit-input"
              />
              <div className="edit-label">🎓 대학원</div>
              <div className="edit-shifts">
                <button type="button" className="edit-btn edit-set" disabled={saving} onClick={() => applyRangeGrad(true)}>지정</button>
                <button type="button" className="edit-btn edit-clear" disabled={saving} onClick={() => applyRangeGrad(false)}>해제</button>
              </div>
              <div className="edit-label">📚 시험기간</div>
              <div className="edit-shifts">
                <button type="button" className="edit-btn edit-set" disabled={saving} onClick={() => applyRangeExam(true)}>지정</button>
                <button type="button" className="edit-btn edit-clear" disabled={saving} onClick={() => applyRangeExam(false)}>해제</button>
              </div>
              <div className="edit-label">근무 일괄 변경</div>
              <div className="edit-shifts">
                {(['주', '야', '비', '올'] as ShiftType[]).map(s => {
                  const { bg, color } = SHIFT_COLORS[s];
                  return (
                    <button key={s} type="button" className="edit-shift" style={{ backgroundColor: bg, color }} disabled={saving} onClick={() => applyRangeShift(s)}>
                      {s}
                    </button>
                  );
                })}
              </div>
              <div className="edit-actions">
                <button type="button" className="edit-btn edit-cancel" onClick={() => setRangeSel(null)} disabled={saving}>닫기</button>
              </div>
              {saving && <div className="edit-saving">저장 중…</div>}
            </div>
          </div>
        )}

        {/* 사이드바가 닫혀 있어도 보이는 알림 */}
        {msg && !sidebarOpen && <div className="toast">{msg}</div>}
      </div>

      <style jsx global>{`
        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: 'Noto Sans KR', sans-serif; background: #f0f2f5; }
        .app { display: flex; min-height: 100vh; position: relative; }

        .overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.4); z-index: 100; }
        .sidebar {
          position: fixed; top: 0; left: -300px; width: 300px; height: 100vh;
          background: #1e1e2e; color: #cdd6f4; z-index: 200;
          transition: left 0.3s ease; overflow-y: auto;
        }
        .sidebar.open { left: 0; }
        .sidebar-header {
          display: flex; justify-content: space-between; align-items: center;
          padding: 16px; background: #181825; font-size: 16px; font-weight: 700;
          position: sticky; top: 0;
        }
        .sidebar-header button { background: none; border: none; color: #cdd6f4; font-size: 18px; cursor: pointer; }
        .sidebar-content { padding: 12px; }
        .sidebar-stat { padding: 8px 4px; font-size: 14px; border-bottom: 1px solid #313244; }
        .sidebar-stat-sub { padding: 4px 4px 8px; font-size: 13px; color: #a6adc8; border-bottom: 1px solid #313244; }
        .msg { margin: 8px 0; padding: 8px; background: #313244; border-radius: 6px; font-size: 13px; }
        .section { margin-top: 8px; }
        .section-label { display: block; font-size: 13px; color: #a6adc8; margin-bottom: 4px; }
        .section-toggle {
          width: 100%; text-align: left; background: #313244; border: none;
          color: #cdd6f4; padding: 10px; border-radius: 6px; cursor: pointer; font-size: 13px; font-weight: 600;
        }
        .section-toggle:hover { background: #45475a; }
        .version-tag { padding: 6px 4px 0; font-size: 11px; color: #6c7086; }
        .form { padding: 10px 4px; display: flex; flex-direction: column; gap: 8px; }
        .input, .select, .textarea {
          width: 100%; padding: 8px; border: 1px solid #45475a; border-radius: 6px;
          background: #313244; color: #cdd6f4; font-size: 13px;
        }
        .textarea { resize: vertical; }
        .btn {
          padding: 8px 12px; background: #89b4fa; color: #1e1e2e; border: none;
          border-radius: 6px; cursor: pointer; font-size: 13px; font-weight: 700;
        }
        .btn:hover { background: #74c7ec; }
        .btn-del { background: #f38ba8; }
        .btn-del:hover { background: #eba0ac; }
        .btn-row { display: flex; gap: 8px; }
        .btn-row .btn { flex: 1; }

        .main { flex: 1; display: flex; flex-direction: column; align-items: center; padding: 0 0 32px; }
        .top-bar {
          width: 100%; display: flex; align-items: center; justify-content: space-between;
          padding: 12px 16px; background: #343a40; color: white; position: sticky; top: 0; z-index: 50;
        }
        .top-actions { display: flex; align-items: center; gap: 8px; }
        .menu-btn, .today-btn {
          background: #495057; border: none; color: white; padding: 6px 14px;
          border-radius: 6px; cursor: pointer; font-size: 14px; font-weight: 600;
        }
        .menu-btn:hover, .today-btn:hover { background: #6c757d; }
        .top-title { font-size: 16px; font-weight: 700; }

        .download-btn {
          background: #495057; border: none; color: white;
          width: 36px; height: 36px; border-radius: 6px;
          cursor: pointer; font-size: 18px;
          display: flex; align-items: center; justify-content: center;
          transition: background 0.2s;
        }
        .download-btn:hover { background: #6c757d; }
        .download-btn:disabled { opacity: 0.5; cursor: wait; }

        .calendar-container {
          width: min(800px, 98vw); margin: 16px auto 0;
          background: white; border-radius: 12px; overflow: hidden;
          box-shadow: 0 4px 16px rgba(0,0,0,0.12);
        }
        .cal-header {
          background: #343a40; color: white; display: flex;
          align-items: center; justify-content: space-between; padding: 6px 16px;
        }
        .nav-btn {
          background: none; border: none; color: white; font-size: 28px;
          cursor: pointer; padding: 4px 14px; line-height: 1;
          position: relative; z-index: 2; border-radius: 8px;
        }
        .nav-btn:hover { color: #adb5bd; }
        .nav-btn:active { background: rgba(255,255,255,0.14); }
        .cal-title { text-align: center; }
        .cal-title.tappable {
          display: inline-flex; align-items: center; cursor: pointer; user-select: none;
          padding: 2px 10px; border-radius: 8px;   /* 클릭 영역을 글자 주변으로만 한정 */
        }
        .cal-title.tappable:active { background: rgba(255,255,255,0.14); }
        .cal-title .caret { font-size: 13px; margin-left: 4px; opacity: 0.65; vertical-align: 2px; }
        .cal-year { font-size: 18px; }
        .cal-month { font-size: 30px; font-weight: 700; margin: 0 2px; }

        /* 상단 제목도 그리드와 함께 좌우 슬라이드 */
        .cal-title-viewport { flex: 1; overflow: hidden; position: relative; }
        .cal-title-track { position: relative; will-change: transform; }
        .cal-tpage { width: 100%; text-align: center; }   /* 가운데 정렬 → 제목은 글자폭만 차지 */
        .cal-tpage-cur { position: relative; }
        .cal-tpage-prev { position: absolute; top: 0; left: -100%; }
        .cal-tpage-next { position: absolute; top: 0; left: 100%; }

        /* 월↔연 뷰 줌 전환 */
        .zoomable { transform-origin: center 42%; }
        .zoomable.zoom-anim { transition: transform 0.2s ease; }
        .view-enter { animation: viewIn 0.24s ease; }
        @keyframes viewIn { from { opacity: 0; transform: scale(0.94); } to { opacity: 1; transform: scale(1); } }

        /* 연 뷰 */
        .year-grid {
          display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px;
          padding: 14px; background: white;
        }
        .mini-month {
          background: #fff; border: 1px solid #e9ecef; border-radius: 8px;
          padding: 6px 5px; cursor: pointer; text-align: center; font-family: inherit;
          display: flex; flex-direction: column; gap: 4px;
          transition: background 0.15s, border-color 0.15s, transform 0.1s;
        }
        .mini-month:hover { background: #f1f3f5; border-color: #ced4da; }
        .mini-month:active { transform: scale(0.97); }
        .mini-title { font-size: 13px; font-weight: 700; color: #343a40; }
        .mini-grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 1px; }
        .mini-wday { font-size: 8px; line-height: 1; padding-bottom: 1px; }
        .mini-cell {
          font-size: 9px; line-height: 1; aspect-ratio: 1 / 1;
          display: flex; align-items: center; justify-content: center;
          border-radius: 2px; color: #495057;
        }
        .mini-today { outline: 1.5px solid #007bff; outline-offset: -1px; font-weight: 700; }

        .cal-weekdays {
          display: grid; grid-template-columns: repeat(7, 1fr);
          background: #f8f9fa; border-bottom: 1px solid #dee2e6; padding: 4px 0;
        }
        .cal-wday { text-align: center; font-size: 16px; font-weight: 700; padding: 4px; }

        /* 좌우 페이징: 요일 헤더 아래 그리드 영역만 슬라이드 */
        .cal-viewport {
          position: relative; overflow: hidden;
          touch-action: pan-y;          /* 세로 스크롤 허용, 가로 제스처는 직접 처리 */
        }
        .cal-viewport.dragging { user-select: none; cursor: grabbing; }
        .cal-track { position: relative; will-change: transform; }
        .cal-page { width: 100%; }
        .cal-page-cur { position: relative; }               /* 흐름에 포함 → 뷰포트 높이 결정 */
        .cal-page-prev { position: absolute; top: 0; left: -100%; }
        .cal-page-next { position: absolute; top: 0; left: 100%; }

        .cal-row {
          display: grid; grid-template-columns: repeat(7, 1fr);
          border-bottom: 1px solid #dee2e6;
        }
        .cal-row:last-of-type { border-bottom: none; }
        .cal-cell { height: 56px; position: relative; }
        .cal-cell-inner {
          position: relative; height: 100%; display: flex; flex-direction: column;
          align-items: center; justify-content: center; gap: 2px;
          width: 100%; box-sizing: border-box;
        }
        .cal-cell-inner.today {
          border: 2.5px solid #007bff; background: #e8f0fe; border-radius: 4px; z-index: 2;
        }
        .cal-day {
          font-size: 15px; font-weight: 700; border-radius: 4px;
          padding: 1px 6px; min-width: 26px; text-align: center; position: relative; z-index: 1;
        }
        .cal-shift {
          font-size: 15px; font-weight: 700; border-radius: 3px;
          padding: 0 4px; min-width: 26px; text-align: center; position: relative; z-index: 1;
        }
        .cal-footer {
          padding: 8px 12px; font-size: 14px; font-weight: 600;
          background: #f8f9fa; color: #343a40;
        }

        .cal-cell-inner.clickable { cursor: pointer; }
        @media (hover: hover) {
          .cal-cell-inner.clickable:hover { background: #eef2ff; border-radius: 4px; }
        }
        /* 클릭 직후 잠깐(1.4초) 반짝 — 오늘(파랑)과 구분되도록 앰버색 링 */
        .cal-cell-inner.flash { animation: cellFlash 1.4s ease-out; border-radius: 4px; }
        @keyframes cellFlash {
          0%   { box-shadow: inset 0 0 0 3px rgba(245,159,0,0.95); background: rgba(245,159,0,0.20); }
          70%  { box-shadow: inset 0 0 0 3px rgba(245,159,0,0.55); background: rgba(245,159,0,0.10); }
          100% { box-shadow: inset 0 0 0 3px rgba(245,159,0,0);    background: transparent; }
        }
        /* 범위 선택 중 하이라이트 */
        .cal-cell-inner.range-sel { background: rgba(51,102,204,0.20); border-radius: 3px; box-shadow: inset 0 0 0 1.5px rgba(51,102,204,0.55); }

        /* 근무 변경 팝업 */
        .edit-overlay {
          position: fixed; inset: 0; background: rgba(0,0,0,0.45);
          z-index: 300; display: flex; align-items: center; justify-content: center; padding: 20px;
        }
        .edit-card {
          background: #fff; border-radius: 14px; padding: 20px;
          width: min(340px, 92vw); box-shadow: 0 12px 40px rgba(0,0,0,0.25);
          animation: viewIn 0.18s ease;
        }
        .edit-title { font-size: 17px; font-weight: 700; color: #343a40; text-align: center; margin-bottom: 16px; }
        .edit-shifts { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; margin-bottom: 14px; }
        .edit-shift {
          padding: 14px 0; border: 2px solid transparent; border-radius: 10px;
          font-size: 18px; font-weight: 700; cursor: pointer; font-family: inherit;
          box-shadow: inset 0 0 0 1px #e9ecef;
        }
        .edit-shift.sel { border-color: #343a40; transform: translateY(-1px); box-shadow: 0 3px 8px rgba(0,0,0,0.18); }
        .edit-shift:disabled { opacity: 0.6; cursor: wait; }
        .edit-label { font-size: 12px; font-weight: 700; color: #868e96; margin: 2px 2px 6px; }
        .edit-toggles { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 14px; }
        .edit-toggle {
          padding: 11px 0; border: none; border-radius: 10px; cursor: pointer; font-family: inherit;
          font-size: 13px; font-weight: 700; background: #e9ecef; color: #868e96;
          box-shadow: inset 0 0 0 1px #dee2e6;
        }
        .edit-toggle.on { background: #343a40; color: #fff; box-shadow: none; }
        .edit-input {
          width: 100%; padding: 11px; border: 1px solid #ced4da; border-radius: 8px;
          font-size: 14px; margin-bottom: 14px; background: #fff; color: #212529;
        }
        .edit-actions { display: flex; gap: 8px; }
        .edit-btn {
          flex: 1; padding: 11px 0; border: none; border-radius: 8px;
          font-size: 15px; font-weight: 700; cursor: pointer; font-family: inherit;
        }
        .edit-btn:disabled { opacity: 0.6; cursor: wait; }
        .edit-cancel { background: #e9ecef; color: #495057; }
        .edit-cancel:hover { background: #dee2e6; }
        .edit-save { background: #343a40; color: #fff; }
        .edit-save:hover { background: #212529; }
        .edit-set { background: #364fc7; color: #fff; }
        .edit-set:hover { background: #2b3fa0; }
        .edit-clear { background: #e9ecef; color: #495057; }
        .edit-clear:hover { background: #dee2e6; }
        .edit-saving { text-align: center; font-size: 13px; color: #868e96; margin-top: 10px; }

        .toast {
          position: fixed; top: 64px; left: 50%; transform: translateX(-50%);
          background: #343a40; color: #fff; padding: 10px 18px; border-radius: 999px;
          font-size: 14px; font-weight: 600; z-index: 400; box-shadow: 0 4px 16px rgba(0,0,0,0.25);
          max-width: 90vw; text-align: center;
        }

        .cal-cell-inner.exam-band::before {
          content: ''; position: absolute; z-index: 0; pointer-events: none;
          top: 0; bottom: 0; left: 0; right: 0;
          background: #FFF3E0; border-top: 2px solid ${EXAM_COLOR}; border-bottom: 2px solid ${EXAM_COLOR};
        }
        .cal-cell-inner.exam-start::before { border-left: 2px solid ${EXAM_COLOR}; border-radius: 14px 0 0 14px; }
        .cal-cell-inner.exam-end::before { border-right: 2px solid ${EXAM_COLOR}; border-radius: 0 14px 14px 0; }
        .cal-cell-inner.exam-single::before { border: 2px solid ${EXAM_COLOR}; border-radius: 14px; }

        @media (max-width: 480px) {
          .cal-cell { height: 48px; }
          .cal-day, .cal-shift { font-size: 13px; }
          .cal-wday { font-size: 13px; }
          .year-grid { gap: 6px; padding: 8px; }
          .mini-month { padding: 5px 3px; }
          .mini-cell { font-size: 8px; }
          .mini-wday { font-size: 7px; }
          .mini-title { font-size: 12px; }
        }
      `}</style>
    </>
  );
}

export const getStaticProps = async () => {
  const { githubGet } = await import('../lib/github');

  const today = new Date(new Date().toLocaleString('en-US', { timeZone: 'Asia/Seoul' }));
  const year = today.getFullYear();

  try {
    const [sch, team, grad, exam, hol] = await Promise.all([
      githubGet(process.env.GITHUB_SCHEDULE_PATH || 'vercel_shift_calendar/shift_schedule.json'),
      githubGet('vercel_shift_calendar/team_settings.json'),
      githubGet('vercel_shift_calendar/grad_days.json'),
      githubGet('vercel_shift_calendar/exam_periods.json'),
      (async () => {
        const apiKey = process.env.HOLIDAY_API_KEY;
        if (!apiKey) return {};
        try {
          const url = `http://apis.data.go.kr/B090041/openapi/service/SpcdeInfoService/getRestDeInfo?ServiceKey=${apiKey}&solYear=${year}&numOfRows=100&_type=json`;
          const res = await fetch(url);
          const data = await res.json();
          const body = data?.response?.body;
          if (!body?.items) return {};
          let items = body.items.item || [];
          if (!Array.isArray(items)) items = [items];
          const holidays: Record<string, string[]> = {};
          for (const item of items) {
            const dateStr = String(item.locdate);
            const key = `${dateStr.slice(0, 4)}-${dateStr.slice(4, 6)}-${dateStr.slice(6, 8)}`;
            if (!holidays[key]) holidays[key] = [];
            holidays[key].push(item.dateName);
          }
          return holidays;
        } catch { return {}; }
      })(),
    ]);

    const initialData: InitialData = {
      scheduleData: sch?.data || {},
      scheduleSha: sch?.sha ?? null,
      teamHistory: team?.data?.team_history || [{ start_date: '2000-01-03', team: 'A' }],
      teamSha: team?.sha ?? null,
      gradDays: grad?.data?.dates || [],
      gradSha: grad?.sha ?? null,
      examRanges: exam?.data?.ranges || [],
      examSha: exam?.sha ?? null,
      holidays: (hol as Record<string, string[]>) || {},
    };

    return { props: { initialData }, revalidate: 5 };
  } catch (e) {
    console.error('getStaticProps error:', e);
    const initialData: InitialData = {
      scheduleData: {},
      scheduleSha: null,
      teamHistory: [{ start_date: '2000-01-03', team: 'A' }],
      teamSha: null,
      gradDays: [],
      gradSha: null,
      examRanges: [],
      examSha: null,
      holidays: {},
    };
    return { props: { initialData }, revalidate: 5 };
  }
};
