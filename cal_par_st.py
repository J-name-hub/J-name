import streamlit as st
import calendar
from datetime import datetime
import json

# 파일 이름
STATE_FILE = "calendar_state.json"

# Initialize color mapping
color_mapping = {}

# Page state
if "page" not in st.session_state:
    st.session_state.page = 1

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

def update_calendar():
    start_pattern = st.session_state.pattern
    highlight_team = st.session_state.highlight
    year = st.session_state.year
    month = st.session_state.month
    memo_text = st.session_state.memo
    schedule = generate_schedule(start_pattern, year, month)

    calendar_html = f"<h2>{year}년 {month}월</h2>"
    calendar_html += "<table><tr>" + "".join(f"<th>{day}</th>" for day in ['월', '화', '수', '목', '금', '토', '일']) + "</tr>"

    for week in calendar.monthcalendar(year, month):
        week_html = "<tr>"
        for day in week:
            if day == 0:
                week_html += "<td></td>"
            else:
                color_key = f"{year}-{month}-{day}"
                bg_color = color_mapping.get(color_key, "white")
                label_text = f"{day} 비"
                if bg_color == "yellow":
                    label_text = f"{day} 주"
                elif bg_color == "gray":
                    label_text = f"{day} 야"
                elif bg_color == "green":
                    label_text = f"{day} 올"

                week_html += f'<td style="background-color:{bg_color};width:30px;height:30px;text-align:center;">{label_text}</td>'
        week_html += "</tr>"
        calendar_html += week_html

    calendar_html += "</table>"
    st.markdown(calendar_html, unsafe_allow_html=True)
    save_state(start_pattern, highlight_team, year, month, memo_text, st.session_state.page)

def change_color(day, choice):
    year = st.session_state.year
    month = st.session_state.month
    color_key = f"{year}-{month}-{day}"
    if choice == "비":
        color_mapping[color_key] = "white"
    elif choice == "주":
        color_mapping[color_key] = "yellow"
    elif choice == "야":
        color_mapping[color_key] = "gray"
    elif choice == "올":
        color_mapping[color_key] = "green"
    update_calendar()

def increment_month():
    if st.session_state.month == 12:
        st.session_state.month = 1
        st.session_state.year += 1
    else:
        st.session_state.month += 1
    update_calendar()

def decrement_month():
    if st.session_state.month == 1:
        st.session_state.month = 12
        st.session_state.year -= 1
    else:
        st.session_state.month -= 1
    update_calendar()

def show_page(page):
    st.session_state.page = page
    if page == 1:
        st.experimental_rerun()
    elif page == 2:
        password = st.text_input("비밀번호를 입력하세요:", type="password")
        if password == "0301":
            st.session_state.page = 2
            st.experimental_rerun()
        elif password:
            st.error("비밀번호가 틀렸습니다.")

# Load state
pattern, highlight, saved_year, saved_month, saved_memo, saved_page = load_state()
st.session_state.pattern = pattern
st.session_state.highlight = highlight
st.session_state.year = saved_year
st.session_state.month = saved_month
st.session_state.memo = saved_memo
st.session_state.page = saved_page

# Page layout
if st.session_state.page == 1:
    st.button("관리자", on_click=lambda: show_page(2))
    update_calendar()
elif st.session_state.page == 2:
    st.selectbox("시작 패턴 선택:", ['AB', 'DA', 'CD', 'BC'], key='pattern')
    st.selectbox("조 선택:", ['A', 'B', 'C', 'D'], key='highlight')
    st.selectbox("년도:", list(range(2000, 2101)), key='year')
    st.selectbox("월:", list(range(1, 13)), key='month')
    st.button("업데이트", on_click=update_calendar)
    st.text_area("메모:", key='memo')
    st.button("달력", on_click=lambda: show_page(1))
    update_calendar()
