export function formatKoreanDateTime(
  y: number,
  m: number,
  d: number,
  hh: number,
  mm: number
) {
  const ampm = hh >= 12 ? "오후" : "오전";
  const h12 = hh % 12 === 0 ? 12 : hh % 12;
  const minute = String(mm).padStart(2, "0");
  return `${y}년 ${m}월 ${d}일 ${ampm} ${h12}시 ${minute}분`;
}
