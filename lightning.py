import streamlit as st
import folium
from folium.plugins import MarkerCluster
import requests
from streamlit_folium import st_folium
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET
from math import radians, sin, cos, sqrt, atan2
import pandas as pd
import altair as alt
import pytz
from shapely.geometry import Polygon, Point

# Streamlit secrets에서 API 키 가져오기
API_KEY = st.secrets["api"]["API_KEY"]

# 기상청 낙뢰 API URL
API_URL = "http://apis.data.go.kr/1360000/LgtInfoService/getLgt"

# 좌표 설정
KOREA_CENTER = (36.5, 127.5)
YEONGJONG_CENTER = (37.4917, 126.4833)  # 영종도 중심 좌표

# 영종도의 경계 좌표 (예시)
YEONGJONG_BOUNDARY = [
    (37.4500, 126.3800), (37.4300, 126.4500), (37.4700, 126.5200), (37.5100, 126.5200),
    (37.5000, 126.4800), (37.5000, 126.4200), (37.4700, 126.3900)
]

# 한국 시간대 설정
korea_tz = pytz.timezone('Asia/Seoul')

# 거리 계산 함수
def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371  # 지구의 반경 (km)
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance = R * c
    return distance

# 영종도 내 위치인지 확인하는 함수
def is_within_yeongjong(lat, lon, boundary):
    point = Point(lon, lat)
    polygon = Polygon(boundary)
    return polygon.contains(point)

# Streamlit 설정
st.title("대한민국 낙뢰 발생 지도")
st.write("기상청 낙뢰 API를 활용하여 낙뢰 발생 지점을 지도에 표시합니다.")

# 지도 범위 선택
map_range = st.radio(
    "지도 범위 선택:",
    ('대한민국 전체', '영종도 내', '영종도 테두리에서 반경 2km 이내')
)

# 데이터 가져오기 함수
@st.cache_data
def get_lightning_data(datetime_str):
    try:
        params = {
            'serviceKey': API_KEY,
            'numOfRows': '1000',
            'pageNo': '1',
            'lgtType': '1',
            'dateTime': datetime_str
        }
        response = requests.get(API_URL, params=params)
        if response.ok:
            root = ET.fromstring(response.content)
            items = root.findall('.//item')
            return items
        else:
            st.error(f"API 요청 실패: 상태 코드 {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"API 요청 중 오류 발생: {str(e)}")
        return None

# 특정 날짜의 모든 낙뢰 데이터를 가져오는 함수
@st.cache_data
def get_all_lightning_data(date):
    all_data = []
    for hour in range(24):
        hour_str = f"{hour:02d}"
        datetime_str = date.strftime("%Y%m%d") + hour_str + "00"
        data = get_lightning_data(datetime_str)
        if data:
            all_data.extend(data)
    return all_data

# 날짜 입력 받기 (한국 시간 기준)
selected_date = st.date_input("날짜를 선택하세요", datetime.now(korea_tz).date() - timedelta(days=1))

# 데이터 로딩
data_load_state = st.text('데이터를 불러오는 중...')
all_data = get_all_lightning_data(selected_date)
data_load_state.text('데이터 로딩 완료!')

# 'All' 또는 시간별 선택
time_selection = st.radio("데이터 표시 방식:", ('All', '시간별'))

if time_selection == 'All':
    filtered_data = all_data
else:
    # 낙뢰가 있는 시간만 추출
    lightning_times = sorted(set([datetime.strptime(item.find('dateTime').text, "%Y%m%d%H%M%S").replace(tzinfo=korea_tz) for item in all_data]))
    
    # 30분 단위로 묶기
    def round_to_nearest_half_hour(dt):
        return dt.replace(minute=0, second=0, microsecond=0) + timedelta(minutes=30 * ((dt.minute // 30) + (1 if dt.minute % 30 > 0 else 0)))

    rounded_times = [round_to_nearest_half_hour(t) for t in lightning_times]
    rounded_times = sorted(set(rounded_times))
    
    # 시간 선택
    selected_time = st.selectbox("시간을 선택하세요", rounded_times, format_func=lambda x: x.strftime("%H:%M"))
    
    # 선택된 시간에 따라 데이터 필터링
    filtered_data = [item for item in all_data if abs((datetime.strptime(item.find('dateTime').text, "%Y%m%d%H%M%S").replace(tzinfo=korea_tz) - selected_time).total_seconds()) < 1800]  # 30분 이내

# 영종도 관련 옵션에 대한 시간별 낙뢰 횟수 계산
if map_range in ['영종도 내', '영종도 테두리에서 반경 2km 이내']:
    hourly_data = {}
    for hour in range(24):
        count = 0
        for item in all_data:
            item_time = datetime.strptime(item.find('dateTime').text, "%Y%m%d%H%M%S")
            if item_time.hour == hour:
                lat = float(item.find('wgs84Lat').text)
                lon = float(item.find('wgs84Lon').text)
                if map_range == '영종도 내':
                    if is_within_yeongjong(lat, lon, YEONGJONG_BOUNDARY):
                        count += 1
                elif map_range == '영종도 테두리에서 반경 2km 이내':
                    point = Point(lon, lat)
                    buffer_polygon = Polygon(YEONGJONG_BOUNDARY).buffer(2 / 111)  # 2km buffer
                    if buffer_polygon.contains(point):
                        count += 1
        hourly_data[hour] = count

    if sum(hourly_data.values()) > 0:
        # 시간별 낙뢰 횟수 차트 생성
        df = pd.DataFrame(list(hourly_data.items()), columns=['Hour', 'Count'])
        chart = alt.Chart(df).mark_bar().encode(
            x='Hour:O',
            y='Count:Q'
        ).properties(
            title=f"{selected_date.strftime('%Y-%m-%d')} {map_range} 시간별 낙뢰 횟수"
        )
        st.altair_chart(chart, use_container_width=True)

# 총 낙뢰 횟수 표시
if map_range in ['영종도 내', '영종도 테두리에서 반경 2km 이내'] and sum(hourly_data.values()) > 0:
    total_lightning = sum(hourly_data.values())
    st.write(f"총 낙뢰 횟수: {total_lightning}")

if filtered_data:
    # 지도 생성
    if map_range == '대한민국 전체':
        m = folium.Map(location=KOREA_CENTER, zoom_start=7)
    else:
        m = folium.Map(location=YEONGJONG_CENTER, zoom_start=12)

    marker_cluster = MarkerCluster().add_to(m)

    # 영종도 범위 표시
    if map_range == '영종도 내':
        folium.Polygon(
            locations=YEONGJONG_BOUNDARY,
            color="red",
            fill=True,
            fillColor="red",
            fillOpacity=0.1
        ).add_to(m)
    elif map_range == '영종도 테두리에서 반경 2km 이내':
        buffer_polygon = Polygon(YEONGJONG_BOUNDARY).buffer(2 / 111)
        folium.Polygon(
            locations=[(point.y, point.x) for point in buffer_polygon.exterior.coords],
            color="blue",
            fill=True,
            fillColor="blue",
            fillOpacity=0.1
        ).add_to(m)

    for item in filtered_data:
        lat = float(item.find('wgs84Lat').text)
        lon = float(item.find('wgs84Lon').text)
        location = (lat, lon)

        # 영종도 필터링
        if map_range == '영종도 내':
            if not is_within_yeongjong(lat, lon, YEONGJONG_BOUNDARY):
                continue
        elif map_range == '영종도 테두리에서 반경 2km 이내':
            point = Point(lon, lat)
            if not buffer_polygon.contains(point):
                continue

        # 발생 시간 정보 추출
        datetime_str = item.find('dateTime').text
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
    st.write("선택한 시간에 낙뢰 데이터가 없습니다.")

# 시간 범위 설명
if time_selection == "All":
    st.write(f"{selected_date.strftime('%Y-%m-%d')}의 모든 낙뢰 데이터를 표시합니다.")
else:
    st.write(f"선택한 시간 {selected_time.strftime('%H:%M')}의 낙뢰 데이터를 표시합니다.")
st.write("기상청 API는 일반적으로 선택한 시간을 포함한 10분 간격의 데이터를 제공합니다.")
