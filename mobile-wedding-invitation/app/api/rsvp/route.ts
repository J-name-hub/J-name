import { NextResponse } from "next/server";
import { weddingConfig } from "@/src/config/wedding-config";

type Body = {
  name: string;
  phone?: string;
  attending: "yes" | "no";
  headcount?: number;
  meal?: "yes" | "no";
  message?: string;
};

export async function POST(req: Request) {
  const body = (await req.json()) as Body;

  // 1) 서버 로그 (Vercel 로그에서 확인 가능)
  console.log("[RSVP]", body);

  // 2) (선택) 슬랙 웹훅
  const webhookUrl = weddingConfig.slack?.webhookUrl;
  if (webhookUrl) {
    try {
      const text =
        `*[RSVP]*\n` +
        `- 이름: ${body.name}\n` +
        `- 참석: ${body.attending === "yes" ? "참석" : "불참"}\n` +
        (body.headcount ? `- 인원: ${body.headcount}\n` : "") +
        (body.phone ? `- 연락처: ${body.phone}\n` : "") +
        (body.meal ? `- 식사: ${body.meal === "yes" ? "예" : "아니오"}\n` : "") +
        (body.message ? `- 메모: ${body.message}\n` : "");

      await fetch(webhookUrl, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ text })
      });
    } catch {
      // 개인용이면 실패해도 RSVP는 통과시키는 편이 UX가 좋습니다.
    }
  }

  return NextResponse.json({ ok: true });
}
