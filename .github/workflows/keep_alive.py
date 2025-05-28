# keep_alive.py

import requests

URL = "https://testforcal.streamlit.app"

try:
    response = requests.get(URL, timeout=10)
    print(f"Status code: {response.status_code}")
    if response.status_code == 200:
        print("✅ Streamlit app is up.")
    else:
        print("⚠️ Streamlit app responded but not OK.")
except Exception as e:
    print(f"❌ Failed to reach the app: {e}")
