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
        response = requests.get(API_URL, params=params, timeout=10)  # Added timeout
        response.raise_for_status()  # Raises HTTPError for bad responses

        # Check if the response contains valid XML
        try:
            root = ET.fromstring(response.content)
            items = root.findall('.//item')
            return items
        except ET.ParseError:
            st.error("API 응답을 파싱할 수 없습니다. 잠시 후 다시 시도해 주세요.")
            return []

    except requests.exceptions.HTTPError as http_err:
        st.error(f"HTTP 에러 발생: {http_err}")
    except requests.exceptions.ConnectionError:
        st.error("네트워크 연결 오류가 발생했습니다. 인터넷 연결을 확인하세요.")
    except requests.exceptions.Timeout:
        st.error("요청 시간이 초과되었습니다. 다시 시도해 주세요.")
    except requests.exceptions.RequestException as err:
        st.error(f"API 요청 중 오류가 발생했습니다: {err}")
    
    return []

# 특정 날짜의 모든 낙뢰 데이터를 가져오는 함수 (병렬 처리)
def get_all_lightning_data(date):
    all_data = []
    now = datetime.now(korea_tz)

    def fetch_data(hour, minute):
        # Skip future times if today
        if date == now.date() and (hour > now.hour or (hour == now.hour and minute > now.minute)):
            return []
        time_str = f"{hour:02d}{minute:02d}"
        datetime_str = date.strftime("%Y%m%d") + time_str
        return get_lightning_data(datetime_str)
    
    with ThreadPoolExecutor(max_workers=10) as executor:  # Limit the number of threads
        futures = [executor.submit(fetch_data, hour, minute) for hour in range(24) for minute in range(0, 60, 10)]
        for future in futures:
            try:
                all_data.extend(future.result())
            except Exception as e:
                st.error(f"데이터 수집 중 오류 발생: {e}")

    return all_data

# 날짜 입력 받기 (한국 시간 기준)
# Today, Yesterday, and Day before yesterday
today = datetime.now(korea_tz).date()
yesterday = today - timedelta(days=1)
day_before_yesterday = today - timedelta(days=2)

# Allow only these three dates to be selected
selected_date = st.selectbox(
    "날짜를 선택하세요",
    options=[today, yesterday, day_before_yesterday],
    format_func=lambda x: x.strftime('%Y-%m-%d')
)

# 데이터 로딩
data_load_state = st.text('데이터를 불러오는 중...')
all_data = get_all_lightning_data(selected_date)
data_load_state.text('데이터 로딩 완료!')

# 'All' 또는 시간별 선택
time_selection = st.radio("데이터 표시 방식:", ('All', '시간별'))

# Parsing and handling datetime objects
def parse_datetime(item):
    try:
        datetime_str = item.find('dateTime').text
        return datetime.strptime(datetime_str, "%Y%m%d%H%M%S").replace(tzinfo=korea_tz)
    except (ValueError, AttributeError) as e:
        st.error(f"시간 파싱 오류: {e}")
        return None

if time_selection == 'All':
    filtered_data = all_data
else:
    # 낙뢰가 있는 시간만 추출
    lightning_times = sorted(set([parse_datetime(item) for item in all_data if parse_datetime(item)]))

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
    filtered_data = [
        item for item in all_data
        if parse_datetime(item) and abs((parse_datetime(item) - selected_time).total_seconds()) < 600  # 10분 이내
    ]

# 영종도 관련 시간별 낙뢰 횟수 계산
hourly_data = {}
total_lightning = 0

for hour in range(24):
    count = 0
    for item in all_data:
        item_time = parse_datetime(item)
        if item_time and item_time.hour == hour:
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

# Display data on the map or a no-data message
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

    # icnacc 테두리 추가
    folium.Polygon(
        locations=[
            (37.4802, 126.4525), (37.4808, 126.4535),
            (37.4796, 126.4546), (37.4790, 126.4536)
        ],
        color="green",
        fill=False,
        weight=2,
        tooltip="icnacc"
    ).add_to(m)

    for item in filtered_data:
        lat = float(item.find('wgs84Lat').text)
        lon = float(item.find('wgs84Lon').text)
        location = (lat, lon)

        # 발생 시간 정보 추출
        datetime_str = item.find('dateTime').text
        datetime_obj = datetime.strptime(datetime_str, "%Y%m%d%H%M%S")
        formatted_time = datetime_obj.strftime('%Y-%m-%d %H:%M:%S')

        # 팝업 내용 생성
        popup_content = f"발생 시간: {formatted_time}"

        # 마커 추가
        folium.Marker(
            location,
            popup=popup_content,
            icon=folium.Icon(color='blue', icon='bolt', prefix='fa')
        ).add_to(marker_cluster)

    # folium 맵을 Streamlit 앱에 추가
    st_folium(m, width=700, height=500)
else:
    if time_selection == "All":
        st.warning(f"선택한 날짜 ({selected_date.strftime('%Y-%m-%d')}) 에 낙뢰 데이터가 없습니다.")
    else:
        st.warning('선택한 시간에 대한 낙뢰 데이터가 없습니다.')
