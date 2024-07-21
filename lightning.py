import streamlit as st
import requests
import pandas as pd
import folium
from streamlit_folium import st_folium
from datetime import datetime, timedelta

# 기상청 낙뢰 관측 API에서 데이터를 가져오는 함수
def get_lightning_data(api_key, start_time, end_time):
    url = "YOUR_KMA_API_ENDPOINT"
    params = {
        "serviceKey": api_key,
        "startDt": start_time.strftime("%Y%m%d%H%M"),
        "endDt": end_time.strftime("%Y%m%d%H%M"),
        "type": "json"
    }
    response = requests.get(url, params=params)
    data = response.json()
    return pd.DataFrame(data['response']['body']['items'])

# 영종도 테두리 좌표
yeongjongdo_border = [
    [37.545, 126.490],
    [37.552, 126.490],
    [37.552, 126.605],
    [37.545, 126.605]
]

# Streamlit 앱 설정
st.title("영종도 낙뢰 관측")

# API 키 가져오기
api_key = st.secrets["api"]["API_KEY"]

# 시간 선택
time_option = st.selectbox("시간 선택", ["현재부터 -10시간", "현재부터 -24시간", "일자별 조회"])
if time_option == "일자별 조회":
    selected_date = st.date_input("날짜 선택", datetime.now())
    start_time = datetime(selected_date.year, selected_date.month, selected_date.day)
    end_time = start_time + timedelta(days=1)
else:
    if time_option == "현재부터 -10시간":
        start_time = datetime.now() - timedelta(hours=10)
    else:
        start_time = datetime.now() - timedelta(hours=24)
    end_time = datetime.now()

# 낙뢰 데이터 가져오기
lightning_data = get_lightning_data(api_key, start_time, end_time)

# 지도 생성
m = folium.Map(location=[37.548, 126.548], zoom_start=12)

# 영종도 테두리 추가
folium.PolyLine(yeongjongdo_border, color="blue", weight=2.5, opacity=1).add_to(m)

# 낙뢰 데이터 지도에 추가
for _, row in lightning_data.iterrows():
    folium.Marker([row['latitude'], row['longitude']], popup=f"시간: {row['datetime']}\n강도: {row['intensity']}").add_to(m)

# 지도 출력
st_folium(m, width=700, height=500)
