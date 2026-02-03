# 🛠️ Bluehand_Founder
> **내 주변 현대자동차 블루핸즈(Bluehands)를 가장 빠르게 찾는 방법**

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/)
![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=flat&logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green.svg)

---

## 📌 Project Overview
**Bluehand_Founder**는 사용자의 실시간 위치를 기반으로 주변의 현대자동차 블루핸즈 정비소를 찾아주는 웹 서비스입니다. 
단순한 위치 표시를 넘어, 정비 유형(종합/전문)과 상세 연락처 정보를 제공하여 운전자가 상황에 맞는 최적의 정비소를 선택할 수 있도록 돕습니다.

## 🌟 Key Features
* **📍 내 위치 실시간 연동**: `LocateControl`을 통해 현재 위치 주변의 정비소 즉시 파악
* **🔍 정비소 상세 정보**: 전화번호, 주소, 정비 유형(종합/전문) 등 팝업 정보 제공
* **🗺️ 인터랙티브 지도**: Folium 기반의 확대/축소 및 자유로운 지도 탐색
* **📱 최적화된 UI**: Streamlit을 활용한 직관적이고 가벼운 웹 인터페이스

## 🛠 Tech Stack
* **Frontend/Backend**: Streamlit
* **Visualization**: Folium, Streamlit-Folium
* **Data Handling**: Pandas, Geopandas
* **Language**: Python

## 📖 User Scenario
1. **위치 확인**: 사용자가 지도 상의 '내 위치 찾기' 버튼을 클릭합니다.
2. **검색**: 현재 위치 좌표를 기준으로 반경 내 블루핸즈 지점들이 마커로 표시됩니다.
3. **상세 조회**: 마커를 클릭하여 해당 지점이 '종합 블루핸즈'인지 '전문 블루핸즈'인지 확인합니다.
4. **연락**: 제공된 전화번호를 통해 바로 정비 예약을 진행합니다.

## 🚀 Quick Start

### Installation
```bash
git clone [https://github.com/JJonyeok2/Bluehand_Founder.git](https://github.com/JJonyeok2/Bluehand_Founder.git)
cd Bluehand_Founder
pip install -r requirements.txt
