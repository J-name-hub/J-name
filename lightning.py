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
import base64
import json

# Load secrets
try:
    API_KEY = st.secrets["api"]["API_KEY"]
    GITHUB_TOKEN = st.secrets["github"]["GITHUB_TOKEN"]
    REPO_NAME = st.secrets["github"]["REPO_NAME"]
except KeyError as e:
    st.error(f"Missing secret: {e}")
    st.stop()  # Stop the app if secrets are missing

# 기상청 낙뢰 API URL
API_URL = "http://apis.data.go.kr/1360000/LgtInfoService/getLgt"

# 좌표 설정
YEONGJONG_CENTER = (37.4917, 126.4833)  # 영종도 중심 좌표

# 영종도의 경계 좌표
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

# 날짜 리스트 생성
def get_valid_dates():
    now = datetime.now(korea_tz)
    return [now.date(), now.date() - timedelta(days=1), now.date() - timedelta(days=2)]

valid_dates = get_valid_dates()

# 날짜 선택
selected_date = st.selectbox(
    "날짜를 선택하세요",
    options=valid_dates,
    format_func=lambda x: x.strftime('%Y-%m-%d')
)

# 데이터 가져오기 함수
def get_lightning_data(datetime_str):
    """
    Fetch lightning data for a specific datetime string from the API.

    :param datetime_str: A string representing the datetime in the format 'YYYYMMDDHHMM'
    :return: A list of lightning data items, or an empty list if the request fails
    """
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
            st.error("API 요청 실패: 상태 코드 " + str(response.status_code))
            return []
    except requests.exceptions.RequestException as e:
        st.error("데이터 요청 중 오류 발생: " + str(e))
        return []

# 모든 시간의 낙뢰 데이터 가져오기 함수
def get_all_lightning_data(date):
    """
    Fetch lightning data for an entire day at 10-minute intervals.

    :param date: A datetime.date object representing the day for which data is fetched
    :return: A list of all lightning data items for the specified day
    """
    all_data = []
    now = datetime.now(korea_tz)

    # 10분 간격 데이터 가져오기
    def fetch_data(hour, minute):
        if date == now.date() and (hour > now.hour or (hour == now.hour and minute > now.minute)):
            return []
        time_str = f"{hour:02d}{minute:02d}"
        datetime_str = date.strftime("%Y%m%d") + time_str
        return get_lightning_data(datetime_str)

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(fetch_data, hour, minute) for hour in range(24) for minute in range(0, 60, 10)]
        for future in futures:
            all_data.extend(future.result())

    return all_data

# GitHub에 데이터 저장하기
def save_data_to_github(data, date):
    """
    Save the provided lightning data to GitHub as an XML file.

    :param data: The lightning data to be saved
    :param date: The date for which data is being saved, used for naming the file
    """
    try:
        # GitHub API URL 설정
        folder_name = date.strftime('%Y/%m/%d')
        file_path = f"lightning/{folder_name}/lightning_data.xml"
        url = f"https://api.github.com/repos/{REPO_NAME}/contents/{file_path}"

        # XML 데이터로 변환
        data_xml = "<data>\n" + "\n".join(ET.tostring(item, encoding='unicode') for item in data) + "\n</data>"
        data_bytes = base64.b64encode(data_xml.encode('utf-8')).decode('utf-8')

        # GitHub에서 파일이 이미 존재하는지 확인
        response = requests.get(url, headers={'Authorization': f'token {GITHUB_TOKEN}'})
        if response.status_code == 200:
            # 파일이 존재하면 SHA 값 추출
            sha = response.json()['sha']
            # 파일 업데이트
            payload = {
                "message": f"Update lightning data for {date.strftime('%Y-%m-%d')}",
                "content": data_bytes,
                "sha": sha
            }
        else:
            # 파일 생성
            payload = {
                "message": f"Add lightning data for {date.strftime('%Y-%m-%d')}",
                "content": data_bytes,
            }

        # GitHub에 파일 업로드
        response = requests.put(url, json=payload, headers={'Authorization': f'token {GITHUB_TOKEN}'})
        
        if response.status_code in [200, 201]:
            st.success(f"데이터가 GitHub에 저장되었습니다: {file_path}")
        else:
            st.error(f"GitHub에 데이터 저장 중 오류 발생: {response.json()}")
    except Exception as e:
        st.error(f"GitHub에 데이터 저장 중 오류 발생: {e}")

# GitHub에서 데이터 불러오기
def load_data_from_github(date):
    """
    Load lightning data from GitHub for a specific date.

    :param date: The date for which to load data
    :return: A list of lightning data items, or an empty list if the file doesn't exist or loading fails
    """
    try:
        # GitHub API URL 설정
        folder_name = date.strftime('%Y/%m/%d')
        file_path = f"lightning/{folder_name}/lightning_data.xml"
        url = f"https://api.github.com/repos/{REPO_NAME}/contents/{file_path}"

        # GitHub에서 파일 가져오기
        response = requests.get(url, headers={'Authorization': f'token {GITHUB_TOKEN}'})
        
        if response.status_code == 200:
            file_content = response.json()['content']
            decoded_content = base64.b64decode(file_content).decode('utf-8')

            # XML 파싱
            root = ET.fromstring(decoded_content)
            return root.findall('.//item')
        else:
            st.warning(f"해당 날짜의 파일이 존재하지 않습니다: {response.json().get('message', 'Unknown error')}")
            return []
    except Exception as e:
        st.error(f"GitHub에서 데이터 불러오기 중 오류 발생: {e}")
        return []

# 낙뢰 데이터 지도 생성
def create_lightning_map(data):
    """
    Create a map with markers for each lightning event.

    :param data: The lightning data to be displayed on the map
    :return: A folium Map object
    """
    m = folium.Map(location=YEONGJONG_CENTER, zoom_start=12)
    marker_cluster = MarkerCluster().add_to(m)

    folium.Polygon(
        locations=YEONGJONG_BOUNDARY,
        color="red",
        fill=True,
        fillColor="red",
        fillOpacity=0.1
    ).add_to(m)

    for item in data:
        lat = float(item.find('wgs84Lat').text)
        lon = float(item.find('wgs84Lon').text)

        # Check if the point is within Yeongjongdo's boundary
        point = Point(lon, lat)
        if not yeongjong_polygon.contains(point):
            continue

        datetime_str = item.find('dateTime').text
        datetime_obj = datetime.strptime(datetime_str, "%Y%m%d%H%M%S")
        formatted_time = datetime_obj.strftime('%Y-%m-%d %H:%M:%S')

        # Create a popup with information about the lightning strike
        popup_text = f"Time: {formatted_time}"
        folium.Marker(
            location=(lat, lon),
            popup=popup_text,
            icon=folium.Icon(icon="flash", prefix="fa", color="orange")
        ).add_to(marker_cluster)

    return m

# 시간별 낙뢰 횟수 차트 생성
def create_lightning_chart(data):
    """
    Create a bar chart displaying the count of lightning occurrences by hour.

    :param data: The lightning data used for generating the chart
    :return: An Altair chart object
    """
    hourly_data = {}
    for hour in range(24):
        count = 0
        for item in data:
            item_time = parse_datetime(item)
            if item_time and item_time.hour == hour:
                lat = float(item.find('wgs84Lat').text)
                lon = float(item.find('wgs84Lon').text)
                if yeongjong_polygon.contains(Point(lon, lat)):
                    count += 1
        hourly_data[hour] = count

    if sum(hourly_data.values()) > 0:
        df = pd.DataFrame(list(hourly_data.items()), columns=['Hour', 'Count'])
        chart = alt.Chart(df).mark_bar().encode(
            x='Hour:O',
            y='Count:Q'
        ).properties(
            title=f"{selected_date.strftime('%Y-%m-%d')} 영종도 시간별 낙뢰 횟수"
        )
        return chart
    else:
        st.warning("낙뢰 데이터가 없어 차트를 생성할 수 없습니다.")
        return None

# XML 데이터 파싱 및 오류 처리
def parse_datetime(item):
    """
    Parse the datetime string from an XML item and convert it to a datetime object.

    :param item: An XML element containing the datetime string
    :return: A timezone-aware datetime object, or None if parsing fails
    """
    try:
        datetime_str = item.find('dateTime').text
        return datetime.strptime(datetime_str, "%Y%m%d%H%M%S").replace(tzinfo=korea_tz)
    except (ValueError, AttributeError) as e:
        st.error(f"시간 파싱 오류: {e}")
        return None

# 'All' 또는 시간별 선택
time_selection = st.radio("데이터 표시 방식:", ('All', '시간별'))

# 전역 변수를 사용하여 all_data를 초기화
all_data = []

# 데이터 필터링
filtered_data = None
if time_selection == 'All':
    all_data = get_all_lightning_data(selected_date)
    filtered_data = all_data
else:
    all_data = get_all_lightning_data(selected_date)
    lightning_times = sorted(set([parse_datetime(item) for item in all_data if parse_datetime(item)]))

    def round_to_nearest_ten_minutes(dt):
        discard = timedelta(minutes=dt.minute % 10, seconds=dt.second, microseconds=dt.microsecond)
        dt -= discard
        if discard >= timedelta(minutes=5):
            dt += timedelta(minutes=10)
        return dt

    rounded_times = [round_to_nearest_ten_minutes(t) for t in lightning_times]
    rounded_times = sorted(set(rounded_times))

    selected_time = st.selectbox("시간을 선택하세요", rounded_times, format_func=lambda x: x.strftime("%H:%M"))

    filtered_data = [
        item for item in all_data
        if parse_datetime(item) and abs((parse_datetime(item) - selected_time).total_seconds()) < 600
    ]

# 데이터 로딩 상태
data_load_state = st.text('데이터를 불러오는 중...')
if time_selection == 'All':
    all_data = get_all_lightning_data(selected_date)
data_load_state.text('데이터 로딩 완료!')

import traceback

def comprehensive_debug():
    try:
        st.write("디버깅을 시작합니다.")
        
        st.write("1. API 키 확인")
        st.write(f"API_KEY: {API_KEY[:5]}...{API_KEY[-5:]}")  # API 키의 일부만 표시
        
        st.write("2. 현재 시간 확인")
        now = datetime.now(korea_tz)
        datetime_str = now.strftime("%Y%m%d%H%M")
        st.write(f"현재 시간: {now}, API 요청 시간 문자열: {datetime_str}")
        
        st.write("3. API 요청 시작")
        params = {
            'serviceKey': API_KEY,
            'numOfRows': '1000',
            'pageNo': '1',
            'lgtType': '1',
            'dateTime': datetime_str
        }
        response = requests.get(API_URL, params=params)
        st.write(f"API 응답 상태 코드: {response.status_code}")
        st.write(f"API 응답 내용 (처음 500자): {response.content[:500]}")
        
        st.write("4. XML 파싱")
        root = ET.fromstring(response.content)
        items = root.findall('.//item')
        st.write(f"파싱된 항목 수: {len(items)}")
        
        if len(items) > 0:
            st.write("5. 첫 번째 항목의 내용:")
            for elem in items[0]:
                st.write(f"{elem.tag}: {elem.text}")
        
        st.write("6. 데이터 필터링")
        filtered_data = [
            item for item in items
            if yeongjong_polygon.contains(Point(float(item.find('wgs84Lon').text), float(item.find('wgs84Lat').text)))
        ]
        st.write(f"필터링 후 항목 수: {len(filtered_data)}")
        
        st.write("7. 지도 생성")
        lightning_map = create_lightning_map(filtered_data)
        st_folium(lightning_map, width=700, height=500)
        
        st.write("8. 차트 생성")
        lightning_chart = create_lightning_chart(filtered_data)
        if lightning_chart:
            st.altair_chart(lightning_chart, use_container_width=True)
        else:
            st.warning("차트를 생성할 데이터가 없습니다.")
        
        st.write("디버깅이 완료되었습니다.")
    
    except Exception as e:
        st.error(f"오류 발생: {str(e)}")
        st.write("상세 오류 정보:")
        st.code(traceback.format_exc())

if st.button("종합 디버그 실행"):
    comprehensive_debug()
    
# 버튼 및 동작
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("실시간 데이터 불러오기"):
        # 실시간 데이터 가져오기 및 GitHub에 저장
        all_data = get_all_lightning_data(selected_date)
        save_data_to_github(all_data, selected_date)
        # 지도 생성 및 표시
        lightning_map = create_lightning_map(all_data)
        st_folium(lightning_map, width=700, height=500)

        # 낙뢰 횟수 차트 생성 및 표시
        lightning_chart = create_lightning_chart(all_data)
        if lightning_chart:
            st.altair_chart(lightning_chart, use_container_width=True)

with col2:
    if st.button("일일 데이터(현재까지) 저장"):
        # 현재까지의 데이터를 GitHub에 저장 (이미 파일이 존재하면 덮어쓰기)
        all_data = get_all_lightning_data(selected_date)
        save_data_to_github(all_data, selected_date)

with col3:
    if st.button("데이터 불러오기"):
        # GitHub에서 데이터 불러오기
        data = load_data_from_github(selected_date)

        if data:
            # 지도 생성 및 표시
            lightning_map = create_lightning_map(data)
            st_folium(lightning_map, width=700, height=500)

            # 낙뢰 횟수 차트 생성 및 표시
            lightning_chart = create_lightning_chart(data)
            if lightning_chart:
                st.altair_chart(lightning_chart, use_container_width=True)

# 지도가 초기 로드 후에 항상 표시되도록 합니다.
if all_data:
    lightning_map = create_lightning_map(all_data)
    st_folium(lightning_map, width=700, height=500)
    lightning_chart = create_lightning_chart(all_data)
    if lightning_chart:
        st.altair_chart(lightning_chart, use_container_width=True)
