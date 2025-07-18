import mysql.connector
from datetime import datetime
from flask import jsonify
import json
import requests
import re


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
            self.cursor = self.connection.cursor(dictionary=True)

        except mysql.connector.Error as error:
            print(f"데이터베이스 연결 실패 : {error}")

    ## 데이터베이스 연결해제
    def disconnect(self):
        if self.connection and self.connection.is_connected():
            self.cursor.close()
            self.connection.close()


    ## 회원가입 화주
    def insert_shipper(self,name: str,shipper_id: str,shipper_pw: str,nickname: str,business_registration_num: str | None, phone: str,email: str | None,birth_date: str,gender: int,address: str,profile_img_path: str | None):
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
            print("✅ 화주 회원정보 삽입 성공")
        except Exception as e:
            print(f"❌ 화주 회원정보 삽입 실패: {e}")
        finally:
            self.disconnect()


    ## 회원가입 기사
    def insert_driver(self,name: str,driver_id: str,driver_pw: str,nickname: str,business_registration_num: str | None,phone: str,email: str | None,birth_date: str,gender: int,address: str,profile_img_path: str | None):
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
            print("✅ 기사 회원정보 삽입 성공")
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
            print("화물 운송 요청 데이터 삽입 성공")
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
            print("화물 운송 신청 데이터 조회 성공")
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
            print("화물 매칭 기사 데이터 조회 성공")
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
            print("기사 아이디로 기사+ 차량 데이터 정보 조회")
            return self.cursor.fetchone()
        except Exception as e:
            print(f"기사 아이디로 기사+ 차량 데이터 정보 조회 실패 : {e}")
        finally:
            self.disconnect()

    # 관리자 정보 조회
    def select_admin_by_id(self, admin_id):
        try:
            self.connect()
            query = "select * from admins where admin_id = %s"
            self.cursor.execute(query, (admin_id,))
            print("관리자 정보 조회 성공")
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
            print("화주 아이디로 매칭 정보, 운전자 정보 조회 성공")
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
            print("운송 요청 아이디로 정보 조회 성공")
            return self.cursor.fetchall()

        except Exception as e:
            print(f"운송 요청 아이디로 정보 조회 실패: {e}")
            return None
        finally:
            self.disconnect()


     ## 화주 운송 요청 정보 조회(운송요청아이디)
    def select_request_by_id(self, id):
        try:
            self.connect()
            query = """
            SELECT * FROM freight_request
            WHERE id = %s
            """
            value = (id,)
            self.cursor.execute(query, value)
            print("운송 요청 아이디로 정보 조회 성공")
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
            print("운전자 정보 아이디로 조회 성공")
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
            print("✅ 매칭 내역 조회 성공")
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
            print("화주 테이블 조회")
            return self.cursor.fetchone()
        except Exception as e:
            print(f"화주 테이블 조회 실패: {e}")
        finally:
            self.disconnect()


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
            print("✅ payments 테이블 생성 또는 확인 완료")
        except Exception as e:
            print(f"❌ payments 테이블 생성 실패: {e}")
        finally:
            self.disconnect()

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


    # 운전자 상태 업데이트 함수 (아래 2번 문제 해결을 위해 필요)
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
            print("화물 운송 신청 데이터 조회 성공")
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
            print("화물기사 추천 테이블 조회 성공")
            return self.cursor.fetchall
        except Exception as e:
            print(f"화물기사 추천 테이블 조회 실패 : {e}")
            return []
        finally:
            self.disconnect()