# 교대근무 달력 — Next.js + Vercel

Streamlit 앱을 Next.js로 마이그레이션한 버전입니다.

## 로컬 개발

```bash
npm install
cp .env.local.example .env.local
# .env.local 파일을 열어 값 입력
npm run dev
```

## Vercel 배포 방법

### 1. GitHub에 코드 푸시

```bash
git init
git add .
git commit -m "init: shift calendar next.js"
git remote add origin https://github.com/your-username/shift-calendar.git
git push -u origin main
```

### 2. Vercel에서 프로젝트 연결

1. [vercel.com](https://vercel.com) 접속 → **Add New Project**
2. GitHub 레포지토리 선택
3. Framework: **Next.js** (자동 감지됨)

### 3. 환경변수 설정 (필수!)

Vercel 프로젝트 → **Settings** → **Environment Variables** 에서 아래 값들을 추가:

| 키 | 값 | 설명 |
|---|---|---|
| `GITHUB_TOKEN` | `ghp_...` | GitHub Personal Access Token (repo 권한 필요) |
| `GITHUB_REPO` | `username/repo` | 데이터 JSON 파일이 있는 레포 |
| `GITHUB_SCHEDULE_PATH` | `shift_schedule.json` | 스케줄 파일 경로 |
| `SCHEDULE_PASSWORD` | `your_password` | 스케줄 변경 비밀번호 |
| `HOLIDAY_API_KEY` | `your_key` | 공공데이터포털 공휴일 API 키 |

### 4. 배포

환경변수 설정 후 **Deploy** 클릭하면 완료.  
이후 코드 변경 → GitHub push 시 자동 배포됩니다.

## 파일 구조

```
shift-calendar/
├── pages/
│   ├── index.tsx          # 메인 달력 페이지
│   └── api/
│       ├── schedule.ts    # 스케줄 CRUD API
│       ├── team.ts        # 팀 설정 API
│       ├── grad.ts        # 대학원 날짜 API
│       ├── exam.ts        # 시험기간 API
│       └── holidays.ts    # 공휴일 API 프록시
├── lib/
│   ├── shiftLogic.ts      # 교대 패턴 계산 로직
│   └── github.ts          # GitHub API 유틸
├── .env.local.example
└── README.md
```

## 기존 Streamlit 대비 달라진 점

- `st.secrets` → Vercel **Environment Variables**
- Streamlit 캐시 → Next.js API Route 레벨 캐싱
- 사이드바 → 좌측 슬라이드 오버레이 패널
- Python → TypeScript (로직 동일)
