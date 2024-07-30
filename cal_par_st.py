import streamlit as st
import requests
import json
from datetime import datetime, timedelta
import calendar
import pandas as pd
import pytz
from dateutil.relativedelta import relativedelta
import base64
import os

# GitHub 설정
GITHUB_TOKEN = st.secrets["github"]["token"]
GITHUB_REPO = st.secrets["github"]["repo"]
GITHUB_FILE_PATH = st.secrets["github"]["file_path"]

# 대한민국 공휴일 API 키
HOLIDAY_API_KEY = st.secrets["api_keys"]["holiday_api_key"]

# 설정 파일 경로
TEAM_SETTINGS_FILE = "team_settings.json"

# GitHub에서 스케줄 파일 로드
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

# GitHub에 스케줄 파일 저장
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
    response = requests.put(url, headers=headers, data=json.dumps(data))
    return response.status_code in (200, 201)

# 팀 설정 파일 로드
def load_team_settings():
    if os.path.exists(TEAM_SETTINGS_FILE):
        with open(TEAM_SETTINGS_FILE, "r") as f:
            return json.load(f).get("team", "A")
    return "A"

# 팀 설정 파일 저장
def save_team_settings(team):
    with open(TEAM_SETTINGS_FILE, "w") as f:
        json.dump({"team": team}, f)

# 공휴일 정보 로드
def load_holidays(year):
    url = f"http://apis.data.go.kr/B090041/openapi/service/SpcdeInfoService/getRestDeInfo?ServiceKey={HOLIDAY_API_KEY}&solYear={year}&numOfRows=100&_type=json"
    response = requests.get(url)
    holidays = []
    holiday_info = {}
    if response.status_code == 200:
        try:
            data = response.json()
            if 'response' in data and 'body' in data['response'] and 'items' in data['response']['body']:
                items = data['response']['body']['items']['item']
                if isinstance(items, list):
                    for item in items:
                        locdate = str(item['locdate'])
                        date_str = datetime.strptime(locdate, "%Y%m%d").strftime("%Y-%m-%d")
                        holidays.append(date_str)
                        holiday_info[date_str] = item['dateName']
                elif isinstance(items, dict):  # 공휴일이 한 개일 경우
                    locdate = str(items['locdate'])
                    date_str = datetime.strptime(locdate, "%Y%m%d").strftime("%Y-%m-%d")
                    holidays.append(date_str)
                    holiday_info[date_str] = items['dateName']
        except (json.JSONDecodeError, KeyError):
            pass  # 공휴일이 없는 경우 오류를 무시
    return holidays, holiday_info

# 스케줄 데이터 초기 로드
schedule_data, sha = load_schedule()

# 기본 스케줄 데이터 설정
if not schedule_data:
    schedule_data = {}
    sha = None

# Streamlit 페이지 설정
st.set_page_config(page_title="교대근무 달력", layout="wide")

# 현재 연도와 월을 얻기 위한 함수
def get_current_year_month():
    today = datetime.now(pytz.timezone('Asia/Seoul'))
    return today.year, today.month

# 세션 상태 초기화
if "year" not in st.session_state or "month" not in st.session_state:
    st.session_state.year, st.session_state.month = get_current_year_month()

if "expander_open" not in st.session_state:
    st.session_state.expander_open = False

# 팀 설정 초기화
if "team" not in st.session_state:
    st.session_state.team = load_team_settings()  # 파일에서 팀 설정 로드

year = st.session_state.year
month = st.session_state.month

# 공휴일 로드
holidays, holiday_info = load_holidays(year)

# 달력 생성 함수
def generate_calendar(year, month):
    cal = calendar.Calendar(firstweekday=6)  # 일요일이 첫번째로 오도록 설정
    return cal.monthdayscalendar(year, month)

# 근무 조 설정
shift_colors = {
    "주": "background-color: yellow",
    "야": "background-color: lightgray",
    "비": "background-color: white",
    "올": "background-color: lightgreen"
}

shifts = ["주", "야", "비", "비"]
shift_patterns = {
    "A": shifts,
    "B": shifts[-1:] + shifts[:-1],
    "C": shifts[-2:] + shifts[:-2],
    "D": shifts[-3:] + shifts[:-3],
}

# 날짜에 해당하는 근무 조를 얻는 함수
def get_shift(target_date, team):
    base_date = datetime(2000, 1, 3).date()
    delta_days = (target_date - base_date).days
    pattern = shift_patterns[team]
    return pattern[delta_days % len(pattern)]

# 페이지 제목 설정
titleup_style = "font-size: 18px; font-weight: bold; text-align: center;"
st.markdown(f"<div style='{titleup_style}'>{year}년</div>", unsafe_allow_html=True)

title_style = "font-size: 30px; font-weight: bold; text-align: center;"
st.markdown(f"<div style='{title_style}'>{month}월 교대근무 달력</div>", unsafe_allow_html=True)

today = datetime.now(pytz.timezone('Asia/Seoul')).date()
yesterday = today - timedelta(days=1)

# 이전 월 버튼
if st.button("이전 월"):
    selected_year_month = (year, month - 1)
    if month == 1:
        selected_year_month = (year - 1, 12)
    selected_year, selected_month = selected_year_month
    if selected_year != year or selected_month != month:
        st.session_state.year = selected_year
        st.session_state.month = selected_month
        year = selected_year
        month = selected_month
        st.rerun()

month_days = generate_calendar(year, month)

# 달력 데이터 생성
calendar_data = []
for week in month_days:
    week_data = []
    for day in week:
        if day != 0:
            date_str = f"{year}-{month:02d}-{day:02d}"
            current_date = datetime(year, month, day).date()
            if date_str not in schedule_data:
                schedule_data[date_str] = get_shift(current_date, st.session_state.get("team", "A"))
            background = shift_colors[schedule_data[date_str]]
            day_style = "font-weight: bold; text-align: center; padding: 1px; height: 55px; font-size: 18px;"

            if current_date == today:
                background = "background-color: lightblue"
            elif current_date == yesterday:
                background = shift_colors[schedule_data[date_str]]

            if current_date.weekday() == 5:
                day_style += " color: red;"
            elif current_date.weekday() == 6 or date_str in holidays:
                day_style += " color: red;"
            else:
                day_style += " color: black;"

            shift_text = f"<div>{day}<br><span>{schedule_data[date_str] if schedule_data[date_str] != '비' else '&nbsp;'}</span></div>"
            week_data.append(f"<div style='{background}; {day_style}'>{shift_text}</div>")
        else:
            week_data.append("<div style='height: 55px;'>&nbsp;</div>")  # 빈 셀 높이 맞춤
    calendar_data.append(week_data)

calendar_df = pd.DataFrame(calendar_data, columns=["일", "월", "화", "수", "목", "금", "토"])

# 요일 헤더 스타일 설정
days_header = ["일", "월", "화", "수", "목", "금", "토"]
days_header_style = [
    "background-color: white; text-align: center; font-weight: bold; color: red; font-size: 18px;",
    "background-color: white; text-align: center; font-weight: bold; color: black; font-size: 18px;",
    "background-color: white; text-align: center; font-weight: bold; color: black; font-size: 18px;",
    "background-color: white; text-align: center; font-weight: bold; color: black; font-size: 18px;",
    "background-color: white; text-align: center; font-weight: bold; color: black; font-size: 18px;",
    "background-color: white; text-align: center; font-weight: bold; color: black; font-size: 18px;",
    "background-color: white; text-align: center; font-weight: bold; color: red; font-size: 18px;"
]

calendar_df.columns = [f"<div style='{style}'>{day}</div>" for day, style in zip(days_header, days_header_style)]

# 달력 HTML 표시
st.markdown(
    calendar_df.to_html(escape=False, index=False), 
    unsafe_allow_html=True
)

# 다음 월 버튼
if st.button("다음 월"):
    selected_year_month = (year, month + 1)
    if month == 12:
        selected_year_month = (year + 1, 1)

    selected_year, selected_month = selected_year_month
    if selected_year != year or selected_month != month:
        st.session_state.year = selected_year
        st.session_state.month = selected_month
        year = selected_year
        month = selected_month
        st.rerun()

# 공휴일 설명
# 이어지는 공휴일 그룹화 함수
def group_holidays(holiday_info, month):
    holidays = [date for date in sorted(holiday_info.keys()) if datetime.strptime(date, "%Y-%m-%d").month == month]
    grouped_holidays = {}

    for holiday in holidays:
        day = datetime.strptime(holiday, "%Y-%m-%d").day
        if day not in grouped_holidays:
            grouped_holidays[day] = []
        grouped_holidays[day].append(holiday_info[holiday])

    return grouped_holidays

# 현재 달의 공휴일 그룹화
grouped_holidays = group_holidays(holiday_info, month)

# 그룹화된 공휴일 설명 출력
holiday_descriptions = []
for day, holiday_names in sorted(grouped_holidays.items()):
    if len(holiday_names) > 1:
        holiday_descriptions.append(f"{day}일: {', '.join(holiday_names)}")
    else:
        holiday_descriptions.append(f"{day}일: {holiday_names[0]}")

st.markdown(" / ".join(holiday_descriptions))

# 사이드바: 근무 조 설정
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
            st.rerun()  # 페이지 갱신
        else:
            st.sidebar.error("암호가 일치하지 않습니다.")

# 사이드바: 일자 스케줄 변경
st.sidebar.title("스케줄 변경")
if st.sidebar.button("스케줄 변경 활성화"):
    st.session_state.expander_open = not st.session_state.expander_open

if st.session_state.expander_open:
    with st.expander("스케줄 변경", expanded=True):
        with st.form(key='schedule_change_form'):
            change_date = st.date_input("변경할 날짜", datetime(year, month, 1), key="change_date")
            new_shift = st.selectbox("새 스케줄", ["주", "야", "비", "올"], key="new_shift")
            password = st.text_input("암호 입력", type="password", key="password")
            change_submit_button = st.form_submit_button("스케줄 변경 저장")

            if change_submit_button:
                if password == "0301":
                    change_date_str = change_date.strftime("%Y-%m-%d")
                    schedule_data[change_date_str] = new_shift
                    if save_schedule(schedule_data, sha):
                        st.success("스케줄이 저장되었습니다.")
                    else:
                        st.error("스케줄 저장에 실패했습니다.")
                    st.rerun()  # 페이지 갱신
                else:
                    st.error("암호가 일치하지 않습니다.")

# 사이드바: 달력 이동
st.sidebar.title("달력 이동")

# 월 선택 박스 추가
months = {1: "1월", 2: "2월", 3: "3월", 4: "4월", 5: "5월", 6: "6월", 7: "7월", 8: "8월", 9: "9월", 10: "10월", 11: "11월", 12: "12월"}

desired_months = []
current_date = datetime(year, month, 1)
for i in range(-5, 6):
    new_date = current_date + relativedelta(months=i)
    desired_months.append((new_date.year, new_date.month))

# 년 월 selectbox 추가
selected_year_month = st.sidebar.selectbox(
    "", 
    options=desired_months,
    format_func=lambda x: f"{x[0]}년 {months[x[1]]}",
    index=5  # 현재 달이 중간에 오도록 설정
)

# 선택한 년도와 월로 변경
selected_year, selected_month = selected_year_month
if selected_year != year or selected_month != month:
    st.session_state.year = selected_year
    st.session_state.month = selected_month
    year = selected_year
    month = selected_month
    st.rerun()
