from flask import Flask, render_template, request, jsonify, session, url_for, redirect, Response
from models import DBManager
import json
import requests
from functools import wraps
import threading
import queue
from kafka import KafkaProducer, KafkaConsumer

# Flask 앱을 생성합니다.
app = Flask(__name__)

# 전역 변수들
received_data_list = []
clients = []

app.secret_key = "your_super_secret_key"


# API 키들
TMAP_API_KEY = "eEl7AGPzATadBLtufoN4i6dSx6RZGpcT8Bpq5zsj"
KAKAO_API_KEY = "b57c96e18902eff2c9b26c47c7c9f066"

manager = DBManager()

manager.create_shipper_requests_table()
manager.create_driver_table()
manager.create_shipper_table()


# Kafka Producer 설정
try:
    producer = KafkaProducer(
        bootstrap_servers=['kafka:9092'],
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
    kafka_enabled = True
except Exception as e:
    print(f"Kafka 연결 실패: {e}")
    kafka_enabled = False
    producer = None

#화주 데코레이터
from functools import wraps
from flask import session, redirect, url_for, flash

def login_required_shipper(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'id' not in session or session.get('role') != 'shipper':
            flash('화주 전용 페이지입니다.')
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function

def login_required_driver(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'id' not in session or session.get('role') != 'driver':
            flash('기사 전용 페이지입니다.')
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function

# 루트 URL ('/')에 접속했을 때 index.html 파일을 렌더링합니다.
@app.route('/')
def index():
    return render_template('public/index.html')

# 로그인 페이지
@app.route('/login', methods=['POST'])
def login():
    session['id'] = request.form['user_id']
    session['pw'] = request.form['password']
    user_id = session['id']
    user = manager.select_shipper_by_id(user_id)
    driver = manager.select_driver_by_id(user_id)
    
    if user:
        session['role'] = 'shipper'
        return redirect(url_for('shipper_dashboard'))
    elif driver:
        session['role'] = 'driver'
        return redirect(url_for('driver_dashboard'))
    else:
        return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.clear()  # 또는 session.pop('id', None) 등으로 개별 제거 가능
    return redirect(url_for('index'))

#회원가입페이지    
@app.route('/register')
def register():
    return render_template('public/register.html') 

#데코레이터

# 화주 페이지
## 화주 대시보드
@app.route('/shipper/dashboard')
@login_required_shipper
def shipper_dashboard():
    user_id = session['id']
    my_requests = manager.select_request_by_user_id(user_id)
    all_count = len(my_requests)
    matchings = manager.select_matching_driver_my_request_by_id(user_id)
    in_progress = [mat for mat in matchings if mat.get('delivery_status') == 'in_progress']
    in_progress_count = len(in_progress)
    completed = [mat for mat in matchings if mat.get('delivery_status') == 'completed']
    completed_count = len(completed)
    print(in_progress)
    return render_template('shipper/dashboard.html', my_requests=my_requests, matchings=matchings, in_progress=in_progress, all_count=all_count, in_progress_count= in_progress_count, completed_count=completed_count )

## 화주 화물 의뢰 페이지
@app.route('/shipper/shipper_request')
@login_required_shipper
def shipper_request():
    return render_template('shipper/shipper_request.html')

## 화주 화물 의뢰 정보 DB 저장
@app.route("/shipper/request/submit", methods=["POST"])
@login_required_shipper
def submit_shipper_request():
    try:
        data = request.get_json()
        user_id = session['id']
        print(data)
        print(user_id)
        manager.insert_shipper_request(user_id,data)
        return jsonify({"success": True, "message": "요청이 성공적으로 저장되었습니다."})
    except Exception as e:
        print(f"[에러] 운송 요청 저장 중 오류: {e}")
        return jsonify({"success": False, "message": "운송 요청 저장 중 오류 발생"})

## 화주 운송신청 리스트
@app.route("/shipper/my_requests")
@login_required_shipper
def shipper_my_requests():
    user_id = session['id']
    all_requests = manager.select_shipper_requests_by_id(user_id)
    
    # is_waiting == 1 인 요청만 필터링
    my_requests = [req for req in all_requests if req.get('is_waiting') == 1]
    print(f"나의 요청 목록 : {my_requests}")
    return render_template("shipper/my_requests.html", my_requests=my_requests)


## 기사 매칭 페이지 
@app.route('/shipper/driver_matching')
@login_required_shipper
def driver_matching():
    request_id = request.args.get('id')
    my_request = manager.select_request_by_id(request_id)
    vehicle_type = my_request['vehicle_type']
    all_drivers = manager.select_matching_driver()
    drivers = [driver for driver in all_drivers if driver.get('vehicle_type') == vehicle_type]
    return render_template('shipper/driver_matching.html', drivers=drivers, request_id=request_id)

## 매칭 결과 페이지 
@app.route('/shipper/matching_result', methods=['POST'])
@login_required_shipper
def driver_matching_result():
    request_id = request.form['request_id']
    driver_id = request.form['driver_id']
    user_id = session['id']
    my_request = manager.select_request_by_id(request_id)
    driver = manager.select_driver_by_id(driver_id)

    print(my_request)
    print(driver)
    
    manager.create_matching_table()
    manager.insert_matching_result(user_id, my_request, driver)
    manager.update_request_status_to_matched(request_id)
    my_matching = manager.select_matching_driver_my_request(user_id, driver_id, request_id)
    print(my_matching)
    return render_template("shipper/driver_matching_result.html", my_request=my_request, driver=driver, my_matching=my_matching)

## 화주 운송 내역 페이지
@app.route('/shipper/my_shipments')
@login_required_shipper
def shipper_my_shipments():
    user_id = session['id']
    my_matchings = manager.select_matching_driver_my_request_by_id(user_id)
    print(my_matchings)
    return render_template('shipper/my_shipments.html', my_matchings = my_matchings)

## 화주 결제 페이지
@app.route('/shipper/payments')
@login_required_shipper
def shipper_payments():
    user_id = session['id']
    all_matchings = manager.select_matching_driver_my_request_by_id(user_id)
    completed_delivery = [pay for pay in all_matchings if pay.get('delivery_status') == 'completed']
    print(completed_delivery)
    manager.create_my_payments_table()
    
     # 기존에 저장된 match_id들 조회
    existing_payment_match_ids = set(match["match_id"] for match in manager.select_payments_by_id(user_id))

    for match in completed_delivery:
        if match["match_id"] in existing_payment_match_ids:
            continue  # 이미 결제 테이블에 삽입된 match_id는 건너뜀

        fee = int(match.get('fee', 0))  # 운임료
        commission = int(fee * 0.05)    # 수수료 5%
        total = fee + commission

        payment_data = {
            "user_id": user_id,
            "match_id": match["match_id"],
            "driver_id": match["driver_id"],
            "fee": fee,
            "commission": commission,
            "total_amount": total,
            "origin": match.get("origin"),
            "destination": match.get("destination"),
            "driver_name": match.get("driver_name"),
            "driver_phone": match.get("driver_phone")
        }

        manager.insert_payment(payment_data)

    all_payment = manager.select_payments_by_id(user_id)
    payments = [pay for pay in all_payment if pay.get('is_paid') == 0]
    return render_template('shipper/payments.html', payments=payments)

## 결제 완료 API
@app.route("/api/process_payment", methods=["POST"])
@login_required_shipper
def process_payment():
    data = request.get_json()
    match_id = data.get("match_id")

    # 여기에 실제 결제 처리 로직
    print(f"결제 요청: {match_id}")
    # 예시 성공 응답
    manager.update_payment_is_paid(match_id)
    return jsonify(success=True)

## 화주 마이페이지
@app.route('/shipper/my_page')
@login_required_shipper
def shipper_my_page():
    user_id = session['id']
    shipper = manager.select_shipper_by_id(user_id)
    print(shipper)
    return render_template('shipper/my_page.html', shipper=shipper)

# ---------------------------------------------------------------------------------------------------
# 화물기사 대시보드
@app.route('/driver/dashboard')
@login_required_driver
def driver_dashboard():
    return render_template('driver/dashboard.html')

# 화물기사 요청 화물 상세정보
@app.route('/<int:request_id>')
@login_required_driver
def request_detail(request_id):
    return render_template('driver/request_detail.html', request_id=request_id)

# 화물기사 요청 화물 수락 
@app.route('/request_accept_success')
@login_required_driver
def request_accept_success():
    return render_template('driver/request_accept_success.html')

# 네비게이션
@app.route("/navigation")
@login_required_driver
def navigation_page():
    return render_template("driver/navigation.html")


# 운송 내역
matches = [
    {"id": 1, "company": "(주)가나다 물류", "date": "2025-07-08", "cargo": "가구", "weight": 165, "price": 103000,
     "reviewed": False},
    {"id": 2, "company": "ABC 전자", "date": "2025-07-05", "cargo": "전자제품", "weight": 80, "price": 85000,
     "reviewed": True},
    {"id": 3, "company": "우리식품", "date": "2025-06-30", "cargo": "식품", "weight": 550, "price": 70000, "reviewed": False}
]

# 화물기사 운송 내역
@app.route("/history")
@login_required_driver
def history():
    return render_template("driver/history.html", matches=matches)


#화물기사->화주 리뷰
@app.route("/review/<int:match_id>")
@login_required_driver
def review(match_id):
    match = next((m for m in matches if m["id"] == match_id), None)
    if not match:
        return "해당 운송 내역이 없습니다.", 404
    return render_template("driver/review.html", match=match)

#리뷰 완료
@app.route("/review_success")
@login_required_driver
def review_success():
    return render_template("driver/review_success.html")


#정산 페이지
@app.route('/settlement')
@login_required_driver
def settlement():
    return render_template('driver/settlement.html')


#마이페이지 
@app.route("/mypage")
@login_required_driver
def mypage():
    return render_template("driver/mypage.html")

##공지사항
@app.route("/mypage/notice")
@login_required_driver
def mypage_notice():
    return render_template("driver/mypage_notice.html")

##고객센터
@app.route("/mypage/cs")
@login_required_driver
def mypage_cs():
    return render_template("driver/mypage_cs.html")

## 화물기사가 쓴 리뷰
@app.route("/mypage/reviews")
@login_required_driver
def mypage_reviews():
    return render_template("driver/mypage_reviews.html")

## 매칭 페이지
@app.route('/matching')
@login_required_driver
def matching_page():
    return render_template('driver/matching.html')

# 지오코딩 함수
def geocode(address):
    url = "https://dapi.kakao.com/v2/local/search/address.json"
    headers = {
        "Authorization": f"KakaoAK {KAKAO_API_KEY}",
        "KA": "sdk/1.0 os/javascript lang/ko-KR device/pc origin/http://localhost:5555"
    }
    params = {"query": address}

    try:
        res = requests.get(url, headers=headers, params=params)
        result = res.json()
        print("🔥 카카오 API 응답 내용:", result)

        if 'documents' in result and result['documents']:
            x = result['documents'][0]['x']
            y = result['documents'][0]['y']
            return float(y), float(x)
        else:
            print(f"카카오 API 오류: {result.get('message', '알 수 없는 오류')}")
            return None, None
    except Exception as e:
        print(f"지오코딩 에러: {e}")
        return None, None

# 간단한 주소 매핑 (테스트용)
def geocode_simple(address):
    address_map = {
        "서울특별시": (37.5665, 126.9780),
        "서울시": (37.5665, 126.9780),
        "부산광역시": (35.1796, 129.0756),
        "부산시": (35.1796, 129.0756),
        "강남구": (37.5172, 127.0473),
        "판교": (37.3920, 127.1112)
    }
    for key, coords in address_map.items():
        if key in address:
            return coords
    return (37.5665, 126.9780)  # 기본값

# 경로 처리 API
@app.route("/route_process", methods=['POST'])
def route_process():
    data = request.json
    start_addr = data.get("start_addr")
    end_addr = data.get("end_addr")

    if start_addr and end_addr:
        start_lat, start_lon = geocode(start_addr)
        end_lat, end_lon = geocode(end_addr)

        if not all([start_lat, start_lon]):
            print(f"카카오 API 실패, 간단한 매핑 사용: {start_addr}")
            start_lat, start_lon = geocode_simple(start_addr)

        if not all([end_lat, end_lon]):
            print(f"카카오 API 실패, 간단한 매핑 사용: {end_addr}")
            end_lat, end_lon = geocode_simple(end_addr)

        print(f"시작점: {start_addr} -> ({start_lat}, {start_lon})")
        print(f"도착점: {end_addr} -> ({end_lat}, {end_lon})")
    else:
        return jsonify({"error": "주소 정보가 부족합니다"}), 400

    headers = {
        "appKey": TMAP_API_KEY,
        "Content-Type": "application/json"
    }

    body = {
        "startX": str(start_lon),
        "startY": str(start_lat),
        "endX": str(end_lon),
        "endY": str(end_lat),
        "reqCoordType": "WGS84GEO",
        "resCoordType": "WGS84GEO",
        "searchOption": 0
    }

    try:
        print(f"TMAP API 요청: {body}")
        response = requests.post("https://apis.openapi.sk.com/tmap/routes?version=1", headers=headers, json=body)

        if response.status_code != 200:
            print(f"TMAP API 오류: {response.status_code}, {response.text}")
            return jsonify({"error": f"TMAP API 오류: {response.status_code}"}), 500

        route_data = response.json()
        print(f"TMAP API 응답 성공")

        coords = []
        total_distance = 0
        total_time = 0

        for feature in route_data['features']:
            properties = feature['properties']
            geometry = feature['geometry']

            if geometry['type'] == "LineString":
                for lon, lat in geometry['coordinates']:
                    coords.append({"lat": lat, "lon": lon})
            elif geometry['type'] == "Point" and properties.get("totalDistance") is not None:
                total_distance = properties.get("totalDistance", 0)
                total_time = properties.get("totalTime", 0)

        return jsonify({
            "coords": coords,
            "totalDistance": total_distance,
            "totalTime": total_time,
            "success": True
        })

    except Exception as e:
        print(f"경로 처리 에러: {e}")
        return jsonify({"error": "경로 처리 중 오류가 발생했습니다", "details": str(e)}), 500

# 실시간 위치 전송
@app.route('/send_location', methods=['POST'])
def send_location():
    data = request.json
    print("받은 위치 데이터:", data)

    received_data_list.append(data)

    if kafka_enabled and producer:
        try:
            producer.send('location_topic', data)
            print("Kafka로 위치 데이터 전송 성공")
        except Exception as e:
            print(f"Kafka 전송 에러: {e}")

    for client in clients:
        try:
            client.put(json.dumps(data))
        except:
            pass

    return jsonify({"status": "success"})

# 관리자 로그 조회
@app.route('/admin_log')
def admin_log():
    return jsonify(received_data_list)


@app.route('/start_guidance', methods=['POST'])
def start_guidance():
    data = request.json
    initial_speed = data.get('speed', 60)  # 기본 60km/h

    # 안내 시작 로직
    response_data = {
        'status': 'success',
        'initial_speed': initial_speed,
        'guidance_active': True
    }

    return jsonify(response_data)

# 실시간 스트리밍
@app.route('/stream')
def stream():
    def event_stream():
        q = queue.Queue()
        clients.append(q)
        try:
            while True:
                result = q.get()
                yield f"data: {result}\n\n"
        except GeneratorExit:
            clients.remove(q)

    return Response(event_stream(), mimetype="text/event-stream")

# Kafka Consumer 스레드
def kafka_consumer_thread():
    if not kafka_enabled:
        print("Kafka가 비활성화되어 있습니다.")
        return

    try:
        consumer = KafkaConsumer(
            'location_topic',
            bootstrap_servers=['kafka:9092'],
            value_deserializer=lambda m: json.loads(m.decode('utf-8'))
        )

        print("Kafka Consumer 시작됨")
        for msg in consumer:
            data = msg.value
            print(f"Kafka에서 받은 데이터: {data}")

            for client in clients:
                try:
                    client.put(json.dumps(data))
                except:
                    pass
    except Exception as e:
        print(f"Kafka Consumer 에러: {e}")

if kafka_enabled:
    threading.Thread(target=kafka_consumer_thread, daemon=True).start()
else:
    print("Kafka가 비활성화되어 있어 Consumer 스레드를 시작하지 않습니다.")

# 유틸리티 API
@app.route('/api/location/latest')
def get_latest_location():
    if received_data_list:
        return jsonify(received_data_list[-1])
    return jsonify({"error": "위치 데이터가 없습니다"}), 404

# -----------------------------------------------------------------------------
# 관리자 대시보드
@app.route('/admin/dashboard')
def admin_dashboard():
    return render_template('admin/dashboard.html')
# 이 파일이 직접 실행될 때 Flask 개발 서버를 실행합니다.


if __name__ == '__main__':
    # debug=True 모드로 실행하면 코드 변경 시 서버가 자동으로 재시작됩니다.
    # host와 port를 지정하여 'localhost:4321'로 접속하게 합니다.
    app.run(host='0.0.0.0', port=5555, debug=True)