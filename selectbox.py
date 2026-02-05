import streamlit as st
import mysql.connector
import pandas as pd

st.title("📊 DB 테이블 보기 + 가까운 지점 4곳")

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="mysql",
    database="bluehands_db",
    charset="utf8mb4"
)

# 1) 후보 목록 가져오기
name_list_df = pd.read_sql("""
    SELECT DISTINCT
           a.name AS shop_name,
           b.name AS region_name
      FROM bluehands a
      JOIN `regions` b ON a.`region_id` = b.id
     WHERE a.name IS NOT NULL
     ORDER BY b.name, a.name
     LIMIT 500
""", conn)

options = ["(전체)"] + name_list_df["shop_name"].tolist()

shop_to_label = dict(
    zip(
        name_list_df["shop_name"],
        name_list_df["shop_name"] + " (" + name_list_df["region_name"] + ")"
    )
)

selected_shop = st.selectbox(
    "검색할 지점 선택",
    options,
    format_func=lambda x: x if x == "(전체)" else shop_to_label.get(x, x)
)

st.write("선택:", selected_shop)

# 2) 선택 지점 상세(1개) + 가까운 지점 4개
if selected_shop == "(전체)":
    st.info("특정 지점을 선택하면, 그 지점에서 가까운 지점 4곳을 보여줍니다.")
else:
    # (A) 선택 지점의 좌표/정보 1건 가져오기
    base_df = pd.read_sql("""
        SELECT a.*, b.name AS region_name
          FROM bluehands a
          JOIN `regions` b ON a.`region_id` = b.id
         WHERE a.name = %s
         LIMIT 1
    """, conn, params=(selected_shop,))

    st.subheader("선택 지점")
    st.dataframe(base_df, use_container_width=True)

    if base_df.empty:
        st.warning("선택 지점 정보를 찾지 못했어요.")
    else:
        base_lat = base_df.loc[0, "latitude"]
        base_lng = base_df.loc[0, "longitude"]

        if pd.isna(base_lat) or pd.isna(base_lng):
            st.warning("선택 지점에 위도/경도 값이 없어서 가까운 지점을 계산할 수 없어요.")
        else:
            # (B) 가까운 지점 4곳 (자기 자신 제외)
            near_df = pd.read_sql("""
                SELECT
                    a.id,
                    a.name,
                    b.name AS region_name,
                    a.latitude,
                    a.longitude,
                    ST_Distance_Sphere(
                        POINT(a.longitude, a.latitude),
                        POINT(%s, %s)
                    ) AS distance_m
                FROM bluehands a
                JOIN `regions` b ON a.`region_id` = b.id
                WHERE a.latitude IS NOT NULL
                  AND a.longitude IS NOT NULL
                  AND NOT (a.name = %s AND a.latitude = %s AND a.longitude = %s)
                ORDER BY distance_m
                LIMIT 4
            """, conn, params=(base_lng, base_lat, selected_shop, base_lat, base_lng))

            near_df["distance_km"] = (near_df["distance_m"] / 1000).round(2)

            st.subheader("가까운 지점 4곳")
            st.dataframe(near_df[["name", "region_name", "distance_km"]], use_container_width=True)

conn.close()
