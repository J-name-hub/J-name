import streamlit as st
import requests
import json
import base64
from datetime import datetime, timedelta
import calendar
import pytz
from dateutil.relativedelta import relativedelta

# ✅ 페이지 설정
st.set_page_config(
    page_title="교대근무 달력",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ----------------------------------------
# 🔐 Secrets 및 설정
# ----------------------------------------
GITHUB_TOKEN = st.secrets["github"]["token"]
GITHUB_REPO = st.secrets["github"]["repo"]
GITHUB_FILE_PATH = st.secrets["github"]["file_path"]
GITHUB_TEAM_SETTINGS_PATH = "team_settings.json"
SCHEDULE_CHANGE_PASSWORD = st.secrets["security"]["password"]
HOLIDAY_API_KEY = st.secrets["api_keys"]["holiday_api_key"]

# ----------------------------------------
# 🎨 CSS (모바일 최적화 포함)
# ----------------------------------------
st.markdown("""
    <style>
    body { font-family: 'Roboto', sans-serif; }
    .calendar-container { max-width: 900px; margin: auto; }
    .calendar-header { background: #343a40; color: white; padding: 5px; border-radius: 8px; text-align: center; }
    .calendar-day { font-weight: bold; }
    .calendar-shift { font-size: 16px; font-weight: bold; }
    .holiday { background-color: #FFDDDD; border-radius: 5px; }
    @media (max-width: 768px) {
        .calendar-container { width: 100%; padding: 5px; }
        .calendar-header { font-size: 20px; }
        .calendar-day { font-size: 14px; }
        .calendar-shift { font-size: 14px; }
        .stButton > button { font-size: 14px; padding: 6px 10px; }
    }
    .fab-today {
        position: fixed;
        bottom: 20px;
        right: 20px;
        background-color: #007bff;
        color: white;
        border-radius: 50%;
        width: 50px;
        height: 50px;
        display: flex;
        justify-content: center;
        align-items: center;
        font-size: 20px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.3);
        cursor: pointer;
    }
    </style>
""", unsafe_allow_html=True)

# ----------------------------------------
# 📦 데이터 처리 함수들
# ----------------------------------------

def github_api_request(url, method='GET', headers=None, data=None):
    if headers is None:
        headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    try:
        if method == 'GET':
            response = requests.get(url, headers=headers)
        elif method == 'PUT':
            response = requests.put(url, headers=headers, data=json.dumps(data))
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        st.error(f"GitHub API 오류: {e}")
        return None

def load_schedule():
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_FILE_PATH}"
    content = github_api_request(url)
    if content:
        file_content = base64.b64decode(content['content']).decode('utf-8')
        return json.loads(file_content), content['sha']
    return {}, None

def save_schedule(schedule, sha):
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_FILE_PATH}"
    encoded_content = base64.b64encode(json.dumps(schedule).encode()).decode('utf-8')
    data = {"message": "Update schedule", "content": encoded_content, "sha": sha}
    return github_api_request(url, method='PUT', data=data)

def load_team_history():
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_TEAM_SETTINGS_PATH}"
    content = github_api_request(url)
    if content:
        file_content = base64.b64decode(content['content']).decode('utf-8')
        return json.loads(file_content), content['sha']
    return {"team_history": []}, None

def save_team_history(team_history, sha):
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_TEAM_SETTINGS_PATH}"
    encoded_content = base64.b64encode(json.dumps({"team_history": team_history}).encode()).decode('utf-8')
    data = {"message": "Update team history", "content": encoded_content, "sha": sha}
    return github_api_request(url, method='PUT', data=data)

def load_holidays(year):
    api_url = f"http://apis.data.go.kr/B090041/openapi/service/SpcdeInfoService/getRestDeInfo?ServiceKey={HOLIDAY_API_KEY}&solYear={year}&numOfRows=100&_type=json"
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        data = response.json()
        items = data.get('response', {}).get('body', {}).get('items', {}).get('item', [])
        holidays = {datetime.strptime(str(item['locdate']), "%Y%m%d").strftime("%Y-%m-%d"): item['dateName'] for item in items}
        return holidays
    except Exception as e:
        st.error(f"공휴일 API 오류: {e}")
        return {}

# ----------------------------------------
# 📅 달력 생성 함수
# ----------------------------------------

def generate_calendar(year, month, schedule_data, holidays):
    cal = calendar.Calendar(firstweekday=6)
    today = datetime.now(pytz.timezone('Asia/Seoul')).date()
    month_days = cal.monthdayscalendar(year, month)

    html = '<div class="calendar-container">'
    html += f'<div class="calendar-header">{year}년 {month}월</div>'

    weekdays = ['일', '월', '화', '수', '목', '금', '토']
    html += '<div class="calendar-weekdays">' + ''.join(f'<div style="display:inline-block;width:13%;text-align:center;font-weight:bold;">{day}</div>' for day in weekdays) + '</div>'

    for week in month_days:
        html += '<div class="calendar-row" style="display:flex;">'
        for day in week:
            if day == 0:
                html += '<div style="flex:1; height:50px;"></div>'
            else:
                date_str = f"{year}-{month:02d}-{day:02d}"
                shift = schedule_data.get(date_str, '비')
                holiday_class = 'holiday' if date_str in holidays else ''
                today_class = 'today' if datetime(year, month, day).date() == today else ''
                html += f'<div style="flex:1; height:50px; border:1px solid #ddd; text-align:center;" class="{holiday_class} {today_class}">' \
                        f'<div class="calendar-day">{day}</div>' \
                        f'<div class="calendar-shift">{shift}</div></div>'
        html += '</div>'
    html += '</div>'

    return html

# ----------------------------------------
# 📋 사이드바 (팀 설정 및 스케줄 변경)
# ----------------------------------------

def sidebar_controls(schedule_data, sha, team_history, team_sha):
    st.sidebar.title("⚙️ 설정 및 관리")

    # 팀 히스토리 관리
    with st.sidebar.expander("👥 팀 히스토리 관리", expanded=False):
        for entry in team_history:
            st.write(f"{entry['start_date']} ➡️ {entry['team']}조")
        with st.form(key='team_form'):
            start_date = st.date_input("적용 시작일", datetime.today())
            team = st.selectbox("근무조", ["A", "B", "C", "D"])
            password = st.text_input("암호 입력", type="password")
            submit_team = st.form_submit_button("팀 변경 저장")
            if submit_team:
                if password == SCHEDULE_CHANGE_PASSWORD:
                    team_history.append({"start_date": start_date.strftime("%Y-%m-%d"), "team": team})
                    result = save_team_history(team_history, team_sha)
                    if result:
                        st.success("팀 히스토리가 저장되었습니다.")
                        st.experimental_rerun()
                    else:
                        st.error("저장 실패.")
                else:
                    st.error("암호가 일치하지 않습니다.")

    # 스케줄 변경
    with st.sidebar.expander("📅 스케줄 변경", expanded=False):
        with st.form(key='schedule_form'):
            change_date = st.date_input("변경할 날짜", datetime.today())
            new_shift = st.selectbox("새 근무조", ["주", "야", "비", "올"])
            password = st.text_input("암호 입력", type="password")
            submit_schedule = st.form_submit_button("스케줄 저장")

            if submit_schedule:
                if password == SCHEDULE_CHANGE_PASSWORD:
                    schedule_data[change_date.strftime("%Y-%m-%d")] = new_shift
                    result = save_schedule(schedule_data, sha)
                    if result:
                        st.success("스케줄이 저장되었습니다.")
                        st.experimental_rerun()
                    else:
                        st.error("저장 실패.")
                else:
                    st.error("암호가 일치하지 않습니다.")

# ----------------------------------------
# 🔥 메인 앱
# ----------------------------------------

def main():
    if "year" not in st.session_state or "month" not in st.session_state:
        today = datetime.now(pytz.timezone('Asia/Seoul'))
        st.session_state.year, st.session_state.month = today.year, today.month

    year, month = st.session_state.year, st.session_state.month

    schedule_data, sha = load_schedule()
    team_data, team_sha = load_team_history()
    team_history = team_data.get("team_history", [])
    holidays = load_holidays(year)

    st.markdown(generate_calendar(year, month, schedule_data, holidays), unsafe_allow_html=True)
    sidebar_controls(schedule_data, sha, team_history, team_sha)

    # 📆 달 이동 버튼
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("◀ 이전 월"):
            new_date = datetime(year, month, 1) + relativedelta(months=-1)
            st.session_state.year, st.session_state.month = new_date.year, new_date.month
            st.rerun()
    with col3:
        if st.button("다음 월 ▶"):
            new_date = datetime(year, month, 1) + relativedelta(months=1)
            st.session_state.year, st.session_state.month = new_date.year, new_date.month
            st.rerun()

    # 📆 Today 버튼 플로팅
    st.markdown("<div class='fab-today' onclick='window.location.reload();'>📆</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
