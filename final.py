import os  # 운영체제(OS)와 상호작용하기 위한 라이브러리 (환경변수 값을 읽어올 때 사용)
import math  # 기본적인 수학 계산을 위한 파이썬 내장 라이브러리
import streamlit as st  # 웹 애플리케이션 UI 프레임워크
import mysql.connector  # MySQL 연결/쿼리 실행
import folium  # 지도 생성/마커 표시
from folium.plugins import LocateControl  # 현재 위치 버튼
from streamlit_folium import st_folium  # Streamlit에 Folium 지도 렌더링
import streamlit.components.v1 as components  # HTML/JS 실행
from math import radians, cos, sin, asin, sqrt  # 거리 계산(하버사인)
from streamlit_js_eval import get_geolocation  # 브라우저 GPS API 호출
from dotenv import load_dotenv  # .env 로드

# .env 파일에서 환경 변수(DB 접속 정보 등)를 로드합니다.
load_dotenv()

# -----------------------------------------------------------------------------
# 1. 설정 및 디자인 테마 적용
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="현대자동차 블루핸즈 찾기",
    page_icon="🚘",
    layout="wide",
    initial_sidebar_state="expanded",
)

# [CSS] 전체 디자인 커스텀
st.markdown(
    """
<style>
    /* 1. 폰트 설정 (Pretendard) */
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    html, body, [class*="css"] { font-family: 'Pretendard', sans-serif; }

    /* 2. 헤더 디자인 */
    .main-header {
        background: linear-gradient(135deg, #002c5f 0%, #0054a6 100%);
        padding: 2.5rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
        box-shadow: 0 4px 12px rgba(0, 44, 95, 0.15);
    }
    .main-header h1 { font-weight: 700; margin: 0; font-size: 2rem; color: white !important; }
    .main-header p  { font-size: 1rem; opacity: 0.9; margin-top: 0.5rem; color: #e0f2fe !important; }

    /* 3. 카드형 레이아웃 */
    .stCard {
        background-color: white;
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid #e5e7eb;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
        margin-bottom: 1.0rem;
    }

    /* 지도 아래 "검색결과 + 범례" 바 (흰색 고정) */
    .result-bar {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 12px 16px;
        margin-top: 12px;
        margin-bottom: 12px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 12px;
        flex-wrap: nowrap;
        white-space: nowrap;
    }
    .result-left {
        font-weight: 800;
        color: #111827;
        font-size: 16px;
    }
    .legend-row {
        display: flex;
        justify-content: flex-end;
        align-items: center;
        gap: 16px;
        flex-wrap: nowrap;
        white-space: nowrap;
    }
    .legend-item {
        display: flex;
        align-items: center;
        gap: 6px;
        font-weight: 700;
        color: #111827;
        font-size: 14px;
    }
    .legend-pin { width: 16px; height: 16px; display: block; }
    .pin-green { fill: #2E7D32; }
    .pin-blue  { fill: #1565C0; }
    .pin-red   { fill: #C62828; }

    /* 4. 버튼 스타일 통일 */
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

    /* 5. 페이지네이션 라디오 버튼 스타일 */
    div[role="radiogroup"] {
        display: flex;
        flex-direction: row;
        flex-wrap: nowrap !important;
        justify-content: center;
        align-items: center;
        gap: 6px;
        width: auto;
    }
    div[role="radiogroup"] label > div:first-child { display: none !important; }

    div[role="radiogroup"] label {
        background: white !important;
        border: 1px solid #d1d5db !important;
        border-radius: 6px !important;
        width: 36px !important;
        height: 36px !important;
        padding: 0 !important;
        margin: 0 !important;
        display: flex;
        justify-content: center;
        align-items: center;
        cursor: pointer;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }
    div[role="radiogroup"] label > div {
        color: #4b5563 !important;
        font-size: 14px !important;
        font-weight: 500 !important;
        text-align: center !important;
        width: 100% !important;
        height: 100% !important;
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        margin: 0 !important;
        padding: 0 !important;
        padding-bottom: 1px !important;
        line-height: normal !important;
    }
    div[role="radiogroup"] label:hover {
        border-color: #0054a6 !important;
        color: #0054a6 !important;
        background-color: #f0f7ff !important;
    }
    div[role="radiogroup"] label[data-baseweb="radio"] {
        background-color: #0054a6 !important;
        border-color: #0054a6 !important;
    }
    div[role="radiogroup"] label[data-baseweb="radio"] > div {
        color: white !important;
        font-weight: 700 !important;
    }

    /* ---------------------------------------------------------------------
       [핵심] 페이지네이션 "뷰포트(화면) 정중앙" 고정
       - 사이드바 ON/OFF 여부와 무관하게 화면 가운데로 맞춤
       - st.columns로 만들어진 3개 컬럼을 content 폭으로 줄이고 가운데로 모음
    --------------------------------------------------------------------- */

    /* radiogroup(숫자 버튼)이 들어있는 "그 행(stHorizontalBlock)"만 골라서 처리 */
    div[data-testid="stHorizontalBlock"]:has(div[role="radiogroup"]) {
        width: 100vw !important;
        margin-left: calc(50% - 50vw) !important;
        margin-right: calc(50% - 50vw) !important;
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        gap: 12px !important;
        padding-bottom: 20px !important;
    }

    /* 그 행 안의 3개 column을 "늘어나지 않게" 내용 폭으로 줄임 */
    div[data-testid="stHorizontalBlock"]:has(div[role="radiogroup"]) > div[data-testid="column"] {
        flex: 0 0 auto !important;
        width: auto !important;
        min-width: 0 !important;
    }

    /* 페이지네이션 행 안의 ◀ ▶ 버튼만 고정폭으로 */
    div[data-testid="stHorizontalBlock"]:has(div[role="radiogroup"]) div.stButton > button {
        width: 44px !important;
        min-width: 44px !important;
        height: 36px !important;
        min-height: 36px !important;
        padding: 0 !important;
        display: inline-flex !important;
        justify-content: center !important;
        align-items: center !important;
    }

    /* ◀/▶가 없는 경우에도 자리 유지하는 스페이서 */
    .pager-spacer {
        width: 44px;
        height: 36px;
        opacity: 0;  /* 안 보이게 하되 공간은 유지 */
    }

</style>
""",
    unsafe_allow_html=True,
)

# 필터 옵션
FILTER_OPTIONS = {
    "is_ev": "⚡ 전기차 전담",
    "is_hydrogen": "💧 수소차 전담",
    "is_frame": "🔨 판금/차체 수리",
    "is_cs_excellent": "🏆 우수 협력점",
    "is_n_line": "🏎️ N-Line 전담",
}
FLAG_COLS_SQL = ", ".join(FILTER_OPTIONS.keys())

# 범례 HTML (흰 배경에 올릴 거라 다크모드 대응 불필요)
LEGEND_HTML = """
<div class="legend-row">
  <div class="legend-item">
    <svg class="legend-pin pin-green" viewBox="0 0 24 24">
      <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5S10.62 6.5 12 6.5s2.5 1.12 2.5 2.5S13.38 11.5 12 11.5z"/>
    </svg>
    <span>전문 블루핸즈</span>
  </div>
  <div class="legend-item">
    <svg class="legend-pin pin-blue" viewBox="0 0 24 24">
      <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5S10.62 6.5 12 6.5s2.5 1.12 2.5 2.5S13.38 11.5 12 11.5z"/>
    </svg>
    <span>종합 블루핸즈</span>
  </div>
  <div class="legend-item">
    <svg class="legend-pin pin-red" viewBox="0 0 24 24">
      <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5S10.62 6.5 12 6.5s2.5 1.12 2.5 2.5S13.38 11.5 12 11.5z"/>
    </svg>
    <span>하이테크센터</span>
  </div>
</div>
"""

# 꼭 이 규격으로 할겁니다. 확인들 하세요
DB_CONFIG = {
    "host": os.getenv("MYSQL_HOST"),
    "port": int(os.getenv("MYSQL_PORT", "3306")),
    "user": os.getenv("MYSQL_USER"),
    "password": os.getenv("MYSQL_PASSWORD"),
    "database": os.getenv("MYSQL_DB"),
    "charset": "utf8mb4",
}

PAGE_SIZE = 5

# 최근 클릭한 센터(최대 5개) 저장
if "clicked_centers" not in st.session_state:
    st.session_state.clicked_centers = {}  # {bluehands_id: {"id":.., "name":.., "count":..}}

if "last_click_key" not in st.session_state:
    st.session_state.last_click_key = None

# -----------------------------------------------------------------------------
# 2. 헬퍼 함수
# -----------------------------------------------------------------------------
def get_conn():
    return mysql.connector.connect(**DB_CONFIG)

def haversine(lon1, lat1, lon2, lat2):
    if any(x is None for x in [lon1, lat1, lon2, lat2]):
        return None
    R = 6371
    lon1, lat1, lon2, lat2 = map(radians, [float(lon1), float(lat1), float(lon2), float(lat2)])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    return c * R

def scroll_down():
    js = """<script>setTimeout(function(){window.parent.scrollTo({top: 500, behavior:'smooth'});}, 300);</script>"""
    components.html(js, height=0)

def _service_text_from_row(row: dict) -> str:
    labels = [label for col, label in FILTER_OPTIONS.items() if row.get(col) == 1]
    return "".join(
        [
            f'<span class="badge" style="display:inline-block; background:#eff6ff; color:#1e40af; '
            f'padding:2px 8px; border-radius:9999px; font-size:11px; font-weight:600; margin:2px; '
            f'border:1px solid #dbeafe;">{l}</span>'
            for l in labels
        ]
    )

def format_services_html(row):
    badges = ""
    for col, label in FILTER_OPTIONS.items():
        if row.get(col) == 1:
            badges += (
                f'<span style="background:#f0f7ff; color:#0054a6; padding:3px 6px; border-radius:4px; '
                f'font-size:11px; margin-right:4px; border:1px solid #cce4ff; font-weight:600;">{label}</span>'
            )
    return f'<div style="margin-top:8px; line-height:1.6;">{badges}</div>' if badges else ""

def add_markers_to_map(m, rows, user_lat=None, user_lng=None):
    fg = folium.FeatureGroup(name="검색 결과")
    type_color_map = {1: "green", 2: "blue", 3: "red"}

    for row in rows:
        try:
            lat, lng = float(row["latitude"]), float(row["longitude"])
        except Exception:
            continue

        name = row.get("name", "지점")
        addr = row.get("address", "")
        phone = row.get("phone", "")

        # type_id가 문자열로 올 수도 있어서 int 캐스팅
        type_id = row.get("type_id")
        try:
            type_id = int(type_id)
        except Exception:
            type_id = None

        dist_str = "⚠️ 권한 필요"
        if user_lat is not None and user_lng is not None:
            d = haversine(user_lng, user_lat, lng, lat)
            if d is not None:
                dist_str = f"🚶 {int(d * 1000)}m" if d < 1 else f"내 위치로부터 🚗 {d:.1f}km"

        services_html = format_services_html(row)
        pin_color = type_color_map.get(type_id, "gray")

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
        folium.Marker(
            [lat, lng],
            popup=folium.Popup(html, max_width=300),
            tooltip=name,
            icon=folium.Icon(color=pin_color, icon="car", prefix="fa"),
        ).add_to(fg)

    fg.add_to(m)

def render_result_bar(count: int):
    st.markdown(
        f"""
<div class="result-bar">
  <div class="result-left">검색 결과: <b>{count}</b>개의 지점을 찾았습니다.</div>
  <div class="result-right">{LEGEND_HTML}</div>
</div>
""",
        unsafe_allow_html=True,
    )

# -----------------------------------------------------------------------------
# 3. 테이블 및 페이지네이션 렌더링
# -----------------------------------------------------------------------------
def build_hy_table_html(rows_page: list[dict]) -> str:
    css = """
    <style>
      table.hy { width:100%; border-collapse:separate; border-spacing:0; border:1px solid #e5e7eb; border-radius:8px; overflow:hidden; margin:0; table-layout: fixed; }
      table.hy thead th { background:#f3f4f6; color:#1f2937; padding:14px 12px; text-align:center; font-weight:700; font-size:15px; border-bottom:1px solid #e5e7eb; }
      table.hy tbody td { border-bottom:1px solid #f3f4f6; padding:14px 12px; vertical-align:middle; font-size:14px; color:#4b5563; background:#fff; }
      table.hy tbody tr:last-child td { border-bottom: none; }

      .c-name { width:15%; text-align:center; font-weight:700; color:#111827; }
      .c-addr { width:40%; text-align:left; line-height:1.4; word-break: keep-all; }
      .c-phone { width:10%; text-align:center; color:#0054a6; font-weight:600; }
      .c-svc { width:35%; text-align:center; }

      .muted { color:#9ca3af; font-size:13px; text-align:center; display:block; }
    </style>
    """

    def s(x):
        return "" if x is None else str(x)

    trs = ""
    for r in rows_page:
        name = s(r.get("name"))
        addr = s(r.get("address"))
        phone = s(r.get("phone"))
        svc_html = _service_text_from_row(r)
        if not svc_html:
            svc_html = '<span class="muted">-</span>'

        trs += (
            f"<tr>"
            f'<td class="c-name">{name}</td>'
            f'<td class="c-addr">{addr}</td>'
            f'<td class="c-phone">{phone}</td>'
            f'<td class="c-svc">{svc_html}</td>'
            f"</tr>"
        )

    if not trs:
        trs = '<tr><td colspan="4" style="text-align:center;padding:20px;">검색 결과가 없습니다.</td></tr>'

    html = f"""{css}
<table class="hy">
  <thead>
    <tr>
      <th>지점명</th>
      <th>주소</th>
      <th>전화번호</th>
      <th>서비스 옵션</th>
    </tr>
  </thead>
  <tbody>{trs}</tbody>
</table>
"""
    return html

def render_hy_table_page(rows_page: list[dict]):
    # stCard + table을 "한 번의 st.markdown"으로 출력 (불필요한 빈 흰색 블록 방지)
    table_html = build_hy_table_html(rows_page)
    st.markdown(f'<div class="stCard">{table_html}</div>', unsafe_allow_html=True)

def render_paginated_table(rows_all: list[dict]):
    total = len(rows_all)
    total_pages = max(1, math.ceil(total / PAGE_SIZE))

    if "page" not in st.session_state:
        st.session_state.page = 1

    st.session_state.page = max(1, min(st.session_state.page, total_pages))
    page_now = st.session_state.page

    # 테이블 출력
    start_idx = (page_now - 1) * PAGE_SIZE
    end_idx = start_idx + PAGE_SIZE
    render_hy_table_page(rows_all[start_idx:end_idx])

    block_size = 10
    current_block = (page_now - 1) // block_size
    start_page = current_block * block_size + 1
    end_page = min(start_page + block_size - 1, total_pages)
    options = list(range(start_page, end_page + 1))

    try:
        current_index = options.index(page_now)
    except Exception:
        current_index = 0
        st.session_state.page = options[0]

    from_idx = start_idx + 1
    to_idx = min(end_idx, total)
    st.markdown(
        f'<p style="text-align: center; color: #6b7280; font-size: 0.85rem; margin-bottom: 8px;">'
        f"총 {total}건 중 {from_idx}~{to_idx} (Page {page_now}/{total_pages})</p>",
        unsafe_allow_html=True,
    )

    # 페이지네이션 (◀ 숫자 ▶) - 좌/우 버튼이 없을 때도 자리 유지해서 중심 안 흔들리게 함
    has_prev_block = start_page > 1
    has_next_block = end_page < total_pages

    col_prev, col_radio, col_next = st.columns([1, 6, 1], gap="small", vertical_alignment="center")

    with col_prev:
        if has_prev_block:
            if st.button("◀", key="prev_btn", use_container_width=False):
                st.session_state.page = start_page - 1
                st.rerun()
        else:
            # 버튼 없을 때도 폭 유지(시각적 중심 고정)
            st.markdown('<div class="pager-spacer">.</div>', unsafe_allow_html=True)

    with col_radio:
        selected = st.radio(
            label="페이지 이동",
            options=options,
            index=current_index,
            horizontal=True,
            label_visibility="collapsed",
            key="page_radio",
        )

    with col_next:
        if has_next_block:
            if st.button("▶", key="next_btn", use_container_width=False):
                st.session_state.page = end_page + 1
                st.rerun()
        else:
            st.markdown('<div class="pager-spacer">.</div>', unsafe_allow_html=True)

    if selected != page_now:
        st.session_state.page = selected
        st.rerun()

# -----------------------------------------------------------------------------
# 4. DB 조회
# -----------------------------------------------------------------------------
@st.cache_data(ttl=3600)
def get_regions():
    conn = None
    try:
        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM bluehands_db.regions ORDER BY id")
        return [row[0] for row in cursor.fetchall()]
    except Exception:
        return []
    finally:
        if conn:
            conn.close()

@st.cache_data(ttl=600)
def get_bluehands_data(search_text, selected_filters, region_filter):
    conn = None
    try:
        conn = get_conn()
        cursor = conn.cursor(dictionary=True)
        query = (
            f"SELECT a.id, a.type_id, a.name, a.latitude, a.longitude, a.address, a.phone, {FLAG_COLS_SQL} "
            f"FROM bluehands a LEFT JOIN regions b ON a.region_id = b.id"
        )
        conditions, params = [], []

        if search_text:
            conditions.append("(a.name LIKE %s OR a.address LIKE %s)")
            params.extend([f"%{search_text}%", f"%{search_text}%"])

        if selected_filters:
            for col in selected_filters:
                conditions.append(f"a.{col} = 1")

        if region_filter and region_filter != "(전체)":
            conditions.append("b.name = %s")
            params.append(region_filter)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        cursor.execute(query, params)
        return cursor.fetchall()

    except Exception as e:
        st.error(f"DB Error: {e}")
        return []
    finally:
        if conn:
            conn.close()

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
# 5. 메인 UI
# -----------------------------------------------------------------------------
st.markdown(
    """
<div class="main-header">
  <h1>🚘 현대자동차 블루핸즈 찾기</h1>
  <p>내 주변 가까운 서비스 네트워크를 쉽고 빠르게 검색하세요</p>
</div>
""",
    unsafe_allow_html=True,
)

loc = get_geolocation(component_key="main_geolocation")
user_lat, user_lng = None, None
if loc and "coords" in loc:
    user_lat, user_lng = loc["coords"]["latitude"], loc["coords"]["longitude"]
    st.success("📍 현재 위치 확인 완료")
else:
    st.warning("⚠️ 위치 권한 대기 중... (기본값: 서울 강남)")

with st.sidebar:
    st.header("🔍 검색 필터")
    region_list = get_regions() or ["서울", "부산", "경기"]
    selected_region = st.selectbox("🗺️ 지역 선택 (시/도)", ["(전체)"] + region_list)

    st.write("---")
    st.subheader("🛠️ 서비스 옵션")
    selected_labels = st.multiselect("필요한 정비 항목", options=list(FILTER_OPTIONS.values()), default=[])
    reverse_map = {v: k for k, v in FILTER_OPTIONS.items()}
    selected_service_cols = [reverse_map[label] for label in selected_labels]

    col1, col2 = st.columns([3, 1])
    with col1:
        placeholder_text = f"'{selected_region}' 내 검색" if selected_region != "(전체)" else "지점명 또는 주소"
        search_query = st.text_input(
            "검색어 입력",
            placeholder=placeholder_text,
            key="main_search",
            label_visibility="collapsed",
        )
    with col2:
        if st.button("검색", type="primary", use_container_width=True):
            scroll_down()

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

should_search = search_query or selected_service_cols or (selected_region != "(전체)")

if should_search:
    data_list = get_bluehands_data(search_query, selected_service_cols, selected_region)

    if not data_list:
        st.error("조건에 맞는 검색 결과가 없습니다.")

    # 지도 중심 좌표: 1) 검색결과 첫 지점 2) 추가로 사용자 위치 3) 강남역
    map_center = [37.4979, 127.0276]
    if data_list and data_list[0].get("latitude"):
        try:
            map_center = [float(data_list[0]["latitude"]), float(data_list[0]["longitude"])]
        except Exception:
            if user_lat is not None and user_lng is not None:
                map_center = [user_lat, user_lng]
    elif user_lat is not None and user_lng is not None:
        map_center = [user_lat, user_lng]

    m = folium.Map(location=map_center, zoom_start=13)
    LocateControl().add_to(m)

    if user_lat is not None and user_lng is not None:
        folium.Marker(
            [user_lat, user_lng],
            icon=folium.Icon(color="red", icon="user", prefix="fa"),
        ).add_to(m)

    if data_list:
        add_markers_to_map(m, data_list, user_lat, user_lng)

        # Streamlit에 지도 렌더링
        map_out = st_folium(m, height=500, use_container_width=True)

        # ✅ 핀 클릭했을 때 처리
        clicked = map_out.get("last_object_clicked")
        if clicked and data_list:
            clicked_lat = clicked.get("lat")
            clicked_lng = clicked.get("lng")

            # ✅ 같은 클릭(좌표)이 rerun으로 다시 들어오면 무시
            # 소수점 자리수는 너무 길면 흔들릴 수 있어서 반올림해서 키를 만듦
            click_key = (round(clicked_lat, 6), round(clicked_lng, 6))

            if st.session_state.last_click_key != click_key:
                st.session_state.last_click_key = click_key

                center_row = find_clicked_center_by_latlng(clicked_lat, clicked_lng, data_list)
                if center_row:
                    cid = center_row.get("id")
                    cname = center_row.get("name", "지점")

                    if cid not in st.session_state.clicked_centers:
                        st.session_state.clicked_centers[cid] = {"id": cid, "name": cname, "count": 1}
                    else:
                        st.session_state.clicked_centers[cid]["count"] += 1

                    # ✅ TOP5 즉시 갱신
                    render_top5(top5_placeholder)

    # 지도 출력
    st_folium(m, height=500, use_container_width=True)

    # 검색결과 + 범례 (지도 아래 흰색 바)
    if data_list:
        render_result_bar(len(data_list))

    # 테이블 + 페이지네이션
    if data_list:
        render_paginated_table(data_list)

else:
    st.info("👈 왼쪽 사이드바에서 원하는 지역과 정비 옵션을 선택하거나, 지점명을 검색해보세요.")
    m = folium.Map(location=[37.4979, 127.0276], zoom_start=13)
    st_folium(m, height=450, use_container_width=True)


# FAQ HTML/CSS (resource)
st.markdown("---")
faq_css_path = os.path.join(os.path.dirname(__file__), "resource", "faq.css")
if os.path.exists(faq_css_path):
    with open(faq_css_path, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
faq_html_path = os.path.join(os.path.dirname(__file__), "resource", "faq.html")
if os.path.exists(faq_html_path):
    with open(faq_html_path, "r", encoding="utf-8") as f:
        st.markdown(f.read(), unsafe_allow_html=True)