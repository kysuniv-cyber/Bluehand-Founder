# 🚘 블루핸즈 통합 검색 서비스 (Bluehands Finder)

사용자의 현재 위치 또는 선택한 지역을 기반으로 **현대자동차 블루핸즈(Bluehands)** 정비소를 조회하고, 원하는 정비 옵션(전기차, 수소차, 판금 등)별로 필터링하여 지도와 목록으로 보여주는 웹 애플리케이션입니다.

## ✨ 주요 기능

* **📍 위치 기반 검색**: 사용자 브라우저의 GPS를 활용해 내 위치 주변의 지점을 찾고 거리를 계산합니다. (기본 위치: 서울 강남역)
* **🗺️ 지도 시각화**: Folium 지도를 통해 지점의 위치를 마커로 표시하고, 클릭 시 상세 정보를 제공합니다.
* **🔍 상세 필터링**:
    * **지역 선택**: 시/도 단위로 검색 범위를 설정할 수 있습니다.
    * **서비스 옵션**: 전기차, 수소차, 판금, N-Line 전담 등 특수 정비 가능 여부로 필터링합니다.
* **📃 깔끔한 결과 목록**: 커스텀 HTML/CSS가 적용된 테이블과 페이지네이션 기능을 통해 검색 결과를 보기 쉽게 제공합니다.
* **📱 반응형 UI**: 사이드바를 활용하여 PC와 모바일 환경 모두에서 편리하게 사용할 수 있습니다.

## 🛠️ 기술 스택 (Tech Stack)

* **Python**: 3.10+
* **Web Framework**: [Streamlit](https://streamlit.io/)
* **Database**: MySQL (8.0+)
* **Libraries**:
    * `folium`, `streamlit-folium`: 지도 시각화
    * `mysql-connector-python`: DB 연동
    * `streamlit-js-eval`: GPS 위치 정보 수집
    * `pandas`: 데이터 처리

## ⚙️ 설치 및 실행 방법

### 1. 환경 설정 및 패키지 설치
```bash
# 필수 라이브러리 설치
pip install streamlit mysql-connector-python pandas folium streamlit-folium streamlit-js-eval
```

2. 데이터베이스 설정 (MySQL)
프로젝트 실행을 위해 MySQL에 데이터베이스와 테이블이 생성되어 있어야 합니다.
```sql
CREATE DATABASE IF NOT EXISTS bluehands_db;
USE bluehands_db;

-- 1. 지역 테이블
CREATE TABLE regions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL
);

-- 2. 블루핸즈 테이블
CREATE TABLE bluehands (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    address VARCHAR(255),
    phone VARCHAR(50),
    latitude DOUBLE,
    longitude DOUBLE,
    region_id INT,
    is_ev TINYINT(1) DEFAULT 0,        -- 전기차 전담
    is_hydrogen TINYINT(1) DEFAULT 0,  -- 수소차 전담
    is_frame TINYINT(1) DEFAULT 0,     -- 판금/차체
    is_excellent TINYINT(1) DEFAULT 0, -- 우수 협력점
    is_n_line TINYINT(1) DEFAULT 0,    -- N-Line 전담
    FOREIGN KEY (region_id) REFERENCES regions(id)
);
```
3. DB 연결 정보 수정
소스 코드 내의 DB_CONFIG 딕셔너리를 본인의 MySQL 환경에 맞게 수정해주세요.

### main.py (또는 해당 파일의 내용 수정)
DB_CONFIG = {
    "host": "localhost",
    "user": "root",           # 본인의 MySQL 유저명
    "password": "your_password", # 본인의 MySQL 비밀번호
    "database": "bluehands_db",
    "charset": "utf8mb4",
}

4. 애플리케이션 실행
```bash
streamlit run final.py # 최종 실행 파일은 final.py 입니다.
 ```

📂 프로젝트 구조
📦 bluehands-finder
 ┣ 📜 final.py          # 메인 애플리케이션 소스 코드
 ┣ 📜 elses             #
 ┗ 📜 README.md        # 프로젝트 설명서
