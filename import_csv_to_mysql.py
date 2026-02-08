# File: import_csv_to_mysql.py
# 목적:
#  - bluehands_final_all.csv 를 읽어서
#    regions / service_types / bluehands 테이블에 "정규화"된 형태로 적재한다.
#
# 전제:
#  - pandas를 임포트 해야한다.
#  - CSV는 크롤러 단계에서 이미 전처리 완료(위경도 float, 플래그 0/1)라고 가정한다.
#  - MySQL에 bluehands_db 및 테이블 3개(regions, service_types, bluehands)가 생성되어 있어야 한다.
#
# 주의:
#  - DB 비번을 절대 git에 올리지 말 것(로컬에서만 사용).
#  - 가능하면 환경변수(.env)로 분리하고 .gitignore 처리.

import os
import sys
import re
import pandas as pd
import pymysql

# ===== 사용자 설정(필요시 수정) =====
# 하드코딩 대신 환경변수 우선 사용(로컬에서만 설정)
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "mysql")  # 로컬 테스트용. git 커밋 금지.
MYSQL_DB = os.getenv("MYSQL_DB", "bluehands_db")
CSV_PATH = os.getenv(
    "CSV_PATH",
    r"C:\lecture\_00_bluehands\bluehands_final_all.csv"
)


# ===== CSV 컬럼명(최신 CSV 헤더) =====
COL_REGION = "region"
COL_NAME = "name"
COL_TYPE = "type"
COL_ADDRESS = "address"
COL_PHONE = "phone"
COL_LAT = "latitude"
COL_LNG = "longitude"

COL_IS_EV = "is_ev"
COL_IS_EV_TECH = "is_ev_tech"
COL_IS_HYDROGEN = "is_hydrogen"
COL_IS_FRAME = "is_frame"
COL_IS_AL_FRAME = "is_al_frame"
COL_IS_N_LINE = "is_n_line"
COL_IS_COMMERCIAL_MID = "is_commercial_mid"
COL_IS_COMMERCIAL_BIG = "is_commercial_big"
COL_IS_COMMERCIAL_EV = "is_commercial_ev"
COL_IS_CS_EXCELLENT = "is_cs_excellent"


def die(msg: str) -> None:
    # 목적:
    #  - 더 진행해도 의미가 없는 상황(파일 없음, 헤더 불일치, DB 작업 실패 등)에서 즉시 중단한다.
    print(f"[ERROR] {msg}")
    sys.exit(1)


def connect_mysql():
    # 목적:
    #  - pymysql로 MySQL 연결을 만든다.
    #  - autocommit=False로 두고, 성공 시 commit / 실패 시 rollback으로 안전하게 처리한다.
    return pymysql.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DB,
        charset="utf8mb4",
        autocommit=False,
        cursorclass=pymysql.cursors.DictCursor,
    )


def normalize_str(x):
    # 목적:
    #  - CSV에서 읽은 값 중 None/NaN/빈문자열을 모두 None으로 통일한다.
    #  - 문자열은 좌우 공백을 제거한다.
    if x is None:
        return None
    if isinstance(x, float) and pd.isna(x):
        return None
    s = str(x).strip()
    return s if s != "" else None


def format_phone_kor(x):
    # 목적:
    #  - 전화번호를 "문자열"로 저장하기 위해 하이픈(-)을 넣어준다.
    #  - CSV에서 이미 하이픈이 들어있어도 OK (숫자만 추출 후 재포맷).
    #  - 규칙(대표):
    #     010XXXXXXXX  -> 010-XXXX-XXXX
    #     02XXXXXXXX   -> 02-XXXX-XXXX (또는 02-XXX-XXXX)
    #     0XXYYYYYYYY  -> 0XX-YYY-YYYY (또는 0XX-XXXX-XXXX)
    #  - 매칭이 애매하면 원문(정리된 숫자) 그대로 반환한다.
    s = normalize_str(x)
    if s is None:
        return None

    digits = re.sub(r"[^0-9]", "", s)
    if digits == "":
        return None

    # 휴대폰 010 (11자리)
    if len(digits) == 11 and digits.startswith("010"):
        return f"{digits[0:3]}-{digits[3:7]}-{digits[7:11]}"

    # 서울 02 (9~10자리)
    if digits.startswith("02"):
        if len(digits) == 9:
            return f"{digits[0:2]}-{digits[2:5]}-{digits[5:9]}"
        if len(digits) == 10:
            return f"{digits[0:2]}-{digits[2:6]}-{digits[6:10]}"

    # 그 외 지역번호(보통 3자리) + 국번
    if len(digits) == 10:
        return f"{digits[0:3]}-{digits[3:6]}-{digits[6:10]}"
    if len(digits) == 11:
        return f"{digits[0:3]}-{digits[3:7]}-{digits[7:11]}"

    # 기타(대표번호 1588 등) / 예외 케이스는 숫자만 반환
    return digits


def ensure_required_columns(df: pd.DataFrame):
    # 목적:
    #  - CSV 헤더가 우리가 기대하는 컬럼을 모두 갖고 있는지 검증한다.
    #  - 빠진 컬럼이 있으면 즉시 die()로 중단한다.
    required = [
        COL_REGION, COL_NAME, COL_TYPE,
        COL_ADDRESS, COL_PHONE, COL_LAT, COL_LNG,
        COL_IS_EV, COL_IS_EV_TECH, COL_IS_HYDROGEN,
        COL_IS_FRAME, COL_IS_AL_FRAME, COL_IS_N_LINE,
        COL_IS_COMMERCIAL_MID, COL_IS_COMMERCIAL_BIG,
        COL_IS_COMMERCIAL_EV, COL_IS_CS_EXCELLENT
    ]

    missing = [c for c in required if c not in df.columns]
    if missing:
        die(
            "CSV 헤더에 필요한 컬럼이 없습니다: "
            f"{missing}\n현재 헤더: {list(df.columns)}"
        )


def insert_dim_table(cur, table_name: str, values: list[str]):
    # 목적:
    #  - regions/service_types 같은 차원 테이블에 unique 값들을 넣는다.
    # 전략:
    #  - INSERT IGNORE로 중복은 무시한다.
    sql = f"INSERT IGNORE INTO {table_name} (name) VALUES (%s)"
    data = [(v,) for v in values]
    if data:
        cur.executemany(sql, data)


def load_name_to_id(cur, table_name: str) -> dict:
    # 목적:
    #  - regions/service_types에 들어간 name을 id로 매핑하기 위해
    #    "name -> id" 딕셔너리를 만든다.
    cur.execute(f"SELECT id, name FROM {table_name}")
    rows = cur.fetchall()
    return {r["name"]: r["id"] for r in rows}


def insert_bluehands(cur, rows: list[dict]):
    # 목적:
    #  - bluehands 테이블에 데이터를 bulk insert 한다.
    # 전제:
    #  - DB 스키마는 최신 컬럼을 모두 가지고 있다고 가정한다(동적 컬럼 감지 제거).
    sql = """
    INSERT INTO bluehands (
        name, region_id, type_id,
        address, phone, latitude, longitude,
        is_ev, is_ev_tech, is_hydrogen,
        is_frame, is_al_frame, is_n_line,
        is_commercial_mid, is_commercial_big, is_commercial_ev,
        is_cs_excellent
    ) VALUES (
        %s, %s, %s,
        %s, %s, %s, %s,
        %s, %s, %s,
        %s, %s, %s,
        %s, %s, %s,
        %s
    )
    """

    data = []
    for r in rows:
        data.append((
            r["name"], r["region_id"], r["type_id"],
            r["address"], r["phone"], r["latitude"], r["longitude"],
            r["is_ev"], r["is_ev_tech"], r["is_hydrogen"],
            r["is_frame"], r["is_al_frame"], r["is_n_line"],
            r["is_commercial_mid"], r["is_commercial_big"], r["is_commercial_ev"],
            r["is_cs_excellent"],
        ))

    if data:
        cur.executemany(sql, data)


def main():
    # 0) CSV 파일 존재 확인
    if not os.path.exists(CSV_PATH):
        die(f"CSV 파일을 찾을 수 없습니다: {CSV_PATH}")

    # 1) CSV 로드 + 헤더 검증
    df = pd.read_csv(CSV_PATH, encoding="utf-8")
    ensure_required_columns(df)

    # 2) 문자열 컬럼 정리(공백/빈값/NaN -> None)
    df[COL_REGION] = df[COL_REGION].apply(normalize_str)
    df[COL_NAME] = df[COL_NAME].apply(normalize_str)
    df[COL_TYPE] = df[COL_TYPE].apply(normalize_str)
    df[COL_ADDRESS] = df[COL_ADDRESS].apply(normalize_str)

    # phone은 하이픈 포맷까지 적용(문자열로 저장)
    df[COL_PHONE] = df[COL_PHONE].apply(format_phone_kor)

    # 3) 필수값이 비어있는 행 제거(최소한 region/name/type는 있어야 함)
    df = df.dropna(subset=[COL_REGION, COL_NAME, COL_TYPE])

    # 4) 차원 테이블 값 추출(중복 제거)
    regions = sorted(df[COL_REGION].dropna().unique().tolist())
    types = sorted(df[COL_TYPE].dropna().unique().tolist())

    conn = connect_mysql()
    try:
        with conn.cursor() as cur:
            # 5) regions / service_types 채우기
            insert_dim_table(cur, "regions", regions)
            insert_dim_table(cur, "service_types", types)

            # 6) name -> id 매핑 로드
            region_map = load_name_to_id(cur, "regions")
            type_map = load_name_to_id(cur, "service_types")

            # 7) bluehands rows 구성
            #    - 위경도/플래그는 CSV에서 이미 전처리 완료라고 가정.
            #    - 다만 pandas에서 NaN으로 들어올 수 있으니 NaN -> None/0 정도만 최소 방어.
            out_rows = []
            for _, row in df.iterrows():
                region_id = region_map.get(row[COL_REGION])
                type_id = type_map.get(row[COL_TYPE])
                if region_id is None or type_id is None:
                    continue

                lat = row[COL_LAT]
                lng = row[COL_LNG]
                lat = None if pd.isna(lat) else float(lat)
                lng = None if pd.isna(lng) else float(lng)

                def safe_int(v, default=0):
                    if v is None or (isinstance(v, float) and pd.isna(v)):
                        return int(default)
                    return int(v)

                out_rows.append({
                    "name": row[COL_NAME],
                    "region_id": int(region_id),
                    "type_id": int(type_id),
                    "address": row[COL_ADDRESS],
                    "phone": row[COL_PHONE],
                    "latitude": lat,
                    "longitude": lng,

                    "is_ev": safe_int(row[COL_IS_EV], 0),
                    "is_ev_tech": safe_int(row[COL_IS_EV_TECH], 0),
                    "is_hydrogen": safe_int(row[COL_IS_HYDROGEN], 0),
                    "is_frame": safe_int(row[COL_IS_FRAME], 0),
                    "is_al_frame": safe_int(row[COL_IS_AL_FRAME], 0),
                    "is_n_line": safe_int(row[COL_IS_N_LINE], 0),
                    "is_commercial_mid": safe_int(row[COL_IS_COMMERCIAL_MID], 0),
                    "is_commercial_big": safe_int(row[COL_IS_COMMERCIAL_BIG], 0),
                    "is_commercial_ev": safe_int(row[COL_IS_COMMERCIAL_EV], 0),
                    "is_cs_excellent": safe_int(row[COL_IS_CS_EXCELLENT], 0),
                })

            # 8) bluehands insert
            insert_bluehands(cur, out_rows)

        conn.commit()
        print("[OK] Import completed.")
        print(f"  regions: {len(regions)}")
        print(f"  service_types: {len(types)}")
        print(f"  bluehands: {len(df)} (rows after cleaning), inserted: {len(out_rows)}")

    except Exception as e:
        conn.rollback()
        die(f"Import failed: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
