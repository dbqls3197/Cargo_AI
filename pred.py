import pandas as pd
import numpy as np
import pickle
import mysql.connector
from math import radians, sin, cos, sqrt, atan2


# --- 1. DB 관리 전용 클래스 ---
class PDManager:
    def __init__(self):
        self.connection = None
        self.cursor = None

    def connect(self):
        try:
            self.connection = mysql.connector.connect(
                host="10.0.66.3", user="suyong", password="1234",
                database="cargo_ai", charset="utf8mb4"
            )
            self.cursor = self.connection.cursor(dictionary=True)
            print("✅ DB 연결 성공")
        except mysql.connector.Error as error:
            print(f"🚨 DB 연결 실패: {error}")
            self.connection = None

    def disconnect(self):
        if self.connection and self.connection.is_connected():
            self.cursor.close()
            self.connection.close()
            print("ℹ️ DB 연결 해제")

    def fetch_data_to_dataframe(self, data):
        if not self.connection or not self.connection.is_connected():
            print("🚨 DB 미연결 상태")
            return pd.DataFrame()
        try:
            self.cursor.execute(query, params)
            return pd.DataFrame(data )
        except mysql.connector.Error as error:
            print(f"🚨 쿼리 오류: {error}")
            return pd.DataFrame()


# --- 2. 모델 예측 클래스 ---
class ModelPredictor:
    def __init__(self, model):
        self.model = model
        self.db = PDManager()

    def haversine_distance(self, lat1, lon1, lat2, lon2):
        if any(v is None for v in [lat1, lon1, lat2, lon2]):
            return np.nan
        R = 6371.0
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
        return R * 2 * atan2(sqrt(a), sqrt(1 - a))

    def prepare_data(self, req_df, drv_df, loc_df):
        if req_df.empty or drv_df.empty or loc_df.empty:
            print("🚨 준비 실패: 데이터프레임이 비어 있음")
            return pd.DataFrame()

        req_df['key'] = 1
        drv_df['key'] = 1
        df = pd.merge(req_df, drv_df, on='key').drop('key', axis=1)
        df = pd.merge(df, loc_df, on='driver_id', how='left')

        df.dropna(subset=['req_lat', 'req_lon', 'driver_lat', 'driver_lon'], inplace=True)

        if df.empty:
            print("🚨 유효한 기사 없음 (좌표 없음)")
            return pd.DataFrame()

        df['distance'] = df.apply(
            lambda row: self.haversine_distance(row['req_lat'], row['req_lon'], row['driver_lat'], row['driver_lon']), axis=1)
        df['time_taken'] = df['distance'] / 40 * 60
        df['rejection_prob'] = df['distance'] / (df['distance'].max() + 1e-6)

        print("✅ 데이터 준비 완료")
        return df

    def predict(self, df):
        if df.empty:
            return pd.DataFrame()

        if self.model is None:
            return df.sort_values(by='distance', ascending=True)

        features = ['driver_lat', 'driver_lon', 'req_lat', 'req_lon', 'time_slot', 'vehicle_type', 'cargo_type',
                    'distance', 'time_taken', 'rejection_prob']

        for col in features:
            if col not in df.columns:
                df[col] = 0
                print(f"⚠️ 누락 피처 보완: {col}")

        df['predicted_score'] = self.model.predict(df[features])
        print("✅ 예측 완료")
        return df.sort_values(by='predicted_score', ascending=False)

    def recommend_for_request(self, request_id):
        try:
            self.db.connect()

            query_req = "SELECT * FROM requests WHERE req_id = %s"
            query_drv = "SELECT * FROM drivers WHERE status = 'available'"
            query_loc = "SELECT * FROM driver_locations"

            df_req = self.db.fetch_data_to_dataframe(query_req, (request_id,))
            df_drv = self.db.fetch_data_to_dataframe(query_drv)
            df_loc = self.db.fetch_data_to_dataframe(query_loc)

            print(f"📦 요청 {len(df_req)}, 🚚 기사 {len(df_drv)}, 📍 위치 {len(df_loc)}")

            df_prepared = self.prepare_data(df_req, df_drv, df_loc)
            return self.predict(df_prepared)

        finally:
            self.db.disconnect()


# --- 3. 모델 로더 함수 ---
def load_model(path):
    try:
        with open(path, 'rb') as f:
            model = pickle.load(f)
        print(f"✅ 모델 로드 성공: {path}")
        return model
    except FileNotFoundError:
        print(f"🚨 모델 파일 없음: {path}")
        return None
    except Exception as e:
        print(f"🚨 모델 로드 실패: {e}")
        return None



