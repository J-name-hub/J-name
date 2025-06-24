import streamlit as st
import json
import base64
from datetime import datetime
from zoneinfo import ZoneInfo
from github import Github

# Streamlit 설정
GITHUB_TOKEN = st.secrets["github"]["token"]
GITHUB_REPO = st.secrets["github"]["repo"]
CHANGE_PASSWORD = st.secrets["security"]["password"]

STATIONS = {
    "SRT": [
        "수서", "동탄", "평택지제", "경주", "곡성", "공주", "광주송정", "구례구", "김천(구미)",
        "나주", "남원", "대전", "동대구", "마산", "목포", "밀양", "부산", "서대구",
        "순천", "여수EXPO", "여천", "오송", "울산(통도사)", "익산", "전주",
        "정읍", "진영", "진주", "창원", "창원중앙", "천안아산", "포항"
    ],
    "KTX": [
        "서울", "용산", "대전", "서대전", "천안아산", "영등포", "광명", "수원", "오송",
        "김천구미", "동대구", "경주", "포항", "밀양", "구포", "부산", "울산(통도사)",
        "마산", "창원중앙", "경산", "논산", "익산", "정읍", "광주송정", "목포",
        "전주", "순천", "여수EXPO", "여천", "청량리", "강릉", "행신", "정동진"
    ]
}

# 좌석 유형
seat_type_options = st.secrets["seat_type_options"]

st.set_page_config(page_title="기차표 가상 예매", layout="wide")
st.title("기차표 가상 예매")

# 🔧 사이드바 입력
# 현재 날짜 가져오기
today = datetime.now(ZoneInfo("Asia/Seoul"))

# 형식: "5월 31일 토요일"
formatted_date = today.strftime("%-m월 %-d일 %A")
formatted_date = f"{today.month}월 {today.day}일 {today.strftime('%A')}"

# 요일 한글로 변환
weekday_kor = {
    'Monday': '월요일',
    'Tuesday': '화요일',
    'Wednesday': '수요일',
    'Thursday': '목요일',
    'Friday': '금요일',
    'Saturday': '토요일',
    'Sunday': '일요일'
}
formatted_date = f"{today.month}월 {today.day}일 {weekday_kor[today.strftime('%A')]}"

# 사이드바에 표시
with st.sidebar:
    st.markdown(
        f"""
        <div style='text-align: center; font-size: 25px; font-weight: bold; color: #4da6ff; padding: 10px 0;'>
            오늘은<br>{formatted_date}<br>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.markdown(
        f"""
        <div style='text-align: center; font-size: 80px; font-weight: bold; color: #4da6ff; padding: 10px 0;'>
            🚅
        </div>
        """,
        unsafe_allow_html=True
    )
    st.markdown(
        f"""
        <div style='text-align: center; font-size: 25px; font-weight: bold; color: #4da6ff; padding: 10px 0;'>
            <br>지금 만나러 갑니다
        </div>
        """,
        unsafe_allow_html=True
    )
    
# 열차 종류 선택
rail_type = st.selectbox("열차 종류 선택", ["KTX", "SRT"])

# 출발역 / 도착역 → 같은 줄
col1, col2 = st.columns(2)
with col1:
    departure = st.selectbox("출발역 선택", STATIONS[rail_type])
with col2:
    arrival = st.selectbox("도착역 선택", STATIONS[rail_type])

# 날짜 / 출발 시각 → 같은 줄
col3, col4 = st.columns(2)
with col3:
    date = st.date_input("날짜").strftime("%Y%m%d")
with col4:
    time = f"{st.selectbox('출발 시각', [f'{i:02d}' for i in range(24)])}0000"

# 성인 / 어린이 / 경로 수 → 같은 줄
col5, col6, col7 = st.columns(3)
with col5:
    adult = st.number_input("성인 수", min_value=0, max_value=9, value=1)
with col6:
    child = st.number_input("어린이 수", min_value=0, max_value=9)
with col7:
    senior = st.number_input("경로 수", min_value=0, max_value=9)

# 열차 인덱스 / 좌석 유형 → 같은 줄
col8, col9 = st.columns(2)
with col8:
    selected_train_index = st.number_input("선택할 열차", min_value=1, max_value=15)
with col9:
    seat_type_selected = st.selectbox("좌석 유형", list(seat_type_options[rail_type].keys()))

# 카드결제 옵션
pay = st.checkbox("카드결제")

info = {
    "departure": departure,
    "arrival": arrival,
    "date": date,
    "time": time,
    "adult": adult,
    "child": child,
    "senior": senior,
    "disability1to3": 0,
    "disability4to6": 0
}

choice = {
    "trains": [int(selected_train_index) - 1]
}

seat_type_value = seat_type_options[rail_type][seat_type_selected]

A_options = {
    "type": seat_type_value,
    "pay": pay
}

# 비밀번호 입력
password_input = st.text_input("🔐 암호 입력", type="password")

# 버튼을 화면 너비 전체로 키우기
col_btn = st.columns(1)[0]
with col_btn:
    if st.button("💾 GitHub에 저장", use_container_width=True):
        if password_input != CHANGE_PASSWORD:
            st.error("❌ 암호가 일치하지 않습니다.")
        else:
            config = {
                "rail_type": rail_type,
                "info": info,
                "choice": choice,
                "A_options": A_options
            }

            # GitHub 저장 처리
            g = Github(GITHUB_TOKEN)
            repo = g.get_repo(GITHUB_REPO)
            file_path = "train_streamlit_config.json"

            content = json.dumps(config, indent=2, ensure_ascii=False)
            try:
                contents = repo.get_contents(file_path)
                repo.update_file(file_path, "update config", content, contents.sha)
            except:
                repo.create_file(file_path, "init config", content)

            st.success("✅ GitHub 저장 완료!")
