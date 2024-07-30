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

        # Check for valid response structure
        if "response" in data and "body" in data["response"] and "items" in data["response"]["body"]:
            items = data['response']['body']['items'].get('item', [])
        else:
            items = []

        if isinstance(items, dict):  # In case of a single item
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
    "D": shifts[-3:] + shifts[:-3]
}

# Streamlit 앱
def main():
    st.title("스케줄 관리자")

    schedule, sha = load_schedule()
    if schedule is None:
        st.error("스케줄 데이터를 로드할 수 없습니다.")
        return

    today = datetime.today()
    current_year = today.year
    current_month = today.month

    default_team = load_team_settings_from_github()

    # 사이드바에서 팀 선택
    team = st.sidebar.selectbox("팀 선택", ["A", "B", "C", "D"], index=["A", "B", "C", "D"].index(default_team))
    
    # 달력 연도와 월 선택
    selected_year = st.sidebar.number_input("연도", min_value=2000, max_value=2100, value=current_year, step=1)
    selected_month = st.sidebar.number_input("월", min_value=1, max_value=12, value=current_month, step=1)

    # 공휴일 데이터 로드
    holidays = load_holidays(selected_year)
    if not holidays:
        st.warning("공휴일 데이터가 없습니다. 공휴일 데이터를 다시 로드해주세요.")

    # 달력 생성
    month_days = generate_calendar(selected_year, selected_month)

    # 팀 스케줄 가져오기
    team_schedule = schedule.get(f"{selected_year}-{selected_month:02d}", {}).get(team, {})
    for week in month_days:
        for i, day in enumerate(week):
            if day != 0:
                team_schedule.setdefault(day, shift_patterns[team][(day - 1) % len(shift_patterns[team])])
    
    # 공휴일 설명 생성
    holiday_descriptions = create_holiday_descriptions(holidays, selected_month)
    
    # 달력 표시
    st.header(f"{selected_year}년 {selected_month}월 {team}팀 달력")
    col_labels = ["일", "월", "화", "수", "목", "금", "토"]
    cols = st.columns(7)
    for i, label in enumerate(col_labels):
        cols[i].markdown(f"<b>{label}</b>", unsafe_allow_html=True)

    for week in month_days:
        cols = st.columns(7)
        for i, day in enumerate(week):
            if day == 0:
                cols[i].markdown(" ")
            else:
                shift = team_schedule.get(day, "비")
                bg_color, text_color = shift_colors[shift]
                if datetime(selected_year, selected_month, day).strftime("%Y-%m-%d") in holidays:
                    bg_color = "red"
                    shift = ", ".join(holidays[datetime(selected_year, selected_month, day).strftime("%Y-%m-%d")])
                cols[i].markdown(
                    f'<div style="background-color: {bg_color}; color: {text_color}; text-align: center; padding: 5px;">{day}<br>{shift}</div>',
                    unsafe_allow_html=True
                )
    
    # 휴일 설명
    if holiday_descriptions:
        st.markdown("#### 공휴일 설명")
        for description in holiday_descriptions:
            st.write(description)
    
    # 팀 설정 저장
    if st.sidebar.button("팀 설정 저장"):
        if save_team_settings_to_github(team):
            st.success("팀 설정이 저장되었습니다.")
        else:
            st.error("팀 설정 저장에 실패했습니다.")

    # 스케줄 저장
    if st.sidebar.button("스케줄 저장"):
        if save_schedule(schedule, sha):
            st.success("스케줄이 저장되었습니다.")
        else:
            st.error("스케줄 저장에 실패했습니다.")

if __name__ == "__main__":
    main()
