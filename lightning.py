import streamlit as st
import folium
from folium.plugins import MarkerCluster
import requests
from streamlit_folium import st_folium
from datetime import datetime, timedelta

# Streamlit secrets에서 API 키 가져오기
API_KEY = st.secrets["api"]["API_KEY"]

# 기상청 낙뢰 API URL
API_URL = "http://apis.data.go.kr/1360000/LgtInfoService/getLgt"

# 대한민국 중심 좌표
korea_center = (36.5, 127.5)

# Streamlit 설정
st.title("대한민국 낙뢰 발생 지도")
st.write("기상청 낙뢰 API를 활용하여 대한민국 전역의 낙뢰 발생 지점을 지도에 표시합니다.")

# 날짜 입력 받기
selected_date = st.date_input("날짜를 선택하세요", datetime.today() - timedelta(days=1))
selected_time = st.time_input("시간을 선택하세요", datetime.now().time())

# 선택한 날짜와 시간을 결합하여 datetime 객체 생성
selected_datetime = datetime.combine(selected_date, selected_time)

# 10분 간격으로 분 조정
selected_minute = selected_datetime.minute // 10 * 10
selected_datetime = selected_datetime.replace(minute=selected_minute, second=0, microsecond=0)
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
            data = response.json()
            return data
        else:
            st.error(f"API 요청 실패: 상태 코드 {response.status_code}")
            st.write(response.text)  # 오류 응답 내용 출력
            return None
        
    except requests.exceptions.RequestException as e:
        st.error(f"API 요청 중 오류 발생: {str(e)}")
        return None
    except ValueError as e:
        st.error(f"JSON 디코딩 오류: {str(e)}")
        st.write(response.text)  # 오류 응답 내용 출력
        return None

# 낙뢰 데이터를 가져와서 필터링
data = get_lightning_data(selected_datetime_str)
if data and 'response' in data and 'body' in data['response']:
    items = data['response']['body']['items']['item']
    
    # 지도 생성
    m = folium.Map(location=korea_center, zoom_start=7)
    marker_cluster = MarkerCluster().add_to(m)
    
    for item in items:
        lat = float(item['lgtLat'])
        lon = float(item['lgtLon'])
        location = (lat, lon)
        
        folium.Marker(
            location=location,
            popup=f"낙뢰 발생 위치: 위도 {lat}, 경도 {lon}",
            icon=folium.Icon(color='red', icon='bolt')
        ).add_to(marker_cluster)
    
    # 지도 출력
    st_folium(m, width=725)
else:
    st.write("낙뢰 데이터를 가져올 수 없습니다.")
