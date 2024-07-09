import streamlit as st
import calendar
from datetime import datetime
import json

# 파일 이름
STATE_FILE = "calendar_state.json"

# Initialize color mapping
color_mapping = {}

def save_state(pattern, highlight, year, month, colors, page):
    state = {
        "pattern": pattern,
        "highlight": highlight,
        "year": year,
        "month": month,
        "colors": colors,
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
        return state["pattern"], state["highlight"], state["year"], state["month"], state.get("page", 1)
    except FileNotFoundError:
        return "A", "A", datetime.now().year, datetime.now().month, 1

def generate_schedule(start_pattern, year, month):
    rotations = {
        'A': ['주', '야', '비', '비'],
        'B': ['야', '비', '비', '주'],
        'C': ['비', '비', '주', '야'],
        'D': ['비', '주', '야', '비']
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
                day_schedule = rotations[start_pattern][rotation_index % 4]
                schedule[day] = day_schedule
                rotation_index = (rotation_index + 1) % 4
    
    return schedule

def change_color(year, month, day, choice):
    if choice == "비":
        color_mapping[f"{year}-{month}-{day}"] = "white"
    elif choice == "주":
        color_mapping[f"{year}-{month}-{day}"] = "yellow"
    elif choice == "야":
        color_mapping[f"{year}-{month}-{day}"] = "gray"
    elif choice == "올":
        color_mapping[f"{year}-{month}-{day}"] = "green"
    save_state(st.session_state.pattern, st.session_state.highlight, year, month, color_mapping, st.session_state.page)
    st.experimental_rerun()

def update_calendar():
    year = st.session_state.year
    month = st.session_state.month
    pattern = st.session_state.pattern
    schedule = generate_schedule(pattern, year, month)

    st.write(f"## {year}년 {month}월")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("◀ 이전 월"):
            decrement_month()
    with col3:
        if st.button("다음 월 ▶"):
            increment_month()
    
    col1, col2, col3, col4, col5, col6, col7 = st.columns(7)
    cols = [col1, col2, col3, col4, col5, col6, col7]

    day_names = ['월', '화', '수', '목', '금', '토', '일']
    for i, day_name in enumerate(day_names):
        cols[i].write(f"**{day_name}**")

    month_days = calendar.monthdayscalendar(year, month)
    for week in month_days:
        week_cols = st.columns(7)
        for i, day in enumerate(week):
            if day == 0:
                week_cols[i].write("")
            else:
                color_key = f"{year}-{month}-{day}"
                if color_key in color_mapping:
                    bg_color = color_mapping[color_key]
                else:
                    if day in schedule:
                        duty = schedule[day]
                        if duty == '주':
                            bg_color = "yellow"
                        elif duty == '야':
                            bg_color = "gray"
                        else:
                            bg_color = "white"
                    else:
                        bg_color = "white"

                week_cols[i].markdown(f"<div style='background-color:{bg_color}; padding: 10px;'>{day}</div>", unsafe_allow_html=True)
                if st.session_state.page == 2:
                    if week_cols[i].button(f"Edit {day}", key=f"edit_{year}_{month}_{day}"):
                        change_color(year, month, day, st.selectbox("근무 선택", ["비", "주", "야", "올"], key=f"select_{year}_{month}_{day}"))

def increment_month():
    if st.session_state.month == 12:
        st.session_state.month = 1
        st.session_state.year += 1
    else:
        st.session_state.month += 1
    save_state(st.session_state.pattern, st.session_state.highlight, st.session_state.year, st.session_state.month, color_mapping, st.session_state.page)
    update_calendar()

def decrement_month():
    if st.session_state.month == 1:
        st.session_state.month = 12
        st.session_state.year -= 1
    else:
        st.session_state.month -= 1
    save_state(st.session_state.pattern, st.session_state.highlight, st.session_state.year, st.session_state.month, color_mapping, st.session_state.page)
    update_calendar()

def show_page(page):
    st.session_state.page = page
    save_state(st.session_state.pattern, st.session_state.highlight, st.session_state.year, st.session_state.month, color_mapping, st.session_state.page)
    if page == 1:
        update_calendar()
    elif page == 2:
        st.selectbox("조 선택:", ['A', 'B', 'C', 'D'], key='pattern')
        if st.button("업데이트"):
            update_calendar()

# Load state
pattern, highlight, saved_year, saved_month, saved_page = load_state()

# Initialize session state
if 'pattern' not in st.session_state:
    st.session_state.pattern = pattern
if 'highlight' not in st.session_state:
    st.session_state.highlight = highlight
if 'year' not in st.session_state:
    st.session_state.year = saved_year
if 'month' not in st.session_state:
    st.session_state.month = saved_month
if 'page' not in st.session_state:
    st.session_state.page = saved_page

# Page navigation
col1, col2 = st.columns([1, 1])
with col1:
    if st.session_state.page == 1:
        if st.button("관리자 페이지"):
            show_page(2)
with col2:
    if st.session_state.page == 2:
        if st.button("달력 페이지"):
            show_page(1)

# Show the current page
show_page(st.session_state.page)
