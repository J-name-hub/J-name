import streamlit as st
import requests
import pandas as pd
import folium
from streamlit_folium import st_folium
from datetime import datetime, timedelta

# 기상청 낙뢰 관측 API에서 데이터를 가져오는 함수
def get_lightning_data(api_key, start_time, end_time):
    url = "http://apis.data.go.kr/1360000/LgtInfoService/getLightning"
    params = {
        "serviceKey": api_key,
        "fromTmFc": start_time.strftime("%Y%m%d%H%M"),
        "toTmFc": end_time.strftime("%Y%m%d%H%M"),
        "dataType": "JSON"
    }
    st.write(f"API 요청 URL: {url}")
    st.write(f"요청 파라미터: {params}")
    
    response = requests.get(url, params=params)
    
    if response.status_code != 200:
        st.error(f"API 요청 실패: {response.status_code}")
        return pd.DataFrame()  # 빈 데이터프레임 반환

    try:
        data = response.json()
    except requests.exceptions.JSONDecodeError:
        st.error("응답을 JSON으로 디코딩할 수 없습니다.")
        st.write(response.text)  # 응답 내용 출력
        return pd.DataFrame()  # 빈 데이터프레임 반환

    if "response" in data and "body" in data["response"] and "items" in data["response"]["body"]:
        items = data["response"]["body"]["items"]
        return pd.DataFrame(items)
    else:
        st.error("API 응답 형식이 올바르지 않습니다.")
        st.write(data)  # 응답 데이터 출력
        return pd.DataFrame()  # 빈 데이터프레임 반환

# 영종도 대략적인 해안선 좌표
yeongjongdo_border = [
    [37.514, 126.493],
    [37.553, 126.493],
    [37.553, 126.635],
    [37.514, 126.635],
    [37.514, 126.493]
]

# Streamlit 앱 설정
st.title("영종도 낙뢰 관측")

# API 키 가져오기
api_key = st.secrets["api"]["API_KEY"]

# 시간 선택
time_option = st.selectbox("시간 선택", ["현재부터 -10시간", "현재부터 -24시간", "일자별 조회"])
if time_option == "일자별 조회":
    selected_date = st.date_input("날짜 선택", datetime.now())
    start_time = datetime(selected_date.year, selected_date.month, selected_date.day, selected_date.hour, (selected_date.minute // 10) * 10)
    end_time = start_time + timedelta(minutes=10)
else:
    if time_option == "현재부터 -10시간":
        start_time = datetime.now() - timedelta(hours=10)
    else:
        start_time = datetime.now() - timedelta(hours=24)
    end_time = datetime.now()

# 10분 단위로 시간 조정
start_time = start_time.replace(minute=(start_time.minute // 10) * 10, second=0, microsecond=0)
end_time = end_time.replace(minute=(end_time.minute // 10) * 10, second=0, microsecond=0)

# 낙뢰 데이터 가져오기
lightning_data = get_lightning_data(api_key, start_time, end_time)

# 지도 생성
m = folium.Map(location=[37.533, 126.564], zoom_start=12)

# 영종도 테두리 추가
folium.PolyLine(yeongjongdo_border, color="blue", weight=2.5, opacity=1).add_to(m)

# 낙뢰 데이터 지도에 추가
if not lightning_data.empty:
    for _, row in lightning_data.iterrows():
        folium.Marker([row['latitude'], row['longitude']], popup=f"시간: {row['datetime']}\n강도: {row['intensity']}").add_to(m)
else:
    st.warning("선택한 시간 범위 내에 낙뢰 데이터가 없습니다.")

# 지도 출력
st_folium(m, width=700, height=500)
