import streamlit as st
import json
import base64
from github import Github

# GitHub 설정
GITHUB_TOKEN = st.secrets["github"]["token"]
GITHUB_REPO = st.secrets["github"]["repo"]


STATIONS = {
    "SRT": [
        "수서", "동탄", "평택지제", "경주", "곡성", "공주", "광주송정", "구례구", "김천(구미)",
        "나주", "남원", "대전", "동대구", "마산", "목포", "밀양", "부산", "서대구",
        "순천", "여수EXPO", "여천", "오송", "울산(통도사)", "익산", "전주",
        "정읍", "진영", "진주", "창원", "창원중앙", "천안아산", "포항"
    ],
    "KTX": [
        "서울", "용산", "영등포", "광명", "수원", "천안아산", "오송", "대전", "서대전",
        "김천구미", "동대구", "경주", "포항", "밀양", "구포", "부산", "울산(통도사)",
        "마산", "창원중앙", "경산", "논산", "익산", "정읍", "광주송정", "목포",
        "전주", "순천", "여수EXPO", "청량리", "강릉", "행신", "정동진"
    ]
}

# 좌석 유형 (enum 형식을 문자열로 저장)
seat_type_options = {
    "일반석 우선": "seat_type.GENERAL_FIRST",
    "일반석만": "seat_type.GENERAL_ONLY",
    "특실 우선": "seat_type.SPECIAL_FIRST",
    "특실만": "seat_type.SPECIAL_ONLY"
}

# rail_type 입력
rail_type = st.selectbox("🚅 열차 종류 선택", ["KTX", "SRT"])

# 사용자 입력
info = {
    "departure": st.selectbox("출발역 선택", STATIONS[rail_type]),
    "arrival": st.selectbox("도착역 선택", STATIONS[rail_type]),
    "date": st.date_input("날짜").strftime("%Y%m%d"),
    "time": f"{st.selectbox('출발 시각', [f'{i:02d}' for i in range(24)])}0000",
    "adult": st.number_input("성인 수", min_value=0, max_value=9, value=1),
    "child": st.number_input("어린이 수", min_value=0, max_value=9),
    "senior": st.number_input("경로 수", min_value=0, max_value=9),
    "disability1to3": 0,
    "disability4to6": 0
}

choice = {
    "trains": [st.number_input("선택할 열차 인덱스", min_value=0, max_value=9, value=1)]
}

# 옵션 선택
seat_display = st.selectbox("좌석 유형", list(seat_type_options.keys()))
A_options = {
    "type": seat_type_options[seat_display],
    "pay": st.checkbox("카드결제")
}

if st.button("GitHub에 저장"):
    config = {"rail_type": rail_type, "info": info, "choice": choice, "A_options": A_options}

    # GitHub 저장 처리
    g = Github(GITHUB_TOKEN)  # Streamlit secrets에 저장된 토큰
    repo = g.get_repo(GITHUB_REPO)  # 본인 계정/repo 이름
    file_path = "train_streamlit_config.json"

    content = json.dumps(config, indent=2, ensure_ascii=False)
    try:
        contents = repo.get_contents(file_path)
        repo.update_file(file_path, "update config", content, contents.sha)
    except:
        repo.create_file(file_path, "init config", content)

    st.success("✅ GitHub 저장 완료!")
