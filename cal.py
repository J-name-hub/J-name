import streamlit as st
import calendar
from datetime import datetime
import json

# 파일 이름
STATE_FILE = "calendar_state.json"

# Initialize color mapping
color_mapping = {}

def save_state(pattern, highlight, year, month, memo_text):
    state = {
        "pattern": pattern,
        "highlight": highlight,
        "year": year,
        "month": month,
        "memo": memo_text,
        "colors": color_mapping
    }
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

def load_state():
    try:
        with open(STATE_FILE, "r") as f:
            state = json.load(f)
        global color_mapping
        color_mapping = state.get("colors", {})
        return state["pattern"], state["highlight"], state["year"], state["month"], state.get("memo", "")
    except FileNotFoundError:
        return "AB", "A", datetime.now().year, datetime.now().month, ""

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

def main():
    st.title("교대근무 달력")
    
    pattern, highlight, saved_year, saved_month, saved_memo = load_state()
    
    pattern_var = st.selectbox("2000년 1월 1일 시작 패턴을 선택하세요 (AB, DA, CD, BC):", ['AB', 'DA', 'CD', 'BC'], index=['AB', 'DA', 'CD', 'BC'].index(pattern))
    highlight_var = st.selectbox("강조할 조를 선택하세요 (A, B, C, D):", ['A', 'B', 'C', 'D'], index=['A', 'B', 'C', 'D'].index(highlight))
    year_var = st.selectbox("년도:", list(range(2000, 2101)), index=list(range(2000, 2101)).index(saved_year))
    month_var = st.selectbox("월:", list(range(1, 13)), index=list(range(1, 13)).index(saved_month - 1))
    memo_text = st.text_area("메모:", value=saved_memo)
    
    if st.button("업데이트"):
        save_state(pattern_var, highlight_var, year_var, month_var + 1, memo_text)
    
    schedule = generate_schedule(pattern_var, year_var, month_var + 1)
    
    st.write(f"### {year_var}년 {month_var + 1}월")
    day_names = ['월', '화', '수', '목', '금', '토', '일']
    col = st.columns(8)
    for i, day_name in enumerate(day_names):
        col[i].write(day_name)
    col[7].write("총 근무 시간")
    
    month_days = calendar.monthcalendar(year_var, month_var + 1)
    for week in month_days:
        col = st.columns(8)
        total_hours = 0
        for day_num, day in enumerate(week):
            if day == 0:
                col[day_num].write("")
            else:
                day_schedule = schedule[day]
                day_text = f"{day}\n주간: {day_schedule[0]}\n야간: {day_schedule[1]}"
                color_key = f"{year_var}-{month_var + 1}-{day}"
                
                if color_key in color_mapping:
                    bg_color = color_mapping[color_key]
                else:
                    if day_schedule[0] == highlight_var:
                        bg_color = "yellow"
                    elif day_schedule[1] == highlight_var:
                        bg_color = "gray"
                    else:
                        bg_color = "white"
                
                if bg_color == "yellow":
                    total_hours += 8
                elif bg_color == "gray":
                    total_hours += 11
                elif bg_color == "green":
                    total_hours += 19
                
                col[day_num].markdown(f'<div style="background-color:{bg_color};padding:10px;border-radius:5px">{day_text}</div>', unsafe_allow_html=True)
                
                new_color = col[day_num].selectbox(f"색상 변경 ({day})", ["기본", "휴가", "주간", "야간", "주간+야간"], key=f"color_{day}")
                if new_color == "휴가":
                    color_mapping[color_key] = "white"
                elif new_color == "주간":
                    color_mapping[color_key] = "yellow"
                elif new_color == "야간":
                    color_mapping[color_key] = "gray"
                elif new_color == "주간+야간":
                    color_mapping[color_key] = "green"
        
        total_hours_fg_color = "red" if total_hours > 52 else "black"
        total_hours_font = "bold" if total_hours > 52 else "normal"
        col[7].markdown(f'<div style="color:{total_hours_fg_color};font-weight:{total_hours_font};padding:10px;border-radius:5px">{total_hours} 시간</div>', unsafe_allow_html=True)
    
    save_state(pattern_var, highlight_var, year_var, month_var + 1, memo_text)

if __name__ == "__main__":
    main()
