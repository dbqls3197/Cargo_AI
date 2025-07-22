import mysql.connector
from datetime import datetime
from flask import jsonify
import json
import requests
import re
from typing import Optional



class DBManager:
    def __init__(self):
        self.connection = None
        self.cursor = None

    ## 데이터베이스 연결
    def connect(self):
        try:
            self.connection = mysql.connector.connect(
                host="10.0.66.3",
                user="suyong",
                password="1234",
                database="cargo_ai",
                charset="utf8mb4"
            )
            self.cursor = self.connection.cursor(dictionary=True, buffered=True)
        except mysql.connector.Error as error:
            print(f"데이터베이스 연결 실패 : {error}")

    ## 데이터베이스 연결해제
    def disconnect(self):
        try:
            if self.connection and self.connection.is_connected():
                self.cursor.close()
                self.connection.close()
        except Exception as e:
            print("❌ disconnect 중 오류:", e)
    # def disconnect(self):
    #     if self.connection and self.connection.is_connected():
    #         self.cursor.close()
    #         self.connection.close()


    ## 회원가입 화주
    def insert_shipper(
        self,
        name: str,
        shipper_id: str,
        shipper_pw: str,
        nickname: str,
        business_registration_num: Optional[str],
        phone: str,
        email: Optional[str],
        birth_date: str,
        gender: int,
        address: str,
        profile_img_path: Optional[str]
    ):
        """shippers 테이블에 화주 회원정보 삽입"""
        try:
            self.connect()
            insert_query = """
                INSERT INTO shippers (name,shipper_id,shipper_pw,nickname,business_registration_num,phone,email,birth_date,gender,address,profile_img,created_at) VALUES (
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s
                )
            """
            values = (name,shipper_id,shipper_pw,nickname,business_registration_num,phone,email,birth_date,gender,address,profile_img_path,datetime.now()
            )
            self.cursor.execute(insert_query, values)
            self.connection.commit()
        except Exception as e:
            print(f"❌ 화주 회원정보 삽입 실패: {e}")
        finally:
            self.disconnect()


    ## 회원가입 기사
    def insert_driver(
        self,
        name: str,
        driver_id: str,
        driver_pw: str,
        nickname: str,
        business_registration_num: Optional[str],
        phone: str,
        email: Optional[str],
        birth_date: str,
        gender: int,
        address: str,
        profile_img_path: Optional[str]
    ):
        """drivers 테이블에 기사 회원정보 삽입"""
        try:
            self.connect()
            insert_query = """
                INSERT INTO drivers (name,driver_id,driver_pw,nickname,business_registration_num,phone,email,birth_date,gender,address,profile_img,is_active,created_at
                ) VALUES (
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s, CURRENT_TIMESTAMP()
                )
            """
            values = (name,driver_id,driver_pw,nickname,business_registration_num,phone,email,birth_date,gender,address,profile_img_path,0                           
            )
            self.cursor.execute(insert_query, values)
            self.connection.commit()
        except Exception as e:
            print(f"❌ 기사 회원정보 삽입 실패: {e}")
        finally:
            self.disconnect()

    # 운송 요청 저장
    def insert_freight_request(self, shipper_id, data):
        try:
            self.connect()
            insert_query = """
            INSERT INTO freight_request (
                shipper_id, origin, destination, cargo_type,
                cargo_info, weight, price, special_request,
                pickup_deadline, fast_request
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            values = (
                shipper_id,
                data['origin'],  # 출발지
                data['destination'],  # 도착지
                data['cargo_type'],  # 화물 종류 (예: 차 종류 등)
                data.get('cargo_info'),  # 화물 상세 정보 (nullable)
                data['weight'],  # 무게 (float)
                data['price'],  # 운임 가격
                data.get('special_request'),  # 특이사항 (nullable)
                data.get('pickup_deadline'),  # 마감 시간 (nullable datetime)
                data.get('fast_request')  # 운송 방식 (기본값 0)
            )
            self.cursor.execute(insert_query, values)
            self.connection.commit()
        except Exception as e:
            print(f"화물 운송 요청 데이터 삽입 실패: {e}")
        finally:
            self.disconnect()

    # 운송 요청 조회
    def select_requests_by_shipper_id(self, shipper_id):
        try:
            self.connect()
            query = """
            select * from freight_request where shipper_id = %s
            """
            value = (shipper_id,)
            self.cursor.execute(query, value)
            return self.cursor.fetchall()
        except Exception as e:
            print(f"화물 운송 신청 데이터 조회 실패: {e}")
            return []
        finally:
            self.disconnect()


    # 화물 매칭 기사 조회
    def select_matching_drivers_info(self):
        try:
            self.connect()
            query = """
            SELECT *
            FROM vehicles v
            INNER JOIN drivers d
            ON v.driver_id = d.driver_id; 
            """
            self.cursor.execute(query)
            return self.cursor.fetchall()
        except Exception as e:
            print(f"화물 매칭 기사 데이터 조회 실패: {e}")
        finally:
            self.disconnect()

    
    
    # 기사 아이디로 기사 데이터 조회
    def select_matching_driver_all_info(self, driver_id):
        try:
            self.connect()
            query= """
            SELECT *
            FROM vehicles v
            INNER JOIN drivers d
            ON v.driver_id = d.driver_id
            where d.driver_id = %s;
            """
            self.cursor.execute(query, (driver_id,))
            return self.cursor.fetchone()
        except Exception as e:
            print(f"기사 아이디로 기사+ 차량 데이터 정보 조회 실패 : {e}")
            return []
        finally:
            self.disconnect()


    ## 운송가능한 모든 드라이버 가져오기
    def select_active_drivers_all_info(self):
        try:
            self.connect()
            query= """
            SELECT *
            FROM vehicles v
            INNER JOIN drivers d
            ON v.driver_id = d.driver_id
            where d.is_active = 1
            """
            self.cursor.execute(query,)
            return self.cursor.fetchall()
        except Exception as e:
            print(f"기사 아이디로 기사+ 차량 데이터 정보 조회 실패 : {e}")
            return []
        finally:
            self.disconnect()

    # 관리자 정보 조회
    def select_admin_by_id(self, admin_id):
        try:
            self.connect()
            query = "select * from admins where admin_id = %s"
            self.cursor.execute(query, (admin_id,))
            return self.cursor.fetchone()
        except Exception as e:
            print(f"❌ 관리자 정보 조회 실패: {e}")
        finally:
            self.disconnect()

    ## 화주 아이디로 매칭 정보, 운전자 정보 조회
    def select_matching_info(self, shipper_id):
        try:
            self.connect()
            query ="""
            SELECT 
            m.*, 
            fr.shipper_id,
            fr.request_time,
            fr.weight,
            d.name,
            d.phone,
            v.truck_type,
            v.capacity ,
            v.vehicle_num,
            v.truck_info
            FROM matches m
            INNER JOIN freight_request fr ON fr.id = m.request_id
            INNER JOIN drivers d ON d.driver_id = m.driver_id
            INNER JOIN vehicles v ON d.driver_id = v.driver_id
            WHERE fr.shipper_id = %s;
            """
            self.cursor.execute(query,(shipper_id,))
            return self.cursor.fetchall()
        except Exception as e:
            print(f"화주 아이디로 매칭 정보, 운전자 정보 조회 실패 : {e}")
            return []
        finally:
            self.disconnect()


    ## 화주 운송 요청 정보 조회(화주 아이디)
    def select_request_by_user_id(self, shipper_id):
        try:
            self.connect()
            query = """
            SELECT * FROM freight_request
            WHERE shipper_id = %s
            """
            value = (shipper_id,)
            self.cursor.execute(query, value)
            return self.cursor.fetchall()

        except Exception as e:
            print(f"운송 요청 아이디로 정보 조회 실패: {e}")
            return None
        finally:
            self.disconnect()


     ## 화주 운송 요청 정보 조회(운송요청아이디)
    def select_request_by_id(self, request_id):
        try:
            self.connect()
            query = """
            SELECT * FROM freight_request
            WHERE id = %s
            """
            value = (request_id,)
            self.cursor.execute(query, value)
            return self.cursor.fetchone()

        except Exception as e:
            print(f"운송 요청 아이디로 정보 조회 실패: {e}")
            return None
        finally:
            self.disconnect()

     ## 운전자 id로 운전자 정보 조회
    def select_driver_by_id(self, driver_id):
        try:
            self.connect()
            query = """
            SELECT * FROM drivers
            WHERE driver_id = %s
            """
            value = (driver_id,)
            self.cursor.execute(query, value)
            return self.cursor.fetchone()

        except Exception as e:
            print(f"운전자 정보 아이디로 조회 실패: {e}")
            return None
        finally:
            self.disconnect()


    ## 매칭 완료 정보 저장
    def insert_matching_result(self, request_id, driver_id):
        try:
            self.connect()

            query = """
            INSERT INTO matches (
                request_id, driver_id
            ) VALUES (%s, %s)
            """
            values = (request_id, driver_id)
            self.cursor.execute(query, values)
            self.connection.commit()
            print("✅ 매칭 결과 저장 성공")
        except Exception as e:
            print(f"❌ 매칭 결과 저장 오류: {e}")
        finally:
            self.disconnect()

    ## 매칭완료결과 확인
    def select_matching_driver_my_request(self, driver_id, request_id):
        try:
            self.connect()
            query = """
            SELECT m.*, d.name AS name, d.phone AS driver_phone, fr.origin, fr.destination
            FROM matches m
            JOIN freight_request fr ON m.request_id = fr.id
            JOIN drivers d ON m.driver_id = d.driver_id
            WHERE m.driver_id = %s AND m.request_id = %s
            """
            self.cursor.execute(query, (driver_id, request_id))
            print("✅ 매칭결과 조회 성공")
            return self.cursor.fetchone()
        except Exception as e:
            print(f"❌ 매칭결과 조회 실패: {e}")
        finally:
            self.disconnect()



    ## 매칭 상태 변경
    def update_matching_status(self, request_id):
        try: 
            self.connect()
            query = """
                    UPDATE freight_request 
                    SET is_matched = 1
                    WHERE id = %s 
                    """
            self.cursor.execute(query,(request_id,))
            self.connection.commit()
            print("매치상태 업데이트 성공")
        except Exception as e:
            print(f"❌ 매칭상태 업데이트 실패: {e}")
        finally:
            self.disconnect()



     ## 매칭 내역 조회
    def select_matching_driver_my_request_by_id(self, shipper_id):
        try:
            self.connect()
            query = """
            SELECT m.*, d.name AS driver_name, d.phone AS driver_phone, fr.origin, fr.destination
            FROM matches m
            JOIN freight_request fr ON m.request_id = fr.id
            JOIN drivers d ON m.driver_id = d.id
            WHERE fr.shipper_id = %s
            ORDER BY m.created_at DESC
            """
            self.cursor.execute(query, (shipper_id,))
            return self.cursor.fetchall()
        except Exception as e:
            print(f"❌ 매칭 내역 조회 실패: {e}")
        finally:
            self.disconnect()

    ## 화주 아이디로 정보 조회
    def select_shipper_by_id(self, shipper_id):
        try:
            self.connect()
            query = "select * from shippers WHERE shipper_id = %s"
            self.cursor.execute(query, (shipper_id,))
            return self.cursor.fetchone()
        except Exception as e:
            print(f"화주 테이블 조회 실패: {e}")
        finally:
            self.disconnect()

    ## 결제 테이블 생성
    def create_my_payments_table(self):
        try:
            self.connect()
            query = """
            CREATE TABLE IF NOT EXISTS payments (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                user_id VARCHAR(255) NOT NULL,
                match_id BIGINT NOT NULL,
                driver_id VARCHAR(255) NOT NULL,
                fee INT NOT NULL,
                origin VARCHAR(255),
                destination VARCHAR(255),
                driver_name VARCHAR(255),
                driver_phone VARCHAR(255),
                is_paid TINYINT DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
            self.cursor.execute(query)
            self.connection.commit()
        except Exception as e:
            print(f"❌ payments 테이블 생성 실패: {e}")
        finally:
            self.disconnect()

    ## 결제 정보 삽입
    def insert_payment(self, data):
        try:
            self.connect()
            query = """
            INSERT INTO payments (
                user_id, match_id, driver_id, fee,
                origin, destination, driver_name, driver_phone
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            values = (
                data['user_id'], data['match_id'], data['driver_id'], data['fee'],
                data.get('origin'), data.get('destination'),
                data.get('driver_name'), data.get('driver_phone')
            )
            self.cursor.execute(query, values)
            self.connection.commit()
            print("✅ 결제 정보 삽입 성공")
        except Exception as e:
            print(f"❌ 결제 정보 삽입 실패: {e}")
        finally:
            self.disconnect()

    ## 결제 내역 아이디로 조회
    def select_payments_by_id(self, user_id):
        try:
            self.connect()
            query = """
            SELECT * FROM payments
            WHERE shipper_id  = %s
            ORDER BY created_at DESC
            """
            self.cursor.execute(query, (user_id,))
            print("✅ 결제 내역 조회 성공")
            return self.cursor.fetchall()
        except Exception as e:
            print(f"❌ 결제 내역 조회 실패: {e}")
            return []
        finally:
            self.disconnect()

    ## 결제 상태 업데이트
    def update_payment_is_paid(self, match_id):
        try:
            self.connect()
            query = """
            UPDATE payments
            SET is_paid = 1
            WHERE match_id = %s
            """
            self.cursor.execute(query, (match_id,))
            self.connection.commit()
            print("✅ 결제 상태 업데이트 완료 (is_paid = 1)")
        except Exception as e:
            print(f"❌ 결제 상태 업데이트 실패: {e}")
        finally:
            self.disconnect()


    # 운전자 상태 업데이트 함수
    def update_driver_status(self, driver_id, status_value):
            query = "UPDATE drivers SET is_active = %s WHERE driver_id = %s"
            self.connect()
            try:
                self.cursor.execute(query, (status_value, driver_id))
                self.connection.commit()
                return True
            except Exception as e:
                print(f"DB 오류: 운전자 상태 업데이트 실패 - {e}")
                self.connection.rollback()
                return False
            finally:
                self.disconnect()

    ## 모든 화물 정보 조회
    def select_requests_all_info(self):
        try:
            self.connect()
            query = """
            select * from freight_request 
            """
            self.cursor.execute(query)
            return self.cursor.fetchall()
        except Exception as e:
            print(f"화물 운송 신청 데이터 조회 실패: {e}")
            return []
        finally:
            self.disconnect()

    ## 매치 안된 모든 화물정보 조회
    def select_non_matched_requests_all_info(self):
        try:
            self.connect()
            query = """
            select * from freight_request 
            where is_matched = 0
            """
            self.cursor.execute(query)
            return self.cursor.fetchall()
        except Exception as e:
            print(f"화물 운송 신청 데이터 조회 실패: {e}")
            return []
        finally:
            self.disconnect()

    ## 운전자 id로 기사추천 매칭 정보 조회
    def select_all_recommend_matches(self, driver_id):
        try:
            self.connect()
            query="""
            select * from recommended_matches where dirver_id = %s
            """
            self.cursor.execute(query)
            return self.cursor.fetchall
        except Exception as e:
            print(f"화물기사 추천 테이블 조회 실패 : {e}")
            return []
        finally:
            self.disconnect()

    # 관제 보고서 필요한 데이터 불러오기
    def get_monthly_report(self, month):
        try:
            self.connect()
            query = """
            SELECT COUNT(*) AS total_matches,
                IFNULL(SUM(fr.price), 0) AS total_price
            FROM matches m
            JOIN freight_request fr ON m.request_id = fr.id
            WHERE DATE_FORMAT(m.created_at, '%Y-%m') = %s
            """
            self.cursor.execute(query, (month,))
            return self.cursor.fetchone()
        except Exception as e:
            print(f"❌ 월간 리포트 조회 실패: {e}")
            return {}
        finally:
            self.disconnect()

    def get_driver_report(self, driver_id):
        try:
            self.connect()
            query = """
            SELECT COUNT(*) AS total_trips,
                IFNULL(SUM(fr.price), 0) AS total_price,
                IFNULL(AVG(fr.price), 0) AS avg_price
            FROM matches m
            JOIN freight_request fr ON m.request_id = fr.id
            WHERE m.driver_id = %s
            """
            self.cursor.execute(query, (driver_id,))
            return self.cursor.fetchone()
        except Exception as e:
            print(f"❌ 기사 리포트 조회 실패: {e}")
            return {}
        finally:
            self.disconnect()


    def select_all_matches(self):
        try:
            self.connect()
            query = """
                SELECT m.*, fr.origin, fr.destination, fr.cargo_type, fr.weight
                FROM matches m
                LEFT JOIN freight_request fr ON m.request_id = fr.id
            """
            self.cursor.execute(query)
            result = self.cursor.fetchall()
            print("✅ 전체 matches 조회 성공")
            return result
        except Exception as e:
            print(f"❌ 전체 matches 조회 실패: {e}")
            return []
        finally:
            self.disconnect()

    #모든 운전자 정보 가져오기
    def select_matching_driver(self):
        try:
            self.connect()
            query = "SELECT * FROM drivers"  # 드라이버 테이블에서 모든 정보를 조회하는 쿼리
            self.cursor.execute(query)
            return self.cursor.fetchall()
        except Exception as e:
            print(f"화물 매칭 기사 데이터 조회 실패: {e}")
            return []
        finally:
            self.disconnect()

    def get_active_delivery_count(self):
        try:
            self.connect()
            # matches 테이블의 status 컬럼이 '0'이 운송중을 의미한다면 이대로 유지
            # 만약 'assigned', 'picked_up', 'in_transit' 등의 문자열이라면 쿼리 수정 필요
            query = "SELECT COUNT(*) AS count FROM matches WHERE status = 'in_transit'" # 예시: 'in_transit'이 운송중
            self.cursor.execute(query)
            result = self.cursor.fetchone()
            return result['count'] if result else 0
        except Exception as e:
            print(f"[에러] 운송 중 쿼리 실패: {e}")
            return 0
        finally:
            self.disconnect()

    def get_all_driver_briefs(self):
        try:
            self.connect()
            # drivers 테이블과 vehicles 테이블을 LEFT JOIN하여 필요한 정보를 가져옵니다.
            # is_active 필드를 d.is_active로 명확히 지정하여 혼동을 피합니다.
            query = """
                SELECT
                    d.driver_id,
                    d.name,
                    d.nickname,
                    d.rating,
                    d.is_active,  -- d.is_active 명확히 명시
                    d.driver_lat,
                    d.driver_lon,
                    d.location_updated_at,
                    v.truck_type,  -- 차량 유형 추가
                    v.capacity     -- 적재 용량 추가
                FROM
                    drivers d
                LEFT JOIN
                    vehicles v ON d.driver_id = v.driver_id;
            """
            self.cursor.execute(query)
            # 모든 결과를 딕셔너리 형태로 가져옵니다.
            drivers_briefs = self.cursor.fetchall()

            formatted_drivers = []
            for driver in drivers_briefs:
                # is_active 값을 기반으로 '운행중', '운행종료' 텍스트를 'status' 키로 추가
                status_text = '운행중' if driver.get('is_active') == 0 else '운행종료'
                
                # 차량 정보 (truck_type과 capacity를 합쳐서 'vehicle' 필드로 만듭니다)
                vehicle_info = "정보 없음"
                if driver.get('truck_type') and driver.get('capacity') is not None:
                    # capacity가 톤 단위라면 여기에 '톤' 추가 (예: f"{driver['capacity']}톤")
                    vehicle_info = f"{driver['truck_type']} ({driver['capacity']}kg)"
                elif driver.get('truck_type'):
                    vehicle_info = f"{driver['truck_type']}"
                elif driver.get('capacity') is not None:
                    vehicle_info = f"{driver['capacity']}kg"


                formatted_drivers.append({
                    'driver_id': driver.get('driver_id'),
                    'name': driver.get('name'),
                    'nickname': driver.get('nickname'),
                    'rating': driver.get('rating'),
                    'is_active': driver.get('is_active'), # 원본 is_active 값도 유지
                    'status': status_text, # UI 표시용 상태 (운행중/운행종료)
                    'vehicle': vehicle_info, # 차량 유형 및 톤수 정보
                    'latitude': float(driver.get('driver_lat')) if driver.get('driver_lat') is not None else None,
                    'longitude': float(driver.get('driver_lon')) if driver.get('driver_lon') is not None else None,
                    'location_updated_at': str(driver.get('location_updated_at')) if driver.get('location_updated_at') else None,
                })
            
            print(f"DEBUG: get_all_driver_briefs() successfully returned {len(formatted_drivers)} drivers.")
            # 이 시점에서 formatted_drivers의 각 항목에 'vehicle'과 'status'가 포함되어야 합니다.
            # 이 formatted_drivers를 Flask 라우트가 JSON으로 변환하여 HTML로 보냅니다.
            return formatted_drivers

        except Exception as e:
            print(f"❌ 모든 기사 간략 정보 조회 실패: {e}")
            return []
        finally:
            self.disconnect()
            
# models.py 파일 내에서 get_driver_full_details 함수를 찾아서 아래 코드로 대체하세요.

    def get_driver_full_details(self, driver_id):
        try:
            self.connect()

            # 드라이버의 기본 정보와 현재 진행 중인 운송 요청 정보를 조인하여 가져오는 쿼리
            # 이 쿼리는 driver_id가 실제로 존재하는지 확인하는 용도로만 사용합니다.
            # freight_request 및 matches 테이블 데이터가 없어도 하드코딩을 위해 기본 정보는 가져옵니다.
            query = """
                SELECT
                    d.driver_id, d.name, d.nickname, d.rating, d.is_active,
                    d.driver_lat, d.driver_lon, d.location_updated_at,
                    v.truck_type, v.vehicle_num, v.capacity
                FROM
                    drivers d
                LEFT JOIN
                    vehicles v ON d.driver_id = v.driver_id
                WHERE
                    d.driver_id = %s;
            """
            self.cursor.execute(query, (driver_id,))
            result = self.cursor.fetchone()

            print(f"DEBUG: get_driver_full_details for driver_id={driver_id} raw result: {result}")

            if not result:
                print(f"DEBUG: No driver found for ID {driver_id}")
                return None # 드라이버 자체를 찾을 수 없으면 None 반환

            # is_active 논리 반전 적용 (0:운행중, 1:운행종료)
            is_active_status = '운행중' if result['is_active'] == 0 else '운행종료'

            # 차량 정보 조합 (드라이버 목록에 표시될 요약 정보)
            vehicle_info_brief = "정보 없음"
            if result.get('truck_type') and result.get('capacity') is not None:
                vehicle_info_brief = f"{result['truck_type']} ({result['capacity']}kg)"
            elif result.get('truck_type'):
                vehicle_info_brief = f"{result['truck_type']}"
            elif result.get('capacity') is not None:
                vehicle_info_brief = f"{result['capacity']}kg"

            # 기본 드라이버 정보 구성
            driver_data = {
                'driver_id': result['driver_id'],
                'name': result['name'],
                'nickname': result['nickname'],
                'rating': result['rating'],
                'is_active': result['is_active'],
                'status': is_active_status, # 기본적으로 is_active 상태 사용
                'latitude': float(result['driver_lat']) if result['driver_lat'] is not None else None,
                'longitude': float(result['driver_lon']) if result['driver_lon'] is not None else None,
                'location_updated_at': str(result['location_updated_at']) if result['location_updated_at'] else None,
                'vehicle': vehicle_info_brief,
                'details': {
                    'info': { # info는 일단 기본값으로 초기화
                        'cargoId': '없음',
                        'origin': '없음',
                        'dest': '없음',
                        'cargo_type': '없음',
                        'weight': '없음',
                        'plate_number': '없음',
                        'capacity': '없음',
                        'truck_type': '없음',
                        'trip_status': '정보 없음'
                    },
                    'progress': [],
                    'route': {},
                    'logs': []
                }
            }

            # --- 특정 driver_id에 대한 하드코딩 데이터 적용 ---
            if driver_id == '3333': # 김철수 드라이버
                driver_data['status'] = '운송 중' # 목록에 표시되는 상태도 변경
                driver_data['details']['info'] = {
                    'cargoId': '#20250709-001',
                    'origin': '서울 강남구',
                    'dest': '부산 물류센터',
                    'cargo_type': '전자제품',
                    'weight': '500',
                    'plate_number': '123가4567', # 예시 차량 번호
                    'capacity': '1000', # 예시 적재 용량
                    'truck_type': '1톤 트럭', # 예시 차량 유형
                    'trip_status': '운송 중'
                }
                driver_data['details']['progress'] = [
                    {'step': '서울 상차 완료', 'time': '09:30', 'completed': True},
                    {'step': '대전 하차 완료', 'time': '12:00', 'completed': True},
                    {'step': '부산 이동 중 (진행 중)', 'time': '진행 중', 'completed': False},
                    {'step': '부산 하차 예정', 'time': '17:30', 'completed': False},
                ]
                driver_data['details']['route'] = {
                    'next': '부산 물류센터',
                    'eta': '17:30',
                    'remaining': '250km'
                }
                driver_data['details']['logs'] = [
                    {'time': '12:00', 'log': '대전 하차 완료'},
                    {'time': '09:35', 'log': '운행 시작'},
                    {'time': '09:30', 'log': '서울 상차 완료'},
                ]
            elif driver_id == '2222': # 박희철 드라이버 (매칭 완료 예시)
                driver_data['status'] = '매칭 완료'
                driver_data['details']['info'] = {
                    'cargoId': '#20250709-002',
                    'origin': '경기 성남시',
                    'dest': '대구 물류센터',
                    'cargo_type': '의류',
                    'weight': '200',
                    'plate_number': '567나8901',
                    'capacity': '500',
                    'truck_type': '1.5톤 트럭',
                    'trip_status': '매칭 완료'
                }
                driver_data['details']['progress'] = [
                    {'step': '화물 매칭 완료', 'time': '13:00', 'completed': True},
                    {'step': '경기 성남시 이동 예정', 'time': '예정', 'completed': False},
                    {'step': '상차 예정', 'time': '예정', 'completed': False},
                ]
                driver_data['details']['route'] = {
                    'next': '경기 성남시',
                    'eta': '확인 중',
                    'remaining': '확인 중'
                }
                driver_data['details']['logs'] = [
                    {'time': '13:00', 'log': '화물 매칭 완료, 배차 대기 중입니다.'},
                ]
            else: # 그 외의 드라이버 ID (기본값)
                driver_data['details']['info']['trip_status'] = driver_data['status'] # is_active 상태 반영
                driver_data['details']['progress'] = [{'step': '현재 운송 없음', 'time': '', 'completed': False}]
                driver_data['details']['route'] = {'next': 'N/A', 'eta': 'N/A', 'remaining': 'N/A'}
                driver_data['details']['logs'] = [{'time': 'N/A', 'log': '최근 운송 기록 없음'}]

            print(f"DEBUG: get_driver_full_details() successfully returned data for {driver_id}")
            return driver_data

        except Exception as e:
            print(f"❌ 기사 상세 정보 조회 실패: {e}")
            return None
        finally:
            self.disconnect()

    def get_active_driver_count(self):
        try:
            self.connect()
            # 스키마에 따라 is_active가 0일 때 '운행중' (활성)이므로, 0인 기사 수를 셉니다.
            query = "SELECT COUNT(*) AS count FROM drivers WHERE is_active = 0"
            self.cursor.execute(query)
            result = self.cursor.fetchone()
            return result['count'] if result else 0
        except Exception as e:
            print(f"[에러] 가용 기사 쿼리 실패: {e}")
            return 0
        finally:
            self.disconnect()

    def get_drivers_from_db(self, driver_id: str = None):
        try:
            self.connect()
            if driver_id:
                query = """
                    SELECT driver_id, name, nickname, rating, is_active,
                           latitude, longitude, location_updated_at
                    FROM drivers
                    WHERE driver_id = %s
                """
                self.cursor.execute(query, (driver_id,))
            else:
                query = """
                    SELECT driver_id, name, nickname, rating, is_active,
                           latitude, longitude, location_updated_at
                    FROM drivers
                """
                self.cursor.execute(query)

            result = self.cursor.fetchall()
            print(f"DEBUG: get_drivers_from_db(driver_id={driver_id}) → {len(result)} rows")
            # 단일 레코드만 원한다면:
            # if driver_id and result:
            #     return result[0]
            return result

        except Exception as e:
            print(f"기사 정보 조회 실패: {e}")
            return [] if not driver_id else None

        finally:
            self.disconnect()


    def get_freight_request_by_id(self, request_id: int):
        try:
            self.connect()
            query = """
                SELECT id, shipper_id, origin, destination,
                       cargo_type, cargo_info, weight, price,
                       special_request, request_time, pickup_deadline,
                       surcharge, fast_request, is_matched,
                       req_lat, req_lon
                FROM freight_request
                WHERE id = %s
            """
            self.cursor.execute(query, (request_id,))
            return self.cursor.fetchone()
        except Exception as e:
            print(f"[ERROR] freight_request 조회 실패: {e}")
            return None
        finally:
            self.disconnect()

    def get_driver_matches(self, driver_id: str):
        """
        driver_id 로 매칭 목록을 조회해 dict 리스트로 반환
        """
        try:
            self.connect()
            sql = """
                SELECT
                    m.id            AS id,
                    fr.origin       AS origin,
                    fr.destination  AS destination,
                    fr.cargo_type   AS cargo_type,
                    fr.weight       AS weight,
                    fr.price        AS price,
                    fr.request_time AS request_time,
                    m.created_at    AS created_at
                FROM matches AS m
                JOIN freight_request AS fr
                  ON fr.id = m.request_id
                WHERE m.driver_id = %s
                  AND m.status    = 0
                ORDER BY m.created_at DESC
            """
            self.cursor.execute(sql, (driver_id,))
            return self.cursor.fetchall()   # → [ { 'id':..., 'origin':..., … }, … ]
        except Exception as e:
            print(f"[ERROR] get_driver_matches 실패: {e}")
            return []
        finally:
            self.disconnect()

    def get_matched_request_by_id(self, match_id: int):
        """
        match_id 에 해당하는 단일 매칭 정보를 dict 로 반환
        """
        try:
            self.connect()
            sql = """
                SELECT
                    m.id            AS id,
                    fr.origin       AS origin,
                    fr.destination  AS destination,
                    fr.cargo_type   AS cargo_type,
                    fr.weight       AS weight,
                    fr.price        AS price,
                    fr.request_time AS request_time,
                    m.created_at    AS created_at
                FROM matches AS m
                JOIN freight_request AS fr
                  ON fr.id = m.request_id
                WHERE m.id = %s
            """
            self.cursor.execute(sql, (match_id,))
            return self.cursor.fetchone()  # → { 'id':..., 'origin':..., … } or None
        except Exception as e:
            print(f"[ERROR] get_matched_request_by_id 실패: {e}")
            return None
        finally:
            self.disconnect()


    
    def get_driver_by_id(self, driver_id):
        try:
            self.connect()
            # is_active, rating, nickname 등은 그대로 둡니다.
            # vehicle, status, latitude, longitude, location_updated_at은 이 함수에서 가져오지 않습니다.
            query = """
                SELECT name, driver_id, nickname, rating, is_active
                FROM drivers
                WHERE driver_id = %s
            """
            self.cursor.execute(query, (driver_id,))
            return self.cursor.fetchone()
        except Exception as e:
            print(f"기사 정보 조회 실패: {e}")
            return []
        finally:
            self.disconnect()
    
    # 추천 정보 삽입( 기사 순위 정보 바뀔때마다 업데이트)
    def upsert_recommendation(self, request_id, driver_id, score, distance , rank):
        try:
            self.connect()
            query = """
            INSERT INTO recommended_matches (request_id, driver_id, score, distance, rank)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                score = VALUES(score),
                distance = VALUES(distance),
                rank = VALUES(rank),
                status = IF(status = 'accepted', 'accepted', 'pending'),  -- ✅ 이미 accepted면 유지
                created_at = NOW(),
                responded_at = NULL
            """
            self.cursor.execute(query, (request_id, driver_id, score, distance, rank))
            self.connection.commit()
        except Exception as e:
            print(f"기사 정보 조회 실패: {e}")
        finally:    
            self.disconnect()

    # 기사 아이디로 추천된 모든 정보 가져오기
    def select_recommend_matches_by_id(self, driver_id):
        try:
            self.connect()
            query = """
                SELECT request_id
                FROM recommended_matches
                WHERE driver_id = %s
                """
            self.cursor.execute(query, (driver_id,))
            return self.cursor.fetchall()
        except Exception as e:
            print(f"추천 테이블에서 화물 아이디 조회 실패: {e}")
            return []
        finally:
            self.disconnect()

    # 드라이버 아이디로 추천된 결과 가져오기
    def select_recommend_driver_by_id(self, driver_id):
        try:
            self.connect()
            query = """
                SELECT *
                FROM recommended_matches
                WHERE driver_id = %s
                """
            self.cursor.execute(query, (driver_id,))
            return self.cursor.fetchall()
        except Exception as e:
            print(f"추천 테이블에서 정보 조회 실패: {e}")
            return []
        finally:
            self.disconnect()

    
    def update_recommended_matchies_status(self, request_id, driver_id):
        try: 
            self.connect()
            query = """
                    UPDATE recommended_matches 
                    SET status = 'accepted'
                    WHERE request_id = %s and driver_id = %s 
                    """
            self.cursor.execute(query,(request_id,driver_id))
            self.connection.commit()
            print("추천 매칭 상태 업데이트 성공")
        except Exception as e:
            print(f"❌ 추천 매칭 상태 업데이트 실패: {e}")
        finally:
            self.disconnect()

    def accept_recommended_match(self, request_id, driver_id):
        try:
            self.connect()
            
            query_update = """
                UPDATE recommended_matches 
                SET status = 'accepted', responded_at = NOW()
                WHERE request_id = %s AND driver_id = %s AND status <> 'accepted'
            """
            self.cursor.execute(query_update, (request_id, driver_id))
            
            print("🟡 rowcount 확인:", self.cursor.rowcount)
            print("🟡 요청된 request_id, driver_id:", request_id, driver_id)

            if self.cursor.rowcount == 0:
                print("❗ 이미 수락된 상태이거나, 유효하지 않은 요청입니다.")
                return False

            print("🟢 matches INSERT 시도")
            query_insert = """
                INSERT INTO matches (request_id, driver_id, created_at)
                VALUES (%s, %s, NOW())
                ON DUPLICATE KEY UPDATE created_at = NOW()
            """
            self.cursor.execute(query_insert, (request_id, driver_id))

            self.connection.commit()
            print("✅ 추천 매칭 수락 및 matches 테이블 삽입 또는 갱신 성공")
            return True

        except Exception as e:
            self.connection.rollback()
            print("🔴 matches 삽입 중 rollback 발생")
            print(f"❌ 오류 내용: {e}")
            return False

        finally:
            self.disconnect()

    # def accept_recommended_match(self, request_id, driver_id):
    #     try:
    #         self.connect()
            
    #         query_update = """
    #             UPDATE recommended_matches 
    #             SET status = 'accepted', responded_at = NOW()
    #             WHERE request_id = %s AND driver_id = %s AND status <> 'accepted'
    #         """
    #         self.cursor.execute(query_update, (request_id, driver_id))
            
    #         print("🟡 rowcount 확인:", self.cursor.rowcount)
    #         print("🟡 요청된 request_id, driver_id:", request_id, driver_id)

    #         if self.cursor.rowcount == 0:
    #             print("❗ 이미 수락된 상태이거나, 유효하지 않은 요청입니다.")
    #             return False

    #         print("🟢 matches INSERT 시도")
    #         query_insert = """
    #             INSERT INTO matches (request_id, driver_id, created_at)
    #             VALUES (%s, %s, NOW())
    #         """
    #         self.cursor.execute(query_insert, (request_id, driver_id))

    #         query_match_update = """
    #             UPDATE freight_request SET is_matched = 1 WHERE id = %s
    #         """
    #         self.cursor.execute(query_match_update, (request_id,))

    #         self.connection.commit()
    #         print("✅ 추천 매칭 수락 및 matches 테이블 삽입 성공")
    #         return True

    #     except Exception as e:
    #         self.connection.rollback()
    #         print("🔴 matches 삽입 중 rollback 발생")
    #         print(f"❌ 오류 내용: {e}")
    #         return False

    #     finally:
    #         self.disconnect()


    # (기사데이터 : name, rating, truck_type, truck_info, 추천 정보 : 순위, 예상 접근 거리- 📍 "출발지까지 거리: {{ distance }}km")
    # 화물데이터 : origin, destination, cargo_type, weight, pickup_deadline
    ## 화물정보로 추천 기사 데이터 가져오기
    def get_recommended_matches(self, request_id):
        try:
            self.connect()
            query = """
            SELECT 
            rm.request_id,
            rm.driver_id,
            rm.distance,
            rm.rank,
            d.name AS driver_name,
            d.rating driver_rating,
            d.total_requests AS driver_total_requests,
            v.truck_type,
            v.capacity,
            v.vehicle_num,
            v.truck_info
            FROM recommended_matches rm
            INNER JOIN drivers d ON d.driver_id = rm.driver_id
            INNER JOIN vehicles v ON d.driver_id = v.driver_id
            WHERE rm.request_id = %s and rm.status = 'accepted'
            ORDER BY rm.rank;
            """
            self.cursor.execute(query, (request_id,))
            return self.cursor.fetchall()
        except Exception as e:
            print(f"추천 기사 정보 조회 실패: {e}")
            return []
        finally:
            self.disconnect()