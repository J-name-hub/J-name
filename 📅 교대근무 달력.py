import streamlit as st
import requests
import json
from datetime import datetime, timedelta
import calendar
import pandas as pd
import pytz
from dateutil.relativedelta import relativedelta
import base64

# ✅ 페이지 설정
st.set_page_config(
    page_title="교대근무 달력",   # 탭에 표시될 제목
    page_icon="📅",               # 탭 아이콘 (이모지 가능)
    initial_sidebar_state="collapsed"
)

# GitHub 설정
GITHUB_TOKEN = st.secrets["github"]["token"]
GITHUB_REPO = st.secrets["github"]["repo"]
GITHUB_FILE_PATH = st.secrets["github"]["file_path"]
GITHUB_TEAM_SETTINGS_PATH = "team_settings.json"

# 스케줄 변경 비밀번호
SCHEDULE_CHANGE_PASSWORD = st.secrets["security"]["password"]

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
            # ✅ team_history가 없으면 기본값 리턴
            if "team_history" in settings:
                return settings["team_history"]
            elif "team" in settings:
                return [{"start_date": "2000-01-03", "team": settings["team"]}]
            else:
                return [{"start_date": "2000-01-03", "team": "A"}]
        except json.JSONDecodeError:
            st.error("팀 설정 파일이 유효한 JSON이 아닙니다. 기본값 사용.")
            return [{"start_date": "2000-01-03", "team": "A"}]

    except requests.RequestException as e:
        if e.response is not None and e.response.status_code == 404:
            st.warning("팀 설정 파일을 찾을 수 없습니다. 새 파일을 생성합니다.")
            if save_team_settings_to_github([{"start_date": "2000-01-03", "team": "A"}]):
                return [{"start_date": "2000-01-03", "team": "A"}]
            else:
                st.error("팀 설정 파일 생성 실패. 기본값 사용.")
                return [{"start_date": "2000-01-03", "team": "A"}]
        else:
            st.error(f"GitHub에서 팀 설정 로드 실패: {e}")
            return [{"start_date": "2000-01-03", "team": "A"}]

# GitHub에 팀설정 파일 저장
def save_team_settings_to_github(team_history):
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_TEAM_SETTINGS_PATH}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    try:
        response = requests.get(url, headers=headers)
        sha = response.json()['sha'] if response.status_code == 200 else None

        content_dict = {"team_history": team_history}
        encoded_content = base64.b64encode(json.dumps(content_dict, indent=2).encode()).decode()

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

def get_team_for_date(target_date, team_history):
    sorted_history = sorted(team_history, key=lambda x: x["start_date"])
    current_team = sorted_history[0]["team"]
    for record in sorted_history:
        if target_date >= datetime.strptime(record["start_date"], "%Y-%m-%d").date():
            current_team = record["team"]
        else:
            break
    return current_team

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
    "올": ("lightblue", "black")
}

shifts = ["주", "야", "비", "비"]
shift_patterns = {
    "C": shifts,
    "B": shifts[-1:] + shifts[:-1],
    "A": shifts[-2:] + shifts[:-2],
    "D": shifts[-3:] + shifts[:-3],
}

# 날짜에 해당하는 근무 조를 얻는 함수
@st.cache_data
def get_shift(target_date, team_history, schedule_data):
    team = get_team_for_date(target_date, team_history)
    base_date = datetime(2000, 1, 3).date()
    delta_days = (target_date - base_date).days
    pattern = shift_patterns[team]
    return pattern[delta_days % len(pattern)]

# 근무일수 계산 함수
def calculate_workdays(year, month, team_history, schedule_data):
    total_workdays = 0
    cal = generate_calendar(year, month)
    for week in cal:
        for day in week:
            if day != 0:  # 빈 날 제외
                date_str = f"{year}-{month:02d}-{day:02d}"
                current_date = datetime(year, month, day).date()
                # GitHub에서 저장된 스케줄 데이터 확인
                if date_str in schedule_data:
                    shift = schedule_data[date_str]
                else:
                    shift = get_shift(current_date, team_history, schedule_data)
                if shift in ["주", "야", "올"]:  # 근무일 계산
                    total_workdays += 1
    return total_workdays

def calculate_workdays_until_date(year, month, team_history, schedule_data, end_date):
    total_workdays = 0
    cal = generate_calendar(year, month)
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
                    shift = get_shift(current_date, team_history, schedule_data)
                if shift in ["주", "야", "올"]:  # 근무일 계산
                    total_workdays += 1
    return total_workdays

# 사이드바에 표시할 근무일수 정보를 업데이트합니다
def display_workdays_info(year, month, team_history, schedule_data):
    total_workdays = calculate_workdays(year, month, team_history, schedule_data)
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
        workdays_until_today = calculate_workdays_until_date(year, month, team_history, schedule_data, today)
        remaining_workdays = total_workdays - workdays_until_today

    st.sidebar.title(f"📋 월 근무일수 : {total_workdays}일")
    st.sidebar.write(f"**(오늘제외 남은일수  {remaining_workdays}일)**")

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
        .button-container {
            display: flex;
            justify-content: center;
            gap: 10px;
            margin-bottom: 0;
        }
        .stButton {
            display: inline-block;
        }
        .stButton > button {
            width: 100%;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-size: 16px;
            padding: 8px 14px;
            height: 40px;
            cursor: pointer;
            text-align: center;
            text-decoration: none;
            background-color: #4F4F4F;  /* 어두운 회색 배경 */
            color: #FFFFFF;  /* 흰색 글자 */
            border: 1px solid #6E6E6E;  /* 약간 밝은 회색 테두리 */
            border-radius: 4px;
            transition: all 0.3s ease;
        }
        .stButton > button:hover {
            background-color: #6E6E6E;  /* 호버 시 밝은 회색으로 변경 */
            border-color: #8E8E8E;
        }
        .calendar-container {
            border: 2px solid #dee2e6;
            border-radius: 10px;
            overflow: hidden;
            background-color: white;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
            max-width: 800px;
            margin: 0 auto 0 auto;
            padding: 10px;
        }
        .calendar-header {
            background-color: #343a40;
            color: white;
            text-align: center;
            padding: 3px 0;
            border-radius: 10px 10px 0 0;
            font-size: 28px;
            font-weight: bold;
        }
        .calendar-header .year {
            font-size: 18px;
        }
        .calendar-header .month {
            font-size: 28px;
        }
        .calendar-header-cell {
            flex: 1;
            text-align: center;
            padding: 1px;
            font-weight: bold;
            font-size: 30px;
        }
        .calendar-header-cell:last-child {
            border-right: none;
        }
        .calendar-weekdays {
            display: flex;
            justify-content: space-between;
            background-color: #f8f9fa;
            padding: 3px 0;
            border-bottom: 1px solid #dee2e6;
            font-weight: bold;
            color: #495057;
        }
        .calendar-weekdays-cell {
            flex: 1;
            text-align: center;
            padding: 1px;
            font-weight: bold;
            font-size: 18px;
        }
        .calendar-weekdays-cell:last-child {
            border-right: none;
        }
        .calendar-row {
            display: flex;
            justify-content: space-between;
            padding: 3px 0;
            border-bottom: 1px solid #dee2e6;
        }
        .calendar-row:last-child {
            border-bottom: 0;
        }
        .calendar-cell {
            width: 13%;
            text-align: center;
            position: relative;
            height: 53px;  /* 셀의 전체 높이를 줄임 */
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .calendar-cell:last-child {
            border-right: none;
        }
        .calendar-cell-content {
            border-radius: 5px;
            padding: 1px;  /* 패딩을 줄임 */
            transition: background-color 0.3s ease;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100%;
        }
        .calendar-cell-content.today {
            border: 2px solid #007bff;
            background-color: #E8F0FE;
        }
        .calendar-day {
            font-weight: bold;
            color: #343a40;
            margin-bottom: 0px;  /* 하단 여백을 줄임 */
            font-size: 17px;  /* 글자 크기를 조정 */
        }
        .calendar-shift {
            padding: 0px 2px;
            margin: 1px 0;
            border-radius: 3px;
            font-size: 17px;
            font-weight: bold;
            color: white;
            display: inline-block;
            min-width: 28px;  /* 최소 폭을 약간 늘림 */
            line-height: 1.2;  /* 줄 간격을 조정 */
        }
        .holiday-descriptions {
            margin-top: 10px;
            padding: 5px;
            background-color: #f8f9fa;
            border-radius: 5px;
            font-size: 15px;
            font-weight: bold;
            color: #343a40;
        }
        </style>
    """, unsafe_allow_html=True)

    # 세션 상태 초기화
    if "year" not in st.session_state or "month" not in st.session_state:
        today = datetime.now(pytz.timezone('Asia/Seoul'))
        st.session_state.year, st.session_state.month = today.year, today.month

    if "expander_open" not in st.session_state:
        st.session_state.expander_open = False

    # GitHub에서 팀 설정 로드 및 세션 상태 업데이트
    if "team_history" not in st.session_state:
        st.session_state.team_history = load_team_settings_from_github()

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

    today = datetime.now(pytz.timezone('Asia/Seoul')).date()
    yesterday = today - timedelta(days=1)

    month_days = generate_calendar(year, month)
    calendar_data = create_calendar_data(year, month, month_days, schedule_data, holidays, today, yesterday)
    display_calendar(calendar_data, year, month, holidays)

    # 버튼 컨테이너 시작
    st.markdown('<div class="button-container">', unsafe_allow_html=True)

    coll1, coll2, coll3 = st.columns([1, 3, 1])
    with coll2:
        # 버튼을 위한 컬럼 생성
        col1, col2, col3 = st.columns([3,5,3])
    
        # '이전 월' 버튼
        with col1:
            if st.button("이전 월"):
                update_month(-1)
    
        # '다음 월' 버튼
        with col3:
            if st.button("다음 월"):
                update_month(1)

    # 버튼 컨테이너 종료
    st.markdown('</div>', unsafe_allow_html=True)

    # GitHub에서 스케줄 데이터 로드
    schedule_data, sha = load_schedule(cache_key=datetime.now().strftime("%Y%m%d%H%M%S"))

    sidebar_controls(year, month, schedule_data)

def update_month(delta):
    new_date = datetime(st.session_state.year, st.session_state.month, 1) + relativedelta(months=delta)
    st.session_state.year = new_date.year
    st.session_state.month = new_date.month
    st.rerun()

# 특정 날짜에 연분홍색 배경 적용
highlighted_dates = ["01-27", "03-01", "04-06"]

def create_calendar_data(year, month, month_days, schedule_data, holidays, today, yesterday):
    team_history = load_team_settings_from_github()
    calendar_data = []
    for week in month_days:
        week_data = []
        for day in week:
            if day != 0:
                date_str = f"{year}-{month:02d}-{day:02d}"
                month_day_str = f"{month:02d}-{day:02d}"  # MM-DD 형식
                current_date = datetime(year, month, day).date()

                if date_str not in schedule_data:
                    schedule_data[date_str] = get_shift(current_date, team_history, schedule_data)

                shift = schedule_data[date_str]
                shift_background, shift_color = shift_colors.get(shift, ("white", "black"))

                # 날짜 숫자 배경을 연분홍색으로 변경할 조건
                day_background = "#FFB6C1" if month_day_str in highlighted_dates else "transparent"

                # 주말 및 공휴일 색상 지정
                day_color = "red" if current_date.weekday() in [5, 6] or date_str in holidays else "black"

                # 오늘 날짜 테두리 처리
                today_class = "today" if current_date == today else ""

                shift_text = shift if shift != '비' else '&nbsp;'
                shift_style = f"background-color: {shift_background}; color: {shift_color};" if shift != '비' else f"color: {shift_color};"

                cell_content = f'''
                    <div class="calendar-cell-content {today_class}">
                        <div class="calendar-day" style="background-color: {day_background}; color: {day_color}; 
                        border-radius: 5px; padding: 4px 8px; height: 24px; display: flex; align-items: center; justify-content: center;">
                            {day}
                        </div>
                        <div class="calendar-shift" style="{shift_style}">{shift_text}</div>
                    </div>
                '''
                week_data.append(cell_content)
            else:
                week_data.append('&nbsp;')
        calendar_data.append(week_data)
    return calendar_data

def display_calendar(calendar_data, year, month, holidays):
    # 년월 헤더 생성
    header_html = '<div class="calendar-container"><div class="calendar-header">'
    header_html += f'<div class="calendar-header"><span class="year">{year}.</span><span class="month"> {month}</span></span><span class="year">월</span></div>' + '</div>'
    
    days_weekdays = ["일", "월", "화", "수", "목", "금", "토"]
    # 요일 헤더 생성
    weekdays_html = '<div class="calendar-weekdays">'
    for day in days_weekdays:
        color = "red" if day in ["일", "토"] else "black"
        weekdays_html += f'<div class="calendar-weekdays-cell" style="color: {color};">{day}</div>'
    weekdays_html += '</div>'

    # 달력 데이터 생성
    calendar_html = ''
    for week in calendar_data:
        calendar_html += '<div class="calendar-row">'
        for cell in week:
            calendar_html += f'<div class="calendar-cell">{cell}</div>'
        calendar_html += '</div>'

    # 공휴일 설명 생성
    holiday_html = '<div class="holiday-descriptions">'
    holiday_descriptions = create_holiday_descriptions(holidays, month)
    if holiday_descriptions:
        holiday_html += " / ".join(holiday_descriptions)
    else:
        holiday_html += '&nbsp;'  # 공휴일 데이터가 없을 때 빈 줄 추가
    holiday_html += '</div>'

    # 전체 달력 HTML 조합
    full_calendar_html = header_html + weekdays_html + calendar_html + holiday_html + '</div>'

    # HTML을 Streamlit에 표시
    st.markdown(full_calendar_html, unsafe_allow_html=True)

def sidebar_controls(year, month, schedule_data):

    # team_history 로드
    team_history = load_team_settings_from_github()  # 리스트 반환됨

    # 🔹 1. 현재 조 표시
    st.sidebar.title(f"👥 현재 근무조 : {team_history[-1]['team'] if team_history else 'A'}")

    # 🔹 2. 근무 조 설정
    with st.sidebar.expander("조 설정", expanded=False):
        with st.form(key='team_settings_form'):
            available_teams = ["A", "B", "C", "D"]
            default_team = "A"
            try:
                default_team = team_history[-1]["team"]  # 가장 최근 조
            except (KeyError, IndexError, TypeError):
                default_team = "A"

            team = st.selectbox("조 선택", available_teams, index=available_teams.index(default_team))
            change_start_date = st.date_input("적용 시작일", datetime.today(), key="start_date")
            password_for_settings = st.text_input("암호 입력", type="password", key="settings_password")
            col1, col2, col3 = st.columns([1, 1, 1])
            with col3:
                submit_button = st.form_submit_button("조 설정 저장")

            if submit_button:
                if password_for_settings == SCHEDULE_CHANGE_PASSWORD:
                    new_entry = {
                        "start_date": change_start_date.strftime("%Y-%m-%d"),
                        "team": team
                    }

                    # ✅ 기존 team_history 업데이트
                    team_history_dict = {entry["start_date"]: entry["team"] for entry in team_history}
                    team_history_dict[new_entry["start_date"]] = new_entry["team"]
                    team_history = [{"start_date": k, "team": v} for k, v in sorted(team_history_dict.items())]

                    if save_team_settings_to_github(team_history):
                        st.session_state.team_history = team_history
                        st.sidebar.success(f"{new_entry['start_date']}부터 {team}조로 저장되었습니다.")
                        st.rerun()
                    else:
                        st.sidebar.error("조 설정 저장에 실패했습니다.")
                else:
                    st.sidebar.error("암호가 일치하지 않습니다.")

    toggle_label = "스케줄 변경 비활성화" if st.session_state.expander_open else "스케줄 변경 활성화"
    if st.sidebar.button(toggle_label):
        st.session_state.expander_open = not st.session_state.expander_open
        st.rerun()

    if st.session_state.expander_open:
        coll1, coll2, coll3 = st.columns([1, 3, 1])
        with coll2:
            with st.expander("스케줄 변경", expanded=True):
                with st.form(key='schedule_change_form'):
                    change_date = st.date_input("변경할 날짜", datetime(st.session_state.year, st.session_state.month, 1), key="change_date")
                    new_shift = st.selectbox("새 스케줄", ["주", "야", "비", "올"], key="new_shift")
                    password = st.text_input("암호 입력", type="password", key="password")
                    col1, col2, col3 = st.columns([1, 2, 1])
                    with col3:
                        change_submit_button = st.form_submit_button("스케줄 변경 저장")
    
                    if change_submit_button:
                        if password == SCHEDULE_CHANGE_PASSWORD:
                            schedule_data, sha = load_schedule(cache_key=datetime.now().strftime("%Y%m%d%H%M%S"))
                            change_date_str = change_date.strftime("%Y-%m-%d")
                            schedule_data[change_date_str] = new_shift
                            if save_schedule(schedule_data, sha):
                                st.success("스케줄이 저장되었습니다.")
                                # 캐시 키를 변경하여 새로운 데이터를 로드하도록 함
                                st.session_state.cache_key = datetime.now().strftime("%Y%m%d%H%M%S")
                            else:
                                st.error("스케줄 저장에 실패했습니다.")
                            st.rerun()
                        else:
                            st.error("암호가 일치하지 않습니다.")

    # 🔹 3. 근무일수 정보 표시
    display_workdays_info(st.session_state.year, st.session_state.month, team_history, schedule_data)

    # 🔹 4. 조 순서 안내
    st.sidebar.title("🔁 AB → DA → CD → BC")

    # 🔹 5. 달력 이동
    st.sidebar.title("📆 달력 이동")
    months = {1: "1월", 2: "2월", 3: "3월", 4: "4월", 5: "5월", 6: "6월", 7: "7월", 8: "8월", 9: "9월", 10: "10월", 11: "11월", 12: "12월"}

    desired_months = []
    current_date = datetime(st.session_state.year, st.session_state.month, 1)
    for i in range(-5, 6):
        new_date = current_date + relativedelta(months=i)
        desired_months.append((new_date.year, new_date.month))

    selected_year_month = st.sidebar.selectbox(
        "", 
        options=desired_months,
        format_func=lambda x: f"{x[0]}년 {months[x[1]]}",
        index=5
    )

    selected_year, selected_month = selected_year_month
    if selected_year != st.session_state.year or selected_month != st.session_state.month:
        st.session_state.year = selected_year
        st.session_state.month = selected_month
        st.rerun()

if __name__ == "__main__":
    main()
