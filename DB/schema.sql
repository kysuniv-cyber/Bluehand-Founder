-- schema.sql
-- 현재 프로젝트 DB 스키마(스크린샷 기준)
-- 초기 세팅용입니다. 초기 한번 실행하는걸 권장합니다.
-- regions / service_types / bluehands

CREATE DATABASE IF NOT EXISTS bluehands_db
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_0900_ai_ci;

USE bluehands_db;

-- FK 때문에 drop 순서: 자식 -> 부모
DROP TABLE IF EXISTS bluehands;
DROP TABLE IF EXISTS service_types;
DROP TABLE IF EXISTS regions;

-- 1) 지역 테이블
CREATE TABLE regions (
  id   INT NOT NULL AUTO_INCREMENT,
  name VARCHAR(50) NOT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uk_regions_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2) 서비스 타입 테이블
CREATE TABLE service_types (
  id   INT NOT NULL AUTO_INCREMENT,
  name VARCHAR(50) NOT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uk_service_types_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3) 블루핸즈 지점 테이블(스크린샷 컬럼 기준)
CREATE TABLE bluehands (
  id INT NOT NULL AUTO_INCREMENT,

  name      VARCHAR(200) NOT NULL,
  region_id INT NOT NULL,
  type_id   INT NOT NULL,

  address   VARCHAR(300) NULL,
  phone     VARCHAR(50)  NULL,

  latitude  DOUBLE NULL,
  longitude DOUBLE NULL,

  is_ev        TINYINT(1) NOT NULL DEFAULT 0,
  is_ev_tech          TINYINT(1) NOT NULL DEFAULT 0,
  is_hydrogen         TINYINT(1) NOT NULL DEFAULT 0,
  is_frame            TINYINT(1) NOT NULL DEFAULT 0,
  is_al_frame         TINYINT(1) NOT NULL DEFAULT 0,
  is_n_line           TINYINT(1) NOT NULL DEFAULT 0,
  is_commercial_mid   TINYINT(1) NOT NULL DEFAULT 0,
  is_commercial_big   TINYINT(1) NOT NULL DEFAULT 0,
  is_commercial_ev    TINYINT(1) NOT NULL DEFAULT 0,
  is_cs_excellent     TINYINT(1) NOT NULL DEFAULT 0,

  PRIMARY KEY (id),

  KEY idx_bluehands_region_id (region_id),
  KEY idx_bluehands_type_id (type_id),

  CONSTRAINT fk_bluehands_region
    FOREIGN KEY (region_id) REFERENCES regions(id)
    ON UPDATE CASCADE ON DELETE RESTRICT,

  CONSTRAINT fk_bluehands_type
    FOREIGN KEY (type_id) REFERENCES service_types(id)
    ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

ALTER TABLE bluehands
DROP COLUMN is_excellent;

