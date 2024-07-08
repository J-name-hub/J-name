import streamlit as st
import calendar
from datetime import datetime
import json

# 파일 이름
STATE_FILE = "calendar_state.json"

# Initialize color mapping
color_mapping = {}

def save_state(pattern, highlight, year, month, page):
    state = {
        "pattern": pattern,
        "highlight": highlight,
        "year": year,
        "month": month,
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
        return state["pattern"], state["highlight"], state["year"], state["month"], state.get("page", 1)
    except FileNotFoundError:
        return "AB", "A", datetime.now().year, datetime.now().month, 1

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

def change_color(year, month, day, choice):
    if choice == "비":
        color_mapping[f"{year}-{month}-{day}"] = "white"
    elif choice == "주":
        color_mapping[f"{year}-{month}-{day}"] = "yellow"
    elif choice == "야":
        color_mapping[f"{year}-{month}-{day}"] = "gray"
    elif choice == "올":
        color_mapping[f"{year}-{month}-{day}"] = "green"
    save_state(st.session_state.pattern, st.session_state.highlight, year, month, st.session_state.page)
    st.experimental_rerun()

def update_calendar():
    start_pattern = st.session_state.pattern
    highlight_team = st.session_state.highlight
    year = st.session_state.year
    month = st.session_state.month
    schedule = generate_schedule(start_pattern, year, month)

    st.write(f"## {year}년 {month}월")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("◀ 이전 월", key="prev_month"):
            decrement_month()
    with col3:
        if st.button("다음 월 ▶", key="next_month"):
            increment_month()
    
    col1, col2, col3, col4, col5, col6, col7 = st.columns(7)
    cols = [col1, col2, col3, col4, col5, col6, col7]

    day_names = ['월', '화', '수', '목', '금', '토', '일']
    for i, day_name in enumerate(day_names):
        cols[i].write(f"**{day_name}**")

    month_days = calendar.monthcalendar(year, month)
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
                    if schedule[day][0] == highlight_team:
                        bg_color = "yellow"
                    elif schedule[day][1] == highlight_team:
                        bg_color = "gray"
                    else:
                        bg_color = "white"

                label_text = ""
                if bg_color == "yellow":
                    label_text = f"{day} 주"
                elif bg_color == "gray":
                    label_text = f"{day} 야"
                elif bg_color == "green":
                    label_text = f"{day} 올"
                else:
                    label_text = f"{day} 비"

                week_cols[i].markdown(f"<div style='background-color:{bg_color}; padding: 10px;'>{label_text}</div>", unsafe_allow_html=True)
                if st.session_state.page == 2:
                    if week_cols[i].button(f"Edit {day}", key=f"edit_{year}_{month}_{day}"):
                        change_color(year, month, day, st.selectbox("근무 선택", ["비", "주", "야", "올"], key=f"select_{year}_{month}_{day}"))

def increment_month():
    if st.session_state.month == 12:
        st.session_state.month = 1
        st.session_state.year += 1
    else:
        st.session_state.month += 1
    save_state(st.session_state.pattern, st.session_state.highlight, st.session_state.year, st.session_state.month, st.session_state.page)
    update_calendar()

def decrement_month():
    if st.session_state.month == 1:
        st.session_state.month = 12
        st.session_state.year -= 1
    else:
        st.session_state.month -= 1
    save_state(st.session_state.pattern, st.session_state.highlight, st.session_state.year, st.session_state.month, st.session_state.page)
    update_calendar()

def show_page(page):
    st.session_state.page = page
    save_state(st.session_state.pattern, st.session_state.highlight, st.session_state.year, st.session_state.month, st.session_state.page)
    if page == 1:
        update_calendar()
    elif page == 2:
        st.selectbox("시작 패턴 선택:", ['AB', 'DA', 'CD', 'BC'], key='pattern_admin')
        st.selectbox("조 선택:", ['A', 'B', 'C', 'D'], key='highlight_admin')
        st.selectbox("년도:", list(range(2000, 2101)), key='year_admin')
        st.selectbox("월:", list(range(1, 13)), key='month_admin')
        if st.button("업데이트", key="update_button"):
            st.session_state.pattern = st.session_state.pattern_admin
            st.session_state.highlight = st.session_state.highlight_admin
            st.session_state.year = st.session_state.year_admin
            st.session_state.month = st.session_state.month_admin
            save_state(st.session_state.pattern, st.session_state.highlight, st.session_state.year, st.session_state.month, st.session_state.page)
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
        if st.button("관리자 페이지", key="admin_page"):
            show_page(2)
with col2:
    if st.session_state.page == 2:
        if st.button("달력 페이지", key="calendar_page"):
            show_page(1)

# Show the current page
show_page(st.session_state.page)
