export const metadata = {
  title: "댓글 랜덤 문구 복사",
  description: "카테고리별 랜덤 문구를 복사합니다."
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko">
      <body>{children}</body>
    </html>
  );
}
