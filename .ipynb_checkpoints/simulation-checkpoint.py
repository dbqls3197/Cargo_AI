import pandas as pd
import numpy as np
from math import radians, sin, cos, sqrt, atan2
from datetime import datetime, timedelta
import os

# ==============================================================================
# 1. 상수 및 헬퍼 함수 정의
# ==============================================================================

AVERAGE_TRUCK_SPEED_KPH = 50  # 트럭 평균 속도 (km/h)
CITY_COORDS = {
    '서울': (37.566, 126.978), '부산': (35.180, 129.075), '대구': (35.871, 128.601),
    '인천': (37.456, 126.705), '광주': (35.160, 126.851), '대전': (36.350, 127.384),
    '울산': (35.538, 129.311), '수원': (37.263, 127.028), '창원': (35.228, 128.681),
    '청주': (36.642, 127.489)
}


def calculate_distance(lat1, lon1, lat2, lon2):
    """두 위도/경도 지점 간의 거리를 킬로미터 단위로 계산합니다."""
    R = 6371
    dLat = radians(lat2 - lat1)
    dLon = radians(lon2 - lon1)
    a = sin(dLat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dLon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c


def estimate_time_from_distance(distance_km):
    """거리를 기반으로 예상 운행 시간을 timedelta 객체로 반환합니다."""
    if distance_km < 0: return timedelta(seconds=0)
    hours = distance_km / AVERAGE_TRUCK_SPEED_KPH
    return timedelta(hours=hours)


# ==============================================================================
# 2. 매칭 시뮬레이션 엔진 클래스
# ==============================================================================

class MatchingSimulationEngine:
    """
    과거 데이터를 기반으로 매칭 과정을 시뮬레이션하여 학습용 정답 데이터를 생성합니다.
    """

    def __init__(self, cargo_path, driver_db_path, driver_loc_path):
        print("--- 시뮬레이션 엔진 초기화 시작 ---")

        # 데이터 로드
        self.cargo_df = pd.read_csv(cargo_path)
        driver_harmful_df = pd.read_csv(driver_db_path)
        driver_loc_df = pd.read_csv(driver_loc_path)

        # 드라이버 데이터 통합
        self.driver_database = pd.merge(driver_harmful_df, driver_loc_df, on='driver_id', how='left')
        print(f"-> 총 {len(self.driver_database)}명의 드라이버 정보 로드 완료.")

        # 시간 관련 데이터 타입 변환 및 정렬
        self.cargo_df['request_time_dt'] = pd.to_datetime(self.cargo_df['request_time'])
        self.cargo_df['deadline_dt'] = pd.to_datetime(self.cargo_df['deadline'])
        self.cargo_df = self.cargo_df.sort_values(by='request_time_dt').reset_index(drop=True)
        print(f"-> 총 {len(self.cargo_df)}건의 화물 요청(1년치) 로드 및 시간순 정렬 완료.")

        # 시뮬레이션을 위한 드라이버 상태 초기화
        sim_start_time = self.cargo_df['request_time_dt'].min()
        self.driver_database['next_available_time_dt'] = sim_start_time

        self.simulation_logs = []
        print("--- 시뮬레이션 엔진 초기화 완료 ---\n")

    def run_simulation(self):
        """시간순으로 모든 화물 요청에 대해 매칭 시뮬레이션을 실행합니다."""
        print("--- 1년치 매칭 시뮬레이션 시작 ---")
        total_requests = len(self.cargo_df)

        for index, cargo_request in self.cargo_df.iterrows():
            if (index + 1) % 1000 == 0:
                print(f"-> {index + 1} / {total_requests} 건 처리 중...")

            self._find_and_match_driver(cargo_request)

        print("--- 시뮬레이션 완료 ---")
        return pd.DataFrame(self.simulation_logs)

    def _find_and_match_driver(self, cargo_request):
        """개별 화물 요청에 대해 최적의 드라이버를 찾아 매칭합니다."""

        # 0. 도시 좌표 변환
        origin = cargo_request['origin']
        destination = cargo_request['destination']
        pickup_lat, pickup_lon = CITY_COORDS.get(origin, (None, None))
        delivery_lat, delivery_lon = CITY_COORDS.get(destination, (None, None))

        if pickup_lat is None or delivery_lat is None:
            self._log_result(cargo_request, None, "Failed_InvalidCity")
            return

        # 1. 기본 자격 필터링
        candidates = self.driver_database[
            self.driver_database['max_load_kg'] >= float(cargo_request['weight_kg'])].copy()
        cargo_type = cargo_request['cargo_type']
        if cargo_type == '냉장':
            candidates = candidates[candidates['vehicle_type'] == '냉장']
        elif cargo_type == '냉동':
            candidates = candidates[candidates['vehicle_type'] == '냉동']
        elif cargo_type == '위험물':
            candidates = candidates[candidates['hazmat_capable'] == 1]
        elif cargo_type == '유해물질':
            candidates = candidates[candidates['harmful_substance_capable'] == 1]
        elif cargo_type == '일반':
            candidates = candidates[~candidates['vehicle_type'].isin(['냉장', '냉동'])]

        if candidates.empty:
            self._log_result(cargo_request, None, "Failed_NoQualifiedDriver")
            return

        # 2. 거리 및 시간 제약 필터링
        candidates['distance_to_pickup'] = candidates.apply(
            lambda r: calculate_distance(r['latitude'], r['longitude'], pickup_lat, pickup_lon), axis=1
        )
        distance_pickup_to_delivery = calculate_distance(pickup_lat, pickup_lon, delivery_lat, delivery_lon)

        # 200km 반경 내 드라이버만 1차 후보로 간주 (성능 최적화)
        candidates = candidates[candidates['distance_to_pickup'] <= 200].copy()

        if candidates.empty:
            self._log_result(cargo_request, None, "Failed_NoNearbyDriver")
            return

        # 시간 계산
        candidates['time_to_pickup_td'] = candidates['distance_to_pickup'].apply(estimate_time_from_distance)
        time_pickup_to_delivery_td = estimate_time_from_distance(distance_pickup_to_delivery)

        # (★★★★★ 중요 수정 사항 ★★★★★)
        # np.maximum 대신 .apply를 사용하여 데이터 타입 충돌을 방지합니다.
        cargo_time = cargo_request['request_time_dt']
        candidates['effective_pickup_start_time'] = candidates['next_available_time_dt'].apply(
            lambda driver_available_time: max(cargo_time, driver_available_time)
        )

        # 최종 도착 시간 = 유효 상차 시작 시간 + 픽업지까지 이동 시간 + 상차지에서 도착지까지 이동 시간
        candidates['estimated_delivery_time'] = candidates['effective_pickup_start_time'] + candidates[
            'time_to_pickup_td'] + time_pickup_to_delivery_td

        # 마감 시간을 지킬 수 있는 드라이버만 최종 후보로 선정
        final_candidates = candidates[candidates['estimated_delivery_time'] <= cargo_request['deadline_dt']].copy()

        if final_candidates.empty:
            self._log_result(cargo_request, None, "Failed_TimeConstraint")
            return

        # 3. 최적 드라이버 선택 (픽업지까지 가장 가까운 순서)
        best_driver = final_candidates.sort_values(by=['distance_to_pickup', 'rating'], ascending=[True, False]).iloc[0]

        # 4. 매칭 결과 처리 및 드라이버 상태 업데이트
        self._log_result(cargo_request, best_driver, "Matched")

        # 매칭된 드라이버의 위치와 다음 가용 시간을 업데이트
        driver_idx_to_update = self.driver_database[self.driver_database['driver_id'] == best_driver['driver_id']].index

        # 다음 가용 시간: 배송 완료 시간 + 2시간(휴식/정리)
        self.driver_database.loc[driver_idx_to_update, 'next_available_time_dt'] = best_driver[
                                                                                       'estimated_delivery_time'] + timedelta(
            hours=2)
        # 위치: 배송 완료지
        self.driver_database.loc[driver_idx_to_update, ['latitude', 'longitude']] = [delivery_lat, delivery_lon]

    def _log_result(self, cargo, driver, status):
        """시뮬레이션 결과를 로그 리스트에 추가합니다."""
        log_entry = {
            'request_id': cargo['shipper_id'],  # <--- 'request_id'를 'shipper_id'로 변경
            'request_time': cargo['request_time'],
            'status': status,
            'matched_driver': driver['driver_id'] if driver is not None else None
        }
        self.simulation_logs.append(log_entry)


# ==============================================================================
# 3. 메인 실행 로직
# ==============================================================================

if __name__ == "__main__":
    # 입력 파일 경로
    CARGO_DATA_PATH = 'cargo.csv'
    DRIVER_HARMFUL_DATA_PATH = 'driver_harmful.csv'
    DRIVER_LOC_DATA_PATH = 'driver_loc.csv'

    # 출력 파일 경로
    OUTPUT_CSV_PATH = 'simulation_results_generated.csv'

    # 필수 파일 존재 여부 확인
    required_files = [CARGO_DATA_PATH, DRIVER_HARMFUL_DATA_PATH, DRIVER_LOC_DATA_PATH]
    for f in required_files:
        if not os.path.exists(f):
            print(f"오류: 필수 파일 '{f}'를 찾을 수 없습니다. 스크립트를 종료합니다.")
            exit()

    # 1. 시뮬레이션 엔진 생성
    engine = MatchingSimulationEngine(
        cargo_path=CARGO_DATA_PATH,
        driver_db_path=DRIVER_HARMFUL_DATA_PATH,
        driver_loc_path=DRIVER_LOC_DATA_PATH
    )

    # 2. 시뮬레이션 실행
    simulation_results_df = engine.run_simulation()

    # 3. 결과 저장
    simulation_results_df.to_csv(OUTPUT_CSV_PATH, index=False, encoding='utf-8-sig')

    print(f"\n🎉 시뮬레이션 결과가 '{OUTPUT_CSV_PATH}' 파일로 성공적으로 저장되었습니다.")

    # 결과 요약 출력
    matched_count = simulation_results_df[simulation_results_df['status'] == 'Matched'].shape[0]
    failed_count = simulation_results_df.shape[0] - matched_count
    total_count = simulation_results_df.shape[0]

    print("\n--- 최종 결과 요약 ---")
    print(f"총 요청 건수: {total_count}건")
    print(f"매칭 성공: {matched_count}건 ({(matched_count / total_count) * 100:.2f}%)")
    print(f"매칭 실패: {failed_count}건")
    print("--------------------")