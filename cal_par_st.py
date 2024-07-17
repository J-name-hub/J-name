import streamlit as st
import requests
import folium
from streamlit_folium import folium_static
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET
import certifi

def get_lightning_data(api_key, start_date, end_date):
    url = "https://apis.data.go.kr/1360000/LgtngOccurInfoService/getLgtngOccurInfo"
    params = {
        'serviceKey': api_key,
        'numOfRows': '1000',
        'pageNo': '1',
        'dataType': 'XML',
        'startDt': start_date,
        'endDt': end_date,
        'startHh': '00',
        'endHh': '23'
    }
    try:
        response = requests.get(url, params=params, verify=certifi.where(), timeout=30)
        st.write("API 응답 상태 코드:", response.status_code)
        st.write("API 응답 내용:", response.text)
        
        if response.status_code == 200:
            try:
                root = ET.fromstring(response.content)
                items = root.findall('.//item')
                return [item_to_dict(item) for item in items]
            except ET.ParseError as e:
                st.error(f"XML 파싱 오류: {str(e)}")
                return None
        else:
            st.error(f"API 요청 실패: 상태 코드 {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"요청 중 오류 발생: {str(e)}")
        return None

def item_to_dict(item):
    return {child.tag: child.text for child in item}

def main():
    st.title("영종도 낙뢰 발생 확인")

    # 영종도의 대략적인 좌표
    yeongjeong_lat, yeongjeong_lon = 37.4928, 126.4934

    # API 키 입력
    api_key = st.text_input("기상청 API 키를 입력하세요")

    # 날짜 선택 (오늘 날짜로 고정)
    today = datetime.now().date()
    selected_date = today

    if st.button("낙뢰 정보 조회"):
        if api_key:
            # API 호출
            start_date = selected_date.strftime("%Y%m%d")
            end_date = start_date  # 같은 날짜로 설정
            lightning_data = get_lightning_data(api_key, start_date, end_date)

            if lightning_data is None:
                st.error("API 응답을 처리하는 데 문제가 발생했습니다.")
            elif not lightning_data:
                st.info("해당 기간에 낙뢰 데이터가 없습니다.")
            else:
                # 지도 생성
                m = folium.Map(location=[yeongjeong_lat, yeongjeong_lon], zoom_start=11)

                # 낙뢰 데이터를 지도에 표시
                yeongjeong_strikes = []
                for strike in lightning_data:
                    lat, lon = float(strike['lat']), float(strike['lon'])
                    folium.Marker(
                        [lat, lon],
                        popup=f"낙뢰 발생 시간: {strike.get('occrDt', 'N/A')} {strike.get('occrTm', 'N/A')}",
                        icon=folium.Icon(color='red', icon='bolt', prefix='fa')
                    ).add_to(m)

                    # 영종도 주변 낙뢰 확인
                    if 37.4 <= lat <= 37.6 and 126.3 <= lon <= 126.6:
                        yeongjeong_strikes.append(strike)

                # Streamlit에 지도 표시
                folium_static(m)

                if yeongjeong_strikes:
                    st.warning(f"영종도 주변에서 {len(yeongjeong_strikes)}건의 낙뢰가 발생했습니다.")
                else:
                    st.success("영종도 주변에서 낙뢰 발생이 없습니다.")
        else:
            st.warning("API 키를 입력해주세요.")

if __name__ == "__main__":
    main()