import streamlit as st
import pandas as pd
import calendar
from datetime import datetime, timedelta
import json
import requests
import base64

# GitHub 설정
GITHUB_TOKEN = st.secrets["github"]["token"]
GITHUB_REPO = st.secrets["github"]["repo"]
GITHUB_FILE_PATH = st.secrets["github"]["file_path"]

# GitHub 파일 로드 함수
def load_schedule():
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_FILE_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        content = response.json()
        file_content = base64.b64decode(content['content']).decode('utf-8')
        return json.loads(file_content), content['sha']
    else:
        return {}, None

# GitHub 파일 저장 함수
def save_schedule(schedule, sha):
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_FILE_PATH}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Content-Type": "application/json"
    }
    message = "Update schedule"
    content = base64.b64encode(json.dumps(schedule).encode('utf-8')).decode('utf-8')
    data = {
        "message": message,
        "content": content,
        "sha": sha
    }
    if sha:
        data["sha"] = sha
    response = requests.put(url, headers=headers, data=json.dumps(data))
    if response.status_code == 201 or response.status_code == 200:
        st.success("스케줄이 저장되었습니다.")
    else:
        st.error("스케줄 저장에 실패했습니다.")

# 초기 스케줄 데이터 로드
schedule_data, sha = load_schedule()

# 파일이 없을 경우 기본 값 설정
if not schedule_data:
    schedule_data = {}
    sha = None

# 페이지 설정
st.set_page_config(page_title="교대근무 달력", layout="wide")

# 월 이동 버튼 설정
def get_current_year_month():
    today = datetime.today()
    return today.year, today.month

if "year" not in st.session_state or "month" not in st.session_state:
    st.session_state.year, st.session_state.month = get_current_year_month()

if "expander_open" not in st.session_state:
    st.session_state.expander_open = False

year = st.session_state.year
month = st.session_state.month

# 달력 생성
def generate_calendar(year, month):
    cal = calendar.Calendar()
    month_days = cal.itermonthdays4(year, month)
    return month_days

# 조 색상 설정
shift_colors = {
    "주": "background-color: yellow",
    "야": "background-color: gray",
    "비": "background-color: white",
    "올": "background-color: green"
}

# 교대 근무 조 설정
shifts = ["주", "야", "비", "비"]
shift_patterns = {
    "A": shifts,
    "B": shifts[-1:] + shifts[:-1],
    "C": shifts[-2:] + shifts[:-2],
    "D": shifts[-3:] + shifts[:-3],
}

def get_shift(date, team):
    base_date = datetime(2000, 1, 3)
    delta_days = (date - base_date).days
    pattern = shift_patterns[team]
    return pattern[delta_days % len(pattern)]

# 1페이지: 달력 보기
st.title(f"{year}년 {month}월 교대근무 달력")

# 월 선택 박스 추가
months = {1: "1월", 2: "2월", 3: "3월", 4: "4월", 5: "5월", 6: "6월", 7: "7월", 8: "8월", 9: "9월", 10: "10월", 11: "11월", 12: "12월"}
years = range(year-1, year+1)  # 원하는 년도 범위를 설정합니다.

# 현재 년도와 월을 기준으로 인덱스를 설정합니다.
current_index = (year - (year - 1)) * 12 + (month - 1)

# Add a list to hold the desired months
desired_months = []
current_date = datetime(year, month, 1)
for i in range(-5, 6):
    new_date = current_date + timedelta(days=i*30)  # approximately one month per step
    desired_months.append((new_date.year, new_date.month))

selected_year_month = st.selectbox(
    "", 
    options=desired_months,
    format_func=lambda x: f"{x[0]}년 {months[x[1]]}",
    index=5  # the current month is in the middle of the range
)

# 선택한 년도와 월로 변경
selected_year, selected_month = selected_year_month
if selected_year != year or selected_month != month:
    st.session_state.year = selected_year
    st.session_state.month = selected_month
    year = selected_year
    month = selected_month
    st.experimental_rerun()

month_days = generate_calendar(year, month)

calendar_df = pd.DataFrame(columns=["월", "화", "수", "목", "금", "토", "일"])

week = []
for day in month_days:
    if day[1] == month:
        date_str = f"{day[0]}-{day[1]:02d}-{day[2]:02d}"
        date = datetime(day[0], day[1], day[2])
        if date_str not in schedule_data:
            schedule_data[date_str] = get_shift(date, st.session_state.get("team", "A"))
        background = shift_colors[schedule_data[date_str]]
        day_style = "font-weight: bold; text-align: center; padding: 10px;"
        if day[3] == 5:  # Saturday
            day_style += " color: red;"
        elif day[3] == 6:  # Sunday
            day_style += " color: red;"
        else:
            day_style += " color: black;"
        week.append(f"<div style='{background}; {day_style}'>{day[2]}</div>")
    else:
        week.append("")
    
    if day[3] == 6:  # End of the week
        calendar_df.loc[len(calendar_df)] = week
        week = []

if week:
    calendar_df.loc[len(calendar_df)] = week + [""] * (7 - len(week))

# 요일 헤더 스타일 설정
days_header = ["월", "화", "수", "목", "금", "토", "일"]
days_header_style = ["background-color: white; text-align: center; font-weight: bold; color: black;"] * 5 + ["background-color: white; text-align: center; font-weight: bold; color: red;"] * 2
calendar_df.columns = [f"<div style='{style}'>{day}</div>" for day, style in zip(days_header, days_header_style)]

st.markdown(
    calendar_df.to_html(escape=False, index=False), 
    unsafe_allow_html=True
)

# 근무 시간 설명 추가
st.markdown("**노란색 : 주간, 회색 : 야간, 초록색 : 주야**", unsafe_allow_html=True)
st.markdown("**주간은 9시\\~18시이고, 야간은 18시\\~9시입니다.**", unsafe_allow_html=True)

# 2페이지: 스케줄 설정
st.sidebar.title("근무 조 설정")
team = st.sidebar.selectbox("조 선택", ["A", "B", "C", "D"])
password_for_settings = st.sidebar.text_input("암호 입력", type="password", key="settings_password")

if st.sidebar.button("설정 저장"):
    if password_for_settings == "0301":
        st.session_state["team"] = team
        st.sidebar.success("조가 저장되었습니다.")
        st.experimental_rerun()
    else:
        st.sidebar.error("암호가 일치하지 않습니다.")

# 일자 클릭 시 스케줄 변경 버튼
if st.button("일자 스케줄 변경"):
    st.session_state.expander_open = not st.session_state.expander_open

if st.session_state.expander_open:
    with st.expander("스케줄 변경", expanded=True):
        change_date = st.date_input("변경할 날짜", datetime(year, month, 1), key="change_date")
        new_shift = st.selectbox("새 스케줄", ["주", "야", "비", "올"], key="new_shift")
        password = st.text_input("암호 입력", type="password", key="password")

        if st.button("스케줄 변경 저장"):
            if password == "0301":
                change_date_str = change_date.strftime("%Y-%m-%d")
                schedule_data[change_date_str] = new_shift
                save_schedule(schedule_data, sha)
                st.success("스케줄이 변경되었습니다.")
                st.session_state.expander_open = False
                st.experimental_rerun()
            else:
                st.error("암호가 일치하지 않습니다.")
