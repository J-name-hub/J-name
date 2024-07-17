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
        st.experimental_rerun()

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
    "background-color: white; text-align: center; font-weight: bold; color: red; font-size: 18px;",
]

# 달력 출력
st.write(
    calendar_df.style.apply(lambda _: days_header_style, axis=1).set_properties(**{"text-align": "center"})
    .applymap(lambda _: "background-color: white; text-align: center; font-weight: bold; color: black; font-size: 18px;", subset=pd.IndexSlice[:, days_header[1:6]])
    .applymap(lambda _: "background-color: white; text-align: center; font-weight: bold; color: red; font-size: 18px;", subset=pd.IndexSlice[:, [days_header[0], days_header[6]]])
    .applymap(lambda x: "height: 55px;", subset=pd.IndexSlice[:, :])
    .set_table_styles({"": {"selector": "table", "props": [("border-collapse", "collapse"), ("width", "100%")]}}, overwrite=False)
    .set_table_styles({"": {"selector": "th", "props": [("border", "1px solid black"), ("padding", "5px")]}}, overwrite=False)
    .set_table_styles({"": {"selector": "td", "props": [("border", "1px solid black"), ("padding", "5px")]}}, overwrite=False)
    .hide(axis="index")
    .hide(axis="columns")
    .to_html(), unsafe_allow_html=True
)

# 사이드바: 팀 설정
st.sidebar.title("팀 설정")
team = st.sidebar.selectbox(
    "팀 선택",
    options=["A", "B", "C", "D"],
    index=["A", "B", "C", "D"].index(st.session_state.team)
)
st.session_state.team = team
save_team_settings(team)

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
    "Select Month and Year",  # Provide a meaningful label here
    options=desired_months,
    format_func=lambda x: f"{x[0]}년 {months[x[1]]}",
    index=5,  # 현재 달이 중간에 오도록 설정
    label_visibility="collapsed"  # This will hide the label visually but still provide it for accessibility
)

# 선택한 년도와 월로 변경
selected_year, selected_month = selected_year_month
if selected_year != year or selected_month != month:
    st.session_state.year = selected_year
    st.session_state.month = selected_month
    year = selected_year
    month = selected_month
    st.experimental_rerun()

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
        st.experimental_rerun()

# 스케줄 저장
if st.button("스케줄 저장"):
    if save_schedule(schedule_data, sha):
        st.success("스케줄이 성공적으로 저장되었습니다.")
    else:
        st.error("스케줄 저장 중 오류가 발생했습니다.")
