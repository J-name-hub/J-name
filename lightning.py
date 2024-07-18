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

# 10분 간격 시간 목록 생성 함수
def generate_time_options(selected_date):
    time_options = []
    for hour in range(24):
        for minute in range(0, 60, 10):
            time_options.append(datetime.combine(selected_date, datetime.min.time()).replace(hour=hour, minute=minute))
    return time_options

# 날짜 입력 받기 (한국 시간 기준)
selected_date = st.date_input("날짜를 선택하세요", datetime.now(korea_tz).date() - timedelta(days=1))

# 10분 간격 시간 목록 생성
time_options = generate_time_options(selected_date)

# 현재 선택된 시간의 인덱스 찾기 (한국 시간 기준)
default_time = datetime.now(korea_tz).replace(minute=(datetime.now(korea_tz).minute // 10) * 10, second=0, microsecond=0)

# 현재 선택된 시간의 인덱스 찾기 (한국 시간 기준)
try:
    default_index = time_options.index(min(time_options, key=lambda d: abs(d - default_time)))
except ValueError:
    # default_time이 time_options에 없을 경우 첫 번째 인덱스로 설정
    default_index = 0

# Selectbox로 시간 선택
selected_time = st.selectbox("시간을 선택하세요", time_options, index=default_index, format_func=lambda x: x.strftime("%H:%M"))

# 10분 전/후 버튼
col1, col2, col3 = st.columns([1,1,1])
with col1:
    if st.button("10분 전"):
        current_index = time_options.index(selected_time)
        if current_index > 0:
            selected_time = time_options[current_index - 1]
            st.experimental_rerun()
with col3:
    if st.button("10분 후"):
        current_index = time_options.index(selected_time)
        if current_index < len(time_options) - 1:
            selected_time = time_options[current_index + 1]
            st.experimental_rerun()

# 선택한 날짜와 시간을 결합하여 datetime 객체 생성
selected_datetime = datetime.combine(selected_date, selected_time.time())
selected_datetime_str = selected_datetime.strftime("%Y%m%d%H%M")  # API 형식 (YYYYMMDDHHMM)

# 데이터 가져오기 함수
@st.cache_data
def get_lightning_data(datetime_str):
    try:
        params = {
            'serviceKey': API_KEY,
            'numOfRows': '100',
            'pageNo': '1',
            'lgtType': '1',   # 낙뢰 유형 (1: 지상 낙뢰, 2: 지중 낙뢰)
            'dateTime': datetime_str  # 날짜 및 시간 (YYYYMMDDHHMM)
        }
        response = requests.get(API_URL, params=params)

        # 응답 상태 확인
        if response.ok:
            root = ET.fromstring(response.content)
            items = root.findall('.//item')
            return items
        else:
            st.error(f"API 요청 실패: 상태 코드 {response.status_code}")
            st.write(response.text)  # 오류 응답 내용 출력
            return None

    except requests.exceptions.RequestException as e:
        st.error(f"API 요청 중 오류 발생: {str(e)}")
        return None

# 낙뢰 데이터를 가져와서 필터링
data = get_lightning_data(selected_datetime_str)

# 영종도 관련 옵션에 대한 시간별 낙뢰 횟수 계산
if map_range in ['영종도 내', '영종도 반경 2km 이내']:
    hourly_data = {}
    for hour in range(24):
        hour_str = f"{hour:02d}"
        hour_data = get_lightning_data(selected_date.strftime("%Y%m%d") + hour_str + "00")
        if hour_data:
            count = 0
            for item in hour_data:
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

if data:
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

    for item in data:
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
    st.write("낙뢰 데이터를 가져올 수 없습니다.")

# 시간 범위 설명
st.write(f"선택한 시간 {selected_time.strftime('%H:%M')}을 기준으로 10분 단위로 반올림된 시간의 데이터를 보여줍니다.")
st.write(f"현재 설정: {selected_datetime.strftime('%Y-%m-%d %H:%M')}의 데이터")
st.write("기상청 API는 일반적으로 선택한 시간을 포함한 10분 간격의 데이터를 제공합니다.")