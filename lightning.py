import streamlit as st
import folium
from folium.plugins import MarkerCluster
import requests
from geopy.distance import geodesic
from streamlit_folium import st_folium
from datetime import datetime, timedelta

# Streamlit secrets에서 API 키 가져오기
API_KEY = st.secrets["api"]["API_KEY"]

# 기상청 낙뢰 API URL
API_URL = "http://apis.data.go.kr/1360000/LivingWthrIdxServiceV2/getLightningSttusList"

# 대한민국 중심 좌표
korea_center = (36.5, 127.5)

# Streamlit 설정
st.title("대한민국 낙뢰 발생 지도")
st.write("기상청 낙뢰 API를 활용하여 대한민국 전역의 낙뢰 발생 지점을 지도에 표시합니다.")

# 날짜 입력 받기
selected_date = st.date_input("날짜를 선택하세요", datetime.today() - timedelta(days=1))
selected_date_str = selected_date.strftime("%Y%m%d")  # API에 맞는 형식으로 변환

# 데이터 가져오기 함수
@st.cache_data
def get_lightning_data(date):
    params = {
        'serviceKey': API_KEY,
        'pageNo': '1',
        'numOfRows': '100',
        'dataType': 'JSON',
        'date': date
    }
    response = requests.get(API_URL, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        st.error("데이터를 가져오는 데 실패했습니다.")
        return None

# 낙뢰 데이터를 가져와서 필터링
data = get_lightning_data(selected_date_str)
if data and 'response' in data and 'body' in data['response']:
    items = data['response']['body']['items']['item']
    
    # 지도 생성
    m = folium.Map(location=korea_center, zoom_start=7)
    marker_cluster = MarkerCluster().add_to(m)
    
    for item in items:
        lat = float(item['lat'])
        lon = float(item['lon'])
        location = (lat, lon)
        
        folium.Marker(
            location=location,
            popup=f"낙뢰 발생 위치: {location}",
            icon=folium.Icon(color='red', icon='bolt')
        ).add_to(marker_cluster)
    
    # 지도 출력
    st_folium(m, width=725)
else:
    st.write("낙뢰 데이터를 가져올 수 없습니다.")
