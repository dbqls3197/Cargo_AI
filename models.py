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
        try :
            self.connection = mysql.connector.connect(
                host = "10.0.66.3",
                user = "suyong",
                password="1234",
                database="cargo_ai",
                charset="utf8mb4"
            )
            self.cursor = self.connection.cursor(dictionary=True)
        
        except mysql.connector.Error as error :
            print(f"데이터베이스 연결 실패 : {error}")
    
    ## 데이터베이스 연결해제
    def disconnect(self):
        if self.connection and self.connection.is_connected():
            self.cursor.close()
            self.connection.close()
    
    # 화주 운송신청 테이블 생성
    def create_shipper_requests_table(self):
        try : 
            self.connect()
            create_query = """
            CREATE TABLE IF NOT EXISTS shipper_requests (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id VARCHAR(255),
                origin VARCHAR(255),
                destination VARCHAR(255),
                item_type VARCHAR(50),
                item_weight FLOAT,
                vehicle_type VARCHAR(50),
                pickup_date DATE,
                pickup_time TIME,
                dropoff_date DATE,
                dropoff_time TIME,
                fee INT,
                is_waiting TINYINT DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
            self.cursor.execute(create_query)
            self.connection.commit()
            print("화물 운송 신청 테이블 생성 성공")
        except Exception as e:
            print(f"화물 운송 신청 테이블 생성 실패: {e}")
        finally:
            self.disconnect()

    # 운송 요청 저장 
    def insert_shipper_request(self, user_id, data):
        try : 
            self.connect()
            insert_query = """
            INSERT INTO shipper_requests (
                user_id, origin, destination, item_type, item_weight,
                vehicle_type, pickup_date, pickup_time,
                dropoff_date, dropoff_time, fee
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            values = (
                user_id,
                data['origin'],
                data['destination'],
                data['item_type'],
                data['item_weight'],
                data['vehicle_type'],
                data['pickup_date'],
                data['pickup_time'],
                data['dropoff_date'],
                data['dropoff_time'],
                data['fee']
            )
            self.cursor.execute(insert_query, values)
            self.connection.commit()
            print("화물 운송 신청 데이터 삽입 성공")
        except Exception as e:
            print(f"화물 운송 신청 데이터 삽입 실패: {e}")
        finally:
            self.disconnect()

    # 운송 요청 조회 
    def select_shipper_requests_by_id(self,user_id):
        try : 
            self.connect()
            query = """
            select * from shipper_requests where user_id = %s
            """
            value = (user_id,)
            self.cursor.execute(query,value)
            print("화물 운송 신청 데이터 조회 성공")
            return self.cursor.fetchall()
        except Exception as e:
            print(f"화물 운송 신청 데이터 조회 실패: {e}")
        finally:
            self.disconnect()

    
    #기사 테이블 생성
    def create_driver_table(self):
        try:
            self.connect()
            query = """
            CREATE TABLE IF NOT EXISTS drivers (
                driver_id VARCHAR(100) PRIMARY KEY,
                password VARCHAR(100) NOT NULL,
                name VARCHAR(100) NOT NULL,
                phone VARCHAR(20),
                vehicle_type VARCHAR(50),
                vehicle_capacity FLOAT,
                experience_years INT,
                rating FLOAT,
                accept_rate FLOAT,
                total_deliveries INT DEFAULT 0,
                accident_history TEXT,
                avg_time_delay FLOAT DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            """
            self.cursor.execute(query)
            self.connection.commit()
            print("기사 테이블 생성 성공")
        except Exception as e:
            print(f"기사 테이블 생성 실패: {e}")
        finally:
            self.disconnect()

    #매칭될 기사 조회
    def select_matching_driver(self):
        try : 
            self.connect()
            query = """
            select * from drivers
            """
            self.cursor.execute(query)
            print("화물 매칭 기사 데이터 조회 성공")
            return self.cursor.fetchall()
        except Exception as e:
            print(f"화물 매칭 기사 데이터 조회 실패: {e}")
        finally:
            self.disconnect()

    # 화주 테이블 생성
    def create_shipper_table(self):
        try:
            self.connect()
            query = """
            CREATE TABLE IF NOT EXISTS shippers (
                shipper_id VARCHAR(100) PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                user_id VARCHAR(50) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                phone VARCHAR(20),
                company_name VARCHAR(100),
                total_request INT,
                total_payment INT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            """
            self.cursor.execute(query)
            self.connection.commit()
            print("화주 테이블 생성 성공")
        except Exception as e:
            print(f"❌ 화주 테이블 생성 실패: {e}")
        finally:
            self.disconnect()

    # # 화주 운송 요청 정보 조회(화주 아이디)
    def select_request_by_user_id(self, user_id):
        try:
            self.connect()
            query = """
            SELECT * FROM shipper_requests
            WHERE user_id = %s
            """
            value =(user_id,)
            self.cursor.execute(query, value)
            print("운송 요청 아이디로 정보 조회 성공")
            return self.cursor.fetchall()

        except Exception as e:
            print(f"운송 요청 아이디로 정보 조회 실패: {e}")
            return None
        finally:
            self.disconnect()




    # 화주 운송 요청 정보 조회(운송요청아이디)
    def select_request_by_id(self, request_id):
        try:
            self.connect()
            query = """
            SELECT * FROM shipper_requests
            WHERE id = %s
            """
            value =(request_id,)
            self.cursor.execute(query, value)
            print("운송 요청 아이디로 정보 조회 성공")
            return self.cursor.fetchone()

        except Exception as e:
            print(f"운송 요청 아이디로 정보 조회 실패: {e}")
            return None
        finally:
            self.disconnect()

    # 운전자 id로 운전자 정보 조회
    def select_driver_by_id(self, driver_id):
        try:
            self.connect()
            query = """
            SELECT * FROM drivers
            WHERE driver_id = %s
            """
            value =(driver_id,)
            self.cursor.execute(query, value)
            print("운전자 정보 아이디로 조회 성공")
            return self.cursor.fetchone()

        except Exception as e:
            print(f"운전자 정보 아이디로 조회 실패: {e}")
            return None
        finally:
            self.disconnect()

    # 매칭 완료 테이블 생성
    def create_matching_table(self):
        try:
            self.connect()
            query = """
            CREATE TABLE IF NOT EXISTS matching_driver_my_request (
                match_id INT AUTO_INCREMENT PRIMARY KEY,
                user_id VARCHAR(255),
                request_id INT,
                driver_id VARCHAR(50),
                origin TEXT,
                destination TEXT,
                item_type VARCHAR(100),
                item_weight FLOAT,
                vehicle_type VARCHAR(50),
                pickup_date DATE,
                pickup_time TIME,
                dropoff_date DATE,
                dropoff_time TIME,
                fee INT,
                driver_name VARCHAR(100),
                driver_phone VARCHAR(20),
                driver_vehicle_capacity FLOAT,
                experience_years INT,
                rating FLOAT,
                accept_rate FLOAT,
                total_deliveries INT,
                accident_history TEXT,
                avg_delay_time FLOAT,
                `delivery_status` ENUM('in_progress', 'completed') DEFAULT 'in_progress',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
            self.cursor.execute(query)
            self.connection.commit()
            
        except Exception as e:
            print(f"❌ 테이블 생성 오류: {e}")
        finally:
            self.disconnect()


    # 매칭 완료 정보 저장 
    def insert_matching_result(self, user_id, request_data, driver_data):
        try:
            self.connect()
            query = """
            INSERT INTO matching_driver_my_request (
                user_id, request_id, driver_id, origin, destination, item_type, item_weight, vehicle_type,
                pickup_date, pickup_time, dropoff_date, dropoff_time, fee,
                driver_name, driver_phone, driver_vehicle_capacity, experience_years,
                rating, accept_rate, total_deliveries, accident_history, avg_delay_time
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s, %s
            )
            """
            values = (
                user_id,
                request_data['id'], driver_data['driver_id'], request_data['origin'], request_data['destination'],
                request_data['item_type'], request_data['item_weight'], request_data['vehicle_type'],
                request_data['pickup_date'], str(request_data['pickup_time']),
                request_data['dropoff_date'], str(request_data['dropoff_time']), request_data['fee'],
                driver_data['name'], driver_data['phone'], driver_data['vehicle_capacity'],
                driver_data['experience_years'], driver_data['rating'], driver_data['accept_rate'],
                driver_data['total_deliveries'], driver_data['accident_history'],
                driver_data['avg_delay_time']
            )
            self.cursor.execute(query, values)
            self.connection.commit()
            print("매칭 결과 저장 성공")
        except Exception as e:
            print(f"❌ 매칭 결과 저장 오류: {e}")
        finally:
            self.disconnect()

    # 화물 요청 매칭대기중->매칭완료 변경
    def update_request_status_to_matched(self, request_id):
        try:
            self.connect()
            query = "UPDATE shipper_requests SET is_waiting = 0 WHERE id = %s"
            self.cursor.execute(query, (request_id,))
            self.connection.commit()
            print("is_waiting 상태 업데이트 완료")
        except Exception as e:
            print(f"is_waiting 상태 업데이트 실패: {e}")
        finally:
            self.disconnect()

    # 매칭완료결과 확인 
    def select_matching_driver_my_request(self, user_id, driver_id, request_id):
        try:
            self.connect()
            query = "select * from matching_driver_my_request WHERE user_id = %s and driver_id = %s and request_id = %s"
            self.cursor.execute(query, (user_id, driver_id, request_id))
            print("매칭완료 테이블 조회")
            return self.cursor.fetchall()
        except Exception as e:
            print(f"매칭완료 테이블 조회 실패: {e}")
        finally:
            self.disconnect()
    
    # 매칭 내역 조회
    def select_matching_driver_my_request_by_id(self, user_id):
        try:
            self.connect()
            query = "select * from matching_driver_my_request WHERE user_id = %s"
            self.cursor.execute(query, (user_id,))
            print("매칭완료 테이블 조회")
            return self.cursor.fetchall()
        except Exception as e:
            print(f"매칭완료 테이블 조회 실패: {e}")
        finally:
            self.disconnect()


    # 화주 아이디로 정보 조회
    def select_shipper_by_id(self, user_id):
        try:
            self.connect()
            query = "select * from shippers WHERE user_id = %s"
            self.cursor.execute(query, (user_id,))
            print("화주 테이블 조회")
            return self.cursor.fetchone()
        except Exception as e:
            print(f"화주 테이블 조회 실패: {e}")
        finally:
            self.disconnect()

    # 화주 결제 내역 테이블 생성
    def create_my_payments_table(self):
        try:
            self.connect()
            create_query = """
            CREATE TABLE IF NOT EXISTS my_payments (
                payment_id INT AUTO_INCREMENT PRIMARY KEY,
                user_id VARCHAR(255) NOT NULL,
                match_id INT NOT NULL,
                driver_id VARCHAR(50) NOT NULL,
                fee INT NOT NULL,
                commission INT NOT NULL,
                total_amount INT NOT NULL,
                is_paid TINYINT DEFAULT 0,
                paid_at DATETIME DEFAULT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                origin TEXT,
                destination TEXT,
                driver_name VARCHAR(100),
                driver_phone VARCHAR(20),
                FOREIGN KEY (match_id) REFERENCES matching_driver_my_request(match_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """
            self.cursor.execute(create_query)
            self.connection.commit()
            print("결제 내역 테이블 생성 완료")
        except Exception as e:
            print(f"결제 내역 테이블 생성 오류: {e}")
        finally:
            self.disconnect()
    
    # 결제 내역 테이블 정보 삽입
    def insert_payment(self, payment_data):
        try:
            self.connect()
            insert_query = """
            INSERT INTO my_payments (
                user_id, match_id, driver_id,
                fee, commission, total_amount,
                origin, destination,
                driver_name, driver_phone
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            values = (
                payment_data["user_id"],
                payment_data["match_id"],
                payment_data["driver_id"],
                payment_data["fee"],
                payment_data["commission"],
                payment_data["total_amount"],
                payment_data.get("origin"),
                payment_data.get("destination"),
                payment_data.get("driver_name"),
                payment_data.get("driver_phone")
            )
            self.cursor.execute(insert_query, values)
            self.connection.commit()
            print("결제 정보 삽입 성공")
        except Exception as e:
            print(f"결제 정보 삽입 오류: {e}")
        finally:
            self.disconnect()
    
    # 결제 내역 id로 조회하기
    def select_payments_by_id(self,user_id):
        try:
            self.connect()
            query = "select * from my_payments WHERE user_id = %s"
            self.cursor.execute(query, (user_id,))
            print("화주 테이블 조회")
            return self.cursor.fetchall()
        except Exception as e:
            print(f"화주 테이블 조회 실패: {e}")
        finally:
            self.disconnect()
    
    # 결제 상태 업데이트
    def update_payment_is_paid(self, match_id):
        try:
            self.connect()
            query = """
                    UPDATE my_payments 
                    SET is_paid = 1, paid_at = NOW() 
                    WHERE match_id = %s AND is_paid = 0
                    """
            self.cursor.execute(query, (match_id,))
            self.connection.commit()
            print("is_paid 상태 업데이트 완료")
        except Exception as e:
            print(f"is_paid 상태 업데이트 실패: {e}")
        finally:
            self.disconnect()
        