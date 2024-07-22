import streamlit as st
import requests
from PIL import Image
from io import BytesIO

# 외부 웹페이지의 이미지 URL
image_url = "https://www.weather.go.kr/w/image/lgt.do"

# 웹 페이지의 이미지를 가져오기 위한 요청
response = requests.get(image_url)
image = Image.open(BytesIO(response.content))

# Streamlit 앱에서 이미지 표시
st.image(image, caption='Korea Weather Lightning Map')
