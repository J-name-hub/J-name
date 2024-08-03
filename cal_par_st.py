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
                    holiday_descriptions.append(f"{start_day}일 ~ {end_day}일: {', '.join(current_holiday)}")
                    holiday_descriptions.extend(temp_descriptions)
                else:
                    holiday_descriptions.append(f"{start_day}일 ~ {end_day}일: {', '.join(current_holiday)}")
            i = j
        else:
            i += 1
    return holiday_descriptions

# 근무일 정보 표시
def display_workdays_info(selected_year, selected_month, selected_team):
    # 팀 선택에 따른 근무일 정보 표시
    if selected_team in st.session_state['schedule']:
        selected_team_schedule = st.session_state['schedule'][selected_team]
    else:
        st.warning(f"선택한 팀 {selected_team}의 스케줄 정보가 없습니다.")
        return

    # 스케줄 필터링
    workdays = {date: info for date, info in selected_team_schedule.items()
                if date.startswith(f"{selected_year}-{selected_month:02d}")}

    if not workdays:
        st.info(f"{selected_year}년 {selected_month}월에는 근무일이 없습니다.")
        return

    st.write(f"### {selected_year}년 {selected_month}월 근무일 정보 (팀: {selected_team})")
    workdays_df = pd.DataFrame(list(workdays.items()), columns=["날짜", "정보"])
    st.dataframe(workdays_df)

# 유틸리티 함수: 다음 달 반환
def next_month(year, month):
    if month == 12:
        return year + 1, 1
    else:
        return year, month + 1

# 유틸리티 함수: 이전 달 반환
def previous_month(year, month):
    if month == 1:
        return year - 1, 12
    else:
        return year, month - 1

# 메인 실행 함수
def main():
    st.title("근무 일정 관리 시스템")

    # 현재 날짜와 시간 표시
    now = datetime.now(pytz.timezone('Asia/Seoul'))
    current_date = now.strftime("%Y-%m-%d")
    current_time = now.strftime("%H:%M:%S")
    st.write(f"### 현재 날짜: {current_date}, 현재 시간: {current_time}")

    # GitHub에서 팀 설정 로드
    if 'selected_team' not in st.session_state:
        st.session_state['selected_team'] = load_team_settings_from_github()

    # 스케줄 및 공휴일 데이터 로드
    cache_key = f"{st.session_state['selected_team']}"
    schedule, sha = load_schedule(cache_key)
    holidays = load_holidays(now.year)

    # 스케줄 전역 상태에 저장
    st.session_state['schedule'] = schedule

    # 사용자 입력 받기
    selected_year = st.selectbox("연도 선택", [now.year, now.year + 1], index=0)
    selected_month = st.selectbox("월 선택", list(range(1, 13)), index=now.month - 1)
    st.session_state['selected_team'] = st.selectbox("팀 선택", list(schedule.keys()), index=0)

    # 선택한 팀 표시
    selected_team = st.session_state['selected_team']
    st.write(f"선택한 팀: {selected_team}")

    # 공휴일 정보 표시
    st.write("### 공휴일 정보")
    holiday_descriptions = create_holiday_descriptions(holidays, selected_month)
    if holiday_descriptions:
        st.write(f"{selected_year}년 {selected_month}월의 공휴일:")
        st.write("\n".join(holiday_descriptions))
    else:
        st.write("이번 달에는 공휴일이 없습니다.")

    # 근무일 정보 표시
    display_workdays_info(selected_year, selected_month, selected_team)

    # 다음 및 이전 달 버튼
    if st.button("이전 달"):
        prev_year, prev_month = previous_month(selected_year, selected_month)
        st.session_state['selected_year'] = prev_year
        st.session_state['selected_month'] = prev_month

    if st.button("다음 달"):
        next_year, next_month = next_month(selected_year, selected_month)
        st.session_state['selected_year'] = next_year
        st.session_state['selected_month'] = next_month

    # 스케줄 업데이트 및 저장
    if st.button("스케줄 업데이트"):
        if save_schedule(schedule, sha):
            st.success("스케줄 업데이트 완료")
        else:
            st.error("스케줄 업데이트 실패")

if __name__ == "__main__":
    main()
