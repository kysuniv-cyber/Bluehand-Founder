import streamlit as st
import mysql.connector
import pandas as pd

st.title("📍 지역 선택 (셀렉트박스 1개)")

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="mysql",
    database="bluehands_db",
    charset="utf8mb4"
)

BASE_WHERE = "address IS NOT NULL AND address <> ''"

# --- rerun 호환 (버전 차이 대응) ---
def do_rerun():
    if hasattr(st, "rerun"):
        st.rerun()
    else:
        st.experimental_rerun()

# --- 세션 초기화 ---
if "mode" not in st.session_state:
    st.session_state.mode = "sido"  # "sido" or "gugun"
if "selected_sido" not in st.session_state:
    st.session_state.selected_sido = None
if "selected_gugun" not in st.session_state:
    st.session_state.selected_gugun = None
if "region_pick" not in st.session_state:
    st.session_state.region_pick = "(전체)"

# --- 데이터 로더 ---
def load_sido():
    df = pd.read_sql(f"""
        SELECT DISTINCT TRIM(SUBSTRING_INDEX(address, ' ', 1)) AS sido
          FROM bluehands
         WHERE {BASE_WHERE}
         ORDER BY sido
    """, conn)
    return ["(전체)"] + df["sido"].dropna().tolist()

def load_gugun(sido: str):
    df = pd.read_sql(f"""
        SELECT DISTINCT TRIM(SUBSTRING_INDEX(SUBSTRING_INDEX(address, ' ', 2), ' ', -1)) AS gugun
          FROM bluehands
         WHERE {BASE_WHERE}
           AND TRIM(SUBSTRING_INDEX(address, ' ', 1)) = %s
         ORDER BY gugun
    """, conn, params=(sido,))
    return ["← 시/도 다시 선택", "(전체)"] + df["gugun"].dropna().tolist()

# --- 선택 변경 시 실행될 콜백 ---
def on_region_change():
    v = st.session_state.region_pick

    if st.session_state.mode == "sido":
        if v == "(전체)":
            st.session_state.selected_sido = None
            st.session_state.selected_gugun = None
            return
        # 시/도 선택 → 구/군 모드로 전환
        st.session_state.selected_sido = v
        st.session_state.mode = "gugun"
        st.session_state.region_pick = "(전체)"
        do_rerun()

    else:  # gugun 모드
        if v == "← 시/도 다시 선택":
            st.session_state.mode = "sido"
            st.session_state.selected_sido = None
            st.session_state.selected_gugun = None
            st.session_state.region_pick = "(전체)"
            do_rerun()
        else:
            st.session_state.selected_gugun = None if v == "(전체)" else v

# --- 옵션 만들기 (모드에 따라 바뀜) ---
if st.session_state.mode == "sido":
    options = load_sido()
    label = "시/도 선택"
else:
    options = load_gugun(st.session_state.selected_sido)
    label = f"{st.session_state.selected_sido} 구/군 선택"

# --- ✅ 셀렉트박스 1개 ---
st.selectbox(
    label,
    options,
    key="region_pick",
    on_change=on_region_change,
)

st.write("선택:", st.session_state.selected_sido, ">", st.session_state.selected_gugun)

conn.close()
