import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "교대근무 달력",
  description: "Vercel 배포용 교대근무 달력",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko">
      <body>
        <div className="container">
          {children}
        </div>
      </body>
    </html>
  );
}
