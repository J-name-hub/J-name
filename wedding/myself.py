import streamlit as st
from datetime import date

st.set_page_config(
    page_title="우리 결혼합니다",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# -------------------------------
# 설정 : 이미지 파일 경로
# -------------------------------
HERO_IMAGE = "imgs/hero.jpg"  # 메인 사진
PHOTO_GALLERY = [
    "imgs/photo1.jpg",
    "imgs/photo2.jpg",
    "imgs/photo3.jpg",
    "imgs/photo4.jpg",
]

WEDDING_DATE = date(2025, 10, 18)
WEDDING_TIME_STR = "오후 2시"
VENUE_NAME = "○○웨딩홀 3층"
VENUE_ADDR = "서울시 ○○구 ○○로 123"
NAVER_MAP_URL = "https://map.naver.com"  # 실제 지도 URL로 교체

# -------------------------------
# 기본 스타일 (모바일 프레임)
# -------------------------------
st.markdown(
    """
    <style>
    /* 전체 배경색 */
    .main {
        background-color: #f5f1ec;
    }

    /* 모바일 프레임 */
    .mobile-frame {
        max-width: 430px;
        margin: 0 auto;
        padding: 1.5rem 1.25rem 3rem;
        background-color: #fdfcfb;
        border-radius: 24px;
        box-shadow: 0 16px 40px rgba(0,0,0,0.08);
        font-family: -apple-system,BlinkMacSystemFont,"Noto Sans KR","Apple SD Gothic Neo",sans-serif;
        color: #333;
    }

    /* 상단 여백 제거용 */
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 1.5rem;
    }

    /* 제목, 소제목 */
    .headline {
        font-size: 1.2rem;
        letter-spacing: 0.25em;
        text-transform: uppercase;
        text-align: center;
        color: #777;
        margin-bottom: 0.2rem;
    }
    .names {
        font-size: 1.9rem;
        text-align: center;
        font-weight: 600;
        letter-spacing: 0.16em;
        text-transform: uppercase;
        margin-bottom: 0.4rem;
    }
    .date-text {
        text-align: center;
        color: #555;
        font-size: 0.95rem;
        margin-bottom: 0.8rem;
    }

    /* 섹션 타이틀 */
    .section-title {
        font-size: 1.05rem;
        font-weight: 600;
        margin: 1.6rem 0 0.4rem;
    }
    .section-box {
        background: #faf7f3;
        border-radius: 16px;
        padding: 0.9rem 1rem;
        font-size: 0.95rem;
        line-height: 1.6;
    }

    /* 사진 슬라이드 하단 점 */
    .dots {
        text-align: center;
        font-size: 0.8rem;
        margin-top: 0.4rem;
        letter-spacing: 0.2em;
        color: #b0a69b;
    }

    /* 버튼 모양 링크 */
    .link-button {
        display: inline-block;
        padding: 0.45rem 0.9rem;
        border-radius: 999px;
        border: 1px solid #d2c6b8;
        font-size: 0.85rem;
        text-decoration: none;
        color: #555;
        margin-right: 0.3rem;
        margin-top: 0.4rem;
    }
    .link-button:active {
        background: #ebe0d5;
    }

    /* footer, 메뉴 숨기기 (원하면) */
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """,
    unsafe_allow_html=True,
)

# -------------------------------
# 본문 시작
# -------------------------------
st.markdown("<div class='mobile-frame'>", unsafe_allow_html=True)

# 상단 사진 + 타이틀
st.image(HERO_IMAGE, use_column_width=True)

st.markdown("<div class='headline'>Wedding Invitation</div>", unsafe_allow_html=True)
st.markdown("<div class='names'>JUNHO & YURI</div>", unsafe_allow_html=True)

st.markdown(
    f"<div class='date-text'>{WEDDING_DATE.strftime('%Y.%m.%d (%a)')} · {WEDDING_TIME_STR}</div>",
    unsafe_allow_html=True,
)

st.markdown("---")

# -------------------------------
# 사진 슬라이드
# -------------------------------
st.markdown("### 📸 Our Moments")

idx = st.slider("사진 넘겨보기", 0, len(PHOTO_GALLERY) - 1, 0, label_visibility="collapsed")
st.image(PHOTO_GALLERY[idx], use_column_width=True)

dots = "".join("● " if i == idx else "○ " for i in range(len(PHOTO_GALLERY)))
st.markdown(f"<div class='dots'>{dots}</div>", unsafe_allow_html=True)

# -------------------------------
# 인사말
# -------------------------------
st.markdown("<div class='section-title'>💌 인사말</div>", unsafe_allow_html=True)
st.markdown(
    """
    <div class='section-box'>
    서로의 하루를 함께 채워가고자  
    평생의 동반자가 되기로 약속했습니다.<br><br>
    바쁘시겠지만 오셔서 저희의 새로운 시작을  
    따뜻한 마음으로 축복해 주시면 감사하겠습니다.
    </div>
    """,
    unsafe_allow_html=True,
)

# -------------------------------
# 예식 안내
# -------------------------------
st.markdown("<div class='section-title'>📍 예식 안내</div>", unsafe_allow_html=True)
st.markdown(
    f"""
    <div class='section-box'>
    <b>일시</b>  : {WEDDING_DATE.strftime('%Y년 %m월 %d일 (%a)')} {WEDDING_TIME_STR}<br>
    <b>장소</b>  : {VENUE_NAME}<br>
    <b>주소</b>  : {VENUE_ADDR}<br><br>
    <a class='link-button' href='{NAVER_MAP_URL}' target='_blank'>네이버 지도</a>
    </div>
    """,
    unsafe_allow_html=True,
)

# -------------------------------
# 연락처
# -------------------------------
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

# -------------------------------
# RSVP
# -------------------------------
st.markdown("<div class='section-title'>✏️ 참석 여부</div>", unsafe_allow_html=True)

name = st.text_input("이름")
attend = st.radio("참석 여부", ["참석합니다", "불참합니다", "미정입니다"])
message = st.text_area("축하 메시지 (선택)")

if st.button("전달하기"):
    # TODO: 여기에 구글 시트, DB, 이메일 등 연동
    st.success("전달되었습니다. 감사합니다.")

st.markdown("</div>", unsafe_allow_html=True)
