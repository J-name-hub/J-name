import streamlit as st
import pandas as pd
import calendar
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import json
import requests
import base64
import os
import pytz

# GitHub 설정
GITHUB_TOKEN = st.secrets["github"]["token"]
GITHUB_REPO = st.secrets["github"]["repo"]
GITHUB_FILE_PATH = st.secrets["github"]["file_path"]

# 설정 파일 경로
TEAM_SETTINGS_FILE = "team_settings.json"

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
        return True
    else:
        return False

# 팀 설정 파일 로드 함수
def load_team_settings():
    if os.path.exists(TEAM_SETTINGS_FILE):
        with open(TEAM_SETTINGS_FILE, "r") as f:
            return json.load(f).get("team", "A")
    return "A"

# 팀 설정 파일 저장 함수
def save_team_settings(team):
    with open(TEAM_SETTINGS_FILE, "w") as f:
        json.dump({"team": team}, f)

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
    today = datetime.now(pytz.timezone('Asia/Seoul'))
    return today.year, today.month

if "year" not in st.session_state or "month" not in st.session_state:
    st.session_state.year, st.session_state.month = get_current_year_month()

if "expander_open" not in st.session_state:
    st.session_state.expander_open = False

# 팀 설정 초기화
if "team" not in st.session_state:
    st.session_state.team = load_team_settings()  # 파일에서 팀 설정 로드

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
    "올": "background-color: lightgreen"
}

# 교대 근무 조 설정
shifts = ["주", "야", "비", "비"]
shift_patterns = {
    "A": shifts,
    "B": shifts[-1:] + shifts[:-1],
    "C": shifts[-2:] + shifts[:-2],
    "D": shifts[-3:] + shifts[:-3],
}

def get_shift(target_date, team):
    base_date = datetime(2000, 1, 3).date()  # 기준 날짜를 date 객체로 변경
    delta_days = (target_date - base_date).days
    pattern = shift_patterns[team]
    return pattern[delta_days % len(pattern)]

# 1페이지: 달력 보기

# CSS 스타일 정의
title_style = "font-size: 30px; font-weight: bold; text-align: center;"

# st.markdown을 사용하여 CSS 스타일 적용
st.markdown(f"<div style='{title_style}'>{month}월 교대근무 달력</div>", unsafe_allow_html=True)

# 월 선택 박스 추가
months = {1: "1월", 2: "2월", 3: "3월", 4: "4월", 5: "5월", 6: "6월", 7: "7월", 8: "8월", 9: "9월", 10: "10월", 11: "11월", 12: "12월"}
years = range(year-1, year+1)  # 원하는 년도 범위를 설정합니다.

# 현재 년도와 월을 기준으로 인덱스를 설정합니다.
current_index = (year - (year - 1)) * 12 + (month - 1)

# Add a list to hold the desired months
desired_months = []
current_date = datetime(year, month, 1)
for i in range(-5, 6):
    new_date = current_date + relativedelta(months=i)
    desired_months.append((new_date.year, new_date.month))

today = datetime.now(pytz.timezone('Asia/Seoul')).date()
yesterday = today - timedelta(days=1)

selected_year_month = st.selectbox(
    "", 
    options=desired_months,
    format_func=lambda x: f"{x[0]}년 {months[x[1]]}",
    index=5  # the current month is in the middle of the range
)

# 이전 월 버튼 추가
if st.button("이전 월"):
     selected_year_month = (year, month - 1)
     if month == 1:
        selected_year_month = (year - 1, 12)

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
        current_date = datetime(day[0], day[1], day[2]).date()
        if date_str not in schedule_data:
            schedule_data[date_str] = get_shift(current_date, st.session_state.get("team", "A"))
        background = shift_colors[schedule_data[date_str]]
        day_style = "font-weight: bold; text-align: center; padding: 1px; height: 55px; font-size: 18px;"  # Adjust padding to minimize spacing

        if current_date == today:  # 오늘 날짜 비교
            background = "background-color: lightblue"
        elif current_date == yesterday:  # 전날 날짜 비교
            background = shift_colors[schedule_data[date_str]]

        if day[3] == 5:  # Saturday
            day_style += " color: red;"
        elif day[3] == 6:  # Sunday
            day_style += " color: red;"
        else:
            day_style += " color: black;"
        shift_text = f"<div style='color: black'>{day[2]}<br><span style='color: black;'>{schedule_data[date_str] if schedule_data[date_str] != '비' else '&nbsp;'}</span></div>"  # Always black text for shift
        week.append(f"<div style='{background}; {day_style}'>{shift_text}</div>")
    else:
        week.append("<div style='height: 55px;'>&nbsp;</div>")  # Ensure empty cells also have the same height
    
    if day[3] == 6:  # End of the week
        calendar_df.loc[len(calendar_df)] = week
        week = []

if week:
    calendar_df.loc[len(calendar_df)] = week + [""] * (7 - len(week))

# 요일 헤더 스타일 설정
days_header = ["월", "화", "수", "목", "금", "토", "일"]
days_header_style = ["background-color: white; text-align: center; font-weight: bold; color: black; font-size: 18px;"] * 5 + ["background-color: white; text-align: center; font-weight: bold; color: red; font-size: 18px;"] * 2
calendar_df.columns = [f"<div style='{style}'>{day}</div>" for day, style in zip(days_header, days_header_style)]

st.markdown(
    calendar_df.to_html(escape=False, index=False), 
    unsafe_allow_html=True
)

# 다음 월 버튼 추가
if st.button("다음 월"):
     selected_year_month = (year, month + 1)
     if month == 12:
        selected_year_month = (year + 1, 1)

# 2페이지: 스케줄 설정
st.sidebar.title("근무 조 설정")
with st.sidebar.form(key='team_settings_form'):
    team = st.selectbox("조 선택", ["A", "B", "C", "D"], index=["A", "B", "C", "D"].index(st.session_state.team))
    password_for_settings = st.text_input("암호 입력", type="password", key="settings_password")
    submit_button = st.form_submit_button("설정 저장")

    if submit_button:
        if password_for_settings == "0301":
            st.session_state["team"] = team
            save_team_settings(team)  # 선택한 팀을 파일에 저장
            st.sidebar.success("조가 저장되었습니다.")
            st.experimental_rerun()  # This line ensures the page is rerun to reflect the new team
        else:
            st.sidebar.error("암호가 일치하지 않습니다.")

# 일자 클릭 시 스케줄 변경 버튼
    st.sidebar.title("일자 스케줄 변경")
    with st.sidebar.form(key='schedule_change_form'):
            change_date = st.date_input("변경할 날짜", datetime(year, month, 1), key="change_date")
            new_shift = st.selectbox("새 스케줄", ["주", "야", "비", "올"], key="new_shift")
            password = st.text_input("암호 입력", type="password", key="password")
            change_submit_button = st.form_submit_button("스케줄 변경 저장")

            if change_submit_button:
                if password == "0301":
                    change_date_str = change_date.strftime("%Y-%m-%d")
                    schedule_data[change_date_str] = new_shift
                    if save_schedule(schedule_data, sha):
                        st.sidebar.success("스케줄이 저장되었습니다.")
                    else:
                        st.error("스케줄 저장에 실패했습니다.")
                    st.experimental_rerun()  # This line ensures the page is rerun to reflect the new schedule
                else:
                    st.sidebar.error("암호가 일치하지 않습니다.")
