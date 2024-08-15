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
    "주": ("#FFC107", "black"),
    "야": ("#607D8B", "white"),
    "비": ("white", "black"),
    "올": ("#4CAF50", "white")
}

shifts = ["주", "야", "비", "비"]
shift_patterns = {
    "A": shifts,
    "B": shifts[-1:] + shifts[:-1],
    "C": shifts[-2:] + shifts[:-2],
    "D": shifts[-3:] + shifts[:-3],
}

# 날짜에 해당하는 근무 조를 얻는 함수
@st.cache_data
def get_shift(target_date, team):
    base_date = datetime(2000, 1, 3).date()
    delta_days = (target_date - base_date).days
    pattern = shift_patterns[team]
    return pattern[delta_days % len(pattern)]

# 주어진 월의 총 근무 일수 계산
def calculate_workdays(year, month, team, holidays):
    total_days = calendar.monthrange(year, month)[1]
    workdays = 0
    for day in range(1, total_days + 1):
        date = datetime(year, month, day).date()
        if date.weekday() >= 5 or date.strftime("%Y-%m-%d") in holidays:
            continue
        shift = get_shift(date, team)
        if shift in ["주", "야"]:
            workdays += 1
    return workdays

# 특정 날짜까지 남은 근무 일수 계산
def calculate_workdays_until_date(year, month, day, team, holidays):
    remaining_days = calendar.monthrange(year, month)[1] - day
    workdays = 0
    for d in range(day + 1, day + remaining_days + 1):
        date = datetime(year, month, d).date()
        if date.weekday() >= 5 or date.strftime("%Y-%m-%d") in holidays:
            continue
        shift = get_shift(date, team)
        if shift in ["주", "야"]:
            workdays += 1
    return workdays

# 달력 데이터 생성 함수
def create_calendar_data(cal, year, month, schedule, holidays, team):
    today = datetime.now().date()
    calendar_data = []
    for week in cal:
        week_data = []
        for day in week:
            if day == 0:
                week_data.append(("", ""))
            else:
                date = datetime(year, month, day).date()
                date_str = date.strftime("%Y-%m-%d")
                shift = schedule.get(date_str, get_shift(date, team))
                is_today = (date == today)
                is_holiday = (date_str in holidays)
                day_color, text_color = shift_colors[shift]
                day_style = f"background-color: {day_color}; color: {text_color};"
                if is_today:
                    day_style += " border: 2px solid red;"
                elif is_holiday:
                    day_style += " border: 2px solid #FF5722;"
                week_data.append((day, day_style, shift))
        calendar_data.append(week_data)
    return calendar_data

# 달력 출력 함수
def display_calendar(calendar_data, holidays, team):
    st.write('<style>div.css-1y0tads { gap: 0 !important; }</style>', unsafe_allow_html=True)
    st.write('<div style="display: flex; justify-content: space-between; align-items: center; background-color: #2196F3; color: white; padding: 10px; border-radius: 5px;">'
             f'<h2 style="margin: 0;">{st.session_state["current_year"]}년 {st.session_state["current_month"]}월 - Team {team}</h2>'
             '</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])

    with col1:
        st.write('<div style="display: flex; justify-content: flex-start;">'
                 '<style>button[aria-label="previous month"] { background-color: #FFC107; border: none; border-radius: 5px; color: black; padding: 10px 20px; cursor: pointer; }'
                 'button[aria-label="previous month"]:hover { background-color: #FFB300; }</style>'
                 '<button aria-label="previous month">이전 달</button>'
                 '</div>', unsafe_allow_html=True)

    with col2:
        st.write('<div style="display: flex; justify-content: center;">'
                 '<style>button[aria-label="today"] { background-color: #4CAF50; border: none; border-radius: 5px; color: white; padding: 10px 20px; cursor: pointer; }'
                 'button[aria-label="today"]:hover { background-color: #45A049; }</style>'
                 '<button aria-label="today">오늘</button>'
                 '</div>', unsafe_allow_html=True)

    with col3:
        st.write('<div style="display: flex; justify-content: flex-end;">'
                 '<style>button[aria-label="next month"] { background-color: #FFC107; border: none; border-radius: 5px; color: black; padding: 10px 20px; cursor: pointer; }'
                 'button[aria-label="next month"]:hover { background-color: #FFB300; }</style>'
                 '<button aria-label="next month">다음 달</button>'
                 '</div>', unsafe_allow_html=True)

    st.write('<div style="background-color: #E3F2FD; padding: 10px; border-radius: 5px;">'
             '<style>div.css-17eq0hr div[role="grid"] { display: flex; flex-wrap: wrap; justify-content: space-between; }'
             'div.css-17eq0hr div[role="grid"] div[role="gridcell"] { width: 14%; box-sizing: border-box; padding: 10px; border-radius: 5px; margin-bottom: 10px; }'
             'div.css-17eq0hr div[role="grid"] div[role="gridcell"]:hover { background-color: #BBDEFB; }</style>'
             '<div role="grid">', unsafe_allow_html=True)

    for week_data in calendar_data:
        for day, day_style, shift in week_data:
            if day:
                st.write(f'<div role="gridcell" style="{day_style}">'
                         f'<span style="font-weight: bold;">{day}</span><br>'
                         f'<span>{shift}</span></div>', unsafe_allow_html=True)
            else:
                st.write('<div role="gridcell" style="background-color: transparent;"></div>', unsafe_allow_html=True)

    st.write('</div></div>', unsafe_allow_html=True)

    holiday_descriptions = create_holiday_descriptions(holidays, st.session_state["current_month"])
    if holiday_descriptions:
        st.write('<div style="background-color: #FFEBEE; padding: 10px; border-radius: 5px; margin-top: 10px;">'
                 '<h4 style="margin: 0;">이번 달 공휴일</h4>'
                 '<ul>', unsafe_allow_html=True)
        for desc in holiday_descriptions:
            st.write(f'<li>{desc}</li>', unsafe_allow_html=True)
        st.write('</ul></div>', unsafe_allow_html=True)

# Streamlit 앱 메인 함수
def main():
    # 기본 상태 설정
    if "team" not in st.session_state:
        st.session_state["team"] = load_team_settings_from_github()

    if "current_year" not in st.session_state:
        st.session_state["current_year"] = datetime.now().year

    if "current_month" not in st.session_state:
        st.session_state["current_month"] = datetime.now().month

    st.sidebar.title("설정")
    team = st.sidebar.selectbox("팀 선택", options=["A", "B", "C", "D"], index=["A", "B", "C", "D"].index(st.session_state["team"]))

    if st.sidebar.button("팀 저장"):
        password = st.sidebar.text_input("비밀번호 입력", type="password")
        if password == st.secrets["passwords"]["team_change_password"]:
            st.session_state["team"] = team
            if save_team_settings_to_github(team):
                st.sidebar.success("팀 설정이 저장되었습니다.")
            else:
                st.sidebar.error("팀 설정 저장에 실패했습니다.")
        else:
            st.sidebar.error("비밀번호가 올바르지 않습니다.")

    # 스케줄 불러오기
    schedule, sha = load_schedule()

    # 현재 달력 생성
    calendar_data = generate_calendar(st.session_state["current_year"], st.session_state["current_month"])
    holidays = load_holidays(st.session_state["current_year"])
    calendar_data = create_calendar_data(calendar_data, st.session_state["current_year"], st.session_state["current_month"], schedule, holidays, st.session_state["team"])

    # 달력 출력
    display_calendar(calendar_data, holidays, st.session_state["team"])

    # 근무 일수 정보 출력
    st.sidebar.title("근무 일수")
    workdays = calculate_workdays(st.session_state["current_year"], st.session_state["current_month"], st.session_state["team"], holidays)
    remaining_workdays = calculate_workdays_until_date(st.session_state["current_year"], st.session_state["current_month"], datetime.now().day, st.session_state["team"], holidays)

    st.sidebar.write(f"이번 달 총 근무 일수: {workdays}일")
    st.sidebar.write(f"남은 근무 일수: {remaining_workdays}일")

# 앱 실행
if __name__ == "__main__":
    main()
