"use client";

import { useState } from "react";

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

  const fetchRandomAndCopy = async (key: CategoryKey) => {
    setSelected(key);
    setLoading(true);
    setMessage("");

    try {
      const res = await fetch(`/api/random?category=${key}`, {
        cache: "no-store",
      });

      const raw = await res.text();

      let data: any;
      try {
        data = JSON.parse(raw);
      } catch {
        throw new Error(
          "API가 JSON이 아닌 응답을 반환했습니다:\n" +
            raw.slice(0, 120)
        );
      }

      if (!res.ok || !data.ok) {
        throw new Error(data?.error || "API Error");
      }

      // ✅ 문구 설정
      setText(data.pick);

      // ✅ 자동 복사
      await navigator.clipboard.writeText(data.pick);

      setMessage(
        `자동 복사 완료 (총 ${data.count}개 중 랜덤 1개)`
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
            onClick={() => fetchRandomAndCopy(b.key)}
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
          minHeight: 140,
        }}
      >
        <div
          style={{
            fontSize: 13,
            color: "#666",
            marginBottom: 8,
          }}
        >
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

        <div style={{ marginTop: 14 }}>
          <button
            onClick={manualCopy}
            disabled={!text}
            style={{
              padding: "10px 12px",
              borderRadius: 10,
              border: "1px solid #ddd",
              background: text ? "#fff" : "#f7f7f7",
              cursor: text ? "pointer" : "not-allowed",
              fontWeight: 700,
            }}
          >
            다시 복사
          </button>
        </div>

        {message && (
          <p
            style={{
              marginTop: 10,
              fontSize: 13,
              color: "#444",
            }}
          >
            {message}
          </p>
        )}
      </div>

      <p
        style={{
          marginTop: 16,
          fontSize: 12,
          color: "#666",
        }}
      >
        ※ 카테고리 버튼을 누르면 자동으로 클립보드에 복사됩니다.
        네이버 카페 댓글창에 바로 붙여넣기 하세요.
      </p>
    </main>
  );
}
