import streamlit as st
import requests
import json
from datetime import datetime, timedelta
import calendar
import pandas as pd
import pytz
from dateutil.relativedelta import relativedelta
import base64

# GitHub 설정
GITHUB_TOKEN = st.secrets["github"]["token"]
GITHUB_REPO = st.secrets["github"]["repo"]
GITHUB_FILE_PATH = st.secrets["github"]["file_path"]
GITHUB_TEAM_SETTINGS_PATH = "team_settings.json"

# 대한민국 공휴일 API 키
HOLIDAY_API_KEY = st.secrets["api_keys"]["holiday_api_key"]

# GitHub에서 스케줄 파일 로드
@st.cache_data(ttl=3600)
def load_schedule(cache_key=None):
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_FILE_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        content = response.json()
        file_content = base64.b64decode(content['content']).decode('utf-8')
        return json.loads(file_content), content['sha']
    except requests.RequestException as e:
        st.error(f"GitHub에서 스케줄 로드 실패: {e}")
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
    try:
        response = requests.put(url, headers=headers, data=json.dumps(data))
        response.raise_for_status()
        return True
    except requests.RequestException as e:
        st.error(f"GitHub에 스케줄 저장 실패: {e}")
        return False

# GitHub에서 팀설정 파일 로드
def load_team_settings_from_github():
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_TEAM_SETTINGS_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        content = response.json()
        file_content = base64.b64decode(content['content']).decode('utf-8')
        try:
            settings = json.loads(file_content)
            return settings.get("team", "A")
        except json.JSONDecodeError:
            st.error("팀 설정 파일의 내용이 유효한 JSON 형식이 아닙니다. 기본값 'A'를 사용합니다.")
            return "A"
    except requests.RequestException as e:
        if e.response is not None and e.response.status_code == 404:
            st.warning("팀 설정 파일을 찾을 수 없습니다. 새 파일을 생성합니다.")
            if save_team_settings_to_github("A"):
                return "A"
            else:
                st.error("팀 설정 파일 생성에 실패했습니다. 기본값 'A'를 사용합니다.")
                return "A"
        else:
            st.error(f"GitHub에서 팀 설정 로드 실패: {e}")
            return "A"

# GitHub에 팀설정 파일 저장
def save_team_settings_to_github(team):
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_TEAM_SETTINGS_PATH}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    try:
        # 현재 파일 내용 확인
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            current_content = response.json()
            sha = current_content['sha']
        else:
            sha = None

        # 새 내용 생성 및 인코딩
        new_content = json.dumps({"team": team})
        encoded_content = base64.b64encode(new_content.encode()).decode()

        data = {
            "message": "Update team settings",
            "content": encoded_content,
            "sha": sha
        }

        response = requests.put(url, headers=headers, json=data)
        response.raise_for_status()
        return True
    except requests.RequestException as e:
        st.error(f"GitHub에 팀 설정 저장 실패: {e}")
        return False

# 공휴일 정보 로드
@st.cache_data(ttl=86400)
def load_holidays(year):
    url = f"http://apis.data.go.kr/B090041/openapi/service/SpcdeInfoService/getRestDeInfo?ServiceKey={HOLIDAY_API_KEY}&solYear={year}&numOfRows=100&_type=json"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        # API 응답 구조 확인
        if 'response' not in data or 'body' not in data['response']:
            st.warning(f"{year}년 공휴일 데이터를 찾을 수 없습니다.")
            return {}

        body = data['response']['body']
        if 'items' not in body or not body['items']:
            st.warning(f"{year}년 공휴일 데이터가 없습니다.")
            return {}

        items = body['items'].get('item', [])
        if isinstance(items, dict):
            items = [items]

        holidays = {}
        for item in items:
            date_str = datetime.strptime(str(item['locdate']), "%Y%m%d").strftime("%Y-%m-%d")
            if date_str not in holidays:
                holidays[date_str] = []
            holidays[date_str].append(item['dateName'])
        return holidays
    except requests.RequestException as e:
        st.error(f"공휴일 데이터 로드 실패: {e}")
        return {}
    except KeyError as e:
        st.error(f"공휴일 데이터 구조 오류: {e}")
        return {}
    except Exception as e:
        st.error(f"예상치 못한 오류 발생: {e}")
        return {}

# 공휴일 설명 생성
def create_holiday_descriptions(holidays, month):
    holiday_descriptions = []
    sorted_dates = sorted(holidays.keys())
    i = 0
    while i < len(sorted_dates):
        start_date = sorted_dates[i]
        if datetime.strptime(start_date, "%Y-%m-%d").month == month:
            start_day = datetime.strptime(start_date, "%Y-%m-%d").day
            current_holiday = holidays[start_date]

            end_date = start_date
            end_day = start_day
            j = i + 1
            while j < len(sorted_dates):
                next_date = sorted_dates[j]
                next_day = datetime.strptime(next_date, "%Y-%m-%d").day
                if next_day - end_day == 1 and any(holiday in holidays[next_date] for holiday in current_holiday):
                    end_date = next_date
                    end_day = next_day
                    j += 1
                else:
                    break

            if start_day == end_day:
                holiday_descriptions.append(f"{start_day}일: {', '.join(current_holiday)}")
            else:
                temp_descriptions = []
                for day in range(start_day, end_day + 1):
                    date = (datetime.strptime(start_date, "%Y-%m-%d") + timedelta(days=day - start_day)).strftime("%Y-%m-%d")
                    if date in holidays:
                        day_holidays = holidays[date]
                        if day_holidays != current_holiday:
                            temp_descriptions.append(f"{day}일: {', '.join(day_holidays)}")

                if temp_descriptions:
                    holiday_descriptions.append(f"{start_day}일~{end_day}일: {', '.join(current_holiday)}")
                    holiday_descriptions.extend(temp_descriptions)
                else:
                    holiday_descriptions.append(f"{start_day}일~{end_day}일: {', '.join(current_holiday)}")

            i = j
        else:
            i += 1

    return holiday_descriptions

# 달력 생성 함수
@st.cache_data
def generate_calendar(year, month):
    cal = calendar.Calendar(firstweekday=6)
    return cal.monthdayscalendar(year, month)

# 근무 조 설정
shift_colors = {
    "주": ("yellow", "black"),
    "야": ("lightgray", "black"),
    "비": ("white", "black"),
    "올": ("lightgreen", "black")
}

shifts = ["주", "야", "비", "올"]

# 날짜의 조 계산
def calculate_team_and_shift(date, team):
    reference_date = datetime(2024, 8, 3)  # 주간 근무 시작 날짜 설정
    days_diff = (date - reference_date).days
    week_number = days_diff // 7
    day_in_week = days_diff % 7

    # 팀별 주기
    team_shifts = {
        "A": ["주", "야", "비", "비", "주", "야", "올"],
        "B": ["야", "비", "비", "주", "야", "주", "올"],
        "C": ["비", "비", "주", "야", "주", "야", "올"],
        "D": ["비", "주", "야", "주", "야", "비", "올"]
    }

    current_shifts = team_shifts[team]

    return current_shifts[day_in_week]

# 월간 근무조 계산
def calculate_monthly_shifts(year, month, team):
    cal = generate_calendar(year, month)
    monthly_shifts = []
    for week in cal:
        week_shifts = []
        for day in week:
            if day == 0:
                week_shifts.append(None)
            else:
                date = datetime(year, month, day)
                shift = calculate_team_and_shift(date, team)
                week_shifts.append(shift)
        monthly_shifts.append(week_shifts)
    return monthly_shifts

# 월간 근무조 카운트
def count_workdays_in_month(monthly_shifts, shift_type):
    count = 0
    for week in monthly_shifts:
        count += week.count(shift_type)
    return count

# Streamlit 앱 설정
st.set_page_config(
    page_title="근무일정 관리",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("근무일정 관리 시스템")

# 팀 설정 로드
selected_team = load_team_settings_from_github()

st.sidebar.title("근무일정 설정")

# 팀 선택
team = st.sidebar.selectbox("팀 선택", ["A", "B", "C", "D"], index=["A", "B", "C", "D"].index(selected_team))

# 선택한 팀 저장
if st.sidebar.button("팀 저장"):
    if save_team_settings_to_github(team):
        st.sidebar.success("팀 설정 저장 완료.")
    else:
        st.sidebar.error("팀 설정 저장 실패.")

# 날짜 선택
today = datetime.now()
current_year = today.year
current_month = today.month

year = st.sidebar.selectbox("연도", range(current_year - 1, current_year + 2), index=1)
month = st.sidebar.selectbox("월", range(1, 13), index=current_month - 1)

# 근무일정 로드
schedule, sha = load_schedule(f"{year}-{month}")

# 근무일정 표시
monthly_shifts = calculate_monthly_shifts(year, month, team)

# 공휴일 정보 로드 및 설명 생성
holidays = load_holidays(year)
holiday_descriptions = create_holiday_descriptions(holidays, month)

# 근무조 카운트
work_days_count = count_workdays_in_month(monthly_shifts, "주")
night_days_count = count_workdays_in_month(monthly_shifts, "야")
all_days_count = count_workdays_in_month(monthly_shifts, "올")

# 근무조 카운트 결과 표시
st.sidebar.subheader("근무조 통계")
st.sidebar.write(f"주간 근무: {work_days_count}일")
st.sidebar.write(f"야간 근무: {night_days_count}일")
st.sidebar.write(f"올데이 근무: {all_days_count}일")

# 달력 표시
st.subheader(f"{year}년 {month}월 근무일정 ({team}팀)")
for week_index, week in enumerate(monthly_shifts):
    columns = st.columns(len(week))
    for day_index, day in enumerate(week):
        with columns[day_index]:
            if day is None:
                st.write("")
            else:
                shift = day
                if shift in shift_colors:
                    bg_color, text_color = shift_colors[shift]
                    st.markdown(
                        f'<div style="background-color: {bg_color}; color: {text_color}; padding: 10px; text-align: center;">{week[day_index]}</div>',
                        unsafe_allow_html=True
                    )
                else:
                    st.write(day)

# 공휴일 표시
st.sidebar.subheader("공휴일")
if holiday_descriptions:
    for description in holiday_descriptions:
        st.sidebar.write(description)
else:
    st.sidebar.write("이번 달 공휴일이 없습니다.")
