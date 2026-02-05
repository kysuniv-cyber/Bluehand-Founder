import os
import math
import streamlit as st
import mysql.connector
import pandas as pd
import folium
from folium.plugins import LocateControl
from streamlit_folium import st_folium
import streamlit.components.v1 as components
from math import radians, cos, sin, asin, sqrt
from streamlit_js_eval import get_geolocation
from dotenv import load_dotenv

# .env 파일에서 환경 변수(DB 접속 정보 등)를 로드합니다.
load_dotenv()

# -----------------------------------------------------------------------------
# 1. 설정 및 옵션 정의
# -----------------------------------------------------------------------------
# Streamlit 페이지의 기본 설정을 초기화합니다. (브라우저 탭 제목, 아이콘, 레이아웃 등)
st.set_page_config(
    page_title="블루핸즈 찾기",
    page_icon="🚘",
    layout="wide",  # 화면을 넓게 사용
    initial_sidebar_state="expanded",  # 사이드바를 기본적으로 펼침
)

# 필터 옵션 정의: DB 컬럼명(key)과 화면에 보여줄 텍스트(value) 매핑
FILTER_OPTIONS = {
    "is_ev": "⚡ 전기차 전담",
    "is_hydrogen": "💧 수소차 전담",
    "is_frame": "🔨 판금/차체 수리",
    "is_excellent": "🏆 우수 협력점",
    "is_n_line": "🏎️ N-Line 전담",
}
# SQL 쿼리 작성 시 SELECT 절에 넣기 위해 키값들을 쉼표로 연결한 문자열 생성
FLAG_COLS_SQL = ", ".join(FILTER_OPTIONS.keys())

# 데이터베이스 연결 설정 (환경 변수에서 보안 정보를 가져옴)
DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
    "charset": "utf8mb4",
}

# 한 페이지당 보여줄 목록의 개수 설정
PAGE_SIZE = 5


def _service_text_from_row(row: dict) -> str:
    """
    DB에서 가져온 행(row) 데이터 중 값이 1인 필터 항목만 추출하여
    화면에 보여줄 문자열(예: 전기차 전담 · 우수 협력점)로 변환합니다.
    """
    labels = [label for col, label in FILTER_OPTIONS.items() if row.get(col) == 1]
    return " · ".join(labels)


def render_hy_table_page(rows_page: list[dict]):
    """
    데이터 리스트를 받아 HTML 테이블 형태로 렌더링하는 함수입니다.
    Streamlit 기본 데이터프레임보다 더 예쁜 디자인을 위해 HTML/CSS를 직접 사용합니다.
    """
    # 테이블 스타일 정의 (CSS)
    css = """
    <style>
      table.hy { width:100%; border-collapse:collapse; table-layout:fixed; }
      table.hy thead th{
        background:#0b3b68; color:#fff; padding:12px 10px; text-align:center;
        font-weight:800; border:1px solid #ffffff33; font-size:14px;
      }
      table.hy tbody td{
        border:1px solid #e6e6e6; padding:14px 12px; vertical-align:middle;
        font-size:14px; background:#fff; word-break:break-word;
      }
      .c-name{ width:22%; text-align:center; font-weight:800; }
      .c-addr{ width:48%; text-align:center; }
      .c-phone{ width:15%; text-align:center; }
      .c-svc{ width:15%; text-align:center; }
      .svc{ font-weight:800; color:#0b3b68; }
      .muted{ color:#777; }
    </style>
    """

    def s(x): return "" if x is None else str(x)  # None 값을 빈 문자열로 처리하는 헬퍼

    # 각 행 데이터를 HTML <tr> 태그로 변환
    trs = []
    for r in rows_page:
        name = s(r.get("name"))
        addr = s(r.get("address"))
        phone = s(r.get("phone"))
        svc = _service_text_from_row(r)
        svc_html = f'<span class="svc">{svc}</span>' if svc else '<span class="muted">-</span>'

        trs.append(f"""
          <tr>
            <td class="c-name">{name}</td>
            <td class="c-addr">{addr}</td>
            <td class="c-phone">{phone}</td>
            <td class="c-svc">{svc_html}</td>
          </tr>
        """)

    # 최종 HTML 조립
    html = f"""
    {css}
    <table class="hy">
      <thead>
        <tr>
          <th>업체명</th>
          <th>주소</th>
          <th>전화번호</th>
          <th>서비스 옵션</th>
        </tr>
      </thead>
      <tbody>
        {''.join(trs) if trs else '<tr><td colspan="4" style="text-align:center;padding:16px;">검색 결과가 없습니다.</td></tr>'}
      </tbody>
    </table>
    """
    # Streamlit 컴포넌트로 HTML 렌더링 (높이는 데이터 개수에 따라 자동 조절)
    components.html(html, height=120 + 62 * max(1, len(rows_page)), scrolling=False)


def render_paginated_table(rows_all: list[dict]):
    """
    전체 데이터를 받아 페이지네이션(페이지 나누기) 처리를 하고 테이블을 출력하는 함수입니다.
    """
    total = len(rows_all)
    # 전체 페이지 수 계산 (올림 처리)
    total_pages = max(1, math.ceil(total / PAGE_SIZE))

    # 세션 상태(session_state)에 현재 페이지 번호가 없으면 1로 초기화
    if "page" not in st.session_state:
        st.session_state.page = 1

    # 현재 페이지 번호가 유효 범위를 벗어나지 않도록 보정 (검색 결과가 줄어들었을 때 에러 방지)
    st.session_state.page = max(1, min(st.session_state.page, total_pages))
    page_now = st.session_state.page

    # 현재 페이지에 해당하는 데이터 슬라이싱 (start ~ end)
    start = (page_now - 1) * PAGE_SIZE
    end = start + PAGE_SIZE

    # 슬라이싱된 데이터로 테이블 렌더링 함수 호출
    render_hy_table_page(rows_all[start:end])

    # 페이지 번호 선택 버튼 생성 (라디오 버튼 활용)
    options = list(range(1, total_pages + 1))
    index = options.index(page_now)  # 현재 페이지의 인덱스 찾기

    # UI 레이아웃: 중앙 정렬을 위해 컬럼 분할
    left, center, right = st.columns([1, 2, 1])
    with center:
        selected = st.radio(
            label="",
            options=options,
            index=index,
            horizontal=True,  # 가로로 배치
            key="page_radio",
        )

    # 사용자가 다른 페이지를 선택하면 세션 상태 업데이트 후 화면 리로드(rerun)
    if selected != page_now:
        st.session_state.page = selected
        st.rerun()


def get_conn():
    """DB 연결 객체를 생성하여 반환합니다."""
    return mysql.connector.connect(**DB_CONFIG)


# -----------------------------------------------------------------------------
# 2. 유틸리티 함수
# -----------------------------------------------------------------------------

def haversine(lon1, lat1, lon2, lat2):
    """
    두 지점(위도, 경도) 사이의 거리를 계산하는 하버사인 공식입니다.
    반환 단위: km
    """
    if any(x is None for x in [lon1, lat1, lon2, lat2]): return None
    R = 6371  # 지구 반지름 (km)
    # 각도를 라디안으로 변환
    lon1, lat1, lon2, lat2 = map(radians, [float(lon1), float(lat1), float(lon2), float(lat2)])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    return c * R


def scroll_down():
    """검색 버튼 클릭 시 화면을 아래로 부드럽게 스크롤하는 자바스크립트 실행"""
    js = """<script>setTimeout(function(){window.parent.scrollTo({top: 600, behavior:'smooth'});}, 300);</script>"""
    components.html(js, height=0)


def format_services_html(row):
    """지도 마커의 팝업에 표시할 서비스 배지 HTML 생성"""
    badges = ""
    for col, label in FILTER_OPTIONS.items():
        if row.get(col) == 1:
            badges += f'<span style="background:#e3f2fd; color:#0d47a1; padding:2px 6px; border-radius:4px; font-size:11px; margin-right:4px;">{label}</span>'
    return f'<div style="margin-top:5px;">{badges}</div>' if badges else ""


def add_markers_to_map(m, rows, user_lat=None, user_lng=None):
    """Folium 지도 객체(m)에 검색 결과(rows)를 마커로 추가하는 함수"""
    fg = folium.FeatureGroup(name="검색 결과")
    for row in rows:
        try:
            # 위도, 경도 정보가 없거나 에러 발생 시 건너뜀
            lat, lng = float(row['latitude']), float(row['longitude'])
        except:
            continue

        name = row.get("name", "지점")
        addr = row.get("address", "")
        phone = row.get("phone", "")

        # 사용자 위치가 있으면 거리 계산하여 표시
        dist_str = "⚠️ 권한 필요"
        if user_lat and user_lng:
            d = haversine(user_lng, user_lat, lng, lat)
            if d is not None: dist_str = f"🚶 {int(d * 1000)}m" if d < 1 else f"🚗 {d:.1f}km"

        # 팝업 내용 구성 (HTML)
        services_html = format_services_html(row)
        html = f"""
        <div style="width:240px; font-family:sans-serif;">
            <h4 style="margin:0; color:#0054a6;">{name}</h4>
            <p style="font-size:12px; margin:5px 0;">{addr}</p>
            {services_html}
            <p style="font-size:12px; margin:5px 0; color:blue;">📞 {phone}</p>
            <div style="border-top:1px solid #ddd; padding-top:5px; margin-top:5px;">
                <span style="color:red; font-weight:bold; font-size:13px;">{dist_str}</span>
            </div>
        </div>
        """
        # 마커 추가: 아이콘은 자동차 모양, 색상은 파란색
        folium.Marker([lat, lng], popup=folium.Popup(html, max_width=300), tooltip=name,
                      icon=folium.Icon(color="blue", icon="car", prefix="fa")).add_to(fg)
    fg.add_to(m)


# -----------------------------------------------------------------------------
# 3. DB 조회 함수
# -----------------------------------------------------------------------------
@st.cache_data(ttl=3600)  # 1시간 동안 캐시 유지 (지역 목록은 잘 안 바뀌므로)
def get_regions():
    """DB에서 지역(시/도) 목록을 가져옵니다."""
    conn = None
    try:
        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM regions ORDER BY id")
        return [row[0] for row in cursor.fetchall()]
    except:
        return []
    finally:
        if conn: conn.close()


@st.cache_data(ttl=600)  # 10분 동안 검색 결과 캐시 유지
def get_bluehands_data(search_text, selected_filters, region_filter):
    """조건에 맞는 블루핸즈 지점을 DB에서 검색합니다."""
    conn = None
    try:
        conn = get_conn()
        cursor = conn.cursor(dictionary=True)  # 결과를 딕셔너리 형태로 반환

        # 기본 쿼리: bluehands 테이블과 regions 테이블 조인
        query = f"""
            SELECT a.id, a.name, a.latitude, a.longitude, a.address, a.phone, {FLAG_COLS_SQL}
            FROM bluehands a
            LEFT JOIN regions b ON a.region_id = b.id
        """

        conditions = []  # WHERE 절 조건들을 담을 리스트
        params = []  # SQL 파라미터(값)를 담을 리스트

        # 1. 검색어 조건 (이름 또는 주소에 포함)
        if search_text:
            conditions.append("(a.name LIKE %s OR a.address LIKE %s)")
            ptn = f"%{search_text}%"
            params.extend([ptn, ptn])

        # 2. 서비스 필터 조건 (체크된 항목이 1인 경우)
        if selected_filters:
            for col in selected_filters:
                conditions.append(f"a.{col} = 1")

        # 3. 지역 필터 조건 (전체가 아닌 경우)
        if region_filter and region_filter != "(전체)":
            conditions.append("b.name = %s")
            params.append(region_filter)

        # 조건이 하나라도 있으면 WHERE 절 추가
        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        cursor.execute(query, params)
        return cursor.fetchall()

    except mysql.connector.Error as err:
        st.error(f"❌ SQL 에러: {err}")
        return []
    except Exception as e:
        st.error(f"❌ 기타 에러: {e}")
        return []
    finally:
        if conn: conn.close()


# -----------------------------------------------------------------------------
# 4. 메인 UI 구성
# -----------------------------------------------------------------------------
# 상단 타이틀 배너 (HTML)
st.markdown("""
<div class="main-header" style="background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 50%, #3d7ab5 100%); padding: 2rem; border-radius: 20px; margin-bottom: 2rem; text-align: center; color: white;">
    <h1>🚘 블루핸즈 통합 검색</h1>
</div>
""", unsafe_allow_html=True)

# (1) GPS 확인 로직
# 브라우저의 Geolocation API를 사용하여 현재 위치 좌표 획득
loc = get_geolocation()
user_lat, user_lng = None, None
if loc and 'coords' in loc:
    user_lat, user_lng = loc['coords']['latitude'], loc['coords']['longitude']
    st.success("📍 현재 위치 확인 완료")
else:
    st.warning("⚠️ 위치 권한 대기 중... (기본값: 서울 강남)")

# (2) 사이드바 구성 (검색 필터 및 입력)
with st.sidebar:
    st.header("🔍 검색 필터")

    # 지역 선택 드롭다운
    region_list = get_regions()
    if not region_list:
        region_list = ["서울", "부산", "경기"]  # DB 연결 실패 시 기본값

    selected_region = st.selectbox("🗺️ 지역 선택 (시/도)", ["(전체)"] + region_list)
    st.write("---")

    # 서비스 옵션 멀티 셀렉트
    st.subheader("🛠️ 서비스 옵션")
    selected_labels = st.multiselect("필요한 정비 항목", options=list(FILTER_OPTIONS.values()), default=[])
    # 선택된 라벨을 DB 컬럼명으로 변환
    reverse_map = {v: k for k, v in FILTER_OPTIONS.items()}
    selected_service_cols = [reverse_map[label] for label in selected_labels]

    # (3) 검색어 입력 및 버튼
    col1, col2 = st.columns([4, 1])
    with col1:
        # 지역 선택 여부에 따라 placeholder 텍스트 변경
        placeholder_text = f"'{selected_region}' 내 검색" if selected_region != "(전체)" else "지점명 또는 주소 검색"
        search_query = st.text_input("검색어 입력", placeholder=placeholder_text, key="main_search")

    with col2:
        st.write("")  # 버튼 높이 맞추기용 공백
        st.write("")
        # 검색 버튼 클릭 시 스크롤 이동
        if st.button("검색", use_container_width=True):
            if search_query: scroll_down()

# (4) 결과 조회 및 화면 표시
# 검색어, 필터, 지역 선택 중 하나라도 있으면 검색 실행
should_search = search_query or selected_service_cols or (selected_region != "(전체)")

if should_search:
    # DB 조회 실행
    data_list = get_bluehands_data(search_query, selected_service_cols, selected_region)

    if not data_list:
        st.error("검색 결과가 없습니다.")
    else:
        st.subheader(f"🏢 검색 결과: {len(data_list)}개")

    # 지도 중심 좌표 설정 (우선순위: 사용자 위치 -> 검색 결과 첫 번째 지점 -> 강남역)
    map_center = [37.4979, 127.0276]  # 기본값: 강남역

    if user_lat:
        map_center = [user_lat, user_lng]
    elif data_list and data_list[0].get('latitude'):
        map_center = [float(data_list[0]['latitude']), float(data_list[0]['longitude'])]

    # 지도 생성 및 마커 추가
    m = folium.Map(location=map_center, zoom_start=13)
    LocateControl().add_to(m)  # 현재 위치 찾기 버튼 추가

    # 사용자 위치가 있으면 빨간색 사람 아이콘 마커 표시
    if user_lat: folium.Marker([user_lat, user_lng], icon=folium.Icon(color="red", icon="user", prefix="fa")).add_to(m)

    # 검색된 지점 마커 표시
    if data_list: add_markers_to_map(m, data_list, user_lat, user_lng)

    # Streamlit에 지도 렌더링
    st_folium(m, height=500, use_container_width=True)

    # 하단에 페이징된 테이블 표시
    if data_list:
        df = pd.DataFrame(data_list)
        render_paginated_table(data_list)
else:
    # 초기 진입 화면 (검색 전)
    st.info("👈 왼쪽 상단의 사이드바에서 지역을 선택하거나, 검색어를 입력하세요.")

    # 초기 화면 지도: 기본 위치(강남역) 보여줌
    m = folium.Map(location=[37.4979, 127.0276], zoom_start=13)
    st_folium(m, height=400, use_container_width=True)