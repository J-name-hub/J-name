import streamlit as st
import requests
import folium
from datetime import datetime, timedelta
import json
from streamlit_folium import folium_static

# Streamlit secrets
api_key = st.secrets["api"]["API_KEY"]

# 영종도의 경도 및 위도 경계 정의 (약 15개의 포인트)
yeongjongdo_boundary = [
    (37.479623, 126.411084), (37.476497, 126.415194), (37.471844, 126.417712),
    (37.465057, 126.419517), (37.460584, 126.426742), (37.459110, 126.433967),
    (37.455449, 126.437401), (37.450397, 126.439892), (37.446269, 126.439036),
    (37.442660, 126.436349), (37.439993, 126.429781), (37.439318, 126.423971),
    (37.441231, 126.417712), (37.445185, 126.413259), (37.450054, 126.411273),
    (37.455210, 126.409457), (37.459965, 126.409457), (37.464160, 126.410707)
]

def get_lightning_data(api_key, start_time, end_time):
    data_list = []
    current_time = start_time

    while current_time <= end_time:
        formatted_time = current_time.strftime('%Y%m%d%H%M')
        url = f"http://apis.data.go.kr/1360000/LgtInfoService/getLgt?serviceKey={api_key}&numOfRows=100&pageNo=1&lgtType=1&dateTime={formatted_time}&dataType=JSON"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            st.write(data)  # API로부터 받아온 데이터를 출력
            if 'response' in data and 'body' in data['response'] and 'items' in data['response']['body']:
                data_list.extend(data['response']['body']['items']['item'])
        else:
            st.error("Failed to fetch data from API")
            return None
        current_time += timedelta(minutes=10)

    return data_list

# Streamlit UI
st.title("Yeongjongdo Lightning Tracker")

option = st.selectbox(
    'Select time range',
    ('Last 10 hours', 'Last 24 hours', 'Custom Date')
)

if option == 'Last 10 hours':
    start_time = datetime.now() - timedelta(hours=10)
    end_time = datetime.now()
elif option == 'Last 24 hours':
    start_time = datetime.now() - timedelta(hours=24)
    end_time = datetime.now()
else:
    start_date = st.date_input("Start date", datetime.now() - timedelta(days=1))
    start_time = datetime.combine(start_date, datetime.min.time())
    end_date = st.date_input("End date", datetime.now())
    end_time = datetime.combine(end_date, datetime.max.time())

data = get_lightning_data(api_key, start_time, end_time)

# Folium Map
m = folium.Map(location=[37.471844, 126.417712], zoom_start=13)

# Boundary of Yeongjongdo
folium.Polygon(locations=yeongjongdo_boundary, color='blue', fill=True, fill_opacity=0.2).add_to(m)

# Add lightning data to the map
if data:
    for item in data:
        if 'lat' in item and 'lon' in item:
            folium.Marker(
                location=[item['lat'], item['lon']],
                popup=f"Time: {item['date']}, Strength: {item['str']}",
                icon=folium.Icon(color='red', icon='flash')
            ).add_to(m)
        else:
            st.warning("Missing latitude or longitude in data item")

folium_static(m)
