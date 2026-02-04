import requests
import pandas as pd
import time
import math  # 페이지 계산용

# 1. 설정
url = "https://www.hyundai.com/wsvc/kr/front/biz/serviceNetwork.list.do"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.hyundai.com/kr/ko/service-membership/service-network/service-reservation-search",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "X-Requested-With": "XMLHttpRequest"
}

regions = {
    "서울": "서울특별시",
    "경기": "경기도",
    "인천": "인천광역시"
}

all_data = []

print("🔧 전체 데이터 수집 시작")

for region_alias, region_full_name in regions.items():
    print(f"\n🔄 [{region_alias}] 수집 시작")

    current_page = 1
    total_pages = 1  # 일단 1로 시작해서 첫 요청 후 업데이트

    while current_page <= total_pages:
        # Payload 설정 (pageNo가 계속 변함)
        payload = {
            "pageNo": current_page,
            "searchWord": "",
            "snGubunListSearch": "",
            "selectBoxCity": region_full_name,
            "selectBoxCitySearch": region_full_name,
            "selectBoxTownShipSearch": "",
            "asnCd": ""
        }

        try:
            response = requests.post(url, data=payload, headers=headers)

            if response.status_code == 200:
                data = response.json()
                result_block = data.get('data', {})
                items = result_block.get('result', [])

                # 첫 페이지일 때만 전체 개수 확인해서 목표 페이지 설정
                if current_page == 1:
                    total_count = result_block.get('totalCount', 0)
                    # 10개씩 보여주니까, 총 페이지 = (전체개수 / 10) 올림 처리
                    total_pages = math.ceil(total_count / 10)
                    print(f"   📊 총 {total_count}개 발견 (약 {total_pages} 페이지 예상)")

                if not items:  # 데이터가 없으면 중단
                    break

                for item in items:
                    # 좌표값 가져오기
                    val1 = float(item.get('mapLaeVal', 0) or 0)
                    val2 = float(item.get('mapLoeVal', 0) or 0)

                    # 1. 좌표가 0이면 건너뛰기 (continue 필수!)
                    if val1 == 0 or val2 == 0:
                        print(f"   ⚠️ 좌표 누락된 데이터는 제외: {item.get('asnNm')}")
                        continue  # 👈 이게 있어야 밑으로 안 내려가고 다음 루프로 넘어갑니다.

                    # 2. 좌표 보정 (경도 127... 위도 37...)
                    if val1 > 100:
                        lon, lat = val1, val2
                    else:
                        lon, lat = val2, val1

                    # f12 개발자 도구 까서 확인한 것 !
                    info = {
                        # --- 기본 정보 ---
                        'region': region_alias,
                        'name': item.get('asnNm'),
                        'type': item.get('apimCeqPlntNm'),
                        'address': item.get('pbzAdrSbc'),
                        'phone': item.get('repnTn', '').strip(),
                        'latitude': lat,
                        'longitude': lon,

                        # 1. 친환경차 관련
                        'is_ev': 1 if item.get('spcialSrvH003', '').strip() == 'Y' else 0,  # 전기차 수리
                        'is_ev_tech': 1 if item.get('spcialSrvC002', '').strip() == 'Y' else 0,
                        # 전동차 기술력 우수 (is_excellent)
                        'is_hydrogen': 1 if item.get('spcialSrvH001', '').strip() == 'Y' else 0,  # 수소 전기차 수리
                        # 2. 차체/도장 및 특수 수리
                        'is_frame': 1 if item.get('spcialSrvC001', '').strip() == 'Y' else 0,  # 차체/도장 수리 인증
                        'is_al_frame': 1 if item.get('spcialSrvC006', '').strip() == 'Y' else 0,  # 알루미늄 프레임 수리
                        'is_n_line': 1 if item.get('spcialSrvC009', '').strip() == 'Y' else 0,  # 고성능 N 모델 수리
                        # 3. 상용차(트럭/버스) 관련
                        'is_commercial_mid': 1 if item.get('spcialSrvC010', '').strip() == 'Y' else 0,  # 중형 상용 수리
                        'is_commercial_big': 1 if item.get('spcialSrvC011', '').strip() == 'Y' else 0,  # 대형 상용 수리
                        'is_commercial_ev': 1 if item.get('spcialSrvC012', '').strip() == 'Y' else 0,  # 상용 전동차 수리
                        # 4. CS 우수
                        'is_cs_excellent': 1 if item.get('spcialSrvC003', '').strip() == 'Y' else 0,  # CS 우수 업체
                    }
                    all_data.append(info)

                # 진행 상황 출력 (너무 자주 찍으면 지저분하니 5페이지마다)
                if current_page % 5 == 0:
                    print(f"      ▶ {current_page}/{total_pages} 페이지 수집 중")

                current_page += 1  # 다음 페이지로

            else:
                print(f"      ❌ 요청 실패: {response.status_code}")
                break

        except Exception as e:
            print(f"      ⚠️ 에러 발생: {e}")
            break

        time.sleep(0.2)  # 서버 부하 방지

    print(f"   ✅ [{region_alias}] 완료.")

# 결과 저장
print("=" * 50)
df = pd.DataFrame(all_data)
print(f"💾 최종 수집 결과: 총 {len(df)}개")
print(df.groupby('region')['name'].count())  # 지역별 개수 확인
print(df.head())

# CSV 저장
df.to_csv("bluehands_final_all.csv", index=False, encoding="utf-8-sig")
print("\n 'bluehands_final_all.csv' 파일로 저장했습니다.")