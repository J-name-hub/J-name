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
    base_date = datetime(2000, 1, 3)  # 주간 근무 시작일
    delta_days = (target_date - base_date).days
    shift_index = delta_days % len(shifts)
    return shift_patterns[team][shift_index]

# 근무일수 계산 함수
def calculate_workdays(year, month, team):
    total_workdays = 0
    cal = generate_calendar(year, month)
    for week in cal:
        for day in week:
            if day != 0:  # 빈 날 제외
                current_date = datetime(year, month, day)
                shift = get_shift(current_date, team)
                if shift in ["주", "야", "올"]:  # 근무일 계산
                    total_workdays += 1
    return total_workdays

# 스케줄 편집 기능
def edit_schedule(year, month, schedule, team):
    calendar_html = ""
    today = datetime.now().date()

    calendar.setfirstweekday(calendar.SUNDAY)
    cal = calendar.monthcalendar(year, month)

    st.sidebar.title("근무일 설정")
    holiday = load_holidays(year)

    for week in cal:
        for day in week:
            if day == 0:
                continue

            current_date = datetime(year, month, day)
            if current_date < today:
                continue

            date_str = current_date.strftime("%Y-%m-%d")
            shift = get_shift(current_date, team)

            if date_str not in schedule:
                schedule[date_str] = shift

            shift_color = shift_colors[schedule[date_str]]
            shift_choice = st.sidebar.selectbox(
                f"{date_str} 근무 조",
                ["주", "야", "비", "올"],
                index=["주", "야", "비", "올"].index(schedule[date_str]),
                key=f"edit-{date_str}"
            )

            schedule[date_str] = shift_choice

    return schedule

# 달력 표시 함수
def display_calendar(year, month, schedule, team):
    calendar_html = ""
    today = datetime.now().date()

    calendar.setfirstweekday(calendar.SUNDAY)
    cal = calendar.monthcalendar(year, month)

    # 공휴일 로드
    holidays = load_holidays(year)

    for week in cal:
        calendar_html += '<tr>'
        for day in week:
            if day == 0:
                calendar_html += '<td></td>'
            else:
                current_date = datetime(year, month, day)
                date_str = current_date.strftime("%Y-%m-%d")
                shift = get_shift(current_date, team)
                shift_color = shift_colors[schedule.get(date_str, shift)]

                # 공휴일 및 주말 설정
                is_holiday = date_str in holidays
                is_weekend = current_date.weekday() >= 5
                background_color = 'red' if is_holiday else 'lightgray' if is_weekend else shift_color[0]

                # 셀 스타일
                calendar_html += f'<td style="background-color:{background_color}; color:{shift_color[1]}; padding:5px; text-align:center;">'
                calendar_html += f'<div>{day}</div>'
                calendar_html += f'<div>{schedule.get(date_str, shift)}</div>'
                if is_holiday:
                    calendar_html += f'<div style="color:blue; font-size:small;">{", ".join(holidays[date_str])}</div>'
                calendar_html += '</td>'
        calendar_html += '</tr>'

    calendar_html = f'<table style="width:100%; border-collapse:collapse;">{calendar_html}</table>'
    return calendar_html

# 사이드바에 표시할 근무일수 정보
def display_workdays_info(year, month, team):
    total_workdays = calculate_workdays(year, month, team)
    st.sidebar.markdown(f"**총근무일수: {total_workdays}일**")

# 메인 앱
def main():
    # 타임존 설정
    tz = pytz.timezone('Asia/Seoul')
    current_time = datetime.now(tz)

    st.title("월간 근무표")
    st.sidebar.title("설정")

    # 팀 설정 로드 및 선택
    selected_team = load_team_settings_from_github()

    if st.sidebar.radio("팀 설정 변경", ["A", "B", "C", "D"], index=["A", "B", "C", "D"].index(selected_team)) != selected_team:
        selected_team = st.sidebar.radio("팀 설정 변경", ["A", "B", "C", "D"], index=["A", "B", "C", "D"].index(selected_team))
        if save_team_settings_to_github(selected_team):
            st.success("팀 설정이 저장되었습니다.")
        else:
            st.error("팀 설정 저장 실패")

    # 년과 월 선택
    selected_year = st.sidebar.selectbox("연도", list(range(2020, 2031)), index=current_time.year - 2020)
    selected_month = st.sidebar.selectbox("월", list(range(1, 13)), index=current_time.month - 1)

    # 근무일수 정보 표시
    display_workdays_info(selected_year, selected_month, selected_team)

    # 스케줄 로드
    schedule_data, sha = load_schedule()

    # 해당 월의 스케줄 데이터 가져오기
    if str(selected_year) not in schedule_data:
        schedule_data[str(selected_year)] = {}
    if str(selected_month) not in schedule_data[str(selected_year)]:
        schedule_data[str(selected_year)][str(selected_month)] = {}

    # 스케줄 편집
    schedule = schedule_data[str(selected_year)][str(selected_month)]
    schedule = edit_schedule(selected_year, selected_month, schedule, selected_team)
    schedule_data[str(selected_year)][str(selected_month)] = schedule

    # 스케줄 저장
    if save_schedule(schedule_data, sha):
        st.success("스케줄이 저장되었습니다.")
    else:
        st.error("스케줄 저장 실패")

    # 달력 표시
    calendar_html = display_calendar(selected_year, selected_month, schedule, selected_team)
    st.markdown(calendar_html, unsafe_allow_html=True)

    # 공휴일 설명
    holiday_descriptions = create_holiday_descriptions(load_holidays(selected_year), selected_month)
    if holiday_descriptions:
        st.sidebar.subheader("공휴일")
        for description in holiday_descriptions:
            st.sidebar.markdown(f"- {description}")

if __name__ == "__main__":
    main()
