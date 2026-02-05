# 기능 구현
import mysql.connector

import streamlit as st
import folium
from folium.plugins import LocateControl
from streamlit_folium import st_folium


st.title("현재 사용자 위치")

# 사용자 위치 지도 출력
st.set_page_config(layout="centered")

m = folium.Map(location=[37.4974, 126.9277], zoom_start=18) # 임의 위치
folium.plugins.LocateControl(auto_start=True).add_to(m) #선택사항  True 변경지
LocateControl(
    auto_start=False,
    flyTo=True,
    position="topright"
).add_to(m)

st_folium(m, width=1000, height=600)

m = folium.Map([41.97, 2.81])

st.title("서울권 센터")





