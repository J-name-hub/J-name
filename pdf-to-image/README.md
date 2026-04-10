# 🖼️ PDF → Image 변환기

PDF 파일을 JPG 또는 PNG 이미지로 변환하는 Streamlit 웹 앱입니다.

## ✨ 주요 기능

| 기능 | 설명 |
|------|------|
| **출력 형식** | JPG / PNG 선택 |
| **해상도 설정** | 72 ~ 600 DPI 슬라이더 |
| **JPG 품질** | 50 ~ 100% 조절 |
| **페이지 선택** | 전체 또는 시작~끝 페이지 지정 |
| **일괄 다운로드** | 변환된 이미지 ZIP 압축 다운로드 |
| **미리보기** | 변환 결과 최대 6장 즉시 확인 |

## 🚀 로컬 실행

```bash
# 1. 저장소 클론
git clone https://github.com/<your-username>/<repo-name>.git
cd <repo-name>

# 2. 시스템 의존성 설치 (poppler)
# Ubuntu/Debian
sudo apt-get install poppler-utils

# macOS
brew install poppler

# 3. Python 패키지 설치
pip install -r requirements.txt

# 4. 앱 실행
streamlit run app.py
```

## ☁️ Streamlit Cloud 배포

1. 이 저장소를 GitHub에 Push
2. [share.streamlit.io](https://share.streamlit.io) 접속 후 로그인
3. **New app** → GitHub 저장소 선택 → `app.py` 선택
4. **Deploy** 클릭

> `packages.txt`에 `poppler-utils`가 있어 Streamlit Cloud에서 자동 설치됩니다.

## 📁 파일 구조

```
.
├── app.py            # 메인 Streamlit 앱
├── requirements.txt  # Python 패키지 목록
├── packages.txt      # 시스템 패키지 목록 (Streamlit Cloud용)
└── README.md
```

## 🛠️ 기술 스택

- [Streamlit](https://streamlit.io/) — 웹 UI
- [pdf2image](https://github.com/Belval/pdf2image) — PDF → 이미지 변환 (poppler 기반)
- [pypdf](https://github.com/py-pdf/pypdf) — PDF 페이지 수 파악
- [Pillow](https://python-pillow.org/) — 이미지 처리 및 저장

## 📝 라이선스

MIT
