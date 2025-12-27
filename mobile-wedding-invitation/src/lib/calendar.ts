import { weddingConfig } from '../config/wedding-config';

function pad(n: number) {
  return String(n).padStart(2, '0');
}

// 간단 ICS 생성(로컬 다운로드)
export function buildIcs(): string {
  const { year, month, day, hour, minute } = weddingConfig.date;
  const dt = `${year}${pad(month)}${pad(day)}T${pad(hour)}${pad(minute)}00`;
  const uid = `wedding-${year}${month}${day}-${Math.random().toString(16).slice(2)}`;

  const title = weddingConfig.meta.title;
  const location = weddingConfig.venue.name;
  const desc = weddingConfig.meta.description;

  return [
    'BEGIN:VCALENDAR',
    'VERSION:2.0',
    'PRODID:-//Wedding Invitation//KO//',
    'CALSCALE:GREGORIAN',
    'METHOD:PUBLISH',
    'BEGIN:VEVENT',
    `UID:${uid}`,
    `DTSTAMP:${dt}Z`,
    `DTSTART:${dt}`,
    // 기본 2시간
    `DTEND:${year}${pad(month)}${pad(day)}T${pad(hour + 2)}${pad(minute)}00`,
    `SUMMARY:${escapeIcsText(title)}`,
    `LOCATION:${escapeIcsText(location)}`,
    `DESCRIPTION:${escapeIcsText(desc)}`,
    'END:VEVENT',
    'END:VCALENDAR',
  ].join('\r\n');
}

function escapeIcsText(text: string) {
  return text
    .replace(/\\/g, '\\\\')
    .replace(/\n/g, '\\n')
    .replace(/,/g, '\\,')
    .replace(/;/g, '\\;');
}

// 구글 캘린더 링크
export function buildGoogleCalendarUrl() {
  const { year, month, day, hour, minute } = weddingConfig.date;

  const start = new Date(year, month - 1, day, hour, minute);
  const end = new Date(year, month - 1, day, hour + 2, minute);

  const fmt = (d: Date) => {
    const z = new Date(d.getTime() - d.getTimezoneOffset() * 60000);
    return z.toISOString().replace(/[-:]/g, '').replace(/\.\d{3}Z$/, 'Z');
  };

  const dates = `${fmt(start)}/${fmt(end)}`;
  const text = encodeURIComponent(weddingConfig.meta.title);
  const details = encodeURIComponent(weddingConfig.meta.description);
  const location = encodeURIComponent(weddingConfig.venue.name);

  return `https://calendar.google.com/calendar/render?action=TEMPLATE&text=${text}&details=${details}&location=${location}&dates=${dates}`;
}
