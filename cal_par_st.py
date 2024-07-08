import streamlit as st
import calendar
from datetime import datetime
import json

# 파일 이름
STATE_FILE = "calendar_state.json"

# Initialize color mapping
color_mapping = {}

def save_state(pattern, highlight, year, month, memo_text, page):
    state = {
        "pattern": pattern,
        "highlight": highlight,
        "year": year,
        "month": month,
        "memo": memo_text,
        "colors": color_mapping,
        "page": page
    }
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

def load_state():
    try:
        with open(STATE_FILE, "r") as f:
            state = json.load(f)
        global color_mapping
        color_mapping = state.get("colors", {})
        return state["pattern"], state["highlight"], state["year"], state["month"], state.get("memo", ""), state.get("page", 1)
    except FileNotFoundError:
        return "AB", "A", datetime.now().year, datetime.now().month, "", 1

def generate_schedule(start_pattern, year, month):
    rotations = {
        'AB': [('A', 'B'), ('D', 'A'), ('C', 'D'), ('B', 'C')],
        'DA': [('D', 'A'), ('C', 'D'), ('B', 'C'), ('A', 'B')],
        'CD': [('C', 'D'), ('B', 'C'), ('A', 'B'), ('D', 'A')],
        'BC': [('B', 'C'), ('A', 'B'), ('D', 'A'), ('C', 'D')]
    }
    
    base_date = datetime(2000, 1, 1)
    target_date = datetime(year, month, 1)
    days_diff = (target_date - base_date).days

    rotation_index = (days_diff // 4) % len(rotations[start_pattern])
    schedule = {}
    
    cal = calendar.Calendar()
    month_days = cal.monthdayscalendar(year, month)

    for week in month_days:
        for i, day in enumerate(week):
            if day != 0:
                day_schedule = rotations[start_pattern][rotation_index % len(rotations[start_pattern])]
                schedule[day] = day_schedule
                rotation_index = (rotation_index + 1) % len(rotations[start_pattern])
    
    return schedule

def on_date_click(day, year, month):
    color_options = {
        "비": "white",
        "주": "yellow",
        "야": "gray",
        "올": "green"
    }
    
    choice = st.selectbox(f"{year}-{month}-{day} 근무 선택", list(color_options.keys()))
    color_mapping[f"{year}-{month}-{day}"] = color_options[choice]
    save_state(pattern, highlight, year, month, memo, current_page)
    st.experimental_rerun()

def update_calendar():
    start_pattern = pattern
    highlight_team = highlight
    year = int(selected_year)
    month = int(selected_month)
    schedule = generate_schedule(start_pattern, year, month)

    st.write(f"### {year}년 {month}월")
    st.write("####")

    day_names = ['월', '화', '수', '목', '금', '토', '일']
    cols = st.columns(7)
    for i, day_name in enumerate(day_names):
        cols[i].write(day_name)

    month_days = calendar.monthcalendar(year, month)
    for week in month_days:
        cols = st.columns(7)
        for i, day in enumerate(week):
            if day == 0:
                cols[i].write("")
            else:
                color_key = f"{year}-{month}-{day}"
                if color_key in color_mapping:
                    bg_color = color_mapping[color_key]
                else:
                    if schedule[day][0] == highlight_team:
                        bg_color = "yellow"
                    elif schedule[day][1] == highlight_team:
                        bg_color = "gray"
                    else:
                        bg_color = "white"

                label_text = f"{day} {'주' if bg_color == 'yellow' else '야' if bg_color == 'gray' else '올' if bg_color == 'green' else '비'}"
                cols[i].button(label_text, key=f"{year}-{month}-{day}", on_click=on_date_click, args=(day, year, month))

# Initialize current year and month
now = datetime.now()
current_year = now.year
current_month = now.month

# Load saved state
pattern, highlight, saved_year, saved_month, memo, saved_page = load_state()
if saved_page == 2:
    password_correct = st.text_input("비밀번호를 입력하세요:", type="password")
    if password_correct == "0301":
        show_admin = True
    else:
        show_admin = False
else:
    show_admin = False

# Create main window
st.title("교대근무 달력")

current_page = st.selectbox("페이지 선택", ["달력", "관리자"], index=saved_page - 1)
if current_page == "관리자" and not show_admin:
    st.stop()

pattern = st.selectbox("시작 패턴 선택:", ['AB', 'DA', 'CD', 'BC'], index=['AB', 'DA', 'CD', 'BC'].index(pattern))
highlight = st.selectbox("조 선택:", ['A', 'B', 'C', 'D'], index=['A', 'B', 'C', 'D'].index(highlight))
selected_year = st.selectbox("년도:", list(range(2000, 2101)), index=list(range(2000, 2101)).index(saved_year))
selected_month = st.selectbox("월:", list(range(1, 13)), index=list(range(1, 13)).index(saved_month - 1))

if current_page == "관리자":
    memo = st.text_area("메모:", value=memo)
    if st.button("업데이트"):
        save_state(pattern, highlight, int(selected_year), int(selected_month), memo, 2)
        st.experimental_rerun()

if current_page == "달력":
    update_calendar()
