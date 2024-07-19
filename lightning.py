import streamlit as st
import folium
from folium.plugins import MarkerCluster
import requests
from streamlit_folium import st_folium
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET
import pandas as pd
import altair as alt
import pytz
from shapely.geometry import Polygon, Point
import pyproj
from shapely.ops import transform
from functools import partial

# Streamlit secrets에서 API 키 가져오기
API_KEY = st.secrets["api"]["API_KEY"]

# 기상청 낙뢰 API URL
API_URL = "http://apis.data.go.kr/1360000/LgtInfoService/getLgt"

# 좌표 설정
KOREA_CENTER = (36.5, 127.5)
YEONGJONG_CENTER = (37.4917, 126.4833)  # 영종도 중심 좌표

# 영종도의 경계 좌표 (정확한 좌표로 업데이트)
YEONGJONG_BOUNDARY = [
    (37.4789, 126.3900), (37.4550, 126.4150), (37.4450, 126.4450),
    (37.4500, 126.4800), (37.4750, 126.5150), (37.5050, 126.5050),
    (37.5150, 126.4750), (37.5100, 126.4400), (37.4950, 126.4050)
]

# 한국 시간대 설정
korea_tz = pytz.timezone('Asia/Seoul')

# pyproj를 사용한 버퍼 생성 함수
def create_buffer(polygon, distance):
    proj_wgs84 = pyproj.Proj('epsg:4326')
    proj_meters = pyproj.Proj('epsg:3857')
    project = partial(pyproj.transform, proj_wgs84, proj_meters)
    project_back = partial(pyproj.transform, proj_meters, proj_wgs84)
    poly_utm = transform(project, polygon)
    poly_utm_buffer = poly_utm.buffer(distance)
    return transform(project_back, poly_utm_buffer)

# 영종도 경계와 버퍼 생성
yeongjong_polygon = Polygon(YEONGJONG_BOUNDARY)
yeongjong_buffer = create_buffer(yeongjong_polygon, 2000)  # 2km 버퍼

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

st.write(f"전체 데이터 수: {len(all_data)}")  # 디버그 출력

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

# 필터링 함수
def filter_data(data, map_range):
    filtered = []
    for item in data:
        lat = float(item.find('wgs84Lat').text)
        lon = float(item.find('wgs84Lon').text)
        point = Point(lon, lat)
        
        if map_range == '영종도 내':
            if yeongjong_polygon.contains(point):
                filtered.append(item)
                st.write(f"영종도 내 낙뢰 발견: 위도 {lat}, 경도 {lon}")  # 디버그 출력
        elif map_range == '영종도 테두리에서 반경 2km 이내':
            if yeongjong_buffer.contains(point):
                filtered.append(item)
                st.write(f"영종도 반경 2km 내 낙뢰 발견: 위도 {lat}, 경도 {lon}")  # 디버그 출력
        else:  # 대한민국 전체
            filtered.append(item)
    
    st.write(f"필터링 결과: {len(filtered)}/{len(data)} 개의 데이터")  # 디버그 출력
    return filtered

# 데이터 필터링 적용
filtered_data = filter_data(filtered_data, map_range)

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
                point = Point(lon, lat)
                if map_range == '영종도 내':
                    if yeongjong_polygon.contains(point):
                        count += 1
                elif map_range == '영종도 테두리에서 반경 2km 이내':
                    if yeongjong_buffer.contains(point):
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
        total_lightning = sum(hourly_data.values())
        st.write(f"총 낙뢰 횟수: {total_lightning}")

# 지도 생성 및 마커 추가
if filtered_data:
    if map_range == '대한민국 전체':
        m = folium.Map(location=KOREA_CENTER, zoom_start=7)
    else:
        m = folium.Map(location=YEONGJONG_CENTER, zoom_start=12)
    
    marker_cluster = MarkerCluster().add_to(m)

    # 영종도 범위 표시
    if map_range in ['영종도 내', '영종도 테두리에서 반경 2km 이내']:
        folium.Polygon(
            locations=YEONGJONG_BOUNDARY,
            color="red",
            fill=True,
            fillColor="red",
            fillOpacity=0.1
        ).add_to(m)

    if map_range == '영종도 테두리에서 반경 2km 이내':
        folium.Polygon(
            locations=[(lat, lon) for lon, lat in yeongjong_buffer.exterior.coords],
            color="blue",
            fill=True,
            fillColor="blue",
            fillOpacity=0.1
        ).add_to(m)

    for item in filtered_data:
        lat = float(item.find('wgs84Lat').text)
        lon = float(item.find('wgs84Lon').text)
        location = (lat, lon)

        datetime_str = item.find('dateTime').text
        datetime_obj = datetime.strptime(datetime_str, "%Y%m%d%H%M%S")
        formatted_time = datetime_obj.strftime("%Y-%m-%d %H:%M:%S")

        folium.Marker(
            location=location,
            popup=f"낙뢰 발생 위치: 위도 {lat}, 경도 {lon}<br>발생 시간: {formatted_time}",
            icon=folium.Icon(color='red', icon='bolt')
        ).add_to(marker_cluster)

    st_folium(m, width=725)
else:
    st.write("선택한 범위와 시간에 낙뢰 데이터가 없습니다.")

def filter_data(data, map_range):
    filtered = []
    for item in data:
        lat = float(item.find('wgs84Lat').text)
        lon = float(item.find('wgs84Lon').text)
        point = Point(lon, lat)
        
        if map_range == '영종도 내':
            is_inside = yeongjong_polygon.contains(point)
            st.write(f"좌표: ({lat}, {lon}), 영종도 내부: {is_inside}")  # 디버그 출력
            if is_inside:
                filtered.append(item)
        elif map_range == '영종도 테두리에서 반경 2km 이내':
            is_inside_buffer = yeongjong_buffer.contains(point)
            st.write(f"좌표: ({lat}, {lon}), 영종도 반경 2km 내: {is_inside_buffer}")  # 디버그 출력
            if is_inside_buffer:
                filtered.append(item)
        else:  # 대한민국 전체
            filtered.append(item)
    
    st.write(f"필터링 결과: {len(filtered)}/{len(data)} 개의 데이터")  # 디버그 출력
    return filtered

# 시간 범위 설명
if time_selection == "All":
    st.write(f"{selected_date.strftime('%Y-%m-%d')}의 모든 낙뢰 데이터를 표시합니다.")
else:
    st.write(f"선택한 시간 {selected_time.strftime('%H:%M')}의 낙뢰 데이터를 표시합니다.")
st.write("기상청 API는 일반적으로 선택한 시간을 포함한 10분 간격의 데이터를 제공합니다.")