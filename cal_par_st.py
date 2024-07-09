import streamlit as st
import pandas as pd
import calendar
from datetime import datetime, timedelta
import json
import os

# JSON 파일 경로 설정
FILE_PATH = "shift_schedule.json"

# JSON 파일 로드 함수
def load_schedule():
    if os.path.exists(FILE_PATH):
        with open(FILE_PATH, "r") as file:
            return json.load(file)
    else:
        return {}

# JSON 파일 저장 함수
def save_schedule(schedule):
    with open(FILE_PATH, "w") as file:
        json.dump(schedule, file)

# 초기 스케줄 데이터 로드
schedule_data = load_schedule()

# 페이지 설정
st.set_page_config(page_title="교대근무 달력", layout="wide")

# 월 이동 버튼 설정
def get_current_year_month():
    today = datetime.today()
    return today.year, today.month

def get_next_month(year, month):
    if month == 12:
        return year + 1, 1
    else:
        return year, month + 1

def get_previous_month(year, month):
    if month == 1:
        return year - 1, 12
    else:
        return year, month - 1

if "year" not in st.session_state or "month" not in st.session_state:
    st.session_state.year, st.session_state.month = get_current_year_month()

year = st.session_state.year
month = st.session_state.month

# 달력 생성
def generate_calendar(year, month):
    cal = calendar.Calendar()
    month_days = cal.itermonthdays4(year, month)
    return month_days

# 조 색상 설정
shift_colors = {
    "주": "background-color: yellow",
    "야": "background-color: gray",
    "비": "background-color: white",
    "올": "background-color: green"
}

# 교대 근무 조 설정
shifts = ["주", "야", "비", "비"]
shift_patterns = {
    "A": shifts,
    "B": shifts[-1:] + shifts[:-1],
    "C": shifts[-2:] + shifts[:-2],
    "D": shifts[-3:] + shifts[:-3],
}

def get_shift(date, team):
    base_date = datetime(2000, 1, 1)
    delta_days = (date - base_date).days
    pattern = shift_patterns[team]
    return pattern[delta_days % len(pattern)]

# 1페이지: 달력 보기
st.title(f"{year}년 {month}월")
col1, col2, col3 = st.columns([1, 6, 1])

with col1:
    if st.button("이전 달"):
        st.session_state.year, st.session_state.month = get_previous_month(year, month)
        st.experimental_rerun()

with col3:
    if st.button("다음 달"):
        st.session_state.year, st.session_state.month = get_next_month(year, month)
        st.experimental_rerun()

month_days = generate_calendar(year, month)

st.markdown("###")
calendar_df = pd.DataFrame(columns=["월", "화", "수", "목", "금", "토", "일"])

week = []
for day in month_days:
    if day[1] == month:
        date_str = f"{day[0]}-{day[1]:02d}-{day[2]:02d}"
        date = datetime(day[0], day[1], day[2])
        if date_str not in schedule_data:
            schedule_data[date_str] = get_shift(date, st.session_state.get("team", "A"))
        background = shift_colors[schedule_data[date_str]]
        week.append(f"<div style='{background}; padding:10px'>{day[2]}</div>")
    else:
        week.append("")
    
    if day[3] == 6:  # End of the week
        calendar_df.loc[len(calendar_df)] = week
        week = []

if week:
    calendar_df.loc[len(calendar_df)] = week + [""] * (7 - len(week))

st.markdown(
    calendar_df.to_html(escape=False, index=False), 
    unsafe_allow_html=True
)

# 2페이지: 스케줄 설정
st.sidebar.title("스케줄 설정")
team = st.sidebar.selectbox("조 선택", ["A", "B", "C", "D"])

if st.sidebar.button("설정 저장"):
    st.session_state["team"] = team
    st.sidebar.success("조가 저장되었습니다.")
    st.experimental_rerun()

# 일자 클릭 시 스케줄 변경 버튼
if st.button("일자 스케줄 변경"):
    with st.expander("스케줄 변경"):
        change_date = st.date_input("변경할 날짜", datetime(year, month, 1))
        new_shift = st.selectbox("새 스케줄", ["주", "야", "비", "올"])

        if st.button("스케줄 변경 저장"):
            change_date_str = change_date.strftime("%Y-%m-%d")
            schedule_data[change_date_str] = new_shift
            save_schedule(schedule_data)
            st.success("스케줄이 변경되었습니다.")
            st.experimental_rerun()
