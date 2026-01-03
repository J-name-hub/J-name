"use client";

import { useState } from "react";

type CategoryKey = "expo" | "hall" | "studio" | "dress" | "makeup" | "dowry";

const BUTTONS: { key: CategoryKey; label: string }[] = [
  { key: "expo", label: "업체후기(박람회)" },
  { key: "hall", label: "업체후기(웨딩홀)" },
  { key: "studio", label: "업체후기(스튜디오)" },
  { key: "dress", label: "업체후기(드레스)" },
  { key: "makeup", label: "업체후기(메이크업)" },
  { key: "dowry", label: "업체후기(혼수)" },
];

export default function Home() {
  const [selected, setSelected] = useState<CategoryKey>("expo");
  const [text, setText] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState<string>("");

  const fetchRandom = async (key: CategoryKey) => {
    setSelected(key);
    setLoading(true);
    setMsg("");
    try {
      const res = await fetch(`/api/random?category=${key}`, { cache: "no-store" });
      const data = await res.json();
      if (!res.ok) throw new Error(data?.error || "Fetch failed");
      setText(data.pick);
      setMsg(`불러오기 완료 (총 ${data.count}개 중 랜덤 1개)`);
    } catch (e: any) {
      setMsg(`에러: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  const copy = async () => {
    if (!text) return;
    await navigator.clipboard.writeText(text);
    setMsg("클립보드에 복사했습니다. 네이버 카페 댓글창에 붙여넣기 하세요.");
  };

  return (
    <main style={{ maxWidth: 720, margin: "40px auto", padding: 16, fontFamily: "system-ui" }}>
      <h1 style={{ fontSize: 22, fontWeight: 700, marginBottom: 12 }}>
        네이버 카페 댓글용 랜덤 문구 복사
      </h1>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, marginBottom: 16 }}>
        {BUTTONS.map((b) => (
          <button
            key={b.key}
            onClick={() => fetchRandom(b.key)}
            disabled={loading}
            style={{
              padding: "12px 10px",
              borderRadius: 10,
              border: "1px solid #ddd",
              background: selected === b.key ? "#f2f2f2" : "#fff",
              cursor: loading ? "not-allowed" : "pointer",
              fontWeight: 600,
            }}
          >
            {loading && selected === b.key ? "불러오는 중..." : b.label}
          </button>
        ))}
      </div>

      <div style={{ border: "1px solid #ddd", borderRadius: 12, padding: 14, minHeight: 120 }}>
        <div style={{ fontSize: 13, color: "#666", marginBottom: 8 }}>
          선택: {BUTTONS.find((b) => b.key === selected)?.label}
        </div>

        <div style={{ whiteSpace: "pre-wrap", fontSize: 16, lineHeight: 1.6 }}>
          {text || "버튼을 눌러 문구를 불러오세요."}
        </div>

        <div style={{ display: "flex", gap: 10, marginTop: 12 }}>
          <button
            onClick={() => fetchRandom(selected)}
            disabled={loading}
            style={{
              padding: "10px 12px",
              borderRadius: 10,
              border: "1px solid #ddd",
              background: "#fff",
              cursor: loading ? "not-allowed" : "pointer",
              fontWeight: 600,
            }}
          >
            같은 카테고리 다시 뽑기
          </button>

          <button
            onClick={copy}
            disabled={!text}
            style={{
              padding: "10px 12px",
              borderRadius: 10,
              border: "1px solid #ddd",
              background: !text ? "#f7f7f7" : "#fff",
              cursor: !text ? "not-allowed" : "pointer",
              fontWeight: 700,
            }}
          >
            복사
          </button>
        </div>

        {msg && <p style={{ marginTop: 10, color: "#444", fontSize: 13 }}>{msg}</p>}
      </div>

      <p style={{ marginTop: 14, fontSize: 12, color: "#666" }}>
        팁: 네이버 카페 댓글창에 붙여넣기만 하면 되도록 “문구 끝에 이모지/해시태그/줄바꿈” 등을
        미리 포함시켜 두면 편합니다.
      </p>
    </main>
  );
}
