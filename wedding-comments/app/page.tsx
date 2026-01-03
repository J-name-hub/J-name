"use client";

import { useRef, useState } from "react";

type CategoryKey =
  | "expo"
  | "hall"
  | "studio"
  | "dress"
  | "makeup"
  | "dowry";

const BUTTONS: { key: CategoryKey; label: string }[] = [
  { key: "expo", label: "업체후기(박람회)" },
  { key: "hall", label: "업체후기(웨딩홀)" },
  { key: "studio", label: "업체후기(스튜디오)" },
  { key: "dress", label: "업체후기(드레스)" },
  { key: "makeup", label: "업체후기(메이크업)" },
  { key: "dowry", label: "업체후기(혼수)" },
];

export default function Page() {
  const [selected, setSelected] = useState<CategoryKey>("expo");
  const [text, setText] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  // ✅ 카테고리별 이미 나온 문구 기록
  const usedMap = useRef<Record<CategoryKey, Set<string>>>({
    expo: new Set(),
    hall: new Set(),
    studio: new Set(),
    dress: new Set(),
    makeup: new Set(),
    dowry: new Set(),
  });

  const fetchUniqueAndCopy = async (key: CategoryKey) => {
    setSelected(key);
    setLoading(true);
    setMessage("");

    try {
      let data: any = null;
      let attempt = 0;

      while (attempt < 10) {
        const res = await fetch(`/api/random?category=${key}`, {
          cache: "no-store",
        });

        const raw = await res.text();

        try {
          data = JSON.parse(raw);
        } catch {
          throw new Error("API가 JSON이 아닌 응답을 반환했습니다.");
        }

        if (!res.ok || !data.ok) {
          throw new Error(data?.error || "API Error");
        }

        // 🔁 중복이면 다시 시도
        if (!usedMap.current[key].has(data.pick)) {
          break;
        }

        attempt++;
      }

      if (!data) {
        throw new Error("문구를 불러오지 못했습니다.");
      }

      // ✅ 기록 + 화면 반영
      usedMap.current[key].add(data.pick);
      setText(data.pick);

      // ✅ 자동 복사
      await navigator.clipboard.writeText(data.pick);

      setMessage(
        `자동 복사 완료 (사용 ${usedMap.current[key].size} / ${data.count})`
      );
    } catch (err: any) {
      setMessage(`에러: ${err.message}`);
      setText("");
    } finally {
      setLoading(false);
    }
  };

  const manualCopy = async () => {
    if (!text) return;
    await navigator.clipboard.writeText(text);
    setMessage("클립보드에 다시 복사했습니다.");
  };

  return (
    <main
      style={{
        maxWidth: 720,
        margin: "40px auto",
        padding: 16,
        fontFamily: "system-ui, -apple-system",
      }}
    >
      <h1 style={{ fontSize: 22, fontWeight: 700, marginBottom: 16 }}>
        후기 반응 댓글 랜덤 복사
      </h1>

      {/* 카테고리 버튼 */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: 10,
          marginBottom: 16,
        }}
      >
        {BUTTONS.map((b) => (
          <button
            key={b.key}
            onClick={() => fetchUniqueAndCopy(b.key)}
            disabled={loading}
            style={{
              padding: "12px 10px",
              borderRadius: 10,
              border: "1px solid #ddd",
              background:
                selected === b.key ? "#f2f2f2" : "#fff",
              cursor: loading ? "not-allowed" : "pointer",
              fontWeight: 600,
            }}
          >
            {loading && selected === b.key
              ? "불러오고 복사 중..."
              : b.label}
          </button>
        ))}
      </div>

      {/* 결과 영역 */}
      <div
        style={{
          border: "1px solid #ddd",
          borderRadius: 12,
          padding: 14,
          minHeight: 150,
        }}
      >
        <div style={{ fontSize: 13, color: "#666", marginBottom: 8 }}>
          선택 카테고리:{" "}
          {BUTTONS.find((b) => b.key === selected)?.label}
        </div>

        <div
          style={{
            whiteSpace: "pre-wrap",
            fontSize: 16,
            lineHeight: 1.6,
          }}
        >
          {text || "버튼을 누르면 자동으로 복사됩니다."}
        </div>

        {/* 하단 버튼 */}
        <div style={{ display: "flex", gap: 10, marginTop: 14 }}>
          <button
            onClick={() => fetchUniqueAndCopy(selected)}
            disabled={loading}
            style={{
              padding: "10px 12px",
              borderRadius: 10,
              border: "1px solid #ddd",
              background: "#fff",
              fontWeight: 600,
            }}
          >
            다른 문구
          </button>

          <button
            onClick={manualCopy}
            disabled={!text}
            style={{
              padding: "10px 12px",
              borderRadius: 10,
              border: "1px solid #ddd",
              background: text ? "#fff" : "#f7f7f7",
              fontWeight: 700,
            }}
          >
            다시 복사
          </button>
        </div>

        {message && (
          <p style={{ marginTop: 10, fontSize: 13, color: "#444" }}>
            {message}
          </p>
        )}
      </div>

      <p style={{ marginTop: 16, fontSize: 12, color: "#666" }}>
        ※ 카테고리 버튼 / 다른 문구 버튼 모두 중복 방지 + 자동 복사 적용
      </p>
    </main>
  );
}
