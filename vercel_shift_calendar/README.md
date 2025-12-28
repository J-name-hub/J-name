# 교대근무 달력 (Vercel/Next.js)

Streamlit 앱(교대근무 달력)을 **Vercel에 올릴 수 있는 Next.js 형태**로 재구성한 템플릿입니다.

## 핵심 구조
- 브라우저(프론트): 달력 렌더링 및 편집 UI
- 서버(Next.js API Routes): GitHub Contents API 호출(토큰 보호), data.go.kr 공휴일 API 호출
- 저장소: 기존과 동일하게 GitHub repo 안의 JSON 파일(shift_schedule.json, team_settings.json, grad_days.json, exam_periods.json)을 유지

## 1) 로컬 실행
```bash
npm i
cp .env.example .env.local
# .env.local 편집
npm run dev
```

## 2) Vercel 배포
1. GitHub에 이 프로젝트를 push
2. Vercel에서 Import
3. Project Settings → Environment Variables에 아래 키 등록
   - GITHUB_TOKEN
   - GITHUB_REPO (예: owner/repo)
   - GITHUB_FILE_PATH (예: shift_schedule.json)
   - GITHUB_TEAM_SETTINGS_PATH (기본 team_settings.json)
   - GITHUB_GRAD_DAYS_PATH (기본 grad_days.json)
   - GITHUB_EXAM_PERIODS_PATH (기본 exam_periods.json)
   - SCHEDULE_CHANGE_PASSWORD
   - HOLIDAY_API_KEY
4. Deploy

## 3) 기존 Streamlit 코드 대비 차이
- Streamlit의 st.secrets → Vercel 환경변수로 대체
- GitHub 읽기/쓰기 로직은 동일하게 Contents API 사용
- 캐시는 단순화(Next API는 no-store)
- UI는 Streamlit 대신 React/HTML/CSS로 구현

## 보안 주의
- `GITHUB_TOKEN`, `HOLIDAY_API_KEY`는 반드시 Vercel Env에만 두고, 클라이언트 코드에 절대 넣지 마세요.
