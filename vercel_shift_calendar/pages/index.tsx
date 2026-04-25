// pages/index.tsx
import { useEffect, useState, useCallback, useRef } from 'react';
import Head from 'next/head';
import {
  getTeamForDate, getShift, getMonthDays, getExamClass, formatDate,
  SHIFT_COLORS, TeamHistory, ShiftType
} from '../lib/shiftLogic';

const GRAD_COLOR = '#0066CC';
const EXAM_COLOR = '#FF6F00';
const HIGHLIGHTED_MONTH_DAYS = ['01-27', '03-01', '04-06'];
const AVAILABLE_TEAMS = ['A', 'B', 'C', 'D'];

type ExamRange = { start: string; end: string };

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

function getTodayKST(): Date {
  const now = new Date();
  const kst = new Date(now.toLocaleString('en-US', { timeZone: 'Asia/Seoul' }));
  return new Date(kst.getFullYear(), kst.getMonth(), kst.getDate());
}

function parseRangesText(text: string, year: number): { ranges: ExamRange[]; errors: string[] } {
  const tokens = text.replace(/\n/g, ',').split(',').map(t => t.trim()).filter(Boolean);
  const ranges: ExamRange[] = [];
  const errors: string[] = [];
  for (const t of tokens) {
    try {
      if (t.includes('~')) {
        const [l, r] = t.split('~').map(s => s.trim());
        const [lm, ld] = l.split('/').map(Number);
        const [rm, rd] = r.split('/').map(Number);
        const sd = `${year}-${String(lm).padStart(2,'0')}-${String(ld).padStart(2,'0')}`;
        const ed = `${year}-${String(rm).padStart(2,'0')}-${String(rd).padStart(2,'0')}`;
        ranges.push({ start: sd <= ed ? sd : ed, end: sd <= ed ? ed : sd });
      } else {
        const [m, d] = t.split('/').map(Number);
        const sd = `${year}-${String(m).padStart(2,'0')}-${String(d).padStart(2,'0')}`;
        ranges.push({ start: sd, end: sd });
      }
    } catch { errors.push(t); }
  }
  return { ranges, errors };
}

function parseDatesText(text: string, year: number): { dates: string[]; errors: string[] } {
  const tokens = text.split(',').map(t => t.trim()).filter(Boolean);
  const dates: string[] = [];
  const errors: string[] = [];
  for (const t of tokens) {
    try {
      const [m, d] = t.split('/').map(Number);
      dates.push(`${year}-${String(m).padStart(2,'0')}-${String(d).padStart(2,'0')}`);
    } catch { errors.push(t); }
  }
  return { dates, errors };
}

export default function Home({ initialData }: { initialData: InitialData }) {
  // useState로 today 고정 — 매 렌더마다 재계산되면 자정 근처에서 날짜 비교가 꼬일 수 있음
  const [today] = useState(() => getTodayKST());
  const [year, setYear] = useState(today.getFullYear());
  const [month, setMonth] = useState(today.getMonth() + 1);
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

  const calendarRef = useRef<HTMLDivElement>(null);
  const gradFormRef = useRef<HTMLFormElement>(null);
  const examFormRef = useRef<HTMLFormElement>(null);

  // 연도 변경 시 공휴일만 다시 로드
  const loadHolidays = useCallback(async (y: number) => {
    const hol = await fetch(`/api/holidays?year=${y}`).then(r => r.json());
    setHolidays(hol || {});
  }, []);

  // 백그라운드 전체 리프레시 (데이터 변경 반영)
  const loadAll = useCallback(async () => {
    const [sch, team, grad, exam, hol] = await Promise.all([
      fetch('/api/schedule').then(r => r.json()),
      fetch('/api/team').then(r => r.json()),
      fetch('/api/grad').then(r => r.json()),
      fetch('/api/exam').then(r => r.json()),
      fetch(`/api/holidays?year=${year}`).then(r => r.json()),
    ]);
    setScheduleData(sch.data || {});
    setScheduleSha(sch.sha);
    setTeamHistory(team.team_history || []);
    setGradDays(grad.dates || []);
    setGradSha(grad.sha);
    setExamRanges(exam.ranges || []);
    setExamSha(exam.sha);
    setHolidays(hol || {});
  }, [year]);

  // 마운트 후 백그라운드 리프레시 (SSR 데이터가 최신인지 확인)
  useEffect(() => { loadAll(); }, []); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    loadHolidays(year);
  }, [year, loadHolidays]);

  function getShiftForDate(dateStr: string, dateObj: Date): ShiftType {
    if (scheduleData[dateStr]) return scheduleData[dateStr];
    const team = getTeamForDate(dateObj, teamHistory);
    return getShift(dateObj, team);
  }

  const weeks = getMonthDays(year, month);
  const todayStr = formatDate(today);

  function calculateWorkdays(y: number, m: number) {
    let count = 0;
    const days = getMonthDays(y, m);
    for (const week of days) {
      for (const d of week) {
        if (!d) continue;
        const dateStr = `${y}-${String(m).padStart(2,'0')}-${String(d).padStart(2,'0')}`;
        const dateObj = new Date(y, m-1, d);
        const shift = getShiftForDate(dateStr, dateObj);
        if (['주','야','올'].includes(shift)) count++;
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
        const dateObj = new Date(y, m-1, d);
        if (dateObj > until) return count;
        const dateStr = formatDate(dateObj);
        const shift = getShiftForDate(dateStr, dateObj);
        if (['주','야','올'].includes(shift)) count++;
      }
    }
    return count;
  }

  const totalWorkdays = calculateWorkdays(year, month);
  const firstDate = new Date(year, month-1, 1);
  const lastDate = new Date(year, month, 0);
  let remainingWorkdays = totalWorkdays;
  if (lastDate < today) remainingWorkdays = 0;
  else if (firstDate <= today) remainingWorkdays = totalWorkdays - calculateWorkdaysUntil(year, month, today);

  const currentTeam = teamHistory.length ? getTeamForDate(today, teamHistory) : '미설정';

  function navigateMonth(delta: number) {
    const d = new Date(year, month - 1 + delta, 1);
    setYear(d.getFullYear());
    setMonth(d.getMonth() + 1);
  }

  // ── 이미지 다운로드/공유 ─────────────────────────────────────────
  async function handleDownloadImage() {
    if (!calendarRef.current) return;
    setCapturing(true);
    try {
      const html2canvas = (await import('html2canvas')).default;
      const canvas = await html2canvas(calendarRef.current, {
        backgroundColor: '#ffffff',
        scale: 2,        // 레티나 2x 해상도
        useCORS: true,
        logging: false,
      });

      const filename = `근무달력_${year}년${month}월.png`;

      // 모바일: Web Share API로 사진 앱에 바로 저장 가능
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
        // PC: 파일 다운로드
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
  // ────────────────────────────────────────────────────────────────

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
    const { ranges, errors } = parseRangesText(textRaw, targetYear);
    if (errors.length) setMsg(`⚠️ 무시된 항목: ${errors.join(', ')}`);
    const currentSet = new Set(examRanges.map(r => `${r.start}|${r.end}`));
    if (isDelete) ranges.forEach(r => currentSet.delete(`${r.start}|${r.end}`));
    else ranges.forEach(r => currentSet.add(`${r.start}|${r.end}`));
    const merged = [...currentSet].map(s => { const [start, end] = s.split('|'); return { start, end }; }).sort((a,b)=>a.start.localeCompare(b.start));
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

  const monthExamRanges = examRanges.filter(r => {
    const first = `${year}-${String(month).padStart(2,'0')}-01`;
    const last = `${year}-${String(month).padStart(2,'0')}-${String(new Date(year,month,0).getDate()).padStart(2,'0')}`;
    return !(r.end < first || r.start > last);
  });

  const monthGradDays = gradDays.filter(d => d.startsWith(`${year}-${String(month).padStart(2,'0')}-`));

  function buildHolidayDesc() {
    const parts: string[] = [];
    const monthHols: Record<string, string[]> = {};
    for (const [k,v] of Object.entries(holidays)) {
      if (parseInt(k.split('-')[1]) === month && parseInt(k.split('-')[0]) === year) {
        monthHols[k] = v;
      }
    }
    const sorted = Object.keys(monthHols).sort();
    for (let i = 0; i < sorted.length; ) {
      const start = sorted[i];
      const startDay = parseInt(start.split('-')[2]);
      const names = monthHols[start];
      let endDay = startDay;
      let j = i + 1;
      while (j < sorted.length) {
        const nextDay = parseInt(sorted[j].split('-')[2]);
        if (nextDay - endDay === 1 && monthHols[sorted[j]].some(n => names.includes(n))) {
          endDay = nextDay; j++;
        } else break;
      }
      if (startDay === endDay) parts.push(`${startDay}일: ${names.join(', ')}`);
      else parts.push(`${startDay}일~${endDay}일: ${names.join(', ')}`);
      i = j;
    }
    return parts.join(' / ');
  }

  const monthOptions: { year: number; month: number }[] = [];
  for (let i = -5; i <= 5; i++) {
    const d = new Date(year, month - 1 + i, 1);
    monthOptions.push({ year: d.getFullYear(), month: d.getMonth() + 1 });
  }
  const MONTH_NAMES = ['1월','2월','3월','4월','5월','6월','7월','8월','9월','10월','11월','12월'];

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
                    {o.year}년 {MONTH_NAMES[o.month-1]}
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
                    {['주','야','비','올'].map(s => <option key={s} value={s}>{s}</option>)}
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
          </div>
        </aside>

        <main className="main">
          <div className="top-bar">
            <button className="menu-btn" onClick={() => setSidebarOpen(true)}>☰</button>
            <span className="top-title">교대근무 달력</span>
            <div className="top-actions">
              <button className="today-btn" onClick={() => { setYear(today.getFullYear()); setMonth(today.getMonth()+1); }}>Today</button>
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

          {/* 캡처 대상 영역 */}
          <div ref={calendarRef} className="calendar-container">
            <div className="cal-header">
              <button className="nav-btn" onClick={() => navigateMonth(-1)}>‹</button>
              <div className="cal-title">
                <span className="cal-year">{year}.</span>
                <span className="cal-month">{month}</span>
                <span className="cal-year">월</span>
              </div>
              <button className="nav-btn" onClick={() => navigateMonth(1)}>›</button>
            </div>

            <div className="cal-weekdays">
              {['일','월','화','수','목','금','토'].map((d,i) => (
                <div key={d} className="cal-wday" style={{ color: i === 0 || i === 6 ? 'red' : '#495057' }}>{d}</div>
              ))}
            </div>

            {weeks.map((week, wi) => (
              <div key={`week-${wi}`} className="cal-row">
                {week.map((day, di) => {
                  if (!day) return <div key={`empty-${wi}-${di}`} className="cal-cell" />;
                  const dateStr = `${year}-${String(month).padStart(2,'0')}-${String(day).padStart(2,'0')}`;
                  const monthDay = `${String(month).padStart(2,'0')}-${String(day).padStart(2,'0')}`;
                  const dateObj = new Date(year, month-1, day);
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
                      <div className={`cal-cell-inner ${isToday ? 'today' : ''} ${examClass}`}>
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
              {monthGradDays.length > 0 && <span style={{ color: GRAD_COLOR, fontWeight: 700 }}>대학원</span>}
              {monthGradDays.length > 0 && monthExamRanges.length > 0 && ' | '}
              {monthExamRanges.length > 0 && (
                <span style={{ color: EXAM_COLOR, fontWeight: 700 }}>
                  시험기간: {monthExamRanges.map(r => {
                    const s = new Date(r.start); const e = new Date(r.end);
                    if (r.start === r.end) return `${s.getMonth()+1}/${s.getDate()}`;
                    return `${s.getMonth()+1}/${s.getDate()}~${e.getMonth()+1}/${e.getDate()}`;
                  }).join(', ')}
                </span>
              )}
              {(monthGradDays.length > 0 || monthExamRanges.length > 0) && buildHolidayDesc() && ' | '}
              {buildHolidayDesc()}
            </div>
          </div>
        </main>
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
          cursor: pointer; padding: 0 8px; line-height: 1;
        }
        .nav-btn:hover { color: #adb5bd; }
        .cal-title { text-align: center; }
        .cal-year { font-size: 18px; }
        .cal-month { font-size: 30px; font-weight: 700; margin: 0 2px; }
        .cal-weekdays {
          display: grid; grid-template-columns: repeat(7, 1fr);
          background: #f8f9fa; border-bottom: 1px solid #dee2e6; padding: 4px 0;
        }
        .cal-wday { text-align: center; font-size: 16px; font-weight: 700; padding: 4px; }
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
        }
      `}</style>
    </>
  );
}

export const getStaticProps = async () => {
  // 빌드 시 & 백그라운드 재검증 시 실행 (ISR)
  const { githubGet } = await import('../lib/github');

  const today = new Date(new Date().toLocaleString('en-US', { timeZone: 'Asia/Seoul' }));
  const year = today.getFullYear();

  try {
    const [sch, team, grad, exam, hol] = await Promise.all([
      githubGet(process.env.GITHUB_SCHEDULE_PATH || 'vercel_shift_calendar/shift_schedule.json'),
      githubGet('vercel_shift_calendar/team_settings.json'),
      githubGet('vercel_shift_calendar/grad_days.json'),
      githubGet('vercel_shift_calendar/exam_periods.json'),
      // 공휴일은 공공API 직접 호출
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
