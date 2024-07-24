import streamlit as st
import folium
from folium.plugins import MarkerCluster
import requests
from streamlit_folium import st_folium
from datetime import datetime
import xml.etree.ElementTree as ET
import pandas as pd
import altair as alt
import pytz

# Streamlit secrets에서 API 키 가져오기
API_KEY = st.secrets["api"]["API_KEY"]

# KEPCO 낙뢰정보 API URL
API_URL = "http://openapi.kepco.co.kr/service/lightningInfoService/getLight"

# 영종도의 경계 좌표
YEONGJONG_BOUNDARY = [
    (37.5252, 126.3612),  # 북서쪽 꼭짓점
    (37.5252, 126.5802),  # 북동쪽 꼭짓점
    (37.4122, 126.5802),  # 남동쪽 꼭짓점
    (37.4122, 126.3612)   # 남서쪽 꼭짓점
]

# 영종도 중심 좌표
YEONGJONG_CENTER = (37.4917, 126.4833)

# 한국 시간대 설정
korea_tz = pytz.timezone('Asia/Seoul')

# 데이터 가져오기 함수
def get_lightning_data(date, min_lat, max_lat, min_lon, max_lon):
    try:
        params = {
            'serviceKey': API_KEY,
            'pageNo': '1',
            'numOfRows': '1000',
            'strDate': date.strftime("%Y%m%d"),
            'minLat': min_lat,
            'maxLat': max_lat,
            'minLon': min_lon,
            'maxLon': max_lon
        }
        response = requests.get(API_URL, params=params)
        if response.ok:
            root = ET.fromstring(response.content)
            items = root.findall('.//item')
            return items
        else:
            return []
    except requests.exceptions.RequestException:
        return []

# 날짜 입력 받기 (한국 시간 기준)
selected_date = st.date_input("날짜를 선택하세요", datetime.now(korea_tz).date())

# 데이터 로딩
data_load_state = st.text('데이터를 불러오는 중...')
all_data = get_lightning_data(selected_date, 37.4122, 37.5252, 126.3612, 126.5802)
data_load_state.text('데이터 로딩 완료!')

# 시간별 낙뢰 횟수 계산
hourly_data = {hour: 0 for hour in range(24)}
total_lightning = 0

for item in all_data:
    datetime_str = item.find('receiptDtm').text
    hour = int(datetime_str[8:10])
    hourly_data[hour] += 1
    total_lightning += 1

# 시간별 낙뢰 횟수 차트 생성
if total_lightning > 0:
    df = pd.DataFrame(list(hourly_data.items()), columns=['Hour', 'Count'])
    chart = alt.Chart(df).mark_bar().encode(
        x='Hour:O',
        y='Count:Q'
    ).properties(
        title=f"{selected_date.strftime('%Y-%m-%d')} 영종도 시간별 낙뢰 횟수"
    )
    st.altair_chart(chart, use_container_width=True)

# 총 낙뢰 횟수 표시
st.write(f"영종도 총 낙뢰 횟수: {total_lightning}")

if all_data:
    # 지도 생성
    m = folium.Map(location=YEONGJONG_CENTER, zoom_start=12)

    marker_cluster = MarkerCluster().add_to(m)

    # 영종도 범위 표시
    folium.Polygon(
        locations=YEONGJONG_BOUNDARY,
        color="red",
        fill=True,
        fillColor="red",
        fillOpacity=0.1
    ).add_to(m)

    for item in all_data:
        lat = float(item.find('lat').text)
        lon = float(item.find('lon').text)
        location = (lat, lon)

        # 발생 시간 정보 추출
        datetime_str = item.find('receiptDtm').text
        datetime_obj = datetime.strptime(datetime_str, "%Y%m%d%H%M%S")
        formatted_time = datetime_obj.strftime("%Y-%m-%d %H:%M:%S")

        folium.Marker(
            location=location,
            popup=f"낙뢰 발생 위치: 위도 {lat}, 경도 {lon}<br>발생 시간: {formatted_time}",
            icon=folium.Icon(color='red', icon='bolt')
        ).add_to(marker_cluster)

    # 지도 출력
    st_folium(m, width=725)
else:
    st.write("선택한 날짜에 영종도 지역의 낙뢰 데이터가 없습니다.")

st.write(f"{selected_date.strftime('%Y-%m-%d')}의 영종도 지역 낙뢰 데이터를 표시합니다.")
