from pathlib import Path
from datetime import date
import streamlit as st

# -----------------------------------------
# 기본 설정
# -----------------------------------------
st.set_page_config(
    page_title="우리 결혼합니다",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# 현재 파일 기준 경로
BASE_DIR = Path(__file__).parent

# 이미지 경로 (파일명은 상황에 맞게 수정)
HERO_IMAGE = BASE_DIR / "imgs" / "hero.jpg"
PHOTO_GALLERY = [
    BASE_DIR / "imgs" / "photo1.jpg",
    BASE_DIR / "imgs" / "photo2.jpg",
    BASE_DIR / "imgs" / "photo3.jpg",
    BASE_DIR / "imgs" / "photo4.jpg",
]

# 예식 정보
WEDDING_DATE = date(2025, 10, 18)
WEDDING_TIME_STR = "오후 2시"
VENUE_NAME = "○○웨딩홀 3층"
VENUE_ADDR = "서울시 ○○구 ○○로 123"
NAVER_MAP_URL = "https://map.naver.com"  # 실제 링크로 교체

# -----------------------------------------
# 스타일 (화이트 웨딩톤 + 가운데 정렬)
# -----------------------------------------
st.markdown(
    """
    <style>
    .main {
        background-color: #f5f1ec;
    }

    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 1.5rem;
    }

    .mobile-frame {
        max-width: 430px;
        margin: 0 auto;
        padding: 1.8rem 1.4rem 3rem;
        background: linear-gradient(180deg, #fdfcfb 0%, #f5f1ec 80%);
        border-radius: 26px;
        box-shadow: 0 20px 45px rgba(0,0,0,0.09);
        font-family: -apple-system,BlinkMacSystemFont,"Noto Sans KR","Apple SD Gothic Neo",sans-serif;
        color: #333333;
    }

    .headline {
        font-size: 1.1rem;
        letter-spacing: 0.28em;
        text-transform: uppercase;
        text-align: center;
        color: #a29382;
        margin: 0.5rem 0 0.3rem;
    }

    .names {
        font-size: 2rem;
        text-align: center;
        font-weight: 600;
        letter-spacing: 0.18em;
        text-transform: uppercase;
        margin-bottom: 0.4rem;
    }

    .date-text {
        text-align: center;
        color: #7c6d5c;
        font-size: 0.95rem;
        margin-bottom: 1.0rem;
    }

    .section-title {
        font-size: 1.02rem;
        font-weight: 600;
        margin: 1.6rem 0 0.5rem;
        text-align: center;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        color: #7c6d5c;
    }

    .section-box {
        background: #faf7f3;
        border-radius: 18px;
        padding: 1.0rem 1.1rem;
        font-size: 0.95rem;
        line-height: 1.7;
        text-align: center;
    }

    .dots {
        text-align: center;
        font-size: 0.8rem;
        margin-top: 0.35rem;
        letter-spacing: 0.18em;
        color: #b0a69b;
    }

    .link-button {
        display: inline-block;
        padding: 0.45rem 0.9rem;
        border-radius: 999px;
        border: 1px solid #d2c6b8;
        font-size: 0.85rem;
        text-decoration: none;
        color: #555555;
        margin: 0.4rem 0.2rem 0 0.2rem;
    }

    .link-button:active {
        background: #ebe0d5;
    }

    /* 버튼 통일 스타일 (캐러셀 화살표 + 제출 버튼) */
    .stButton>button {
        border-radius: 999px;
        border: none;
        padding: 0.45rem 0.6rem;
        font-size: 0.9rem;
        background: #e6ded4;
        color: #6b5b4a;
        cursor: pointer;
    }

    .stButton>button:hover {
        background: #d6c6b6;
    }

    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------------------
# 본문 시작
# -----------------------------------------
st.markdown("<div class='mobile-frame'>", unsafe_allow_html=True)

# 상단 메인 사진
st.image(str(HERO_IMAGE), use_column_width=True)

# 타이틀
st.markdown("<div class='headline'>Wedding Invitation</div>", unsafe_allow_html=True)
st.markdown("<div class='names'>JUNHO & YURI</div>", unsafe_allow_html=True)

st.markdown(
    f"<div class='date-text'>{WEDDING_DATE.strftime('%Y.%m.%d')} · {WEDDING_TIME_STR}</div>",
    unsafe_allow_html=True,
)

st.markdown("---")

# -----------------------------------------
# 사진 캐러셀 (좌우 버튼, 가운데 정렬)
# -----------------------------------------
st.markdown("### 📸 Our Moments")

if "photo_idx" not in st.session_state:
    st.session_state.photo_idx = 0

n = len(PHOTO_GALLERY)

left_col, center_col, right_col = st.columns([1, 6, 1])

with left_col:
    if st.button("◀", key="prev", use_container_width=True):
        st.session_state.photo_idx = (st.session_state.photo_idx - 1) % n

with center_col:
    st.image(str(PHOTO_GALLERY[st.session_state.photo_idx]), use_column_width=True)

with right_col:
    if st.button("▶", key="next", use_container_width=True):
        st.session_state.photo_idx = (st.session_state.photo_idx + 1) % n

dots = "".join("● " if i == st.session_state.photo_idx else "○ " for i in range(n))
st.markdown(f"<div class='dots'>{dots}</div>", unsafe_allow_html=True)

# -----------------------------------------
# 인사말
# -----------------------------------------
st.markdown("<div class='section-title'>💌 인사말</div>", unsafe_allow_html=True)
st.markdown(
    """
    <div class='section-box'>
    서로의 하루를 함께 채워가고자<br>
    평생의 동반자가 되기로 약속했습니다.<br><br>
    바쁘시겠지만 오셔서 저희의 새로운 시작을<br>
    따뜻한 마음으로 축복해 주시면 감사하겠습니다.
    </div>
    """,
    unsafe_allow_html=True,
)

# -----------------------------------------
# 예식 안내
# -----------------------------------------
st.markdown("<div class='section-title'>📍 예식 안내</div>", unsafe_allow_html=True)
st.markdown(
    f"""
    <div class='section-box'>
    <b>일시</b> : {WEDDING_DATE.strftime('%Y년 %m월 %d일')} {WEDDING_TIME_STR}<br>
    <b>장소</b> : {VENUE_NAME}<br>
    <b>주소</b> : {VENUE_ADDR}<br><br>
    <a class='link-button' href='{NAVER_MAP_URL}' target='_blank'>네이버 지도</a>
    </div>
    """,
    unsafe_allow_html=True,
)

# -----------------------------------------
# 연락처
# -----------------------------------------
st.markdown("<div class='section-title'>☎️ 연락하기</div>", unsafe_allow_html=True)
st.markdown(
    """
    <div class='section-box'>
    신랑 : 010-1234-5678<br>
    신부 : 010-9876-5432<br><br>
    <a class='link-button' href='tel:01012345678'>신랑에게 전화</a>
    <a class='link-button' href='tel:01098765432'>신부에게 전화</a>
    </div>
    """,
    unsafe_allow_html=True,
)

# -----------------------------------------
# RSVP
# -----------------------------------------
st.markdown("<div class='section-title'>✏️ 참석 여부</div>", unsafe_allow_html=True)

name = st.text_input("이름")
attend = st.radio("참석 여부", ["참석합니다", "불참합니다", "미정입니다"])
message = st.text_area("축하 메시지 (선택)")

if st.button("전달하기", key="submit_rsvp"):
    # TODO: 여기에서 구글 시트 / DB / 이메일 연동 가능
    st.success("전달되었습니다. 감사합니다.")

st.markdown("</div>", unsafe_allow_html=True)
