import streamlit as st
import json
import base64
from github import Github

# 사용자 입력
info = {
    "departure": st.selectbox("출발역", ["서울", "수서"]),
    "arrival": st.selectbox("도착역", ["대전", "동대구"]),
    "date": st.date_input("날짜").strftime("%Y%m%d"),
    "time": st.time_input("출발 시간").strftime("%H%M%S"),
    "adult": st.number_input("성인 수", min_value=0, max_value=9, value=1),
    "child": st.number_input("어린이 수", min_value=0, max_value=9),
    "senior": st.number_input("경로 수", min_value=0, max_value=9),
    "disability1to3": st.number_input("1~3급 장애인", min_value=0, max_value=9),
    "disability4to6": st.number_input("4~6급 장애인", min_value=0, max_value=9)
}

choice = {
    "trains": [st.number_input("선택할 열차 인덱스", min_value=0, max_value=9, value=1)]
}

options = {
    "type": st.selectbox("좌석 유형", ["GENERAL_ONLY", "GENERAL_FIRST", "SPECIAL_ONLY", "SPECIAL_FIRST"]),
    "pay": st.checkbox("카드결제")
}

if st.button("GitHub에 저장"):
    config = {"info": info, "choice": choice, "options": options}

    # GitHub 저장 처리
    g = Github(st.secrets["GITHUB_TOKEN"])  # Streamlit secrets에 저장된 토큰
    repo = g.get_repo("J-name/repo")  # 본인 계정/repo 이름
    file_path = "train_streamlit_config.json"

    content = json.dumps(config, indent=2, ensure_ascii=False)
    try:
        contents = repo.get_contents(file_path)
        repo.update_file(file_path, "update config", content, contents.sha)
    except:
        repo.create_file(file_path, "init config", content)

    st.success("✅ GitHub 저장 완료!")
