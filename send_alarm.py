import json
import requests
from datetime import datetime
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

def check_alarm_conditions(schedule, now_str, today_str):
    messages = []

    if now_str == schedule.get("weekday", {}).get("time"):
        messages.append(schedule["weekday"]["message"])

    if now_str == schedule.get("night", {}).get("time"):
        messages.append(schedule["night"]["message"])

    for custom in schedule.get("custom", []):
        if custom["date"] == today_str and custom["time"] == now_str:
            messages.append(custom["message"])

    return messages

def main():
    now = datetime.now()
    now_str = now.strftime("%H:%M")
    today_str = now.strftime("%Y-%m-%d")

    schedule = load_json("alarm_schedule.json")
    messages = check_alarm_conditions(schedule, now_str, today_str)

    for msg in messages:
        send_telegram_message(msg)

if __name__ == "__main__":
    main()
