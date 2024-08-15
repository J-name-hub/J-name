import streamlit as st
import calendar
from datetime import datetime, timedelta
import pytz
import requests
import json
import base64
from dateutil.relativedelta import relativedelta

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

# 근무 조 설정
shift_patterns = {
    "A": ["주", "야", "비", "비"],
    "B": ["비", "주", "야", "비"],
    "C": ["비", "비", "주", "야"],
    "D": ["야", "비", "비", "주"],
}

# 날짜에 해당하는 근무 조를 얻는 함수
@st.cache_data
def get_shift(target_date, team):
    base_date = datetime(2000, 1, 3).date()
    delta_days = (target_date - base_date).days
    pattern = shift_patterns[team]
    return pattern[delta_days % len(pattern)]

# 근무일수 계산 함수
def calculate_workdays(year, month, team, schedule_data):
    total_workdays = 0
    cal = calendar.monthcalendar(year, month)
    for week in cal:
        for day in week:
            if day != 0:  # 빈 날 제외
                date_str = f"{year}-{month:02d}-{day:02d}"
                current_date = datetime(year, month, day).date()
                # GitHub에서 저장된 스케줄 데이터 확인
                if date_str in schedule_data:
                    shift = schedule_data[date_str]
                else:
                    shift = get_shift(current_date, team)
                if shift in ["주", "야", "올"]:  # 근무일 계산
                    total_workdays += 1
    return total_workdays

def calculate_workdays_until_date(year, month, team, schedule_data, end_date):
    total_workdays = 0
    cal = calendar.monthcalendar(year, month)
    for week in cal:
        for day in week:
            if day != 0:  # 빈 날 제외
                date_str = f"{year}-{month:02d}-{day:02d}"
                current_date = datetime(year, month, day).date()
                if current_date > end_date:
                    return total_workdays
                # GitHub에서 저장된 스케줄 데이터 확인
                if date_str in schedule_data:
                    shift = schedule_data[date_str]
                else:
                    shift = get_shift(current_date, team)
                if shift in ["주", "야", "올"]:  # 근무일 계산
                    total_workdays += 1
    return total_workdays

# 사이드바에 표시할 근무일수 정보를 업데이트합니다
def display_workdays_info(year, month, team, schedule_data):
    total_workdays = calculate_workdays(year, month, team, schedule_data)
    today = datetime.now(pytz.timezone('Asia/Seoul')).date()
    
    # 현재 월의 첫날과 마지막 날을 구합니다
    first_date = datetime(year, month, 1).date()
    _, last_day = calendar.monthrange(year, month)
    last_date = datetime(year, month, last_day).date()
    
    # 이전 월, 현재 월, 미래 월을 구분하여 처리합니다
    if last_date < today:  # 이전 월
        remaining_workdays = 0
    elif first_date > today:  # 미래 월
        remaining_workdays = total_workdays
    else:  # 현재 월
        remaining_workdays = calculate_workdays_until_date(year, month, team, schedule_data, today)
    
    st.sidebar.write(f"**{year}년 {month}월**")
    st.sidebar.write(f"- 총 근무일수: {total_workdays}일")
    st.sidebar.write(f"- 오늘까지 근무일수: {remaining_workdays}일")

def main():
    st.set_page_config(page_title="교대근무 달력", layout="wide")

    # CSS 스타일 추가
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap');
        body {
            font-family: 'Roboto', sans-serif;
            background-color: #f8f9fa;
        }
        .calendar-container {
            display: grid;
            grid-template-columns: repeat(7, 1fr);
            gap: 5px;
            max-width: 100%;
            margin: 0 auto;
            padding: 20px;
        }
        .calendar-cell {
            text-align: center;
            padding: 10px;
            border: 1px solid #dee2e6;
            border-radius: 5px;
            background-color: white;
        }
        .calendar-day {
            font-weight: bold;
            margin-bottom: 5px;
            color: #343a40;
        }
        .calendar-shift {
            padding: 5px;
            border-radius: 3px;
            font-size: 12px;
            font-weight: 500;
            color: white;
            margin-top: 5px;
        }
        .calendar-shift.주 { background-color: #f8c291; }
        .calendar-shift.야 { background-color: #d1d8e0; }
        .calendar-shift.비 { background-color: #dff9fb; color: #1e3799; }
        .calendar-shift.올 { background-color: #badc58; }
        .calendar-header {
            text-align: center;
            font-size: 24px;
            font-weight: bold;
            grid-column: span 7;
            margin-bottom: 10px;
        }
        </style>
    """, unsafe_allow_html=True)

    today = datetime.now(pytz.timezone('Asia/Seoul')).date()
    current_year = today.year
    current_month = today.month

    # 팀 선택 및 변경
    selected_team = load_team_settings_from_github()
    team = st.sidebar.selectbox("팀을 선택하세요", ["A", "B", "C", "D"], index=["A", "B", "C", "D"].index(selected_team))
    if team != selected_team:
        if save_team_settings_to_github(team):
            st.sidebar.success(f"팀 설정이 '{team}'로 변경되었습니다.")

    # 현재 달, 이전 달, 다음 달 선택
    selected_year = st.sidebar.selectbox("년도를 선택하세요", [current_year, current_year - 1, current_year + 1], index=0)
    selected_month = st.sidebar.selectbox("월을 선택하세요", list(range(1, 13)), index=current_month - 1)

    # 공휴일 정보 로드
    holidays = load_holidays(selected_year)

    # GitHub에서 스케줄 로드
    schedule_data, sha = load_schedule(cache_key=f"{selected_year}-{selected_month}")

    # 근무일수 정보 표시
    display_workdays_info(selected_year, selected_month, team, schedule_data)

    # 달력 헤더 표시
    st.markdown(f"<div class='calendar-header'>{selected_year}년 {selected_month}월 교대근무 달력</div>", unsafe_allow_html=True)

    # 달력 표시
    cal = calendar.monthcalendar(selected_year, selected_month)
    st.markdown("<div class='calendar-container'>", unsafe_allow_html=True)
    for week in cal:
        for day in week:
            if day != 0:
                date = datetime(selected_year, selected_month, day).date()
                shift = schedule_data.get(str(date), get_shift(date, team))
                day_color = "red" if date.weekday() >= 5 else "black"
                if str(date) in holidays:
                    holiday_str = ", ".join(holidays[str(date)])
                    tooltip = f"{holiday_str} (공휴일)"
                    shift = "비"
                else:
                    tooltip = ""

                st.markdown(f"""
                    <div class="calendar-cell" title="{tooltip}">
                        <div class="calendar-day" style="color: {day_color};">{day}</div>
                        <div class="calendar-shift {shift}">{shift}</div>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown('<div class="calendar-cell"></div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
