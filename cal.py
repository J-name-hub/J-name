import tkinter as tk
from tkinter import ttk, messagebox
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

def on_date_click(event, day, year, month, day_label):
    def change_color(choice):
        if choice == "휴가":
            day_label.config(bg="white")
            color_mapping[f"{year}-{month}-{day}"] = "white"
        elif choice == "주간":
            day_label.config(bg="yellow")
            color_mapping[f"{year}-{month}-{day}"] = "yellow"
        elif choice == "야간":
            day_label.config(bg="gray")
            color_mapping[f"{year}-{month}-{day}"] = "gray"
        elif choice == "주간+야간":
            day_label.config(bg="green")
            color_mapping[f"{year}-{month}-{day}"] = "green"
        save_state(pattern_var.get(), highlight_var.get(), year, month, memo_textbox.get("1.0", "end-1c"))
        update_calendar()
        popup.destroy()

    popup = tk.Toplevel(root)
    popup.title("색상 선택")

    tk.Label(popup, text="변경할 색상을 선택하세요:").pack(pady=10)

    tk.Button(popup, text="휴가", command=lambda: change_color("휴가")).pack(fill='x')
    tk.Button(popup, text="주간", command=lambda: change_color("주간")).pack(fill='x')
    tk.Button(popup, text="야간", command=lambda: change_color("야간")).pack(fill='x')
    tk.Button(popup, text="주간+야간", command=lambda: change_color("주간+야간")).pack(fill='x')

    popup.transient(root)
    popup.grab_set()
    root.wait_window(popup)

def update_calendar(event=None):
    start_pattern = pattern_var.get()
    highlight_team = highlight_var.get()
    year = int(year_combobox.get())
    month = int(month_combobox.get())
    memo_text = memo_textbox.get("1.0", "end-1c")
    schedule = generate_schedule(start_pattern, year, month)

    for widget in calendar_frame.winfo_children():
        widget.destroy()
    
    # Display the year and month
    year_month_label = tk.Label(calendar_frame, text=f"{year}년 {month}월", font=("Helvetica", 16), pady=10)
    year_month_label.grid(row=0, column=0, columnspan=8)

    # Display the day names
    day_names = ['월', '화', '수', '목', '금', '토', '일', '총 근무 시간']
    for i, day_name in enumerate(day_names):
        color = "red" if day_name in ['토', '일'] else "black"
        tk.Label(calendar_frame, text=day_name, fg=color).grid(row=1, column=i)

    # Display the days and schedules
    month_days = calendar.monthcalendar(year, month)
    for week_num, week in enumerate(month_days):
        total_hours = 0
        for day_num, day in enumerate(week):
            if day == 0:
                tk.Label(calendar_frame, text="").grid(row=week_num + 2, column=day_num)
            else:
                day_schedule = schedule[day]
                is_weekend = day_num in [5, 6]  # Saturday and Sunday
                day_text = f"{day}\n주간: {day_schedule[0]}\n야간: {day_schedule[1]}"
                
                # Load saved color if exists
                color_key = f"{year}-{month}-{day}"
                if color_key in color_mapping:
                    bg_color = color_mapping[color_key]
                else:
                    if day_schedule[0] == highlight_team:
                        bg_color = "yellow"
                    elif day_schedule[1] == highlight_team:
                        bg_color = "gray"
                    else:
                        bg_color = "white"
                
                fg_color = "red" if is_weekend else "black"
                day_label = tk.Label(calendar_frame, text=day_text, relief="solid", width=15, height=4, fg=fg_color, bg=bg_color)
                day_label.grid(row=week_num + 2, column=day_num)
                day_label.bind("<Button-1>", lambda event, d=day, dl=day_label: on_date_click(event, d, year, month, dl))
                
                # Calculate total hours
                if bg_color == "yellow":
                    total_hours += 8
                elif bg_color == "gray":
                    total_hours += 11
                elif bg_color == "green":
                    total_hours += 19

        # Display total hours
        total_hours_fg_color = "red" if total_hours > 52 else "black"
        total_hours_font = ("Helvetica", 12, "bold") if total_hours > 52 else ("Helvetica", 12)
        tk.Label(calendar_frame, text=f"{total_hours} 시간", fg=total_hours_fg_color, font=total_hours_font).grid(row=week_num + 2, column=7)

    # Save current state
    save_state(start_pattern, highlight_team, year, month, memo_text)

def increment_month():
    month = int(month_combobox.get())
    if month == 12:
        month_combobox.set(1)
        year_combobox.set(int(year_combobox.get()) + 1)
    else:
        month_combobox.set(month + 1)
    update_calendar()

def decrement_month():
    month = int(month_combobox.get())
    if month == 1:
        month_combobox.set(12)
        year_combobox.set(int(year_combobox.get()) - 1)
    else:
        month_combobox.set(month - 1)
    update_calendar()

# Initialize current year and month
now = datetime.now()
current_year = now.year
current_month = now.month

# Create main window
root = tk.Tk()
root.title("교대근무 달력")

# Bind Enter key to update_calendar function
root.bind('<Return>', update_calendar)

# Create frame for controls
frame = ttk.Frame(root)
frame.pack(pady=10)

# Pattern selection
pattern_label = ttk.Label(frame, text="2000년 1월 1일 시작 패턴을 선택하세요 (AB, DA, CD, BC):")
pattern_label.grid(row=0, column=0, padx=5, pady=5)
pattern_var = tk.StringVar(value='AB')
pattern_combobox = ttk.Combobox(frame, textvariable=pattern_var, values=['AB', 'DA', 'CD', 'BC'], state='readonly')
pattern_combobox.grid(row=0, column=1, padx=5, pady=5)

# Highlight team selection
highlight_label = ttk.Label(frame, text="강조할 조를 선택하세요 (A, B, C, D):")
highlight_label.grid(row=1, column=0, padx=5, pady=5)
highlight_var = tk.StringVar(value='A')
highlight_combobox = ttk.Combobox(frame, textvariable=highlight_var, values=['A', 'B', 'C', 'D'], state='readonly')
highlight_combobox.grid(row=1, column=1, padx=5, pady=5)

# Year input
year_label = ttk.Label(frame, text="년도:")
year_label.grid(row=2, column=0, padx=5, pady=5)
year_var = tk.StringVar(value=current_year)
year_combobox = ttk.Combobox(frame, textvariable=year_var, values=list(range(2000, 2101)), state='readonly')
year_combobox.grid(row=2, column=1, padx=5, pady=5)

# Month input
month_label = ttk.Label(frame, text="월:")
month_label.grid(row=3, column=0, padx=5, pady=5)
month_var = tk.StringVar(value=current_month)
month_combobox = ttk.Combobox(frame, textvariable=month_var, values=list(range(1, 13)), state='readonly')
month_combobox.grid(row=3, column=1, padx=5, pady=5)

# Up and Down buttons for month
up_button = tk.Button(frame, text="▲", command=increment_month)
up_button.grid(row=3, column=2, padx=5, pady=5)
down_button = tk.Button(frame, text="▼", command=decrement_month)
down_button.grid(row=3, column=3, padx=5, pady=5)

# Update button
update_button = tk.Button(frame, text="업데이트", bg='green', fg='white', command=update_calendar)
update_button.grid(row=4, columnspan=4, pady=10)

# Memo functionality
memo_label = ttk.Label(frame, text="메모:")
memo_label.grid(row=5, column=0, padx=5, pady=5)
memo_textbox = tk.Text(frame, width=30, height=4)
memo_textbox.grid(row=5, column=1, columnspan=3, padx=5, pady=5)

# Calendar display
calendar_frame = ttk.Frame(root)
calendar_frame.pack(pady=10)

# Initialize schedule based on saved state or current date
pattern, highlight, saved_year, saved_month, saved_memo = load_state()
pattern_var.set(pattern)
highlight_var.set(highlight)
year_var.set(saved_year)
month_var.set(saved_month)
memo_textbox.insert("1.0", saved_memo)
update_calendar()

# Run the main loop
root.mainloop()
