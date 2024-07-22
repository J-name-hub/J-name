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
from concurrent.futures import ThreadPoolExecutor
from shapely.geometry import Polygon, Point
import time

# Streamlit secrets에서 API 키 가져오기
API_KEY = st.secrets["api"]["API_KEY"]

# 기상청 낙뢰 API URL
API_URL = "http://apis.data.go.kr/1360000/LgtInfoService/getLgt"

# 좌표 설정
YEONGJONG_CENTER = (37.4917, 126.4833)  # 영종도 중심 좌표

# 영종도의 경계 좌표 (예시)
YEONGJONG_BOUNDARY = [
    (37.5252, 126.3612),  # 북서쪽 꼭짓점
    (37.5252, 126.5802),  # 북동쪽 꼭짓점
    (37.4122, 126.5802),  # 남동쪽 꼭짓점
    (37.4122, 126.3612)   # 남서쪽 꼭짓점
]

# 영종도 경계를 Polygon 객체로 변환
yeongjong_polygon = Polygon(YEONGJONG_BOUNDARY)

# 한국 시간대 설정
korea_tz = pytz.timezone('Asia/Seoul')

# 데이터 가져오기 함수
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
            return []
    except requests.exceptions.RequestException:
        return []

# 특정 날짜의 모든 낙뢰 데이터를 가져오는 함수 (병렬 처리)
def get_all_lightning_data(date):
    all_data = []
    now = datetime.now(korea_tz)
    
    def fetch_data(hour, minute):
        if date == now.date() and (hour > now.hour or (hour == now.hour and minute > now.minute)):
            return []
        time_str = f"{hour:02d}{minute:02d}"
        datetime_str = date.strftime("%Y%m%d") + time_str
        return get_lightning_data(datetime_str)
    
    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(fetch_data, hour, minute) for hour in range(24) for minute in range(0, 60, 10)]
        for future in futures:
            all_data.extend(future.result())
    
    return all_data

# 페이지 주기적 새로고침
if 'last_refreshed' not in st.session_state:
    st.session_state.last_refreshed = time.time()

if time.time() - st.session_state.last_refreshed > 600:
    st.session_state.last_refreshed = time.time()
    st.experimental_rerun()

# 날짜 입력 받기 (한국 시간 기준)
selected_date = st.date_input("날짜를 선택하세요", datetime.now(korea_tz).date())

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

    # 10분 단위로 묶기
    def round_to_nearest_ten_minutes(dt):
        discard = timedelta(minutes=dt.minute % 10, seconds=dt.second, microseconds=dt.microsecond)
        dt -= discard
        if discard >= timedelta(minutes=5):
            dt += timedelta(minutes=10)
        return dt

    rounded_times = [round_to_nearest_ten_minutes(t) for t in lightning_times]
    rounded_times = sorted(set(rounded_times))

    # 시간 선택
    selected_time = st.selectbox("시간을 선택하세요", rounded_times, format_func=lambda x: x.strftime("%H:%M"))

    # 선택된 시간에 따라 데이터 필터링
    filtered_data = [item for item in all_data if abs((datetime.strptime(item.find('dateTime').text, "%Y%m%d%H%M%S").replace(tzinfo=korea_tz) - selected_time).total_seconds()) < 600]  # 10분 이내

# 영종도 관련 시간별 낙뢰 횟수 계산
hourly_data = {}
total_lightning = 0

for hour in range(24):
    count = 0
    for item in all_data:
        item_time = datetime.strptime(item.find('dateTime').text, "%Y%m%d%H%M%S")
        if item_time.hour == hour:
            lat = float(item.find('wgs84Lat').text)
            lon = float(item.find('wgs84Lon').text)
            if yeongjong_polygon.contains(Point(lon, lat)):
                count += 1
    hourly_data[hour] = count
    total_lightning += count

if sum(hourly_data.values()) > 0:
    # 시간별 낙뢰 횟수 차트 생성
    df = pd.DataFrame(list(hourly_data.items()), columns=['Hour', 'Count'])
    chart = alt.Chart(df).mark_bar().encode(
        x='Hour:O',
        y='Count:Q'
    ).properties(
        title=f"{selected_date.strftime('%Y-%m-%d')} 영종도 시간별 낙뢰 횟수"
    )
    st.altair_chart(chart, use_container_width=True)

# 총 낙뢰 횟수 표시
if total_lightning > 0:
    st.write(f"영종도 총 낙뢰 횟수: {total_lightning}")

if filtered_data:
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

    for item in filtered_data:
        lat = float(item.find('wgs84Lat').text)
        lon = float(item.find('wgs84Lon').text)
        location = (lat, lon)

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
