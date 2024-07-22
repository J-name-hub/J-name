import streamlit as st
import requests
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO

# 웹 페이지 URL
page_url = "https://www.weather.go.kr/w/image/lgt.do"

# 웹 페이지를 가져오기 위한 요청
response = requests.get(page_url)
soup = BeautifulSoup(response.content, 'html.parser')

# "낙뢰" 링크를 포함한 <a> 태그를 찾기
lightning_link = soup.find('a', text='낙뢰')

if lightning_link and 'href' in lightning_link.attrs:
    lightning_page_url = 'https://www.weather.go.kr' + lightning_link['href']

    # 낙뢰 페이지에서 이미지 URL 추출
    lightning_page_response = requests.get(lightning_page_url)
    lightning_soup = BeautifulSoup(lightning_page_response.content, 'html.parser')

    # 이 부분은 실제 웹 페이지 구조에 따라 조정이 필요할 수 있습니다.
    img_tag = lightning_soup.find('img')  # 적절한 img 태그 선택
    if img_tag and 'src' in img_tag.attrs:
        image_url = img_tag['src']
        # 절대 URL로 변환 (필요 시)
        if not image_url.startswith('http'):
            image_url = 'https://www.weather.go.kr' + image_url

        # 이미지 가져오기
        img_response = requests.get(image_url)
        image = Image.open(BytesIO(img_response.content))

        # Streamlit 앱에서 이미지 표시
        st.image(image, caption='Korea Weather Lightning Map')
    else:
        st.write("낙뢰 페이지에서 이미지를 찾을 수 없습니다.")
else:
    st.write("낙뢰 링크를 찾을 수 없습니다.")
