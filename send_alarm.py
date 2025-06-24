import json
import requests
from datetime import datetime, timedelta
import os

# 팀 변경 이력 로드
def load_team_history(path="team_settings.json"):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        return data.get("team_history", [{"start_date": "2000-01-03", "team": "A"}])

# 조 변경 이력을 바탕으로 날짜별 팀 반환
def get_team_for_date(target_date, team_history):
    sorted_history = sorted(team_history, key=lambda x: x["start_date"])
    current_team = sorted_history[0]["team"]
    for record in sorted_history:
        if target_date >= datetime.strptime(record["start_date"], "%Y-%m-%d").date():
            current_team = record["team"]
        else:
            break
    return current_team

# 기본 근무조 계산 + 수동 변경조 반영
def get_shift_for_date(target_date, team_history, shift_schedule):
    date_str = target_date.strftime("%Y-%m-%d")
    if date_str in shift_schedule:
        return shift_schedule[date_str]

    team = get_team_for_date(target_date, team_history)
    base_date = datetime(2000, 1, 3).date()
    delta_days = (target_date - base_date).days
    shift_patterns = {
        "C": ["주", "야", "비", "비"],
        "B": ["비", "주", "야", "비"],
        "A": ["비", "비", "주", "야"],
        "D": ["야", "비", "비", "주"],
    }
    pattern = shift_patterns.get(team, ["주", "야", "비", "비"])
    return pattern[delta_days % len(pattern)]

# JSON 파일 로드
def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# 텔레그램 메시지 전송
def send_telegram_message(text):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        print("❌ 환경변수가 설정되지 않았습니다. 메시지 전송 취소")
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = {"chat_id": chat_id, "text": text}
    response = requests.post(url, data=data)

    if response.ok:
        print(f"✅ 메시지 전송 성공: {text}")
    else:
        print(f"❌ 메시지 전송 실패: {response.status_code} - {response.text}")

# 시간 근접 여부 확인 (±60초)
def is_time_near(target_time_str, now, seconds=60):
    try:
        target = datetime.strptime(target_time_str, "%H:%M").replace(
            year=now.year, month=now.month, day=now.day
        )
        delta = abs((now - target).total_seconds())
        return delta <= seconds
    except Exception as e:
        print(f"⛔ 시간 파싱 오류: {e}")
        return False

# 알람 조건 확인
def check_alarm_conditions(now, today_str, shift_schedule, team_history, alarm_schedule):
    messages = []

    for custom in alarm_schedule.get("custom", []):
        if custom.get("date") == today_str and is_time_near(custom["time"], now):
            messages.append(custom["message"])

    today_shift = get_shift_for_date(now.date(), team_history, shift_schedule)

    if today_shift in ("주", "올"):
        for item in alarm_schedule.get("weekday", []):
            if is_time_near(item["time"], now):
                messages.append(item["message"])

    if today_shift in ("야", "올"):
        for item in alarm_schedule.get("night", []):
            if is_time_near(item["time"], now):
                messages.append(item["message"])

    return messages

# 메인 함수
def main():
    now = datetime.utcnow() + timedelta(hours=9)  # KST
    today_str = now.strftime("%Y-%m-%d")

    alarm_schedule = load_json("alarm_schedule.json")
    shift_schedule = load_json("shift_schedule.json")
    team_history = load_team_history("team_settings.json")

    # ✅ 근무조 확인 로그
    today_shift = get_shift_for_date(now.date(), team_history, shift_schedule)
    print(f"📌 오늘 날짜: {today_str}")
    print(f"📌 오늘 근무조: {today_shift}")

    messages = check_alarm_conditions(now, today_str, shift_schedule, team_history, alarm_schedule)

    for msg in messages:
        send_telegram_message(msg)

    # ✅ 강제 테스트 메시지 전송 (원할 경우 주석 제거)
    # send_telegram_message("🔔 테스트 메시지입니다. (알림 테스트용)")

if __name__ == "__main__":
    main()
