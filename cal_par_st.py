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
        items = data['response']['body']['items'].get('item', [])
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
        return None

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
            font-size: 16px;
            padding: 8px 16px;
        }
        </style>
        """, unsafe_allow_html=True)

    # 사용자 입력 받기
    st.sidebar.title("교대근무 달력 설정")
    selected_year = st.sidebar.selectbox("연도 선택", [2023, 2024, 2025, 2026], index=0)
    selected_month = st.sidebar.selectbox("월 선택", list(range(1, 13)), index=datetime.now().month - 1)
    selected_team = st.sidebar.selectbox("팀 선택", ["A", "B", "C", "D"], index=0)
    
    # 데이터 로드
    schedule, sha = load_schedule(f"{selected_year}_{selected_month}")
    team_settings = load_team_settings_from_github()

    # 달력 생성
    cal_data = generate_calendar(selected_year, selected_month)
    st.title(f"{selected_year}년 {selected_month}월 달력")

    # 공휴일 로드 및 오류 처리
    holidays = load_holidays(selected_year)
    if holidays is None:
        st.warning("공휴일 데이터를 로드할 수 없습니다. 인터넷 연결을 확인하거나 나중에 다시 시도하세요.")
    elif not holidays:
        st.warning("해당 연도의 공휴일 데이터가 존재하지 않습니다.")
    else:
        holiday_descriptions = create_holiday_descriptions(holidays, selected_month)
        if holiday_descriptions:
            st.markdown(f"### 공휴일 목록 ({selected_year}년 {selected_month}월)")
            for description in holiday_descriptions:
                st.markdown(f"- {description}")

    # 스케줄 데이터에 팀 이름 설정
    if not schedule:
        schedule[selected_team] = {}

    # 달력 표시
    st.write("## 달력")
    cal_html = "<table style='border-collapse: collapse; width: 100%;'>"
    cal_html += "<thead><tr>"
    for day in ["일", "월", "화", "수", "목", "금", "토"]:
        cal_html += f"<th style='border: 1px solid black; padding: 5px;'>{day}</th>"
    cal_html += "</tr></thead>"
    cal_html += "<tbody>"
    for week in cal_data:
        cal_html += "<tr>"
        for day in week:
            if day == 0:
                cal_html += "<td style='border: 1px solid black; padding: 10px;'></td>"
            else:
                date_str = f"{selected_year}-{selected_month:02d}-{day:02d}"
                current_shift = get_shift(datetime(selected_year, selected_month, day).date(), selected_team)
                background_color, text_color = shift_colors[current_shift]
                
                # 공휴일 표시
                holiday_info = ""
                if holidays and date_str in holidays:
                    holiday_names = holidays[date_str]
                    holiday_info = "<br>".join(holiday_names)
                    if holiday_names:
                        background_color = "lightcoral"
                        text_color = "white"
                
                # 기존 스케줄 데이터 로드
                if date_str in schedule[selected_team]:
                    selected_shift = schedule[selected_team][date_str]
                    if selected_shift:
                        current_shift = selected_shift
                        background_color, text_color = shift_colors[current_shift]
                
                cal_html += f"<td style='border: 1px solid black; padding: 10px; background-color: {background_color}; color: {text_color}; text-align: center;'>"
                cal_html += f"<div>{day}</div>"
                cal_html += f"<div>{current_shift}</div>"
                if holiday_info:
                    cal_html += f"<div style='font-size: 10px; margin-top: 5px;'>{holiday_info}</div>"
                
                # 셀렉트 박스 추가
                new_shift = st.selectbox(
                    label=f"shift_{day}",
                    options=list(shift_colors.keys()),
                    index=list(shift_colors.keys()).index(current_shift),
                    key=f"shift_{selected_year}_{selected_month}_{day}",
                    label_visibility="collapsed"
                )
                if new_shift != current_shift:
                    schedule[selected_team][date_str] = new_shift
                
                cal_html += "</td>"
        cal_html += "</tr>"
    cal_html += "</tbody>"
    cal_html += "</table>"

    # HTML로 달력 표시
    st.markdown(cal_html, unsafe_allow_html=True)

    # 스케줄 저장
    if st.button("스케줄 저장"):
        if save_schedule(schedule, sha):
            st.success("스케줄이 성공적으로 저장되었습니다.")
        else:
            st.error("스케줄 저장에 실패했습니다.")

if __name__ == "__main__":
    main()
