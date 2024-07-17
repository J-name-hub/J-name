import streamlit as st
import folium
from folium.plugins import MarkerCluster
import requests
from geopy.distance import geodesic
from streamlit_folium import st_folium

# Streamlit secrets에서 API 키 가져오기
API_KEY = st.secrets["api"]["API_KEY"]

# 기상청 낙뢰 API URL
API_URL = "http://apis.data.go.kr/1360000/LivingWthrIdxServiceV2/getLightningSts"

# 영종도 중심 좌표
yeongjongdo_center = (37.4935, 126.4900)

# Streamlit 설정
st.title("영종도 및 반경 2km 내 낙뢰 발생 지도")
st.write("기상청 낙뢰 API를 활용하여 영종도 및 반경 2km 내에서 발생한 낙뢰를 지도에 표시합니다.")

# 데이터 가져오기 함수
@st.cache
def get_lightning_data():
    params = {
        'serviceKey': API_KEY,
        'pageNo': '1',
        'numOfRows': '100',
        'dataType': 'JSON'
    }
    response = requests.get(API_URL, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        st.error("데이터를 가져오는 데 실패했습니다.")
        return None

# 낙뢰 데이터를 가져와서 필터링
data = get_lightning_data()
if data:
    items = data.get('response', {}).get('body', {}).get('items', {}).get('item', [])
    
    # 지도 생성
    m = folium.Map(location=yeongjongdo_center, zoom_start=13)
    marker_cluster = MarkerCluster().add_to(m)
    
    for item in items:
        lat = float(item.get('lat', 0))
        lon = float(item.get('lon', 0))
        location = (lat, lon)
        
        # 영종도 중심으로부터 반경 2km 내에 있는지 확인
        if geodesic(yeongjongdo_center, location).km <= 2:
            folium.Marker(
                location=location,
                popup=f"낙뢰 발생 위치: {location}",
                icon=folium.Icon(color='red', icon='bolt')
            ).add_to(marker_cluster)
    
    # 지도 출력
    st_folium(m, width=725)
else:
    st.write("낙뢰 데이터를 가져올 수 없습니다.")
