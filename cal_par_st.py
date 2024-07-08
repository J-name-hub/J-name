import streamlit as st
import calendar
from datetime import datetime
import json

# 파일 이름
STATE_FILE = "calendar_state.json"

# Initialize color mapping
if 'color_mapping' not in st.session_state:
    st.session_state.color_mapping = {}

def save_state(pattern, highlight, year, month, memo_text, page):
    state = {
        "pattern": pattern,
        "highlight": highlight,
        "year": year,
        "month": month,
        "memo": memo_text,
        "colors": st.session_state.color_mapping,
        "page": page
    }
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

def load_state():
    try:
        with open(STATE_FILE, "r") as f:
            state = json.load(f)
        st.session_state.color_mapping = state.get("colors", {})
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
    choice = st.radio(f"Change color for {day}/{month}/{year}", ["비", "주", "야", "올"])
    if choice:
        if choice == "비":
            st.session_state.color_mapping[f"{year}-{month}-{day}"] = "white"
        elif choice == "주":
            st.session_state.color_mapping[f"{year}-{month}-{day}"] = "yellow"
        elif choice == "야":
            st.session_state.color_mapping[f"{year}-{month}-{day}"] = "gray"
        elif choice == "올":
            st.session_state.color_mapping[f"{year}-{month}-{day}"] = "green"
        save_state(st.session_state.pattern, st.session_state.highlight, year, month, st.session_state.memo, st.session_state.page)
        st.experimental_rerun()

def update_calendar():
    year = st.session_state.year
    month = st.session_state.month
    schedule = generate_schedule(st.session_state.pattern, year, month)
    
    st.write(f"### {year}년 {month}월")
    
    day_names = ['월', '화', '수', '목', '금', '토', '일']
    st.write(" | ".join(day_names))
    
    month_days = calendar.monthcalendar(year, month)
    for week in month_days:
        week_display = []
        for day in week:
            if day == 0:
                week_display.append(" ")
            else:
                color_key = f"{year}-{month}-{day}"
                if color_key in st.session_state.color_mapping:
                    bg_color = st.session_state.color_mapping[color_key]
                else:
                    if schedule[day][0] == st.session_state.highlight:
                        bg_color = "yellow"
                    elif schedule[day][1] == st.session_state.highlight:
                        bg_color = "gray"
                    else:
                        bg_color = "white"

                label_text = f"{day}"
                if bg_color == "yellow":
                    label_text += " 주"
                elif bg_color == "gray":
                    label_text += " 야"
                elif bg_color == "green":
                    label_text += " 올"
                else:
                    label_text += " 비"
                
                week_display.append(f"<div style='background-color:{bg_color};'>{label_text}</div>")
        st.write(" | ".join(week_display))

def show_page(page):
    st.session_state.page = page
    if page == 1:
        st.write("### 달력")
        update_calendar()
    elif page == 2:
        st.write("### 관리자 설정")
        st.selectbox("시작 패턴 선택:", ['AB', 'DA', 'CD', 'BC'], key='pattern')
        st.selectbox("조 선택:", ['A', 'B', 'C', 'D'], key='highlight')
        st.selectbox("년도:", list(range(2000, 2101)), key='year')
        st.selectbox("월:", list(range(1, 13)), key='month')
        st.text_area("메모:", key='memo')
        st.button("업데이트", on_click=update_calendar)

# Initialize current year and month
now = datetime.now()
if 'year' not in st.session_state:
    st.session_state.year = now.year
if 'month' not in st.session_state:
    st.session_state.month = now.month

# Load initial state
if 'loaded' not in st.session_state:
    pattern, highlight, saved_year, saved_month, saved_memo, saved_page = load_state()
    st.session_state.pattern = pattern
    st.session_state.highlight = highlight
    st.session_state.year = saved_year
    st.session_state.month = saved_month
    st.session_state.memo = saved_memo
    st.session_state.page = saved_page
    st.session_state.loaded = True

st.sidebar.title("교대근무 달력")
st.sidebar.button("달력 보기", on_click=lambda: show_page(1))
st.sidebar.button("관리자", on_click=lambda: show_page(2))

show_page(st.session_state.page)
