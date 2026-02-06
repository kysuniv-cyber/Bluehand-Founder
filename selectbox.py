import streamlit as st
import mysql.connector
import pandas as pd
import re

st.title("📊 시/도 → 구/군 필터링 (주소 기반)")

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="mysql",
    database="bluehands_db",
    charset="utf8mb4"
)

base_where = "a.address IS NOT NULL AND a.address <> ''"

# 시/도 목록
sido_df = pd.read_sql(f"""                                          -- SUBSTRING_INDEX(a.address, ' ', 1)
    SELECT DISTINCT TRIM(SUBSTRING_INDEX(a.address, ' ', 1)) AS sido     -- 문자열을 공백 기준으로 잘라서 앞에서 1개 가져오기   
      FROM bluehands a                                                   -- TRIM: 앞 뒤 공백 제거
     WHERE {base_where}  -- WHERE a.address IS NOT NULL AND a.address <> ''
     ORDER BY sido       -- 주소가 아예 없는 데이터 제외,  주소가 빈 문자열("")인 데이터 제외
""", conn)
sido_options = ["(전체)"] + sido_df["sido"].dropna().tolist() # .dropna: 혹시라도 값이 없는 행(NaN)이 있으면 제거
                                                             # .tolist(): 리스트로 변환
# ✅ 초기값, setdefault:해당 키가 없을 때만 값을 넣어라
st.session_state.setdefault("search_text", "")               # "" 저장 / 이미 있으면 그대로 유지
st.session_state.setdefault("selected_sido", "(전체)")        # "(전체)" / 저장 사용자가 선택한 값 유지
st.session_state.setdefault("selected_gugun", "(전체)")       # "(전체)" / 저장 사용자가 선택한 값 유지

# 버튼 클릭시 돌어거는 함수,  78번 줄
def reset_filters():
    st.session_state["search_text"] = ""
    st.session_state["selected_sido"] = "(전체)"
    st.session_state["selected_gugun"] = "(전체)"

# ---------------------------
# 🔎 검색 텍스트박스
# ---------------------------
search_text = st.text_input(
    "지점명 / 주소 / 지역명 검색",
    key="search_text",
    placeholder="예: 강남 현대 / 분당 현대 / 서울 테헤란로 ..."    #처음에 써 있는 글
).strip()

# ---------------------------
# 셀렉트박스
# ---------------------------
col1, col2 = st.columns(2)

with col1:
    selected_sido = st.selectbox("시/도 선택", sido_options, key="selected_sido")

if selected_sido == "(전체)":
    gugun_options = ["(전체)"]
else:
    gugun_df = pd.read_sql(f"""
        SELECT DISTINCT TRIM(SUBSTRING_INDEX(SUBSTRING_INDEX(a.address, ' ', 2), ' ', -1)) AS gugun 
        -- 주소에서 두번째 단어 추출(ex. 인천광역시 동구에서 동구)
        
          FROM bluehands a
         WHERE {base_where}
           AND TRIM(SUBSTRING_INDEX(a.address, ' ', 1)) = %s
         ORDER BY gugun
    """, conn, params=(selected_sido,))
    gugun_options = ["(전체)"] + gugun_df["gugun"].dropna().tolist()

    if st.session_state.get("selected_gugun") not in gugun_options:
        st.session_state["selected_gugun"] = "(전체)"

with col2:
    selected_gugun = st.selectbox(
        "구/군 선택",
        gugun_options,
        key="selected_gugun",
        disabled=(selected_sido == "(전체)")
    )

st.button("🔄 필터 리셋", on_click=reset_filters)    # 32번 줄

st.write("선택:", selected_sido, ">", selected_gugun, "| 검색:", search_text if search_text else "(없음)")

# ---------------------------
# 조건 만들기 (사용자가 고른 필터를 WHERE 절로 변환하는 단계)
# ---------------------------

# 기본 조건: 주소가 있는 지점만 조회
where_clauses = [base_where]

# SQL의 %s 자리에 실제로 들어갈 값들을 모아두는 리스트
# (SQL 인젝션 방지 + 자동 따옴표 처리)
params = []

# ---------------------------
# 1️⃣ 시/도 필터
# ---------------------------
# 사용자가 "(전체)"가 아닌 특정 시/도를 선택했을 때만 조건 추가
if selected_sido != "(전체)":

    # 주소의 "첫 번째 단어" = 시/도
    # 예: "서울특별시 강남구 테헤란로" → 서울특별시
    where_clauses.append("TRIM(SUBSTRING_INDEX(a.address, ' ', 1)) = %s")

    # 위의 %s 자리에 들어갈 실제 값
    params.append(selected_sido)

    # ---------------------------
    # 2️⃣ 구/군 필터
    # ---------------------------
    # 구/군도 "(전체)"가 아닐 때만 조건 추가
    if selected_gugun != "(전체)":

        # 주소의 "두 번째 단어" = 구/군
        # SUBSTRING_INDEX(a.address, ' ', 2) → "서울특별시 강남구"
        # 다시 거기서 뒤에서 한 단어(-1) → "강남구"
        where_clauses.append(
            "TRIM(SUBSTRING_INDEX(SUBSTRING_INDEX(a.address, ' ', 2), ' ', -1)) = %s"
        )

        # 두 번째 %s에 들어갈 값
        params.append(selected_gugun)

# ---------------------------
# 🔽 이후 단계에서 이렇게 사용됨
# where_sql = " AND ".join(where_clauses)
# → 여러 조건을 AND로 연결해서 최종 WHERE 절 완성
#
# 예시 결과:
# WHERE a.address IS NOT NULL AND a.address <> ''
#   AND TRIM(SUBSTRING_INDEX(a.address, ' ', 1)) = %s
#   AND TRIM(SUBSTRING_INDEX(SUBSTRING_INDEX(a.address, ' ', 2), ' ', -1)) = %s
#
# params = ['서울특별시', '강남구']
# ---------------------------


# ✅ 다단어 AND 검색 (LIKE)
# 예: 사용자가 "강남 현대" 입력하면
# → ["강남", "현대"] 두 단어로 나눔
if search_text:

    # 공백 기준으로 단어 분리
    # r"\s+" = 스페이스 여러 개도 하나로 처리
    tokens = [t for t in re.split(r"\s+", search_text) if t]

    # 각 단어(tok)가
    # 지점명(a.name) OR 주소(a.address) OR 지역명(r.name)
    # 중 하나에라도 포함되어야 함
    # 그리고 단어들 사이 관계는 AND
    for tok in tokens:

        where_clauses.append("""
            (
                a.name LIKE %s OR
                a.address LIKE %s OR
                r.name LIKE %s
            )
        """)

        # LIKE 검색용 와일드카드
        # "%강남%" → 앞뒤에 뭐가 있어도 포함되면 OK
        kw = f"%{tok}%"

        # 위에 %s 3개에 들어갈 실제 값들
        params.extend([kw, kw, kw])


# 지금까지 모은 조건들을 AND로 연결해서
# 최종 WHERE 절 문자열 완성
# 예:
# "a.address IS NOT NULL ... AND a.name LIKE %s AND ..."
where_sql = " AND ".join(where_clauses)


# 최종 실행될 SQL 쿼리
query = f"""
    SELECT a.*, r.name AS region_name, t.name AS type_name
      FROM bluehands a
      JOIN regions r ON a.region_id = r.id      -- 지역 이름 가져오려고 조인
      JOIN service_types t ON a.type_id = t.id  -- 서비스 타입 이름 가져오려고 조인
     WHERE {where_sql}                          -- 위에서 만든 조건들 적용
     ORDER BY a.name                            -- 지점명 가나다순 정렬
     LIMIT 200                                  -- 너무 많으면 느려지니까 200개 제한
"""


# SQL 실행 + 결과를 판다스 DataFrame으로 가져오기
# params 리스트의 값들이 %s 자리에 순서대로 안전하게 들어감
result_df = pd.read_sql(query, conn, params=params)

result_df = pd.read_sql(query, conn, params=params)

st.subheader("조회 결과")
st.dataframe(result_df, use_container_width=True)

conn.close()
