import streamlit as st
import json
import base64
import requests
from datetime import datetime

# GitHub 연동 정보
GITHUB_TOKEN = st.secrets["github"]["token"]
GITHUB_REPO = st.secrets["github"]["repo"]
ALARM_FILE_PATH = "alarm_schedule.json"
PASSWORD = st.secrets["security"]["password"]

# GitHub에서 알림 데이터 불러오기
def load_alarm_schedule():
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{ALARM_FILE_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        content = response.json()
        sha = content["sha"]
        decoded = base64.b64decode(content["content"]).decode("utf-8")
        return json.loads(decoded), sha
    else:
        return {"weekday": [], "night": [], "custom": []}, None

# GitHub에 저장
def save_alarm_schedule(data, sha=None):
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{ALARM_FILE_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    encoded = base64.b64encode(json.dumps(data, ensure_ascii=False, indent=2).encode()).decode()
    payload = {
        "message": "Update alarm schedule",
        "content": encoded,
        "sha": sha
    }
    response = requests.put(url, headers=headers, json=payload)
    return response.status_code == 200 or response.status_code == 201

# 암호 인증
if "auth_alarm" not in st.session_state:
    st.session_state.auth_alarm = False

if not st.session_state.auth_alarm:
    pw = st.text_input("🔒 암호를 입력하세요", type="password")
    if pw == PASSWORD:
        st.session_state.auth_alarm = True
        st.experimental_rerun()
    else:
        st.stop()

# 알림 데이터 불러오기
data, sha = load_alarm_schedule()
weekday_alarms = data.get("weekday", [])
night_alarms = data.get("night", [])
custom_alarms = data.get("custom", [])

st.title("🔔 근무 스케줄별 알림 설정")

# 🔶 주간 알림
st.subheader("🟡 주간 알림")
for i, alarm in enumerate(weekday_alarms):
    col1, col2, col3 = st.columns([2, 5, 1])
    with col1:
        alarm["time"] = st.time_input(f"주간시간{i}", value=datetime.strptime(alarm["time"], "%H:%M").time(), key=f"wd_time_{i}")
    with col2:
        alarm["message"] = st.text_input(f"주간메시지{i}", value=alarm["message"], key=f"wd_msg_{i}")
    with col3:
        if st.button("삭제", key=f"wd_del_{i}"):
            weekday_alarms.pop(i)
            st.session_state.updated = True
            st.experimental_rerun()

if st.button("➕ 주간 알림 추가"):
    weekday_alarms.append({"time": "08:00", "message": ""})
    st.experimental_rerun()

# 🔶 야간 알림
st.subheader("🌙 야간 알림")
for i, alarm in enumerate(night_alarms):
    col1, col2, col3 = st.columns([2, 5, 1])
    with col1:
        alarm["time"] = st.time_input(f"야간시간{i}", value=datetime.strptime(alarm["time"], "%H:%M").time(), key=f"nt_time_{i}")
    with col2:
        alarm["message"] = st.text_input(f"야간메시지{i}", value=alarm["message"], key=f"nt_msg_{i}")
    with col3:
        if st.button("삭제", key=f"nt_del_{i}"):
            night_alarms.pop(i)
            st.session_state.updated = True
            st.experimental_rerun()

if st.button("➕ 야간 알림 추가"):
    night_alarms.append({"time": "20:00", "message": ""})
    st.experimental_rerun()

# 🔶 일자별 알림
st.subheader("📅 특정일 알림")
for i, alarm in enumerate(custom_alarms):
    col1, col2, col3, col4 = st.columns([2, 2, 4, 1])
    with col1:
        alarm["date"] = st.date_input(f"날짜{i}", value=datetime.strptime(alarm["date"], "%Y-%m-%d").date(), key=f"cs_date_{i}")
    with col2:
        alarm["time"] = st.time_input(f"시간{i}", value=datetime.strptime(alarm["time"], "%H:%M").time(), key=f"cs_time_{i}")
    with col3:
        alarm["message"] = st.text_input(f"메시지{i}", value=alarm["message"], key=f"cs_msg_{i}")
    with col4:
        if st.button("삭제", key=f"cs_del_{i}"):
            custom_alarms.pop(i)
            st.session_state.updated = True
            st.experimental_rerun()

if st.button("➕ 특정일 알림 추가"):
    custom_alarms.append({"date": datetime.today().strftime("%Y-%m-%d"), "time": "09:00", "message": ""})
    st.experimental_rerun()

# 🔄 저장
if st.button("💾 전체 저장"):
    to_save = {
        "weekday": [{"time": a["time"].strftime("%H:%M"), "message": a["message"]} for a in weekday_alarms],
        "night": [{"time": a["time"].strftime("%H:%M"), "message": a["message"]} for a in night_alarms],
        "custom": [{"date": a["date"].strftime("%Y-%m-%d"), "time": a["time"].strftime("%H:%M"), "message": a["message"]} for a in custom_alarms]
    }
    success = save_alarm_schedule(to_save, sha)
    if success:
        st.success("✔ GitHub에 저장 완료!")
    else:
        st.error("❌ 저장 실패. GitHub 설정 확인 필요.")
