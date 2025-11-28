from pathlib import Path
from datetime import date, datetime
import json
import base64
import requests
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

# 이미지 경로 (파일명은 실제 파일명에 맞게 수정)
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
# 실제 카운트다운용 (14:00 기준, 한국시간 가정)
WEDDING_DATETIME = datetime(2025, 10, 18, 14, 0, 0)

VENUE_NAME = "○○웨딩홀 3층"
VENUE_ADDR = "서울시 ○○구 ○○로 123"

# 지도 embed (네이버/카카오/구글에서 복사한 iframe으로 교체)
MAP_IFRAME = """
<iframe
  width="100%"
  height="260"
  frameborder="0"
  style="border:0;border-radius:16px;"
  src="https://maps.google.com/maps?q=37.5665,126.9780&z=15&output=embed"
  allowfullscreen>
</iframe>
"""

NAVER_MAP_URL = "https://map.naver.com"  # 필요 시 유지

# -----------------------------------------
# GitHub 설정 (secrets에서 로드)
# -----------------------------------------
GITHUB_TOKEN = st.secrets["github"]["token"]
GITHUB_REPO = st.secrets["github"]["repo"]         # 예: "J-name-hub/J-name"
GITHUB_FILE_PATH = st.secrets["github"]["file_path"]  # 예: "wedding/comments.json"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_FILE_PATH}"


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
        margin-bottom: 0.3rem;
    }

    .dday-text {
        text-align: center;
        color: #a0805c;
        font-size: 0.9rem;
        margin-bottom: 1.1rem;
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

    /* 버튼 공통 스타일 */
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
# 유틸: D-day & 카운트다운
# -----------------------------------------
def get_countdown_string():
    now = datetime.now()
    delta = WEDDING_DATETIME - now
    sec = int(delta.total_seconds())

    if sec <= 0:
        return "오늘의 예식 또는 이미 지난 예식입니다."

    days = sec // 86400
    sec %= 86400
    hours = sec // 3600
    sec %= 3600
    minutes = sec // 60

    dday_str = f"D-{days}" if days > 0 else "D-Day"
    return f"{dday_str} · {days}일 {hours}시간 {minutes}분 남았습니다."


# -----------------------------------------
# 유틸: 월 달력 HTML (예식 날짜 강조)
# -----------------------------------------
import calendar

def render_calendar_html(target_date: date) -> str:
    cal = calendar.Calendar(firstweekday=6)  # 일요일 시작
    year, month = target_date.year, target_date.month
    weeks = cal.monthdayscalendar(year, month)

    html = """
    <table style="width:100%;border-collapse:collapse;font-size:0.8rem;color:#65574a;">
      <thead>
        <tr>
          <th style="padding:4px;">Su</th>
          <th style="padding:4px;">Mo</th>
          <th style="padding:4px;">Tu</th>
          <th style="padding:4px;">We</th>
          <th style="padding:4px;">Th</th>
          <th style="padding:4px;">Fr</th>
          <th style="padding:4px;">Sa</th>
        </tr>
      </thead>
      <tbody>
    """
    for week in weeks:
        html += "<tr>"
        for day in week:
            if day == 0:
                html += "<td style='padding:4px;height:26px;'></td>"
            elif day == target_date.day:
                html += (
                    "<td style='padding:4px;height:26px;'>"
                    "<div style='margin:0 auto;width:26px;height:26px;"
                    "border-radius:50%;background:#d8c5aa;color:#fff;"
                    "display:flex;align-items:center;justify-content:center;'>"
                    f"{day}</div></td>"
                )
            else:
                html += f"<td style='padding:4px;height:26px;'>{day}</td>"
        html += "</tr>"
    html += "</tbody></table>"
    return html


# -----------------------------------------
# 유틸: GitHub에 댓글 읽기/쓰기
# -----------------------------------------
def load_comments():
    """GitHub에서 comments.json 읽어오기 (없으면 빈 리스트)"""
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    res = requests.get(GITHUB_API_URL, headers=headers)

    if res.status_code == 200:
        data = res.json()
        content = base64.b64decode(data["content"]).decode("utf-8")
        try:
            comments = json.loads(content)
        except json.JSONDecodeError:
            comments = []
        sha = data["sha"]
        return comments, sha
    elif res.status_code == 404:
        # 파일이 없으면 새로 만들 예정
        return [], None
    else:
        st.error("댓글을 불러오는 중 오류가 발생했습니다.")
        return [], None


def save_comment(name: str, message: str):
    """GitHub comments.json에 댓글 추가"""
    if not name.strip() or not message.strip():
        st.warning("이름과 내용을 모두 입력해 주세요.")
        return

    comments, sha = load_comments()
    new_item = {
        "name": name.strip(),
        "message": message.strip(),
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }
    comments.append(new_item)

    new_content = json.dumps(comments, ensure_ascii=False, indent=2)
    b64_content = base64.b64encode(new_content.encode("utf-8")).decode("utf-8")

    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Content-Type": "application/json",
    }

    payload = {
        "message": "Update wedding comments",
        "content": b64_content,
        "branch": "main",
    }
    if sha:
        payload["sha"] = sha

    res = requests.put(GITHUB_API_URL, headers=headers, data=json.dumps(payload))

    if res.status_code in (200, 201):
        st.success("댓글이 등록되었습니다.")
    else:
        st.error("댓글 저장 중 오류가 발생했습니다.")


# -----------------------------------------
# 배경 음악 (자동 재생 시도)
# -----------------------------------------
BGM_HTML = """
<audio autoplay loop>
  <source src="https://www.w3schools.com/html/horse.ogg" type="audio/ogg">
  <source src="https://www.w3schools.com/html/horse.mp3" type="audio/mpeg">
</audio>
"""
# 실제 사용 시 위의 src를 본인이 업로드한 mp3 주소로 교체


# -----------------------------------------
# 본문 시작
# -----------------------------------------
st.markdown("<div class='mobile-frame'>", unsafe_allow_html=True)

# 배경 음악 embed (브라우저 정책 때문에 자동 재생이 안 될 수도 있음)
st.components.v1.html(BGM_HTML, height=0, width=0)

# 상단 메인 사진
st.image(str(HERO_IMAGE), use_column_width=True)

# 타이틀 & D-day
st.markdown("<div class='headline'>Wedding Invitation</div>", unsafe_allow_html=True)
st.markdown("<div class='names'>JUNHO & YURI</div>", unsafe_allow_html=True)

st.markdown(
    f"<div class='date-text'>{WEDDING_DATE.strftime('%Y.%m.%d')} · {WEDDING_TIME_STR}</div>",
    unsafe_allow_html=True,
)

countdown_str = get_countdown_string()
st.markdown(f"<div class='dday-text'>{countdown_str}</div>", unsafe_allow_html=True)

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
# 예식 안내 + 달력 + 지도
# -----------------------------------------
st.markdown("<div class='section-title'>📍 예식 안내</div>", unsafe_allow_html=True)

col_info, col_cal = st.columns(2)

with col_info:
    st.markdown(
        f"""
        <div class='section-box' style='font-size:0.9rem;'>
        <b>일시</b> : {WEDDING_DATE.strftime('%Y년 %m월 %d일')} {WEDDING_TIME_STR}<br>
        <b>장소</b> : {VENUE_NAME}<br>
        <b>주소</b> : {VENUE_ADDR}<br>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_cal:
    cal_html = render_calendar_html(WEDDING_DATE)
    st.markdown(
        f"""
        <div class='section-box' style='font-size:0.85rem;'>
        {WEDDING_DATE.year}년 {WEDDING_DATE.month}월
        {cal_html}
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)

# 지도 embed
st.markdown("<div class='section-box'>", unsafe_allow_html=True)
st.components.v1.html(MAP_IFRAME, height=270, scrolling=False)
st.markdown(
    f"<a class='link-button' href='{NAVER_MAP_URL}' target='_blank'>네이버 지도 앱에서 보기</a>",
    unsafe_allow_html=True,
)
st.markdown("</div>", unsafe_allow_html=True)

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
# 댓글 남기기
# -----------------------------------------
st.markdown("<div class='section-title'>💬 축하 댓글</div>", unsafe_allow_html=True)

with st.form("comment_form", clear_on_submit=True):
    c_name = st.text_input("이름")
    c_msg = st.text_area("축하 메시지를 남겨주세요")
    submitted = st.form_submit_button("댓글 남기기")

    if submitted:
        save_comment(c_name, c_msg)

# 기존 댓글 불러오기
comments, _ = load_comments()
if comments:
    for item in reversed(comments):  # 최근 것이 위로 오게
        st.markdown(
            f"""
            <div class='section-box' style='margin-top:0.5rem;text-align:left;'>
              <b>{item.get("name","손님")}</b>
              <span style='font-size:0.75rem;color:#9a8b7a;'>
                · {item.get("created_at","")}
              </span>
              <div style='margin-top:0.4rem;white-space:pre-wrap;'>{item.get("message","")}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
else:
    st.markdown(
        "<div class='section-box'>아직 댓글이 없습니다. 첫 축하 메시지를 남겨주세요. 😊</div>",
        unsafe_allow_html=True,
    )

st.markdown("</div>", unsafe_allow_html=True)
