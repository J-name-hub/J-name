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
    return {}, None

# GitHub에 스케줄 파일 저장
def save_schedule(schedule, sha):
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_FILE_PATH}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Content-Type": "application/json"
    }
    content = base64.b64encode(json.dumps(schedule).encode('utf-8')).decode('utf-8')
    data = {
        "message": "Update schedule",
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
    holidays, holiday_info = [], {}
    if response.status_code == 200:
        data = response.json()
        items = data.get('response', {}).get('body', {}).get('items', {}).get('item', [])
        if not isinstance(items, list):
            items = [items]
        for item in items:
            locdate = str(item['locdate'])
            date_str = datetime.strptime(locdate, "%Y%m%d").strftime("%Y-%m-%d")
            holidays.append(date_str)
            holiday_info[date_str] = item['dateName']
    return holidays, holiday_info

# 달력 생성 함수
def generate_calendar(year, month):
    cal = calendar.Calendar(firstweekday=6)  # 일요일이 첫번째로 오도록 설정
    return cal.monthdayscalendar(year, month)

# 근무 조 설정
shift_colors = {
    "주": "background-color: #ffeb3b",  # 밝은 노란색
    "야": "background-color: #bdbdbd",  # 밝은 회색
    "비": "background-color: #ffffff",  # 흰색
    "올": "background-color: #a5d6a7"   # 밝은 녹색
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
def set_page_titles(year, month):
    titleup_style = "font-size: 18px; font-weight: bold; text-align: center; margin-top: 10px;"
    st.markdown(f"<div style='{titleup_style}'>{year}년</div>", unsafe_allow_html=True)

    title_style = "font-size: 36px; font-weight: bold; text-align: center; margin-bottom: 20px;"
    st.markdown(f"<div style='{title_style}'>{month}월 교대근무 달력</div>", unsafe_allow_html=True)

# 세션 상태 초기화
def initialize_session():
    if "year" not in st.session_state or "month" not in st.session_state:
        today = datetime.now(pytz.timezone('Asia/Seoul'))
        st.session_state.year, st.session_state.month = today.year, today.month

    if "expander_open" not in st.session_state:
        st.session_state.expander_open = False

    if "team" not in st.session_state:
        st.session_state.team = load_team_settings()  # 파일에서 팀 설정 로드

# 달력 데이터 생성
def generate_calendar_data(year, month, schedule_data, holidays):
    month_days = generate_calendar(year, month)
    calendar_data = []
    today = datetime.now(pytz.timezone('Asia/Seoul')).date()
    yesterday = today - timedelta(days=1)
    
    for week in month_days:
        week_data = []
        for day in week:
            if day != 0:
                date_str = f"{year}-{month:02d}-{day:02d}"
                current_date = datetime(year, month, day).date()
                if date_str not in schedule_data:
                    schedule_data[date_str] = get_shift(current_date, st.session_state.get("team", "A"))
                background = shift_colors[schedule_data[date_str]]
                day_style = "font-weight: bold; text-align: center; padding: 5px; height: 60px; font-size: 20px; border: 1px solid #ddd;"

                if current_date == today:
                    background = "background-color: #90caf9"  # 밝은 파란색
                elif current_date == yesterday:
                    background = shift_colors[schedule_data[date_str]]

                if current_date.weekday() in [5, 6] or date_str in holidays:
                    day_style += " color: red;"
                else:
                    day_style += " color: black;"

                shift_text = f"<div>{day}<br><span>{schedule_data[date_str] if schedule_data[date_str] != '비' else '&nbsp;'}</span></div>"
                week_data.append(f"<div style='{background}; {day_style}'>{shift_text}</div>")
            else:
                week_data.append("<div style='height: 60px;'>&nbsp;</div>")  # 빈 셀 높이 맞춤
        calendar_data.append(week_data)
    
    return pd.DataFrame(calendar_data, columns=["일", "월", "화", "수", "목", "금", "토"])

# 달력 데이터 스타일 설정
def style_calendar_df(calendar_df):
    days_header = ["일", "월", "화", "수", "목", "금", "토"]
    days_header_style = [
        "background-color: #fff; text-align: center; font-weight: bold; color: red; font-size: 20px; border: 1px solid #ddd;",
        *["background-color: #fff; text-align: center; font-weight: bold; color: black; font-size: 20px; border: 1px solid #ddd;"] * 5,
        "background-color: #fff; text-align: center; font-weight: bold; color: red; font-size: 20px; border: 1px solid #ddd;"
    ]

    calendar_df.columns = [f"<div style='{style}'>{day}</div>" for day, style in zip(days_header, days_header_style)]

# 이어지는 공휴일 그룹화 함수
def group_holidays(holiday_info, month):
    holidays = [date for date in sorted(holiday_info.keys()) if datetime.strptime(date, "%Y-%m-%d").month == month]
    grouped_holidays, current_group = [], []

    for i, holiday in enumerate(holidays):
        if not current_group:
            current_group.append(holiday)
        else:
            last_holiday = datetime.strptime(current_group[-1], "%Y-%m-%d")
            current_holiday = datetime.strptime(holiday, "%Y-%m-%d")
            if (current_holiday - last_holiday).days == 1:
                current_group.append(holiday)
            else:
                grouped_holidays.append(current_group)
                current_group = [holiday]

    if current_group:
        grouped_holidays.append(current_group)

    return grouped_holidays

# 공휴일 설명 표시
def display_holiday_descriptions(holiday_info, month):
    grouped_holidays = group_holidays(holiday_info, month)
    holiday_descriptions = []

    for group in grouped_holidays:
        if len(group) > 1:
            start_date = datetime.strptime(group[0], "%Y-%m-%d").day
            end_date = datetime.strptime(group[-1], "%Y-%m-%d").day
            holiday_descriptions.append(f"{start_date}일 ~ {end_date}일: {holiday_info[group[0]]}")
        else:
            single_date = datetime.strptime(group[0], "%Y-%m-%d").day
            holiday_descriptions.append(f"{single_date}일: {holiday_info[group[0]]}")

    st.markdown(" / ".join(holiday_descriptions))

# 사이드바 설정
def setup_sidebar():
    # 근무 조 설정
    st.sidebar.title("근무 조 설정")
    with st.sidebar.form(key='team_settings_form'):
        team = st.selectbox("조 선택", ["A", "B", "C", "D"], index=["A", "B", "C", "D"].index(st.session_state.team))
        password_for_settings = st.text_input("암호 입력", type="password", key="settings_password")
        submit_button = st.form_submit_button("설정 저장")

        if submit_button:
            if password_for_settings == "0301":
                st.session_state["team"] = team
                save_team_settings(team)
                st.sidebar.success("조가 저장되었습니다.")
                st.experimental_rerun()
            else:
                st.sidebar.error("암호가 일치하지 않습니다.")

    # 일자 스케줄 변경
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
                        st.experimental_rerun()
                    else:
                        st.error("암호가 일치하지 않습니다.")

    # 달력 이동
    st.sidebar.title("달력 이동")
    months = {1: "1월", 2: "2월", 3: "3월", 4: "4월", 5: "5월", 6: "6월", 7: "7월", 8: "8월", 9: "9월", 10: "10월", 11: "11월", 12: "12월"}

    desired_months = [(datetime(year, month, 1) + relativedelta(months=i)).timetuple()[:2] for i in range(-5, 6)]
    selected_year_month = st.sidebar.selectbox(
        "", 
        options=desired_months,
        format_func=lambda x: f"{x[0]}년 {months[x[1]]}",
        index=5
    )

    selected_year, selected_month = selected_year_month
    if selected_year != year or selected_month != month:
        st.session_state.year = selected_year
        st.session_state.month = selected_month
        st.experimental_rerun()

# 메인 함수
def main():
    # 스케줄 데이터 초기 로드
    global schedule_data, sha
    schedule_data, sha = load_schedule()
    if not schedule_data:
        schedule_data, sha = {}, None

    initialize_session()
    year, month = st.session_state.year, st.session_state.month

    # 공휴일 로드
    holidays, holiday_info = load_holidays(year)

    # 페이지 제목 설정
    set_page_titles(year, month)

    # 이전 월 버튼
    if st.button("이전 월"):
        if month == 1:
            st.session_state.year, st.session_state.month = year - 1, 12
        else:
            st.session_state.month -= 1
        st.experimental_rerun()

    # 달력 데이터 생성 및 스타일 적용
    calendar_df = generate_calendar_data(year, month, schedule_data, holidays)
    style_calendar_df(calendar_df)
    
    # 달력 HTML 표시
    st.markdown(calendar_df.to_html(escape=False, index=False), unsafe_allow_html=True)

    # 다음 월 버튼
    if st.button("다음 월"):
        if month == 12:
            st.session_state.year, st.session_state.month = year + 1, 1
        else:
            st.session_state.month += 1
        st.experimental_rerun()

    # 공휴일 설명 출력
    display_holiday_descriptions(holiday_info, month)

    # 사이드바 설정
    setup_sidebar()

# 실행
if __name__ == "__main__":
    st.set_page_config(page_title="교대근무 달력", layout="wide")
    main()
