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
            if day != 0:
                date_str = f"{year}-{month:02d}-{day:02d}"
                current_date = datetime(year, month, day).date()
                shift = schedule_data.get(date_str, get_shift(current_date, team))
                if shift in ["주", "야", "올"]:
                    total_workdays += 1
    return total_workdays

def calculate_workdays_until_date(year, month, team, schedule_data, end_date):
    total_workdays = 0
    cal = calendar.monthcalendar(year, month)
    for week in cal:
        for day in week:
            if day != 0:
                date_str = f"{year}-{month:02d}-{day:02d}"
                current_date = datetime(year, month, day).date()
                if current_date > end_date:
                    return total_workdays
                shift = schedule_data.get(date_str, get_shift(current_date, team))
                if shift in ["주", "야", "올"]:
                    total_workdays += 1
    return total_workdays

def display_workdays_info(year, month, team, schedule_data):
    total_workdays = calculate_workdays(year, month, team, schedule_data)
    today = datetime.now(pytz.timezone('Asia/Seoul')).date()
    
    first_date = datetime(year, month, 1).date()
    _, last_day = calendar.monthrange(year, month)
    last_date = datetime(year, month, last_day).date()
    
    if last_date < today:
        remaining_workdays = 0
    elif first_date > today:
        remaining_workdays = total_workdays
    else:
        workdays_until_today = calculate_workdays_until_date(year, month, team, schedule_data, today)
        remaining_workdays = total_workdays - workdays_until_today

    st.sidebar.markdown(f"**월 근무일수: {total_workdays}일**")
    st.sidebar.markdown(f"**(오늘 제외 남은 일수: {remaining_workdays}일)**")

def main():
    st.set_page_config(page_title="교대근무 달력", layout="wide")

    st.markdown("""
        <style>
        .calendar-container { display: flex; flex-wrap: wrap; justify-content: center; }
        .calendar-month { margin: 10px; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }
        .calendar-header { font-size: 18px; font-weight: bold; text-align: center; margin-bottom: 10px; }
        .calendar-weekdays { display: flex; justify-content: space-between; font-weight: bold; }
        .calendar-weekday { width: 30px; text-align: center; }
        .calendar-week { display: flex; }
        .calendar-day { width: 30px; height: 30px; display: flex; flex-direction: column; align-items: center; justify-content: center; }
        .calendar-date { font-size: 12px; }
        .calendar-shift { font-size: 10px; font-weight: bold; }
        .shift-주 { color: #f8c291; }
        .shift-야 { color: #d1d8e0; }
        .shift-비 { color: #dff9fb; }
        .shift-올 { color: #badc58; }
        .today { background-color: #e9ecef; border-radius: 50%; }
        .weekend { color: red; }
        .holiday { color: red; }
        </style>
    """, unsafe_allow_html=True)

    if "year" not in st.session_state or "month" not in st.session_state:
        today = datetime.now(pytz.timezone('Asia/Seoul'))
        st.session_state.year, st.session_state.month = today.year, today.month

    if "team" not in st.session_state:
        st.session_state.team = load_team_settings_from_github()

    year = st.session_state.year
    month = st.session_state.month

    try:
        holidays = load_holidays(year)
    except Exception as e:
        st.error(f"공휴일 데이터 로드 중 오류 발생: {e}")
        holidays = {}
    schedule_data, sha = load_schedule(cache_key=datetime.now().strftime("%Y%m%d%H%M%S"))

    if not schedule_data:
        schedule_data = {}
        sha = None

    st.title(f"{year}년 {month}월 교대근무 달력")

    col1, col2, col3 = st.columns([1, 3, 1])
    with col1:
        if st.button("이전 월"):
            new_date = datetime(year, month, 1) - relativedelta(months=1)
            st.session_state.year, st.session_state.month = new_date.year, new_date.month
            st.rerun()
    with col3:
        if st.button("다음 월"):
            new_date = datetime(year, month, 1) + relativedelta(months=1)
            st.session_state.year, st.session_state.month = new_date.year, new_date.month
            st.rerun()

    today = datetime.now(pytz.timezone('Asia/Seoul')).date()
    
    st.markdown('<div class="calendar-container">', unsafe_allow_html=True)
    
    for m in range(month, month + 3):
        current_year, current_month = year, m
        if current_month > 12:
            current_year += 1
            current_month -= 12
        
        st.markdown(f'<div class="calendar-month">', unsafe_allow_html=True)
        st.markdown(f'<div class="calendar-header">{current_year}년 {current_month}월</div>', unsafe_allow_html=True)
        st.markdown('<div class="calendar-weekdays">', unsafe_allow_html=True)
        for day in ["일", "월", "화", "수", "목", "금", "토"]:
            st.markdown(f'<div class="calendar-weekday">{day}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        cal = calendar.monthcalendar(current_year, current_month)
        for week in cal:
            st.markdown('<div class="calendar-week">', unsafe_allow_html=True)
            for day in week:
                if day != 0:
                    date = datetime(current_year, current_month, day).date()
                    date_str = date.strftime("%Y-%m-%d")
                    is_today = (date == today)
                    is_weekend = (date.weekday() >= 5)
                    is_holiday = (date_str in holidays)
                    
                    shift = schedule_data.get(date_str, get_shift(date, st.session_state.team))
                    
                    day_class = "weekend" if is_weekend else ""
                    day_class += " holiday" if is_holiday else ""
                    day_class += " today" if is_today else ""
                    
                    st.markdown(f"""
                        <div class="calendar-day {day_class}">
                            <div class="calendar-date">{day}</div>
                            <div class="calendar-shift shift-{shift}">{shift if shift != '비' else '&nbsp;'}</div>
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown('<div class="calendar-day"></div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

    sidebar_controls(year, month, schedule_data)

def sidebar_controls(year, month, schedule_data):
    st.sidebar.title("근무 조 설정")
    with st.sidebar.form(key='team_settings_form'):
        team = st.selectbox("조 선택", ["A", "B", "C", "D"], index=["A", "B", "C", "D"].index(st.session_state.team))
        password_for_settings = st.text_input("암호 입력", type="password", key="settings_password")
        submit_button = st.form_submit_button("설정 저장")

        if submit_button:
            if password_for_settings == "0301":
                if save_team_settings_to_github(team):
                    st.session_state.team = team
                    st.sidebar.success(f"{team}조로 저장되었습니다.")
                    st.rerun()
                else:
                    st.sidebar.error("조 설정 저장에 실패했습니다.")
            else:
                st.sidebar.error("암호가 일치하지 않습니다.")

    st.sidebar.title("스케줄 변경")

    months = {1: "1월", 2: "2월", 3: "3월", 4: "4월", 5: "5월", 6: "6월", 7: "7월", 8: "8월", 9: "9월", 10: "10월", 11: "11월", 12: "12월"}

    desired_months = []
    current_date = datetime(st.session_state.year, st.session_state.month, 1)
    for i in range(-5, 6):
        new_date = current_date + relativedelta(months=i)
        desired_months.append((new_date.year, new_date.month))

    selected_year_month = st.sidebar.selectbox(
        "달력 이동", 
        options=desired_months,
        format_func=lambda x: f"{x[0]}년 {months[x[1]]}",
        index=5
    )

    selected_year, selected_month = selected_year_month
    if selected_year != st.session_state.year or selected_month != st.session_state.month:
        st.session_state.year = selected_year
        st.session_state.month = selected_month
        st.rerun()

    with st.sidebar.form(key='schedule_change_form'):
        change_date = st.date_input("변경할 날짜", datetime(st.session_state.year, st.session_state.month, 1), key="change_date")
        new_shift = st.selectbox("새 스케줄", ["주", "야", "비", "올"], key="new_shift")
        password = st.text_input("암호 입력", type="password", key="password")
        change_submit_button = st.form_submit_button("스케줄 변경 저장")

        if change_submit_button:
            if password == "0301":
                schedule_data, sha = load_schedule(cache_key=datetime.now().strftime("%Y%m%d%H%M%S"))
                change_date_str = change_date.strftime("%Y-%m-%d")
                schedule_data[change_date_str] = new_shift
                if save_schedule(schedule_data, sha):
                    st.sidebar.success("스케줄이 저장되었습니다.")
                    st.session_state.cache_key = datetime.now().strftime("%Y%m%d%H%M%S")
                    st.rerun()
                else:
                    st.sidebar.error("스케줄 저장에 실패했습니다.")
            else:
                st.sidebar.error("암호가 일치하지 않습니다.")

    display_workdays_info(selected_year, selected_month, st.session_state.team, schedule_data)

if __name__ == "__main__":
    main()
