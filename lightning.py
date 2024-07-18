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

# Streamlit secrets에서 API 키 가져오기
API_KEY = st.secrets["api"]["API_KEY"]

# 기상청 낙뢰 API URL
API_URL = "http://apis.data.go.kr/1360000/LgtInfoService/getLgt"

# 좌표 설정
KOREA_CENTER = (36.5, 127.5)
YEONGJONG_CENTER = (37.4917, 126.4833)  # 영종도 중심 좌표

# 한국 시간대 설정
korea_tz = pytz.timezone('Asia/Seoul')

# 거리 계산 함수
def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371  # 지구의 반경 (km)
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    distance = R * c
    return distance

# Streamlit 설정
st.title("대한민국 낙뢰 발생 지도")
st.write("기상청 낙뢰 API를 활용하여 낙뢰 발생 지점을 지도에 표시합니다.")

# 지도 범위 선택
map_range = st.radio(
    "지도 범위 선택:",
    ('대한민국 전체', '영종도 내', '영종도 반경 2km 이내')
)

# 데이터 가져오기 함수
@st.cache_data
def get_lightning_data(datetime_str):
    try:
        params = {
            'serviceKey': API_KEY,
            'numOfRows': '1000',  # 더 많은 데이터를 요청
            'pageNo': '1',
            'lgtType': '1',   # 낙뢰 유형 (1: 지상 낙뢰, 2: 지중 낙뢰)
            'dateTime': datetime_str  # 날짜 및 시간 (YYYYMMDDHHMM)
        }
        response = requests.get(API_URL, params=params)
        if response.ok:
            root = ET.fromstring(response.content)
            items = root.findall('.//item')
            if not items:
                st.write(f"No data for {datetime_str}")  # 데이터가 없는 경우 로그
            return items
        else:
            st.error(f"API 요청 실패: 상태 코드 {response.status_code}")
            st.write(response.text)
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"API 요청 중 오류 발생: {str(e)}")
        return None

# 특정 날짜의 모든 낙뢰 데이터를 가져오는 함수
def get_all_lightning_data(date):
    all_data = []
    for hour in range(24):
        for minute in range(0, 60, 10):  # 10분 단위로 요청
            hour_str = f"{hour:02d}"
            minute_str = f"{minute:02d}"
            datetime_str = date.strftime("%Y%m%d") + hour_str + minute_str
            data = get_lightning_data(datetime_str)
            if data:
                all_data.extend(data)
    return all_data

# 날짜 입력 받기 (한국 시간 기준)
selected_date = st.date_input("날짜를 선택하세요", datetime.now(korea_tz).date() - timedelta(days=1))

# 선택한 날짜의 모든 낙뢰 데이터 가져오기
all_data = get_all_lightning_data(selected_date)

# 낙뢰가 있는 시간만 추출
lightning_times = sorted(set([datetime.strptime(item.find('dateTime').text, "%Y%m%d%H%M%S").replace(tzinfo=korea_tz) for item in all_data]))

# 시간 옵션 생성
time_options = [datetime.combine(selected_date, datetime.min.time()).replace(hour=t.hour, minute=t.minute, tzinfo=korea_tz) for t in lightning_times]
time_options.insert(0, "All")  # 'All' 옵션 추가

# 현재 시간이 선택된 날짜와 같은 날이면 현재 시간까지만 표시
if selected_date == datetime.now(korea_tz).date():
    current_time = datetime.now(korea_tz)
    time_options = [t for t in time_options if t == "All" or t <= current_time]

# 시간 선택
selected_time = st.selectbox("시간을 선택하세요", time_options, format_func=lambda x: "All" if x == "All" else x.strftime("%H:%M"))

# 선택된 시간에 따라 데이터 필터링
if selected_time == "All":
    filtered_data = all_data
else:
    filtered_data = [item for item in all_data if abs((datetime.strptime(item.find('dateTime').text, "%Y%m%d%H%M%S").replace(tzinfo=korea_tz) - selected_time).total_seconds()) <= 600]  # 10분 이내

# 영종도 관련 옵션에 대한 시간별 낙뢰 횟수 계산
if map_range in ['영종도 내', '영종도 반경 2km 이내']:
    hourly_data = {}
    for hour in range(24):
        count = 0
        for item in all_data:
            item_time = datetime.strptime(item.find('dateTime').text, "%Y%m%d%H%M%S")
            if item_time.hour == hour:
                lat = float(item.find('wgs84Lat').text)
                lon = float(item.find('wgs84Lon').text)
                if map_range == '영종도 내':
                    if 37.4667 <= lat <= 37.5167 and 126.4333 <= lon <= 126.5333:
                        count += 1
                elif map_range == '영종도 반경 2km 이내':
                    if haversine_distance(YEONGJONG_CENTER[0], YEONGJONG_CENTER[1], lat, lon) <= 2:
                        count += 1
        hourly_data[hour] = count

    # 시간별 낙뢰 횟수 차트 생성
    df = pd.DataFrame(list(hourly_data.items()), columns=['Hour', 'Count'])
    chart = alt.Chart(df).mark_bar().encode(
        x='Hour:O',
        y='Count:Q'
    ).properties(
        title=f"{selected_date.strftime('%Y-%m-%d')} {map_range} 시간별 낙뢰 횟수"
    )
    st.altair_chart(chart, use_container_width=True)

if filtered_data:
    # 지도 생성
    if map_range == '대한민국 전체':
        m = folium.Map(location=KOREA_CENTER, zoom_start=7)
    else:
        m = folium.Map(location=YEONGJONG_CENTER, zoom_start=12)

    marker_cluster = MarkerCluster().add_to(m)

    # 영종도 범위 표시
    if map_range == '영종도 내':
        folium.Rectangle(
            bounds=[(37.4667, 126.4333), (37.5167, 126.5333)],
            color="red",
            fill=True,
            fillColor="red",
            fillOpacity=0.1
        ).add_to(m)
    elif map_range == '영종도 반경 2km 이내':
        folium.Circle(
            location=YEONGJONG_CENTER,
            radius=2000,  # 반경 2km (미터 단위)
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
            if not (37.4667 <= lat <= 37.5167 and 126.4333 <= lon <= 126.5333):
                continue
        elif map_range == '영종도 반경 2km 이내':
            if haversine_distance(YEONGJONG_CENTER[0], YEONGJONG_CENTER[1], lat, lon) > 2:
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
if selected_time == "All":
    st.write(f"{selected_date.strftime('%Y-%m-%d')}의 모든 낙뢰 데이터를 표시합니다.")
else:
    st.write(f"선택한 시간 {selected_time.strftime('%H:%M')}의 낙뢰 데이터를 표시합니다.")
st.write("기상청 API는 일반적으로 선택한 시간을 포함한 10분 간격의 데이터를 제공합니다.")