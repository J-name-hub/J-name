"use client";

import React, { useEffect, useMemo, useState } from "react";
import html2canvas from "html2canvas";
import { monthMatrix, parseYmd, ymd, addDays } from "../lib/date";
import {
  expandExamDates,
  getTeamForDate,
  resolveShift,
  type ScheduleMap,
  type TeamHistoryItem,
  type Shift,
} from "../lib/shift";

type HolidaysMap = Record<string, string[]>;
type ExamRange = { start: string; end: string };

const WEEKDAYS = ["일", "월", "화", "수", "목", "금", "토"];

function cls(...xs: Array<string | false | null | undefined>) {
  return xs.filter(Boolean).join(" ");
}

function shiftClass(s: Shift) {
  if (s === "주") return "shiftBadge shift-day";
  if (s === "야") return "shiftBadge shift-night";
  if (s === "올") return "shiftBadge shift-all";
  return "shiftBadge shift-off";
}

function formatMonthTitle(y: number, m: number) {
  return `${y}.${String(m)}월`;
}

function parseMdDates(md: string, year: number): { dates: string[]; errors: string[] } {
  const raw = (md || "").replace(/，/g, ",");
  const tokens = raw
    .split(",")
    .map((t) => t.trim())
    .filter(Boolean);
  const out: string[] = [];
  const errors: string[] = [];
  for (const t of tokens) {
    const m = t.match(/^(\d{1,2})\s*\/\s*(\d{1,2})$/);
    if (!m) {
      errors.push(t);
      continue;
    }
    const mm = Number(m[1]),
      dd = Number(m[2]);
    const d = new Date(year, mm - 1, dd);
    if (d.getFullYear() !== year || d.getMonth() !== mm - 1 || d.getDate() !== dd) {
      errors.push(t);
      continue;
    }
    out.push(ymd(d));
  }
  return { dates: out, errors };
}

function parseMdRanges(md: string, year: number): { ranges: ExamRange[]; errors: string[] } {
  const raw = (md || "").replace(/，/g, ",").replace(/\n/g, ",");
  const tokens = raw
    .split(",")
    .map((t) => t.trim())
    .filter(Boolean);
  const ranges: ExamRange[] = [];
  const errors: string[] = [];
  for (const t of tokens) {
    try {
      if (t.includes("~")) {
        const [l, r] = t.split("~", 2).map((x) => x.trim());
        const lm = l.match(/^(\d{1,2})\s*\/\s*(\d{1,2})$/);
        const rm = r.match(/^(\d{1,2})\s*\/\s*(\d{1,2})$/);
        if (!lm || !rm) throw new Error("bad");
        const sd = new Date(year, Number(lm[1]) - 1, Number(lm[2]));
        const ed = new Date(year, Number(rm[1]) - 1, Number(rm[2]));
        const s = ymd(sd),
          e = ymd(ed);
        ranges.push(s <= e ? { start: s, end: e } : { start: e, end: s });
      } else {
        const m = t.match(/^(\d{1,2})\s*\/\s*(\d{1,2})$/);
        if (!m) throw new Error("bad");
        const d = new Date(year, Number(m[1]) - 1, Number(m[2]));
        const s = ymd(d);
        ranges.push({ start: s, end: s });
      }
    } catch {
      errors.push(t);
    }
  }
  return { ranges, errors };
}

export default function Home() {
  const now = new Date();
  const [year, setYear] = useState<number>(now.getFullYear());
  const [month, setMonth] = useState<number>(now.getMonth() + 1);

  const [holidays, setHolidays] = useState<HolidaysMap>({});
  const [schedule, setSchedule] = useState<ScheduleMap>({});
  const [scheduleSha, setScheduleSha] = useState<string | null>(null);

  const [teamHistory, setTeamHistory] = useState<TeamHistoryItem[]>([{ start_date: "2000-01-03", team: "A" }]);
  const [teamSha, setTeamSha] = useState<string | null>(null);

  const [gradDates, setGradDates] = useState<string[]>([]);
  const [gradSha, setGradSha] = useState<string | null>(null);

  const [examRanges, setExamRanges] = useState<ExamRange[]>([]);
  const [examSha, setExamSha] = useState<string | null>(null);

  const [notice, setNotice] = useState<{ kind: "ok" | "err"; text: string } | null>(null);

  // edit inputs
  const [pw, setPw] = useState<string>("");
  const [changeDate, setChangeDate] = useState<string>(ymd(new Date(year, month - 1, 1)));
  const [newShift, setNewShift] = useState<Shift>("주");

  const [teamStartDate, setTeamStartDate] = useState<string>(ymd(new Date()));
  const [teamNew, setTeamNew] = useState<"A" | "B" | "C" | "D">("A");

  const [gradYear, setGradYear] = useState<number>(now.getFullYear());
  const [gradMd, setGradMd] = useState<string>("");

  const [examYear, setExamYear] = useState<number>(now.getFullYear());
  const [examMd, setExamMd] = useState<string>("");

  // click-to-change sheet
  const [pickerOpen, setPickerOpen] = useState(false);
  const [pickedDate, setPickedDate] = useState<string | null>(null);

  const monthCells = useMemo(() => monthMatrix(year, month), [year, month]);
  const todayStr = ymd(new Date());

  const examDates = useMemo(() => expandExamDates(examRanges), [examRanges]);

  function examBandClass(dateStr: string) {
    if (!examDates.has(dateStr)) return null;
    const d = parseYmd(dateStr);
    const prev = ymd(addDays(d, -1));
    const next = ymd(addDays(d, 1));
    const prevIn = examDates.has(prev);
    const nextIn = examDates.has(next);
    if (prevIn && nextIn) return "examBand";
    if (!prevIn && nextIn) return "examBand examStart";
    if (prevIn && !nextIn) return "examBand examEnd";
    return "examBand examSingle";
  }

  async function loadAll(y: number) {
    const h = await fetch(`/api/holidays?year=${y}`).then((r) => r.json());
    setHolidays(h.holidays || {});
    const s = await fetch(`/api/schedule`).then((r) => r.json());
    setSchedule(s.schedule || {});
    setScheduleSha(s.sha ?? null);

    const t = await fetch(`/api/team-settings`).then((r) => r.json());
    setTeamHistory(t.team_history || [{ start_date: "2000-01-03", team: "A" }]);
    setTeamSha(t.sha ?? null);

    const g = await fetch(`/api/grad-days`).then((r) => r.json());
    setGradDates(g.dates || []);
    setGradSha(g.sha ?? null);

    const e = await fetch(`/api/exam-periods`).then((r) => r.json());
    setExamRanges(e.ranges || []);
    setExamSha(e.sha ?? null);
  }

  useEffect(() => {
    loadAll(year).catch((e) => setNotice({ kind: "err", text: String(e) }));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    fetch(`/api/holidays?year=${year}`)
      .then((r) => r.json())
      .then((h) => setHolidays(h.holidays || {}))
      .catch(() => setHolidays({}));
  }, [year]);

  function moveMonth(delta: number) {
    const d = new Date(year, month - 1, 1);
    d.setMonth(d.getMonth() + delta);
    setYear(d.getFullYear());
    setMonth(d.getMonth() + 1);
    setChangeDate(ymd(new Date(d.getFullYear(), d.getMonth(), 1)));
  }

  const currentTeam = useMemo(() => getTeamForDate(new Date(), teamHistory), [teamHistory]);

  async function saveScheduleChange() {
    setNotice(null);
    try {
      const next = { ...schedule, [changeDate]: newShift };
      const r = await fetch("/api/schedule", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ password: pw, schedule: next, sha: scheduleSha }),
      });
      const out = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(out.error || "save failed");
      setSchedule(next);
      setScheduleSha(out.sha ?? scheduleSha);
      setNotice({ kind: "ok", text: "스케줄이 저장되었습니다." });
    } catch (e: any) {
      setNotice({ kind: "err", text: e?.message ?? String(e) });
    }
  }

  async function saveTeamHistory() {
    setNotice(null);
    try {
      const dict = new Map<string, "A" | "B" | "C" | "D">();
      for (const it of teamHistory) dict.set(it.start_date, it.team);
      dict.set(teamStartDate, teamNew);
      const merged = Array.from(dict.entries())
        .sort((a, b) => a[0].localeCompare(b[0]))
        .map(([start_date, team]) => ({ start_date, team }));
      const r = await fetch("/api/team-settings", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ password: pw, team_history: merged, sha: teamSha }),
      });
      const out = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(out.error || "save failed");
      setTeamHistory(merged);
      setTeamSha(out.sha ?? teamSha);
      setNotice({ kind: "ok", text: "조 설정이 저장되었습니다." });
    } catch (e: any) {
      setNotice({ kind: "err", text: e?.message ?? String(e) });
    }
  }

  async function saveGrad(addMode: boolean) {
    setNotice(null);
    const { dates, errors } = parseMdDates(gradMd, gradYear);
    try {
      const set = new Set<string>(gradDates);
      for (const d of dates) addMode ? set.add(d) : set.delete(d);
      const next = Array.from(set).sort();
      const r = await fetch("/api/grad-days", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ password: pw, dates: next, sha: gradSha }),
      });
      const out = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(out.error || "save failed");
      setGradDates(next);
      setGradSha(out.sha ?? gradSha);
      setNotice({
        kind: "ok",
        text: `대학원 날짜가 ${addMode ? "저장" : "삭제"}되었습니다.${errors.length ? " (일부 무시됨)" : ""}`,
      });
    } catch (e: any) {
      setNotice({ kind: "err", text: e?.message ?? String(e) });
    }
  }

  async function saveExam(addMode: boolean) {
    setNotice(null);
    const { ranges, errors } = parseMdRanges(examMd, examYear);
    try {
      const key = (r: ExamRange) => `${r.start}~${r.end}`;
      const set = new Map<string, ExamRange>();
      for (const r of examRanges) set.set(key(r), r);
      for (const r of ranges) {
        const k = key(r);
        addMode ? set.set(k, r) : set.delete(k);
      }
      const next = Array.from(set.values()).sort((a, b) => (a.start + a.end).localeCompare(b.start + b.end));
      const r = await fetch("/api/exam-periods", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ password: pw, ranges: next, sha: examSha }),
      });
      const out = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(out.error || "save failed");
      setExamRanges(next);
      setExamSha(out.sha ?? examSha);
      setNotice({
        kind: "ok",
        text: `시험기간이 ${addMode ? "저장" : "삭제"}되었습니다.${errors.length ? " (일부 무시됨)" : ""}`,
      });
    } catch (e: any) {
      setNotice({ kind: "err", text: e?.message ?? String(e) });
    }
  }

  const monthExamLabels = useMemo(() => {
    const first = ymd(new Date(year, month - 1, 1));
    const last = ymd(new Date(year, month, 0));
    const out: string[] = [];
    for (const r of examRanges) {
      if (r.end < first || r.start > last) continue;
      const s = parseYmd(r.start);
      const e = parseYmd(r.end);
      const fmt = (d: Date) =>
        `${String(d.getMonth() + 1).padStart(2, "0")}/${String(d.getDate()).padStart(2, "0")}`;
      out.push(r.start === r.end ? fmt(s) : `${fmt(s)}~${fmt(e)}`);
    }
    return out;
  }, [examRanges, year, month]);

  const holidayText = useMemo(() => {
    const out: string[] = [];
    for (const [ds, names] of Object.entries(holidays)) {
      const d = parseYmd(ds);
      if (d.getFullYear() !== year || d.getMonth() + 1 !== month) continue;
      out.push(`${d.getDate()}일(${WEEKDAYS[d.getDay()]}): ${names.join(", ")}`);
    }
    return out.sort((a, b) => {
      const da = Number(a.split("일")[0].replace(/[^0-9]/g, ""));
      const db = Number(b.split("일")[0].replace(/[^0-9]/g, ""));
      return da - db;
    });
  }, [holidays, year, month]);

  const hasHolidayData = useMemo(() => Object.keys(holidays).length > 0, [holidays]);

  async function saveAsImage() {
    const el = document.getElementById("calendar-capture");
    if (!el) return;
    const canvas = await html2canvas(el, { scale: 2 });
    const url = canvas.toDataURL("image/png");
    const a = document.createElement("a");
    a.href = url;
    a.download = `${year}-${String(month).padStart(2, "0")}-calendar.png`;
    a.click();
  }

  return (
    <>
      <div className="card" id="calendar-capture">
        <div className="header">
          <div>
            <div className="title">{formatMonthTitle(year, month)}</div>
            <div className="subtitle">현재 근무조: {currentTeam}</div>
          </div>
          <div className="topRightActions">
            <button className="btn" onClick={saveAsImage}>이미지 저장</button>
          </div>
        </div>

        <div className="grid">
          {WEEKDAYS.map((d, i) => (
            <div key={d} className="weekday" style={{ color: i === 0 || i === 6 ? "#ef4444" : undefined }}>
              {d}
            </div>
          ))}

        <div className="toolbar">
          <button className="btn" onClick={() => moveMonth(-1)}>
            이전 월
          </button>
          <button
            className="btn"
            onClick={() => {
              const t = new Date();
              setYear(t.getFullYear());
              setMonth(t.getMonth() + 1);
              setChangeDate(ymd(new Date(t.getFullYear(), t.getMonth(), 1)));
            }}
          >
            Today
          </button>
          <button className="btn" onClick={() => moveMonth(1)}>
            다음 월
          </button>
        </div>

          {monthCells.map((day, idx) => {
            if (!day) return <div key={idx} className="cell" />;

            const dateStr = ymd(new Date(year, month - 1, day));
            const dateObj = new Date(year, month - 1, day);

            const sft = resolveShift(dateObj, teamHistory, schedule);
            const holidayNames = holidays[dateStr] || [];
            const isHoliday = holidayNames.length > 0;
            const isWeekend = dateObj.getDay() === 0 || dateObj.getDay() === 6;
            const isGrad = gradDates.includes(dateStr);

            const band = examBandClass(dateStr);

            const dayColor = isGrad ? "var(--grad)" : isHoliday || isWeekend ? "#ef4444" : "#111827";

            return (
              <div
                key={idx}
                className={cls("cell", "clickable")}
                onClick={() => {
                  setPickedDate(dateStr);
                  setChangeDate(dateStr);
                  setPickerOpen(true);
                }}
                role="button"
                tabIndex={0}
              >
                {band ? <div className={band} /> : null}
                <div className="contentTop">
                  <div className={cls("todayWrap", dateStr === todayStr && "isToday")}>
                    <div className="daynum" style={{ color: dayColor }}>
                      {day}
                    </div>
                    <div className={shiftClass(sft)}>
                      <span className={sft === "비" ? "shiftText hiddenText" : "shiftText"} aria-label={sft}>
                        {sft}
                      </span>
                    </div>
                  </div>
                
                  {holidayNames.length ? <div className="holidayName">{holidayNames.join(", ")}</div> : null}
                </div>
              </div>
            );
          })}
        </div>

        <div className="legend">
          <span className="pill">
            <span className="dot dot-grad" />
            대학원
          </span>

          {!hasHolidayData ? (
            <span className="pill" style={{ borderColor: "rgba(239,68,68,.35)", background: "rgba(239,68,68,.06)" }}>
              공휴일 데이터 없음 (HOLIDAY_API_KEY 미설정/오류 가능)
            </span>
          ) : null}

          {monthExamLabels.length ? (
            <span className="pill" style={{ borderColor: "rgba(255,111,0,.35)", background: "rgba(255,111,0,.08)" }}>
              시험기간: {monthExamLabels.join(", ")}
            </span>
          ) : null}

        </div>
      </div>

      <div className="card panel">
        <h3>편집 (GitHub에 저장됨)</h3>

        <details className="accordion">
          <summary className="accordionSummary">편집 암호</summary>
          <div className="accordionBody">
            <label>편집 암호</label>
            <input
              className="input"
              type="password"
              value={pw}
              onChange={(e) => setPw(e.target.value)}
              placeholder="SCHEDULE_CHANGE_PASSWORD"
            />
            <div className="help">암호가 맞으면 아래 기능들이 GitHub 파일에 반영됩니다(서버에서만 검증).</div>
          </div>
        </details>

        <details className="accordion">
          <summary className="accordionSummary">스케줄 변경</summary>
          <div className="accordionBody">
            <div style={{ display: "grid", gridTemplateColumns: "1fr 110px 120px", gap: 8 }}>
              <input className="input" type="date" value={changeDate} onChange={(e) => setChangeDate(e.target.value)} />
              <select className="select" value={newShift} onChange={(e) => setNewShift(e.target.value as Shift)}>
                <option value="주">주</option>
                <option value="야">야</option>
                <option value="비">비</option>
                <option value="올">올</option>
              </select>
              <button className="btn" onClick={saveScheduleChange}>
                저장
              </button>
            </div>
            <div className="help">달력 날짜 클릭으로도 변경 가능합니다(해당 날짜만 override).</div>
          </div>
        </details>

        <details className="accordion">
          <summary className="accordionSummary">조 설정 (팀 변경)</summary>
          <div className="accordionBody">
            <div style={{ display: "grid", gridTemplateColumns: "1fr 110px 120px", gap: 8 }}>
              <input className="input" type="date" value={teamStartDate} onChange={(e) => setTeamStartDate(e.target.value)} />
              <select className="select" value={teamNew} onChange={(e) => setTeamNew(e.target.value as any)}>
                <option value="A">A</option>
                <option value="B">B</option>
                <option value="C">C</option>
                <option value="D">D</option>
              </select>
              <button className="btn" onClick={saveTeamHistory}>
                저장
              </button>
            </div>
            <div className="help">team_settings.json의 team_history를 갱신합니다.</div>
          </div>
        </details>

        <details className="accordion">
          <summary className="accordionSummary">대학원 날짜 편집</summary>
          <div className="accordionBody">
            <div style={{ display: "grid", gridTemplateColumns: "120px 1fr", gap: 8, alignItems: "center" }}>
              <input className="input" type="number" value={gradYear} onChange={(e) => setGradYear(Number(e.target.value))} />
              <textarea className="textarea" value={gradMd} onChange={(e) => setGradMd(e.target.value)} placeholder="예: 8/15, 8/17, 12/3" />
            </div>
            <div style={{ display: "flex", gap: 8, marginTop: 8, flexWrap: "wrap" }}>
              <button className="btn" onClick={() => saveGrad(true)}>
                저장(추가)
              </button>
              <button className="btn" onClick={() => saveGrad(false)}>
                삭제
              </button>
            </div>
            <div className="help">입력은 M/D 콤마 구분입니다. 예: 9/1, 9/4</div>
          </div>
        </details>

        <details className="accordion">
          <summary className="accordionSummary">시험기간 편집</summary>
          <div className="accordionBody">
            <div style={{ display: "grid", gridTemplateColumns: "120px 1fr", gap: 8, alignItems: "center" }}>
              <input className="input" type="number" value={examYear} onChange={(e) => setExamYear(Number(e.target.value))} />
              <textarea
                className="textarea"
                value={examMd}
                onChange={(e) => setExamMd(e.target.value)}
                placeholder="예: 9/15~9/19, 12/2~12/3, 9/20"
              />
            </div>
            <div style={{ display: "flex", gap: 8, marginTop: 8, flexWrap: "wrap" }}>
              <button className="btn" onClick={() => saveExam(true)}>
                저장(추가)
              </button>
              <button className="btn" onClick={() => saveExam(false)}>
                삭제
              </button>
            </div>
            <div className="help">기간은 M/D~M/D, 단일일은 M/D로 입력합니다.</div>
          </div>
        </details>

        <div className="notice">
          GitHub 토큰/공휴일 API키는 브라우저에 노출되지 않도록, 모든 GitHub 호출을 Next.js API Route에서 처리합니다. (Vercel 환경변수 설정 필요)
        </div>

        {notice ? <div className={cls("notice", notice.kind)}>{notice.text}</div> : null}
      </div>

      {pickerOpen && pickedDate ? (
        <div className="overlay" onClick={() => setPickerOpen(false)}>
          <div className="sheet" onClick={(e) => e.stopPropagation()}>
            <div className="sheetTitle">근무 변경</div>
            <div className="sheetSub">{pickedDate}</div>

            <div className="shiftButtons">
              {(["주", "야", "비", "올"] as Shift[]).map((s) => (
                <button key={s} className={cls("shiftBtn", newShift === s && "active")} onClick={() => setNewShift(s)}>
                  {s}
                </button>
              ))}
            </div>

            <div className="sheetActions">
              <button
                className="btn"
                onClick={async () => {
                  await saveScheduleChange();
                  setPickerOpen(false);
                }}
              >
                저장
              </button>
              <button className="btn" onClick={() => setPickerOpen(false)}>
                취소
              </button>
            </div>

            <div className="help">해당 날짜만 override로 저장됩니다.</div>
          </div>
        </div>
      ) : null}
    </>
  );
}
