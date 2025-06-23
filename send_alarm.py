import json
import requests
from datetime import datetime, timedelta
import os

# JSON 파일 로드
def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# 텔레그램 메시지 전송
def send_telegram_message(text):
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = {"chat_id": chat_id, "text": text}
    requests.post(url, data=data)

# 시간 근접 여부 확인 (±60초)
def is_time_near(target_time_str, now, seconds=60):
    try:
        target = datetime.strptime(target_time_str, "%H:%M").replace(
            year=now.year, month=now.month, day=now.day
        )
        delta = abs((now - target).total_seconds())
        return delta <= seconds
    except:
        return False

# 알람 조건 확인
def check_alarm_conditions(shift_data, alarm_schedule, now, today_str):
    messages = []

    # 1. custom 알림 (날짜 기반)
    for custom in alarm_schedule.get("custom", []):
        if custom.get("date") == today_str and is_time_near(custom["time"], now):
            messages.append(custom["message"])

    # 2. 근무조 기반 알림
    today_shift = shift_data.get(today_str)  # 예: "주", "야", "올", "비"

    if not today_shift or today_shift == "비":
        return messages  # 비근무일 또는 정보 없음

    # 주간 알림
    if today_shift in ("주", "올"):
        for item in alarm_schedule.get("weekday", []):
            if item.get("shift") == "주" and is_time_near(item["time"], now):
                messages.append(item["message"])

    # 야간 알림
    if today_shift in ("야", "올"):
        for item in alarm_schedule.get("night", []):
            if item.get("shift") == "야" and is_time_near(item["time"], now):
                messages.append(item["message"])

    return messages

# 메인 함수
def main():
    now = datetime.utcnow() + timedelta(hours=9)  # 한국 시간 기준
    today_str = now.strftime("%Y-%m-%d")

    alarm_schedule = load_json("alarm_schedule.json")
    shift_schedule = load_json("shift_schedule.json")

    messages = check_alarm_conditions(shift_schedule, alarm_schedule, now, today_str)

    for msg in messages:
        send_telegram_message(msg)

if __name__ == "__main__":
    main()
