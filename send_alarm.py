import json
import requests
from datetime import datetime, timedelta
import os

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def send_telegram_message(text):
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = {"chat_id": chat_id, "text": text}
    requests.post(url, data=data)

# ±1분 허용
def is_time_near(target_time_str, now, seconds=60):
    try:
        target = datetime.strptime(target_time_str, "%H:%M").replace(
            year=now.year, month=now.month, day=now.day
        )
        delta = abs((now - target).total_seconds())
        return delta <= seconds
    except:
        return False

def check_alarm_conditions(schedule, now, today_str):
    messages = []

    # 주간 알림
    for item in schedule.get("weekday", []):
        if is_time_near(item["time"], now):
            messages.append(item["message"])

    # 야간 알림
    for item in schedule.get("night", []):
        if is_time_near(item["time"], now):
            messages.append(item["message"])

    # 특정일 알림
    for custom in schedule.get("custom", []):
        if custom["date"] == today_str and is_time_near(custom["time"], now):
            messages.append(custom["message"])

    return messages

def main():
    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")

    schedule = load_json("alarm_schedule.json")
    messages = check_alarm_conditions(schedule, now, today_str)

    for msg in messages:
        send_telegram_message(msg)

if __name__ == "__main__":
    main()
