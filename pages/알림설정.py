import streamlit as st
import json
import base64
import requests
from datetime import datetime

GITHUB_TOKEN = st.secrets["github"]["token"]
GITHUB_REPO = st.secrets["github"]["repo"]
ALARM_FILE_PATH = "alarm_schedule.json"
PASSWORD = st.secrets["security"]["password"]

# GitHub 파일 로드
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
        return {"custom": []}, None

# GitHub 파일 저장
def save_alarm_schedule(data, sha=None):
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{ALARM_FILE_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    message = "Update alarm schedule"
    encoded = base64.b64encode(json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")).decode()
    payload = {
        "message": message,
        "content": encoded,
        "sha": sha
    }
    response = requests.put(url, headers=headers, json=payload)
    return response.status_code == 200 or response.status_code == 201

# 암호 인증
if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    pw = st.text_input("암호 입력", type="password")
    if pw == PASSWORD:
        st.session_state.auth = True
        st.session_state["alarm_updated"] = True  # rerun 플래그 설정
    else:
        st.stop()

if st.session_state.get("alarm_updated"):
    st.session_state["alarm_updated"] = False
    st.experimental_rerun()

# 알림 데이터 불러오기
data, sha = load_alarm_schedule()
custom_alarms = data.get("custom", [])

# 기존 알림 편집 UI
st.title("📅 일정 알림 설정")
st.markdown("#### 기존 알림 목록")

for i, item in enumerate(custom_alarms):
    with st.expander(f"{item['date']} {item['time']}"):
        item['date'] = st.date_input(f"날짜 {i}", value=datetime.strptime(item['date'], "%Y-%m-%d").date(), key=f"date_{i}")
        item['time'] = st.time_input(f"시간 {i}", value=datetime.strptime(item['time'], "%H:%M").time(), key=f"time_{i}")
        item['message'] = st.text_area(f"메시지 {i}", value=item['message'], key=f"msg_{i}")
        if st.button(f"❌ 삭제 {i}"):
            custom_alarms.pop(i)
            st.experimental_rerun()

# 새 알림 추가
st.markdown("---")
st.subheader("🆕 새 알림 추가")

with st.form("new_alarm_form"):
    new_date = st.date_input("날짜", value=datetime.today())
    new_time = st.time_input("시간", value=datetime.strptime("09:00", "%H:%M").time())
    new_message = st.text_area("알림 메시지", "")
    submitted = st.form_submit_button("추가")
    if submitted:
        custom_alarms.append({
            "date": new_date.strftime("%Y-%m-%d"),
            "time": new_time.strftime("%H:%M"),
            "message": new_message
        })
        st.success("알림이 추가되었습니다.")
        st.experimental_rerun()

# 저장 버튼
if st.button("💾 전체 저장"):
    success = save_alarm_schedule({"custom": custom_alarms}, sha)
    if success:
        st.success("GitHub에 저장되었습니다.")
    else:
        st.error("저장에 실패했습니다.")
