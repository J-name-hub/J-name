import streamlit as st
import requests
import folium
from streamlit_folium import folium_static
from datetime import datetime, timedelta

def get_lightning_data(api_key, start_date, end_date):
    url = "http://apis.data.go.kr/1360000/LgtngOccurInfoService/getLgtngOccurInfo"
    params = {
        'serviceKey': api_key,
        'numOfRows': '1000',
        'pageNo': '1',
        'dataType': 'json',  # 'JSON'에서 'json'으로 변경
        'startDt': start_date,
        'endDt': end_date,
        'startHh': '00',
        'endHh': '23'
    }
    response = requests.get(url, params=params)
    st.write("API 응답 상태 코드:", response.status_code)
    st.write("API 응답 내용:", response.text)
    
    try:
        return response.json()
    except requests.exceptions.JSONDecodeError as e:
        st.error(f"JSON 디코딩 오류: {str(e)}")
        return None

def main():
    st.title("영종도 낙뢰 발생 확인")

    # 영종도의 대략적인 좌표
    yeongjeong_lat, yeongjeong_lon = 37.4928, 126.4934

    # API 키 입력
    api_key = st.text_input("기상청 API 키를 입력하세요")

    # 날짜 선택
    today = datetime.now().date()
    selected_date = st.date_input("날짜를 선택하세요", today)

    if st.button("낙뢰 정보 조회"):
        if api_key:
            # API 호출
            start_date = selected_date.strftime("%Y%m%d")
            end_date = selected_date.strftime("%Y%m%d")  # 같은 날짜로 설정
            lightning_data = get_lightning_data(api_key, start_date, end_date)

            if lightning_data is None:
                st.error("API 응답을 처리하는 데 문제가 발생했습니다.")
            elif 'response' in lightning_data:
                if 'body' in lightning_data['response']:
                    items = lightning_data['response']['body'].get('items', {}).get('item', [])
                    if not items:
                        st.info("해당 기간에 낙뢰 데이터가 없습니다.")
                    else:
                        # 지도 생성
                        m = folium.Map(location=[yeongjeong_lat, yeongjeong_lon], zoom_start=11)

                        # 낙뢰 데이터를 지도에 표시
                        yeongjeong_strikes = []
                        for strike in items:
                            lat, lon = float(strike['lat']), float(strike['lon'])
                            folium.Marker(
                                [lat, lon],
                                popup=f"낙뢰 발생 시간: {strike['occrDt']} {strike['occrTm']}",
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
                    st.error("API 응답에 'body' 데이터가 없습니다.")
            else:
                st.error("API 응답 형식이 올바르지 않습니다.")
        else:
            st.warning("API 키를 입력해주세요.")

if __name__ == "__main__":
    main()