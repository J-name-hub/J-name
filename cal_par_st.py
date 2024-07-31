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
    base_date = datetime(2000, 1, 3).date()
    delta_days = (target_date - base_date).days
    pattern = shift_patterns[team]
    return pattern[delta_days % len(pattern)]

def main():
    st.set_page_config(page_title="교대근무 달력", layout="wide")

    # CSS 스타일 추가
    st.markdown("""
        <style>
        .stButton > button {
            width: 100%;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-size: 16px;
            padding: 0px 4px;
            height: 30px;
            cursor: pointer;
            text-align: center;
            text-decoration: none;
        }
        .calendar-container {
            border: 1px solid #ddd;
            border-radius: 5px;
            overflow: hidden;
            background-color: #f9f9f9;
        }
        .calendar-header {
            display: flex;
            width: 100%;
            border-bottom: 1px solid #ddd;
            background-color: #e9ecef;
        }
        .calendar-header-cell {
            flex: 1;
            text-align: center;
            padding: 10px 5px;
            font-weight: bold;
            font-size: 18px;
            border-right: 1px solid #ddd;
        }
        .calendar-header-cell:last-child {
            border-right: none;
        }
        .calendar-row {
            display: flex;
            width: 100%;
            border-bottom: 1px solid #ddd;
        }
        .calendar-row:last-child {
            border-bottom: none;
        }
        .calendar-cell {
            flex: 1;
            text-align: center;
            height: 80px;
            font-size: 16px;
            display: flex;
            flex-direction: column;
            justify-content: flex-start;
            align-items: center;
            border-right: 1px solid #ddd;
            padding: 5px;
            background-color: white;
        }
        .calendar-cell:last-child {
            border-right: none;
        }
        .calendar-cell-content {
            width: 100%;
            height: 100%;
            display: flex;
            flex-direction: column;
            justify-content: flex-start;
            align-items: center;
        }
        .calendar-cell-content.today {
            background-color: #e6f3ff;
            border-radius: 5px;
        }
        .calendar-day {
            font-weight: bold;
            margin-bottom: 2px;
        }
        .calendar-shift {
            padding: 2px 5px;
            border-radius: 3px;
            font-size: 14px;
            font-weight: bold;
            margin-bottom: 2px;
        }
        .calendar-holiday {
            font-size: 10px;
            color: red;
            margin-top: 2px;
            max-width: 100%;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        .space-before-button {
            margin-top: 20px;
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

    titleup_style = "font-size: 18px; font-weight: bold; text-align: center;"
    st.markdown(f"<div style='{titleup_style}'>{year}년</div>", unsafe_allow_html=True)

    title_style = "font-size: 30px; font-weight: bold; text-align: center;"
    st.markdown(f"<div style='{title_style}'>{month}월 교대근무 달력</div>", unsafe_allow_html=True)

    today = datetime.now(pytz.timezone('Asia/Seoul')).date()
    yesterday = today - timedelta(days=1)

    # '이전 월' 버튼
    if st.button("이전 월"):
        update_month(-1)

    month_days = generate_calendar(year, month)
    calendar_data = create_calendar_data(year, month, month_days, schedule_data, holidays, today, yesterday)
    display_calendar(calendar_data)

    # 공백 추가
    st.markdown("<div class='space-before-button'></div>", unsafe_allow_html=True)

    holiday_descriptions = create_holiday_descriptions(holidays, month)
    st.markdown(" / ".join(holiday_descriptions))

    # '다음 월' 버튼
    if st.button("다음 월"):
        update_month(1)

    sidebar_controls()

def update_month(delta):
    new_date = datetime(st.session_state.year, st.session_state.month, 1) + relativedelta(months=delta)
    st.session_state.year = new_date.year
    st.session_state.month = new_date.month
    st.rerun()

def create_calendar_data(year, month, month_days, schedule_data, holidays, today, yesterday):
    calendar_data = []
    for week in month_days:
        week_data = []
        for day in week:
            if day != 0:
                date_str = f"{year}-{month:02d}-{day:02d}"
                current_date = datetime(year, month, day).date()
                if date_str not in schedule_data:
                    schedule_data[date_str] = get_shift(current_date, st.session_state.get("team", "A"))
                
                shift = schedule_data[date_str]
                shift_background, shift_color = shift_colors.get(shift, ("white", "black"))
                
                if current_date.weekday() == 5 or current_date.weekday() == 6 or date_str in holidays:
                    day_color = "red"
                else:
                    day_color = "black"

                today_class = "today" if current_date == today else ""

                shift_text = shift if shift != '비' else '&nbsp;'
                
                # 공휴일 정보 추가
                holiday_text = ""
                if date_str in holidays:
                    holiday_text = f'<div class="calendar-holiday" title="{holidays[date_str][0]}">{holidays[date_str][0]}</div>'

                cell_content = f'''
                    <div class="calendar-cell-content {today_class}">
                        <span class="calendar-day" style="color: {day_color};">{day}</span>
                        <span class="calendar-shift" style="background-color: {shift_background}; color: {shift_color};">{shift_text}</span>
                        {holiday_text}
                    </div>
                '''
                week_data.append(cell_content)
            else:
                week_data.append('<div class="calendar-cell-content"></div>')
        calendar_data.append(week_data)
    return calendar_data

def display_calendar(calendar_data):
    days_header = ["일", "월", "화", "수", "목", "금", "토"]
    
    st.markdown('<div class="calendar-container">', unsafe_allow_html=True)
    
    # 요일 헤더 생성
    header_html = '<div class="calendar-header">'
    for day in days_header:
        color = "red" if day in ["일", "토"] else "black"
        header_html += f'<div class="calendar-header-cell" style="color: {color};">{day}</div>'
    header_html += '</div>'
    st.markdown(header_html, unsafe_allow_html=True)
    
    # 달력 데이터 생성
    for week in calendar_data:
        week_html = '<div class="calendar-row">'
        for cell in week:
            week_html += f'<div class="calendar-cell">{cell}</div>'
        week_html += '</div>'
        st.markdown(week_html, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

def sidebar_controls():
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
    if st.sidebar.button("스케줄 변경 활성화"):
        st.session_state.expander_open = not st.session_state.expander_open

    if st.session_state.expander_open:
        with st.expander("스케줄 변경", expanded=True):
            with st.form(key='schedule_change_form'):
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
                            st.success("스케줄이 저장되었습니다.")
                            # 캐시 키를 변경하여 새로운 데이터를 로드하도록 함
                            st.session_state.cache_key = datetime.now().strftime("%Y%m%d%H%M%S")
                        else:
                            st.error("스케줄 저장에 실패했습니다.")
                        st.rerun()
                    else:
                        st.error("암호가 일치하지 않습니다.")
    
    st.sidebar.title("달력 이동")
    months = {1: "1월", 2: "2월", 3: "3월", 4: "4월", 5: "5월", 6: "6월", 7: "7월", 8: "8월", 9: "9월", 10: "10월", 11: "11월", 12: "12월"}

    desired_months = []
    current_date = datetime(st.session_state.year, st.session_state.month, 1)
    for i in range(-5, 6):
        new_date = current_date + relativedelta(months=i)
        desired_months.append((new_date.year, new_date.month))

    selected_year_month = st.sidebar.selectbox(
        "월 선택", 
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
