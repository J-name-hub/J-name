import streamlit as st
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
from datetime import datetime, timedelta

# 대한민국 중심 좌표
korea_center = (36.5, 127.5)

# Streamlit 설정
st.title("대한민국 낙뢰 발생 지도")
st.write("기상청 낙뢰 API를 활용하여 대한민국 전역의 낙뢰 발생 지점을 지도에 표시합니다.")

# 날짜 입력 받기
selected_date = st.date_input("날짜를 선택하세요", datetime.today() - timedelta(days=1))

# 하드코딩된 예시 데이터 (2023년 7월 15일)
example_data = [
    {'lat': 37.5665, 'lon': 126.9780},  # 서울
    {'lat': 35.1796, 'lon': 129.0756},  # 부산
    {'lat': 35.8714, 'lon': 128.6014},  # 대구
    {'lat': 37.4563, 'lon': 126.7052},  # 인천
    {'lat': 35.1595, 'lon': 126.8526}   # 광주
]

# 지도 생성
m = folium.Map(location=korea_center, zoom_start=7)
marker_cluster = MarkerCluster().add_to(m)

for item in example_data:
    lat = item['lat']
    lon = item['lon']
    location = (lat, lon)
    
    folium.Marker(
        location=location,
        popup=f"낙뢰 발생 위치: {location}",
        icon=folium.Icon(color='red', icon='bolt')
    ).add_to(marker_cluster)

# 지도 출력
st_folium(m, width=725)
