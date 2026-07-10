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

## 추가된 기능 / 수정 내역 (2026-07)

- **좌우 스와이프로 월 이동**: 달력 영역을 왼쪽으로 밀면 다음 달, 오른쪽으로 밀면 이전 달. 세로 스크롤은 그대로 동작.
- **버전 체크(캐시 초기화)**: `lib/version.ts`의 `APP_VERSION` 값을 배포할 때마다 새로 올리면, 방문자의 브라우저가 버전 변경을 감지해 캐시를 자동으로 비우고 새로고침합니다. 코드 수정 후 과거 화면이 남아 보이는 문제를 방지합니다. 사이드바에 수동 **"🔄 캐시 비우고 새로고침"** 버튼도 있습니다.
  - ⚠️ **배포할 때마다 `lib/version.ts`의 `APP_VERSION`을 꼭 바꿔주세요.** (예: `2026.07.10.1` → `2026.07.10.2`)
- **버그 수정**
  - 시험기간/대학원 날짜에 잘못된 형식(`9.15`, `abc`, `9/`, `13/40` 등)을 입력하면 조용히 쓰레기 값이 저장되던 문제 → 이제 무시 항목으로 걸러내고 알려줍니다.
  - 스케줄/대학원/시험 저장 시 오래된 sha로 인해 간헐적으로 발생하던 `GitHub PUT failed: 409` 저장 실패 → 항상 최신 sha 기준으로 저장.
  - 초기 로드 시 공휴일 API가 두 번 호출되던 중복 제거.
  - 날짜 문자열 파싱을 시간대에 안전하게 변경(시험 밴드/푸터 표시).
