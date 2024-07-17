import subprocess

def install_packages():
    packages = ["matplotlib", "Pillow"]
    for package in packages:
        subprocess.run(["pip", "install", package])

install_packages()


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
import matplotlib.pyplot as plt
from PIL import Image
from io import BytesIO

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

# 달력 이미지를 생성하는 함수
def create_calendar_image(year, month, schedule_data, shift_colors):
    cal = calendar.Calendar(firstweekday=6)  # 일요일이 첫번째로 오도록 설정
    month_days = cal.monthdayscalendar(year, month)
    
    fig, ax = plt.subplots(figsize=(10, 8))
    ax.set_axis_off()

    table_data = []
    for week in month_days:
        week_data = []
        for day in week:
            if day != 0:
                date_str = f"{year}-{month:02d}-{day:02d}"
                current_date = datetime(year, month, day).date()
                shift = schedule_data.get(date_str, "")
                day_text = f"{day}\n{shift if shift != '비' else ''}"
                week_data.append(f"{day_text}")
            else:
                week_data.append("")
        table_data.append(week_data)

    table = ax.table(cellText=table_data, cellLoc='center', loc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(14)
    table.scale(1.2, 1.2)

    for i, week in enumerate(month_days):
        for j, day in enumerate(week):
            if day != 0:
                date_str = f"{year}-{month:02d}-{day:02d}"
                shift = schedule_data.get(date_str, "")
                cell = table[i + 1, j]
                cell.set_facecolor(shift_colors.get(shift, "white"))
    
    img_buf = BytesIO()
    plt.savefig(img_buf, format='png')
    plt.close(fig)
    img_buf.seek(0)
    img = Image.open(img_buf)
    
    return img

# 이미지를 GitHub에 업로드하는 함수
def upload_image_to_github(image, year, month):
    image_name = f"{year}년_{month}월.png"
    img_buf = BytesIO()
    image.save(img_buf, format='PNG')
    img_buf.seek(0)
    img_content = base64.b64encode(img_buf.read()).decode('utf-8')

    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/images/{image_name}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "message": f"Upload calendar image for {year}년 {month}월",
        "content": img_content,
    }
    response = requests.put(url, headers=headers, data=json.dumps(data))
    return response.status_code in (200, 201)

# GitHub에서 달력 이미지 URL 생성 함수
def get_calendar_image_url(year, month):
    image_name = f"{year}년_{month}월.png"
    return f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/images/{image_name}"

# Streamlit에서 이미지 로드 및 표시
def display_calendar_image(year, month):
    image_url = get_calendar_image_url(year, month)
    st.image(image_url, caption=f"{year}년 {month}월 교대근무 달력", use_column_width=True)

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

# 근무 조 설정
shift_colors = {
    "주": "#FFFF99",  # yellow
    "야": "#D3D3D3",  # lightgray
    "비": "#FFFFFF",  # white
    "올": "#90EE90"   # lightgreen
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

today = datetime.now(pytz.timezone('Asia/Seoul')).date()
yesterday = today - timedelta(days=1)

# 달력 이미지 생성
calendar_img = create_calendar_image(year, month, schedule_data, shift_colors)

# 생성된 이미지 GitHub에 업로드
if upload_image_to_github(calendar_img, year, month):
    st.success("달력 이미지가 GitHub에 업로드되었습니다.")
else:
    st.error("이미지 업로드에 실패했습니다.")

# Streamlit 페이지 구성
st.title(f"{year}년 {month}월 교대근무 달력")

# 달력 이미지 표시
display_calendar_image(year, month)

# 팀 설정
with st.expander("팀 설정", expanded=st.session_state.expander_open):
    selected_team = st.selectbox("팀 선택", options=["A", "B", "C", "D"], index=["A", "B", "C", "D"].index(st.session_state.team))
    if selected_team != st.session_state.team:
        st.session_state.team = selected_team
        save_team_settings(selected_team)
        st.session_state.expander_open = True  # 선택 후 펼침 상태 유지
        st.experimental_rerun()

# 이전/다음 월 버튼
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
