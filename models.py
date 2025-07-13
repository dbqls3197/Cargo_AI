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
    
    def create_shipper_requests_table(self):
        try : 
            self.connect()
            create_query = """
            CREATE TABLE IF NOT EXISTS shipper_requests (
                id INT AUTO_INCREMENT PRIMARY KEY,
                origin VARCHAR(255),
                destination VARCHAR(255),
                item_type VARCHAR(100),
                item_weight FLOAT,
                vehicle_type VARCHAR(100),
                pickup_date DATE,
                pickup_time TIME,
                dropoff_date DATE,
                dropoff_time TIME,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
            self.cursor.execute(create_query)
            self.connection.commit()
            print("화물 의뢰 테이블 생성 성공")
        except Exception as error:
            print(f"화물 의뢰 테이블 생성 실패: {error}")
        finally:
            self.disconnect()

    # 운송 요청 저장 함수
    def insert_shipper_request(self, data):
        try : 
            self.connect()
            insert_query = """
            INSERT INTO shipper_requests (
                origin, destination, item_type, item_weight,
                vehicle_type, pickup_date, pickup_time,
                dropoff_date, dropoff_time
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            values = (
                data['origin'],
                data['destination'],
                data['itemType'],
                data['itemWeight'],
                data['vehicleType'],
                data['pickupDate'],
                data['pickupTime'],
                data['dropoffDate'],
                data['dropoffTime']
            )
            self.cursor.execute(insert_query, values)
            self.connection.commit()
        except Exception as error:
            print(f"화물 의뢰 데이터 삽입 실패: {error}")
        finally:
            self.disconnect()