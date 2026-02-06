import os  # 운영체제(OS)와 상호작용하기 위한 라이브러리 (환경변수 값을 읽어올 때 사용)
import math  # 기본적인 수학 계산을 위한 파이썬 내장 라이브러리
import streamlit as st  # 쉽고 빠르게 웹 애플리케이션을 만들기 위한 Python 프레임워크 (UI/UX 구성의 핵심)
import mysql.connector  # Python 코드와 원격 MySQL 데이터베이스를 연결해주는 커넥터 (SQL 실행 및 데이터 조회)
import pandas as pd  # 데이터 조작 및 분석을 위한 라이브러리 (DB에서 가져온 데이터를 DataFrame 표 형태로 변환)
import folium  # 지리 정보 시각화를 위한 지도 라이브러리 (지도 생성, 마커 표시 등)
from folium.plugins import LocateControl  # 지도 상에 '현재 내 위치 찾기' 버튼 기능을 추가하는 플러그인
from streamlit_folium import st_folium  # Folium으로 만든 지도를 Streamlit 웹 화면에 렌더링(표시)하기 위한 전용 컴포넌트
import streamlit.components.v1 as components  # 커스텀 HTML이나 JavaScript(화면 스크롤 등)를 실행하기 위한 Streamlit 컴포넌트
from math import radians, cos, sin, asin, sqrt  # 두 지점(위도, 경도) 사이의 거리를 계산하는 하버사인(Haversine) 공식에 필요한 수학 함수들
from streamlit_js_eval import get_geolocation  # 웹 브라우저의 GPS API를 호출하여 사용자의 현재 위도/경도를 가져오는 라이브러리
from dotenv import load_dotenv  # .env 파일에 저장된 민감한 정보(DB 비밀번호, API 키 등)를 환경변수로 로드하여 보안을 유지하는 라이브러리

# .env 파일에서 환경 변수(DB 접속 정보 등)를 로드합니다.
load_dotenv()

# -----------------------------------------------------------------------------
# 1. 설정 및 디자인 테마 적용
# -----------------------------------------------------------------------------
# Streamlit 페이지의 기본 설정을 초기화합니다. (브라우저 탭 제목, 아이콘, 레이아웃 등)
st.set_page_config(
    page_title="현대자동차 블루핸즈 찾기",
    page_icon="🚘",
    layout="wide",  # 화면을 넓게 사용
    initial_sidebar_state="expanded",  # 사이드바를 기본적으로 펼침
)

# [CSS] 전체 디자인 커스텀 (폰트, 여백, 카드 스타일, 페이지네이션 정렬 등)
st.markdown("""
<style>
    /* 1. 전체 폰트 및 기본 스타일 설정 (Pretendard 폰트 사용) */
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    html, body, [class*="css"] {
        font-family: 'Pretendard', sans-serif;
    }

    /* 2. 메인 헤더 그라데이션 배너 디자인 */
    .main-header {
        background: linear-gradient(135deg, #002c5f 0%, #0054a6 100%); /* 현대차 브랜드 블루 계열 */
        padding: 2.5rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
        box-shadow: 0 4px 12px rgba(0, 44, 95, 0.15);
    }
    .main-header h1 {
        font-weight: 700;
        margin: 0;
        font-size: 2rem;
        color: white !important;
    }
    .main-header p {
        font-size: 1rem;
        opacity: 0.9;
        margin-top: 0.5rem;
        color: #e0f2fe !important;
    }

    /* 3. 카드형 레이아웃 스타일 (지도, 테이블 등을 감싸는 박스) */
    .stCard {
        background-color: white;
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid #e5e7eb;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
        margin-bottom: 1.5rem;
    }

    /* 4. 버튼 스타일 통일 (검색, 페이징 버튼) */
    div.stButton > button {
        background-color: white;
        color: #374151;
        border: 1px solid #d1d5db;
        border-radius: 6px;
        padding: 0.5rem 1rem;
        font-weight: 600;
        font-size: 14px;
        transition: all 0.2s;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }
    /* 검색 버튼(파란색 강조) 스타일 */
    div[data-testid="column"] button[kind="primary"] {
        background-color: #0054a6;
        color: white;
        border: none;
    }
    div.stButton > button:hover {
        border-color: #0054a6;
        color: #0054a6;
        background-color: #f9fafb;
    }

    /* 5. 페이지네이션 라디오 버튼 컨테이너 (중앙 정렬, 줄바꿈 방지) */
    div[role="radiogroup"] {
        display: flex;
        flex-direction: row;
        flex-wrap: nowrap !important; /* 줄바꿈 절대 금지 */
        justify-content: center;
        align-items: center;
        gap: 6px;
        width: 100%;
    }

    /* 6. 라디오 버튼의 동그라미(Input) 숨기기 */
    div[role="radiogroup"] label > div:first-child { 
        display: none !important; 
    }

    /* 7. 숫자 버튼 스타일 (네모난 버튼 형태) */
    div[role="radiogroup"] label {
        background: white !important;
        border: 1px solid #d1d5db !important;
        border-radius: 6px !important;
        width: 36px !important;  /* 너비 고정 */
        height: 36px !important; /* 높이 고정 */
        padding: 0 !important;
        margin: 0 !important;
        display: flex;
        justify-content: center;
        align-items: center;
        cursor: pointer;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }

    /* 8. 숫자 텍스트 정렬 (Flexbox로 수직/수평 중앙 정렬) - [수정됨: 정중앙 보정] */
    div[role="radiogroup"] label > div {
        color: #4b5563 !important;
        font-size: 14px !important;
        font-weight: 500 !important;
        text-align: center !important;
        width: 100% !important;
        height: 100% !important;

        /* Flexbox로 텍스트 정중앙 배치 */
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;

        margin: 0 !important;
        padding: 0 !important;
        padding-bottom: 1px !important; /* 미세 조정: 폰트 베이스라인 보정 */
        line-height: normal !important;
    }

    /* 9. 마우스 올렸을 때 (Hover) */
    div[role="radiogroup"] label:hover {
        border-color: #0054a6 !important;
        color: #0054a6 !important;
        background-color: #f0f7ff !important;
    }

    /* 10. 선택된 버튼 스타일 (Active) */
    div[role="radiogroup"] label[data-baseweb="radio"] {
        background-color: #0054a6 !important;
        border-color: #0054a6 !important;
    }
    div[role="radiogroup"] label[data-baseweb="radio"] > div {
        color: white !important;
        font-weight: 700 !important;
    }

    /* 11. 좌우 이동 버튼 높이 맞춤 */
    div[data-testid="column"] .stButton button {
        height: 36px !important;
        min-height: 36px !important;
        padding: 0px 12px !important;
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
    }

    /* 12. 사이드바 너비 고정 */
    section[data-testid="stSidebar"] {
        width: 350px !important;
        min-width: 350px !important;
        max-width: 350px !important;
    }
</style>
""", unsafe_allow_html=True)

# 필터 옵션 정의: DB 컬럼명(key)과 화면에 보여줄 텍스트(value) 매핑
FILTER_OPTIONS = {
    "is_ev": "⚡ 전기차 전담",
    "is_hydrogen": "💧 수소차 전담",
    "is_frame": "🔨 판금/차체 수리",
    "is_cs_excellent": "🏆 우수 협력점",
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

# 최근 클릭한 센터(최대 5개) 저장
if "clicked_centers" not in st.session_state:
    st.session_state.clicked_centers = {}  # {bluehands_id: {"id":.., "name":.., "count":..}}

if "last_click_key" not in st.session_state:
    st.session_state.last_click_key = None



# -----------------------------------------------------------------------------
# 2. 헬퍼 함수 정의
# -----------------------------------------------------------------------------

def get_conn():
    """DB 연결 객체를 생성하여 반환합니다."""
    return mysql.connector.connect(**DB_CONFIG)


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
    js = """<script>setTimeout(function(){window.parent.scrollTo({top: 500, behavior:'smooth'});}, 300);</script>"""
    components.html(js, height=0)


def _service_text_from_row(row: dict) -> str:
    """
    DB에서 가져온 행(row) 데이터 중 값이 1인 필터 항목만 추출하여
    화면에 보여줄 HTML 배지 형태로 변환합니다. (디자인 개선됨)
    """
    labels = [label for col, label in FILTER_OPTIONS.items() if row.get(col) == 1]
    # 깔끔한 배지 스타일 적용
    return "".join([
                       f'<span class="badge" style="display:inline-block; background:#eff6ff; color:#1e40af; padding:2px 8px; border-radius:9999px; font-size:11px; font-weight:600; margin:2px; border:1px solid #dbeafe;">{l}</span>'
                       for l in labels])


def format_services_html(row):
    """지도 마커의 팝업에 표시할 서비스 배지 HTML 생성"""
    badges = ""
    for col, label in FILTER_OPTIONS.items():
        if row.get(col) == 1:
            badges += f'<span style="background:#f0f7ff; color:#0054a6; padding:3px 6px; border-radius:4px; font-size:11px; margin-right:4px; border:1px solid #cce4ff; font-weight:600;">{label}</span>'
    return f'<div style="margin-top:8px; line-height:1.6;">{badges}</div>' if badges else ""


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

        # 사용자 위치가 있으면 거리 계산하여 표시 -> 하버사인 이용
        dist_str = "⚠️ 권한 필요"
        if user_lat and user_lng:
            d = haversine(user_lng, user_lat, lng, lat)
            if d is not None: dist_str = f"🚶 {int(d * 1000)}m" if d < 1 else f"내 위치로부터 🚗 {d:.1f}km"

        # 팝업 내용 구성 (HTML)
        services_html = format_services_html(row)
        html = f"""
        <div style="width:240px; font-family:'Pretendard', sans-serif;">
            <h4 style="margin:0; color:#0054a6; font-size:16px;">{name}</h4>
            <p style="font-size:12px; margin:5px 0; color:#555;">{addr}</p>
            {services_html}
            <p style="font-size:13px; margin:8px 0; color:#333; font-weight:bold;">📞 {phone}</p>
            <div style="border-top:1px solid #eee; padding-top:5px; margin-top:5px;">
                <span style="color:#e11d48; font-weight:bold; font-size:12px;">{dist_str}</span>
            </div>
        </div>
        """
        # 마커 추가: 아이콘은 자동차 모양, 색상은 파란색
        folium.Marker([lat, lng], popup=folium.Popup(html, max_width=300), tooltip=name,
                      icon=folium.Icon(color="blue", icon="car", prefix="fa")).add_to(fg)
    fg.add_to(m)


# -----------------------------------------------------------------------------
# 3. 테이블 및 페이지네이션 렌더링 함수 (디자인 및 정렬 개선됨)
# -----------------------------------------------------------------------------

def render_hy_table_page(rows_page: list[dict]):
    """
    데이터 리스트를 받아 HTML 테이블 형태로 렌더링하는 함수입니다.
    CSS를 사용하여 깔끔하고 현대적인 테이블 디자인을 적용했습니다.
    [수정] 모든 컬럼의 텍스트를 가운데 정렬(text-align: center)로 변경했습니다.
    """
    # 테이블 디자인 (CSS)
    css = """
    <style>
      table.hy { 
        width:100%; border-collapse:separate; border-spacing:0; 
        border:1px solid #e5e7eb; border-radius:8px; overflow:hidden; 
        margin-bottom: 10px;
      }
      table.hy thead th {
        background:#f3f4f6; color:#1f2937; padding:14px 12px; text-align:center;
        font-weight:700; font-size:15px; border-bottom:1px solid #e5e7eb;
      }
      table.hy tbody td {
        border-bottom:1px solid #f3f4f6; padding:14px 12px; vertical-align:middle;
        font-size:14px; color:#4b5563; background:#fff;
      }
      table.hy tbody tr:last-child td { border-bottom: none; }

      /* [수정] 모든 컬럼 text-align: center 적용 */
      .c-name { width:20%; font-weight:700; color:#111827; text-align:center; }
      .c-addr { width:45%; text-align:left; line-height:1.4; } /* 주소는 길어서 왼쪽 정렬 유지 */
      .c-phone { width:15%; text-align:center; color:#0054a6; font-weight:600; }
      .c-svc { width:20%; text-align:center; } /* [수정] 서비스 옵션도 가운데 정렬 */

      .muted { color:#9ca3af; font-size:13px; text-align:center; display:block; }
    </style>
    """

    def s(x):
        return "" if x is None else str(x)

    trs = []
    for r in rows_page:
        name = s(r.get("name"))
        addr = s(r.get("address"))
        phone = s(r.get("phone"))
        svc_html = _service_text_from_row(r)
        if not svc_html: svc_html = '<span class="muted">-</span>'

        trs.append(f"""
          <tr>
            <td class="c-name">{name}</td>
            <td class="c-addr">{addr}</td>
            <td class="c-phone">{phone}</td>
            <td class="c-svc">{svc_html}</td>
          </tr>
        """)

    html = f"""
    {css}
    <table class="hy">
      <thead>
        <tr>
          <th>지점명</th>
          <th>주소</th>
          <th>전화번호</th>
          <th>서비스 옵션</th>
        </tr>
      </thead>
      <tbody>
        {''.join(trs) if trs else '<tr><td colspan="4" style="text-align:center;padding:20px;">검색 결과가 없습니다.</td></tr>'}
      </tbody>
    </table>
    """
    # Streamlit 컴포넌트로 HTML 렌더링 (높이는 데이터 개수에 따라 자동 조절)
    components.html(html, height=80 + 70 * max(1, len(rows_page)), scrolling=False)


def render_paginated_table(rows_all: list[dict]):
    """
    [디자인 최종_완성]
    - 양옆 여백을 줄여 버튼 사라짐 현상 해결
    - 버튼과 숫자의 높이/색상을 통일하여 난잡해 보이지 않게 함
    """
    # 1. 페이지 계산 로직
    total = len(rows_all)
    total_pages = max(1, math.ceil(total / PAGE_SIZE))

    if "page" not in st.session_state:
        st.session_state.page = 1

    st.session_state.page = max(1, min(st.session_state.page, total_pages))
    page_now = st.session_state.page

    # 2. 데이터 슬라이싱 및 테이블 출력
    start_idx = (page_now - 1) * PAGE_SIZE
    end_idx = start_idx + PAGE_SIZE

    # 카드형 컨테이너 안에 테이블 렌더링
    render_hy_table_page(rows_all[start_idx:end_idx])
    st.markdown('</div>', unsafe_allow_html=True)

    # 3. 10개 단위 블록 계산
    block_size = 10
    current_block = (page_now - 1) // block_size
    start_page = current_block * block_size + 1
    end_page = min(start_page + block_size - 1, total_pages)

    options = list(range(start_page, end_page + 1))

    try:
        current_index = options.index(page_now)
    except ValueError:
        current_index = 0
        st.session_state.page = options[0]

    # 4. UI 그리기: [공백(3)] [◀(1)] [숫자영역(6)] [▶(1)] [공백(3)]
    # - 양옆 공백을 줄여서(3), 버튼이 들어갈 공간(1)을 확실히 보장함
    st.write("")

    # 페이지 정보 텍스트 (가운데 정렬)
    from_idx = start_idx + 1
    to_idx = min(end_idx, total)
    st.markdown(
        f'<p style="text-align: center; color: #6b7280; font-size: 0.85rem; margin-bottom: 8px;">'
        f'총 {total}건 중 {from_idx}~{to_idx} (Page {page_now}/{total_pages})</p>',
        unsafe_allow_html=True,
    )

    # 안전한 비율로 컬럼 생성 (버튼 사라짐 방지)
    _, col_prev, col_radio, col_next, _ = st.columns([3, 1, 6, 1, 3], gap="small", vertical_alignment="center")

    # (A) [◀] 버튼
    with col_prev:
        if start_page > 1:
            if st.button("◀", key="prev_btn", use_container_width=True):
                st.session_state.page = start_page - 1
                st.rerun()

    # (B) 페이지 번호 (라디오 버튼)
    with col_radio:
        selected = st.radio(
            label="페이지 이동",
            options=options,
            index=current_index,
            horizontal=True,
            label_visibility="collapsed",
            key="page_radio",
        )

    # (C) [▶] 버튼
    with col_next:
        if end_page < total_pages:
            if st.button("▶", key="next_btn", use_container_width=True):
                st.session_state.page = end_page + 1
                st.rerun()

    # 5. 페이지 변경 시 실행
    if selected != page_now:
        st.session_state.page = selected
        st.rerun()


# -----------------------------------------------------------------------------
# 4. DB 조회 함수
# -----------------------------------------------------------------------------
@st.cache_data(ttl=3600)  # 1시간 동안 캐시 유지 (지역 목록은 잘 안 바뀌므로)
def get_regions():
    """DB에서 지역(시/도) 목록을 가져옵니다."""
    conn = None
    try:
        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM bluehands_db.regions ORDER BY id")
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

def find_clicked_center_by_latlng(clicked_lat, clicked_lng, rows, tol=1e-6):
    """
    st_folium이 준 클릭좌표(clicked_lat/lng)를 rows(data_list) 안의 지점과 매칭.
    - 정확히 같으면 바로 매칭
    - 아니면 가장 가까운(거리 최소) 지점 선택
    """
    if clicked_lat is None or clicked_lng is None:
        return None

    best = None
    best_d = float("inf")

    for r in rows:
        try:
            lat = float(r.get("latitude"))
            lng = float(r.get("longitude"))
        except:
            continue

        # (1) 거의 동일 좌표면 즉시 매칭
        if abs(lat - clicked_lat) < tol and abs(lng - clicked_lng) < tol:
            return r

        # (2) 아니면 가장 가까운 것 선택 (단순 제곱거리)
        d = (lat - clicked_lat) ** 2 + (lng - clicked_lng) ** 2
        if d < best_d:
            best_d = d
            best = r

    return best
# -----------------------------------------------------------------------------
# 5. 메인 UI 구성
# -----------------------------------------------------------------------------
# 상단 타이틀 배너 (HTML + CSS 디자인 적용)
st.markdown("""
<div class="main-header">
    <h1>🚘 현대자동차 블루핸즈 찾기</h1>
    <p>내 주변 가까운 서비스 네트워크를 쉽고 빠르게 검색하세요</p>
</div>
""", unsafe_allow_html=True)

# (1) GPS 확인 로직
# 브라우저의 Geolocation API를 사용하여 현재 위치 좌표 획득
# [수정] duplicate key 에러 해결을 위해 key 파라미터를 'component_key'로 변경
loc = get_geolocation(component_key="main_geolocation")
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
    col1, col2 = st.columns([3, 1])  # 비율 조정
    with col1:
        # 지역 선택 여부에 따라 placeholder 텍스트 변경
        placeholder_text = f"'{selected_region}' 내 검색" if selected_region != "(전체)" else "지점명 또는 주소"
        search_query = st.text_input("검색어 입력", placeholder=placeholder_text, key="main_search",
                                     label_visibility="collapsed")

    with col2:
        # 검색 버튼 클릭 시 스크롤 이동
        if st.button("검색", type="primary", use_container_width=True):  # Primary 타입으로 강조
            if search_query: scroll_down()


# -----------------------------
# 📌 많이 클릭한 센터 TOP 5 (검색창 아래에 고정 표시)
# - st_folium 클릭 이벤트는 아래쪽(지도 렌더링 이후)에서 처리되므로,
#   여기서는 placeholder를 만들어두고, 클릭 처리 후 같은 placeholder를 다시 그려서 '즉시' 갱신합니다.
# -----------------------------
    top5_placeholder = st.empty()

    def render_top5(ph):
        with ph.container():
            st.write("---")
            st.markdown("### 📌 많이 클릭한 센터 TOP 5")

            if not st.session_state.clicked_centers:
                st.caption("지도에서 핀을 클릭하면 여기에 표시됩니다.")
                return

            sorted_centers = sorted(
                st.session_state.clicked_centers.values(),
                key=lambda x: x.get("count", 0),
                reverse=True
            )

            top5 = sorted_centers[:5]
            for i, item in enumerate(top5, 1):
                st.write(f"{i}. {item.get('name', '지점')} ({item.get('count', 0)}회)")

    # 첫 렌더 (클릭 처리 전 상태)
    render_top5(top5_placeholder)



# (4) 결과 조회 및 화면 표시
# 검색어, 필터, 지역 선택 중 하나라도 있으면 검색 실행
should_search = search_query or selected_service_cols or (selected_region != "(전체)")

if should_search:
    # DB 조회 실행
    data_list = get_bluehands_data(search_query, selected_service_cols, selected_region)

    if not data_list:
        st.error("조건에 맞는 검색 결과가 없습니다.")
    else:
        st.markdown(f"##### 🏢 검색 결과: **{len(data_list)}**개의 지점을 찾았습니다.")

    # [지도 중심 좌표 설정 로직]
    # 수정된 우선순위: 1. 검색 결과 첫 번째 지점 -> 2. 사용자 위치 -> 3. 강남역(기본값)
    map_center = [37.4979, 127.0276]  # 3순위: 기본값 (강남역)

    # 1순위 체크: 검색된 데이터(data_list)가 있고 위/경도 정보가 존재하는 경우
    if data_list and data_list[0].get('latitude'):
        try:
            # 첫 번째 검색 결과의 좌표를 실수형으로 변환하여 중심점으로 설정
            map_center = [float(data_list[0]['latitude']), float(data_list[0]['longitude'])]
        except (ValueError, TypeError):
            # 만약 좌표 데이터가 손상되어 변환 실패 시, 사용자 위치가 있다면 사용 (2순위)
            if user_lat:
                map_center = [user_lat, user_lng]

    # 2순위 체크: 검색 결과가 없거나 좌표가 없을 때, 사용자 위치가 있다면 중심으로 설정
    elif user_lat:
        map_center = [user_lat, user_lng]

    # 지도 생성 및 마커 추가 (카드형 컨테이너 적용)
    m = folium.Map(location=map_center, zoom_start=13)
    LocateControl().add_to(m)  # 현재 위치 찾기 버튼 추가

    # 사용자 위치가 있으면 빨간색 사람 아이콘 마커 표시
    if user_lat: folium.Marker([user_lat, user_lng], icon=folium.Icon(color="red", icon="user", prefix="fa")).add_to(m)

    # 검색된 지점 마커 표시
    if data_list: add_markers_to_map(m, data_list, user_lat, user_lng)

    # Streamlit에 지도 렌더링
    map_out = st_folium(m, height=500, use_container_width=True)

    # ✅ 핀 클릭했을 때 처리
    clicked = map_out.get("last_object_clicked")  # {"lat":.., "lng":..} 형태로 들어옴
    if clicked and data_list:
        clicked_lat = clicked.get("lat")
        clicked_lng = clicked.get("lng")

        center_row = find_clicked_center_by_latlng(clicked_lat, clicked_lng, data_list)
        if center_row:
            cid = center_row.get("id")
            cname = center_row.get("name", "지점")

            # 중복이면 기존 항목 제거 후 맨 앞에 재삽입 (다빈도 클릭 우선)
            if cid not in st.session_state. clicked_centers:
                st.session_state.clicked_centers[cid] = {
                    "id": cid,
                    "name": cname,
                    "count": 1
                }
            else:
                st.session_state.clicked_centers[cid]["count"] += 1
            # ✅ TOP5 즉시 갱신
            render_top5(top5_placeholder)


    # 하단에 페이징된 테이블 표시 (함수 내부에서 stCard 적용됨)
    if data_list:
        df = pd.DataFrame(data_list)
        render_paginated_table(data_list)
else:
    # 초기 진입 화면 (검색 전)
    st.info("👈 왼쪽 사이드바에서 원하는 지역과 정비 옵션을 선택하거나, 지점명을 검색해보세요.")

    # 초기 화면 지도: 기본 위치(강남역) 보여줌
    m = folium.Map(location=[37.4979, 127.0276], zoom_start=13)
    st_folium(m, height=450, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)



