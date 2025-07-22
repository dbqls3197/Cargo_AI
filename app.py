from flask import Flask, render_template, request, jsonify, session, url_for, redirect, Response, flash
from models import DBManager
import json
import requests
from functools import wraps
import threading
import queue
from kafka import KafkaProducer, KafkaConsumer
import random
import base64
import os
from werkzeug.utils import secure_filename
from pred import PDManager, ModelPredictor, load_model
import pandas as pd
from sklearn.model_selection import train_test_split
from lightgbm import LGBMRanker


# Flask 앱을 생성합니다.
app = Flask(__name__)

# --------------------------------------------------------------
# pip install flask-cors
# 토스 결제 서버 연동 : CORS 설정
# 토스 결제 페이지  : localhost:8000
# --------------------------------------------------------------
from flask_cors import CORS
app = Flask(__name__)
CORS(app)



# 전역 변수들
received_data_list = []
clients = []

app.secret_key = "your_super_secret_key"

# 파일 업로드 경로 설정
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')
# 업로드 폴더가 없으면 생성
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# API 키들
TMAP_API_KEY = "eEl7AGPzATadBLtufoN4i6dSx6RZGpcT8Bpq5zsj"
KAKAO_API_KEY = "b57c96e18902eff2c9b26c47c7c9f066"

manager = DBManager()
pd_manager = PDManager()

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


# --- 사용자 인증 데코레이터 -----------------------------------------------------------------
def login_required_shipper(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'id' not in session or session.get('role') != 'shipper':
            flash('화주 전용 페이지입니다. 먼저 로그인해주세요.')
            return redirect(url_for('index'))  # 'login_page' -> 'index'로 수정
        return f(*args, **kwargs)

    return decorated_function


def login_required_driver(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'id' not in session or session.get('role') != 'driver':
            flash('기사 전용 페이지입니다. 먼저 로그인해주세요.')
            return redirect(url_for('index'))  # 'login_page' -> 'index'로 수정
        return f(*args, **kwargs)

    return decorated_function



def login_required_admin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'id' not in session or session.get('role') != 'admin':
            flash('관리자 전용 페이지입니다. 먼저 로그인해주세요.')
            return redirect(url_for('index'))
        return f(*args, **kwargs)

    return decorated_function



# --- 공용 페이지 ---------------------------------------------------------------------
@app.route('/')
def index():
    return render_template('public/index.html')

# 회원가입
## 유저 타입 선택
@app.route('/public/user_type_select')
def user_type_select():
    return render_template('public/user_type_select.html')


## 유저 타입 처리
@app.route('/signup/<user_type>')
def signup_page(user_type):
    """지정된 사용자 유형에 맞는 회원가입 페이지를 렌더링합니다."""
    template_name = f'public/signup_{user_type}.html'
    if user_type not in ['shipper', 'driver']:  # 'admin' 제거
        return redirect(url_for('user_type_select'))
    try:
        return render_template(template_name, user_type=user_type)
    except Exception as e:
        print(f"Error loading template for {user_type}: {e}")
        return redirect(url_for('user_type_select'))
    

# --- 기사 회원가입 데이터 처리 라우트 ---
@app.route('/do_signup_driver', methods=['POST'])
def do_signup_driver():
    # 1) 폼 데이터 수집
    name            = request.form['name']
    driver_id       = request.form['username']
    driver_pw       = request.form['password']
    nickname        = request.form['nickname']
    biz_num         = request.form.get('business_number')  # NULL 허용
    phone           = request.form['phone_number']
    email           = request.form.get('email')
    birth_date      = request.form['birthdate']           # YYYY-MM-DD
    raw_gender      = request.form['gender']              # '0'/'1' 등
    gender          = int(raw_gender)                     # 이미 0,1로 설정되어 있다고 가정
    address         = request.form['address']

    # 2) 프로필 사진 저장
    profile = request.files.get('profile_picture')
    profile_path = None
    if profile and allowed_file(profile.filename):
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        filename = secure_filename(profile.filename)
        profile_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        profile.save(profile_path)

    # 3) DB에 삽입
    db = DBManager()
    db.insert_driver(
        name=name,
        driver_id=driver_id,
        driver_pw=driver_pw,
        nickname=nickname,
        business_registration_num=biz_num,
        phone=phone,
        email=email,
        birth_date=birth_date,
        gender=gender,
        address=address,
        profile_img_path=profile_path
    )
    return render_template('public/signup_success_driver.html')


# --- 화주 회원가입 데이터 처리 라우트 ---
@app.route('/do_signup_submit/<user_type>', methods=['POST'])
def do_signup_submit(user_type):
    if user_type == 'shipper':
        # 1) 폼 데이터 수집
        name    = request.form.get('name')
        username= request.form.get('user_id')
        password= request.form.get('password')
        nickname= request.form.get('nickname')
        biz_num = request.form.get('business_registration_num')
        phone   = request.form.get('phone')
        email   = request.form.get('email')
        birth   = request.form.get('birth_date')  # 'YYYY-MM-DD'
        gender  = int(request.form.get('gender'))
        address = request.form.get('address')

        # 2) 프로필 이미지 저장 (기존 로직 재사용)
        profile_img = request.files.get('profile_img')
        profile_path = None
        if profile_img and allowed_file(profile_img.filename):
            filename = secure_filename(profile_img.filename)
            profile_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            profile_img.save(profile_path)

        # 3) DB에 삽입
        db = DBManager()
        db.insert_shipper(name=name,shipper_id=username,shipper_pw=password,nickname=nickname,business_registration_num=biz_num,phone=phone,
            email=email,birth_date=birth,gender=gender,address=address,profile_img_path=profile_path
        )

        return render_template('public/signup_success_shipper.html')

    return redirect(url_for('signup_page'))


## 로그인 페이지
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        user_id_input = request.form['user_id'] # 사용자 입력 ID
        user_pw_input = request.form['password'] # 사용자 입력 PW

        # 세션에 일단 ID와 PW 저장 (선택 사항, 필요에 따라 로그인 성공 후에만 저장할 수도 있음)
        session['id'] = user_id_input
        session['pw'] = user_pw_input

        # manager를 통해 사용자, 운전자, 관리자 정보 조회
        user = manager.select_shipper_by_id(user_id_input)
        driver = manager.select_driver_by_id(user_id_input)
        admin = manager.select_admin_by_id(user_id_input)
        if user:
            session['role'] = 'shipper'
            if user['shipper_pw'] == user_pw_input: # 세션 PW 대신 직접 입력 PW 사용
                # 필요한 경우 여기에 shipper_id도 세션에 저장
                session['loggedInUserId'] = user['shipper_id'] # 예시: 발송인 ID 저장
                return redirect(url_for('shipper_dashboard'))
            else :
                flash("비밀번호가 일치하지 않습니다.", "error")
                return redirect(url_for('login'))
        elif driver:
            session['role'] = 'driver'
            if driver['driver_pw'] == user_pw_input: # 세션 PW 대신 직접 입력 PW 사용
                session['loggedInDriverId'] = driver['driver_id']
                return redirect(url_for('driver_dashboard'))
            else :
                flash("비밀번호가 일치하지 않습니다.", "error")
                return redirect(url_for('login'))
        elif admin:
            session['role'] = 'admin'
            if admin['admin_pw'] == user_pw_input : # 세션 PW 대신 직접 입력 PW 사용

                session['loggedInAdminId'] = admin['admin_id'] # 예시: 관리자 ID 저장
                return redirect(url_for('admin_dashboard'))
            else :
                flash("비밀번호가 일치하지 않습니다.", "error")
                return redirect(url_for('login'))
        else :
            flash("일치하는 아이디가 없습니다.", "error")
            return redirect(url_for('login'))
    return render_template("public/login.html")


## 로그아웃
@app.route('/logout')
def logout():
    session.clear()
    flash('성공적으로 로그아웃되었습니다.')
    return redirect(url_for('index'))



@app.route('/api/get_current_driver_id', methods=['GET'])
def get_current_driver_id():
    # 로그인 여부 및 역할 확인
    if 'id' not in session or session.get('role') != 'driver':
        return jsonify({'success': False, 'message': '로그인된 드라이버가 아닙니다.'}), 401
    
    # 세션에서 드라이버 ID를 가져와 반환
    driver_id = session.get('id') # 또는 session.get('loggedInDriverIdForJs') 사용 가능
    return jsonify({'success': True, 'driver_id': driver_id})


# -----------------------------------------------------------------------------
# [추가] 관리자 페이지 라우트
# -----------------------------------------------------------------------------
@app.route('/admin/dashboard')
@login_required_admin
def admin_dashboard():
    db = DBManager()
    운송중_건수 = db.get_active_delivery_count()
    가용_기사_수 = db.get_active_driver_count()

    return render_template(
        'admin/dashboard.html',
        운송중_건수=운송중_건수,
        가용_기사_수=가용_기사_수
    )


@app.route('/admin/realtime')
@login_required_admin
def realtime_monitoring():
    db = DBManager()
    driver_list = db.get_all_driver_briefs()  # 모든 기사 목록

    # 예시: 'DRV001' 기사를 선택했을 때
    selected_driver = db.get_driver_by_id("DRV001")  # 특정 기사 정보 조회

    return render_template(
        'admin/realtime.html',
        drivers=driver_list,
        selected_driver=selected_driver
    )

@app.route('/api/drivers/<string:driver_id>/details', methods=['GET'])
def get_driver_details_api(driver_id):
    driver_data = manager.get_driver_full_details(driver_id)
    if driver_data:
        return jsonify(driver_data)
    else:
        return jsonify({"error": "Driver not found or no details available"}), 404
    

@app.route('/api/selected_driver/<string:selected_driver_id>') # <selected_driver_id>를 URL 인자로 받도록 수정
def get_selected_driver(selected_driver_id): # 함수 인자로 selected_driver_id 받기
    try:
        db_manager = DBManager() # 함수 내에서 DBManager 인스턴스 다시 생성 (또는 전역 변수 사용)
        selected_driver = db_manager.get_driver_full_details(selected_driver_id)
        
        if not selected_driver:
            return jsonify({"error": "Driver not found"}), 404

        return jsonify({
            'id': selected_driver.get('driver_id'), # get_driver_full_details는 딕셔너리를 반환
            'name': selected_driver.get('name'),
            'vehicle': selected_driver.get('vehicle'), # vehicle_type으로 변경될 수 있음
            'status': selected_driver.get('status'),
            'rating': selected_driver.get('rating'),
            'nickname': selected_driver.get('nickname'),
            # models.py에서 이미 'latitude'와 'longitude' 키로 가공하여 반환하므로, 그대로 사용합니다.
            'latitude': selected_driver.get('latitude'),
            'longitude': selected_driver.get('longitude'),
            'location_updated_at': selected_driver.get('location_updated_at'),
            'is_active': selected_driver.get('is_active'),
            'details': selected_driver.get('details') # 운송 진행, 경로, 로그 등 추가 정보
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/admin/cargo-approval')
@login_required_admin
def admin_cargo_approval():
    return render_template('admin/cargo_approval.html')


@app.route('/admin/driver-approval')
@login_required_admin
def admin_driver_approval():
    return render_template('admin/driver_approval.html')


@app.route('/admin/user-management')
@login_required_admin
def admin_user_management():
    return render_template('admin/user_management.html')


@app.route('/admin/reports')
@login_required_admin
def admin_reports():
    drivers = manager.select_matching_driver()
    transports = manager.select_all_matches()  # matches 테이블 기준

    return render_template('admin/reports.html', drivers=drivers, transports=transports)

@app.route('/api/reports/monthly_performance')
def api_monthly_performance():
    month = request.args.get("month")
    if not month:
        return jsonify({"error": "month 파라미터가 필요합니다."}), 400
    report = manager.get_monthly_report(month)
    return jsonify(report)

@app.route('/api/reports/driver_performance')
def api_driver_performance():
    driver_id = request.args.get("driver_id")
    if not driver_id:
        return jsonify({"error": "driver_id 파라미터가 필요합니다."}), 400
    report = manager.get_driver_report(driver_id)
    return jsonify(report)


@app.route('/admin/inquiry')
@login_required_admin
def admin_inquiry():
    return render_template('admin/inquiry.html')


@app.route('/admin/settings')
@login_required_admin
def admin_settings():
    return render_template('admin/settings.html')


# -----------------------------------------------------------------------------
# 화주 페이지
# -----------------------------------------------------------------------------

## 화주 대시보드
@app.route('/shipper/dashboard')
@login_required_shipper
def shipper_dashboard():
    shipper_id = session['id']
    my_requests = manager.select_requests_by_shipper_id(shipper_id) or []
    my_requests_count = len(my_requests)
    not_matched = [req for req in my_requests if req['is_matched'] == 0] or []
    my_matchings = manager.select_matching_info(shipper_id)# 매칭정보 가져옴
    in_progress = [mat for mat in my_matchings if mat['status'] == 0] or []
    completed = [mat for mat in my_matchings if mat['status'] == 1] or []
    in_progress_count = len(in_progress)
    completed_count = len(completed)
    return render_template('shipper/dashboard.html', my_requests = my_requests, my_requests_count=my_requests_count, not_matched=not_matched,
                           in_progress_count=in_progress_count, completed_count=completed_count
                           )

# 화주 운송 요청 페이지 
@app.route('/shipper/shipper_request')
@login_required_shipper
def shipper_request():
    return render_template('shipper/shipper_request.html')

# 화주 운송 요청 제출
@app.route("/shipper/request/submit", methods=["POST"])
@login_required_shipper
def submit_shipper_request():
    try:
        data = request.get_json()
        user_id = session['id']
        manager.insert_freight_request(user_id, data)
        return jsonify({"success": True, "message": "요청이 성공적으로 저장되었습니다."})
    except Exception as e:
        return jsonify({"success": False, "message": "운송 요청 저장 중 오류 발생"})


## 화주 비매칭 운송 요청 목록
@app.route("/shipper/my_requests")
@login_required_shipper
def shipper_my_requests():
    shipper_id = session['id']  # shipper_id로 받아야 DB컬럼과 일치
    all_requests = manager.select_requests_by_shipper_id(shipper_id) 
    non_matched = [mat for mat in all_requests if mat['is_matched'] == 0] 
    return render_template("shipper/my_requests.html", my_requests= non_matched )


## 화주 기사 매칭
@app.route('/shipper/driver_matching')
@login_required_shipper
def driver_matching():
    request_id = request.args.get('id') # 화물 번호
    select_request = manager.select_request_by_id(request_id) # 선택한 화물
    print(f"선택된 화물 요청 정보: {select_request}")
    # 화물 번호에 대한 추천기사의 정보 가져오기 (기사데이터 : name, rating, truck_type, truck_info, 추천 정보 : 순위, 예상 접근 거리- 📍 "출발지까지 거리: {{ distance }}km")
    recommend_matches = manager.get_recommended_matches(request_id) or [] #
    print(f"추천 정보: {recommend_matches}" ) 
    return render_template('shipper/driver_matching.html',recommend_matches = recommend_matches, select_request = select_request)


## 화주 매칭 결과
@app.route('/shipper/matching_result', methods=['POST'])
@login_required_shipper
def driver_matching_result():
    request_id = request.form['request_id']
    driver_id = request.form['driver_id']
    my_request = manager.select_request_by_id(request_id)
    driver = manager.select_matching_driver_all_info(driver_id)
    manager.insert_matching_result(request_id, driver_id)
    my_matching = manager.select_matching_driver_my_request(driver_id, request_id)
    manager.update_matching_status(request_id)
    return render_template("shipper/driver_matching_result.html", my_request=my_request, driver=driver,
                           my_matching=my_matching)


## 화주 운송 내역
@app.route('/shipper/my_shipments')
@login_required_shipper
def shipper_my_shipments():
    shipper_id = session['id']
    my_matchings = manager.select_matching_info(shipper_id)# 매칭정보 가져옴
    in_progress = [mat for mat in my_matchings if mat['status'] == 0] or []
    completed = [mat for mat in my_matchings if mat['status'] == 1] or []
    return render_template('shipper/my_shipments.html', in_progress= in_progress, completed=completed, my_matchings= my_matchings)


## 운송 내역 기사 추적
@app.route('/shipper/tracking/<match_id>')
@login_required_shipper
def shipper_tracking(match_id):
    return render_template('shipper/shipper_tracking.html',match_id=match_id,KAKAO_API_KEY=KAKAO_API_KEY)


# -------------------------------------------------------------------------------------------------
# 화주 결제 페이지
# -------------------------------------------------------------------------------------------------
@app.route('/shipper/payments')
@login_required_shipper
def shipper_payments():
    user_id = session['id']
    all_matchings = manager.select_matching_driver_my_request_by_id(user_id)
    completed_delivery = [pay for pay in all_matchings if pay.get('delivery_status') == 'completed']
    manager.create_my_payments_table()
    existing_payment_match_ids = set(match["match_id"] for match in manager.select_payments_by_id(user_id))
    for match in completed_delivery:
        if match["match_id"] in existing_payment_match_ids:
            continue
        fee = int(match.get('fee', 0))
        commission = int(fee * 0.05)
        total = fee + commission
        payment_data = {
            "user_id": user_id, "match_id": match["match_id"], "driver_id": match["driver_id"],
            "fee": fee, "commission": commission, "total_amount": total,
            "origin": match.get("origin"), "destination": match.get("destination"),
            "driver_name": match.get("driver_name"), "driver_phone": match.get("driver_phone")
        }
        manager.insert_payment(payment_data)
    all_payment = manager.select_payments_by_id(user_id)
    payments = [pay for pay in all_payment if pay.get('is_paid') == 0]
    return render_template('shipper/payments.html', payments=payments)


# -------------------------------------------------------------------------------------------------
# 화주 토스결제 완료 후 돌아오는 페이지
# -------------------------------------------------------------------------------------------------
@app.route('/shipper/payments_result')
@login_required_shipper
def shipper_payments_result():
    user_id = session['id']
    
    # 결제 상태 업데이트
    try:
        # 새로운 연결 생성
        manager.connect()
        
        # 방법 1: 특정 payment_id를 받아서 업데이트하는 경우
        payment_id = request.args.get('payment_id')
        if payment_id:
            query = "UPDATE payments SET is_paid=1 WHERE id=%s"
            manager.cursor.execute(query, (payment_id,))
        else:
            # 방법 2: 현재 사용자의 모든 미결제 건을 완료 처리하는 경우
            query = "UPDATE payments SET is_paid=1 WHERE shipper_id=%s AND is_paid=0"
            manager.cursor.execute(query, (user_id,))
        
        manager.connection.commit()
        print("✅ 결제 상태 업데이트 완료")
        
    except Exception as e:
        print(f"결제 상태 업데이트 오류: {e}")
        if manager.connection:
            manager.connection.rollback()
    finally:
        manager.disconnect()
    
    return redirect(url_for('shipper_dashboard'))


@app.route("/api/process_payment", methods=["POST"])
@login_required_shipper
def process_payment():
    data = request.get_json()
    match_id = data.get("match_id")
    manager.update_payment_is_paid(match_id)
    return jsonify(success=True)


@app.route('/shipper/my_page')
@login_required_shipper
def shipper_my_page():
    shipper_id = session['id']
    shipper = manager.select_shipper_by_id(shipper_id)
    return render_template('shipper/my_page.html', shipper=shipper)


# -----------------------------------------------------------------------------
# 화물기사 페이지
# -----------------------------------------------------------------------------

# 기사 대시보드
@app.route('/driver/dashboard')
@login_required_driver
def driver_dashboard():
    # 1) 모델 로드
    BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
    MODEL_PATH = os.path.join(BASE_DIR, 'model', 'lgbm_ranker_model.pkl')
    model = load_model(MODEL_PATH)
    mp_manager = ModelPredictor(model)

    # 2) 현재 기사 정보 (세션)
    driver_id = session['id']
    driver = manager.select_matching_driver_all_info(driver_id) or [] # 로그인한 기사의 모든 정보 가져오기
    driver_name = driver['name'] # 로그인한 기사의 이름
    # 3) 화물 요청 및 전체 기사 목록 조회
    freight_requests = manager.select_non_matched_requests_all_info()  # 매치 안된 화물 모든정보 
    print(f"매치 안된 화물 모든정보:{freight_requests}")
    all_drivers = manager.select_active_drivers_all_info()       # 운송 가능한 화물기사 모두의 정보
    # 4) 후보 (request × driver) 조합으로 피처 행 생성
    rows = []
    for fr in freight_requests:
        # 화물 요청의 위/경도
        origin = fr['origin']
        req_lat, req_lon = geocode(origin) # 화물의 출발지 주소 => 위도 경도
        for dr in all_drivers:
            # ① 용량, 화물타입, 정보, 위험물/유해물 필터 (룰 기반)
            if dr['capacity'] > fr['weight'] and dr['truck_type'] == fr['cargo_type'] and dr['truck_info'] == fr['cargo_info'] :
            
                # ② 거리 계산 (km)
                distance = mp_manager.haversine_distance(
                    dr['driver_lat'], dr['driver_lon'],
                    req_lat, req_lon
                )
                print(distance)
                if distance < 200 :
            

                    # ③ 평점·수락률·휴식시간
                    acceptance_rate  = dr['accepted_requests'] / max(dr['total_requests'],1)
                    rating = dr.get('rating', 0)

                    # ④ 피처 행 추가
                    rows.append({
                        'request_id':        fr['id'],
                        'driver_id':         dr['driver_id'],
                        'distance':          distance,
                        'rating':            rating,
                        'acceptance_rate':   acceptance_rate
                        
                    })
    df_cand = pd.DataFrame(rows)
    # 🔐 예외 처리: 빈 데이터프레임이면 안전하게 템플릿으로 리턴
    if df_cand.empty:
        print("❌ 조건에 맞는 추천 대상이 없습니다.")
        return render_template('driver/dashboard.html',
                            driver_id=driver_id,
                            driver_name=driver_name,
                            combined_list=[])

    feature_cols = ['distance','rating','acceptance_rate']
    df_cand['score'] = model.predict(df_cand[feature_cols])
    print(f"예측된 점수: {df_cand['score']}")
    # 6) request_id 별로 내림차순 정렬하여 상위 N (예: top 3) 추출
    recommendations = {}
    recommend_list = []
    for req_id, grp in df_cand.groupby('request_id'):
        topk = (
            grp.sort_values('score', ascending=False)
                .head(3)[['driver_id','score','distance','rating','acceptance_rate']]
                .to_dict(orient='records')
        )
        recommendations[req_id] = topk
        request_id = req_id
        rinfo = manager.select_request_by_id(request_id)
        recommend_list.append(rinfo)

    # print(f"화물정보 : {recommend_list} ")
    # print(f"예측결과 : {recommendations} ")

    for req_id, drivers in recommendations.items():
    
        # 새 추천 삽입 (rank 부여)
        for rank, info in enumerate(drivers, start=1):
            manager.upsert_recommendation(
                request_id=req_id,
                driver_id=info['driver_id'],
                distance = info['distance'],
                score=info['score'],
                rank=rank
            )

    recommend_request_id = manager.select_recommend_matches_by_id(driver_id) # 드라이버 아이디로 추천된 화물번호 가져오기
    recommend_driver_info = manager.select_recommend_driver_by_id(driver_id) # 드라이버 아이디로 추천된 결과 가져오기

    recommend_requests_info = []
    for req in recommend_request_id :
        request_id = req['request_id']
        req = manager.select_request_by_id(request_id) # 화물 id로 화물정보 받아오기
        recommend_requests_info.append(req)

    combined_list = []

    # request_id → 화물정보 dict 로 매핑
    request_map = {r['id']: r for r in recommend_requests_info}

    # recommend_driver_info는 match 테이블 기반
    for match in recommend_driver_info:
        req_id = match['request_id']
        if req_id in request_map:
            combined_list.append({
                'match': match,
                'request': request_map[req_id]
            })

    # 7) 템플릿에 전달
    return render_template('driver/dashboard.html'
                        , driver_id = driver_id, driver_name=driver_name, combined_list=combined_list
                        )


## 화물 요청 상세보기
@app.route('/driver/request/<int:request_id>')
@login_required_driver
def request_detail(request_id):
    request_info = manager.select_request_by_id(request_id) # 화물 id로 화물 정보 가져오기
    shipper_id = request_info['shipper_id']  # 화물 정보에서 화주아이디 추출
    shipper_info = manager.select_shipper_by_id(shipper_id) # 화주 아이디로 화주정보 추출
    return render_template('driver/request_detail.html', request_id=request_id, request_info=request_info, shipper_info = shipper_info)

## 화물 요청 수락 
@app.route('/driver/request_accept_success/<int:request_id>')
@login_required_driver
def request_accept_success(request_id):
    driver_id = session['id']
    
    # 🔥 추천 매칭 수락 및 matches 삽입 로직 포함된 메서드 사용
    success = manager.accept_recommended_match(request_id, driver_id)

    if not success:
        flash("❗ 이미 수락된 요청이거나 오류가 발생했습니다.", "error")
        return redirect(url_for('driver_dashboard'))

    # ✅ 성공했으면 요청 정보 및 화주 정보 조회
    request_info = manager.select_request_by_id(request_id)
    shipper_info = manager.select_shipper_by_id(request_info['shipper_id'])

    return render_template(
        'driver/request_accept_success.html',
        request_id=request_id,
        request_info=request_info,
        shipper_info=shipper_info
    )


@app.route('/accept_match/<int:request_id>/<driver_id>', methods=['POST'])
def accept_match(request_id, driver_id):
    db = DBManager()
    success = db.accept_recommended_match(request_id, driver_id)
    
    if success:
        return jsonify({"message": "매칭 수락 성공"}), 200
    else:
        return jsonify({"message": "이미 수락되었거나 유효하지 않은 요청입니다."}), 400

# 기사 운송 요청 목록
@app.route('/driver/navigation', defaults={'request_id': None, 'match_id': None})
@app.route('/driver/navigation/request/<int:request_id>', defaults={'match_id': None})
@app.route('/driver/navigation/match/<int:match_id>', defaults={'request_id': None})
@login_required_driver
def navigation_page(request_id, match_id):
    logged_in_driver_id = session.get('loggedInDriverId')
    if not logged_in_driver_id:
        flash("드라이버 ID를 찾을 수 없습니다. 다시 로그인해주세요.", "error")
        return redirect(url_for('login'))

    db = DBManager()

    # 1) request_id로 조회되는 원본 운송 요청
    freight_request = None
    if request_id is not None:
        freight_request = db.get_freight_request_by_id(request_id)
        if not freight_request:
            flash("해당 운송 요청을 찾을 수 없습니다.", "error")
            return redirect(url_for('driver_history'))

    # 2) match_id로 조회되는 매칭 정보
    match = None
    if match_id is not None:
        match = db.get_matched_request_by_id(match_id)
        if not match:
            flash("해당 매칭 정보를 찾을 수 없습니다.", "error")
            return redirect(url_for('driver_history'))

    return render_template(
        'driver/navigation.html',
        logged_in_driver_id=logged_in_driver_id,
        freight_request=freight_request,
        match=match,
    )

matches = [
    {"id": 1, "company": "(주)가나다 물류", "date": "2025-07-08", "cargo": "가구", "weight": 165, "price": 103000,
     "reviewed": False},
    {"id": 2, "company": "ABC 전자", "date": "2025-07-05", "cargo": "전자제품", "weight": 80, "price": 85000,
     "reviewed": True},
    {"id": 3, "company": "우리식품", "date": "2025-06-30", "cargo": "식품", "weight": 550, "price": 70000, "reviewed": False}
]

@app.route('/driver/accept/<int:request_id>', methods=['POST'])
def accept_recommendation(request_id):
    driver_id = session.get('loggedInDriverId')  # 세션에서 드라이버 ID 추출
    if not driver_id:
        flash("드라이버 로그인 정보가 없습니다.", "error")
        return redirect(url_for('driver_login'))

    db = DBManager()
    result = db.accept_recommended_match(request_id, driver_id)

    if result:
        flash("매칭을 수락했습니다.", "success")
    else:
        flash("매칭 수락에 실패했습니다.", "error")

    return redirect(url_for('driver_dashboard'))

@app.route("/driver/history")
@login_required_driver
def history():
    driver_id = session['loggedInDriverId']
    db = DBManager()
    matches = db.get_driver_matches(driver_id)
    return render_template("driver/history.html", matches=matches)

@app.route("/driver/review/<int:match_id>")
@login_required_driver
def review(match_id):
    match = next((m for m in matches if m["id"] == match_id), None)
    if not match: return "해당 운송 내역이 없습니다.", 404
    return render_template("driver/review.html", match=match)


@app.route("/driver/review_success")
@login_required_driver
def review_success():
    return render_template("driver/review_success.html")


@app.route('/driver/settlement')
@login_required_driver
def settlement():
    return render_template('driver/settlement.html')


@app.route("/driver/mypage")
@login_required_driver
def mypage():
    return render_template("driver/mypage.html")


@app.route("/driver/mypage/notice")
@login_required_driver
def mypage_notice():
    return render_template("driver/mypage_notice.html")


@app.route("/driver/mypage/cs")
@login_required_driver
def mypage_cs():
    return render_template("driver/mypage_cs.html")


@app.route("/driver/mypage/reviews")
@login_required_driver
def mypage_reviews():
    return render_template("driver/mypage_reviews.html")


@app.route('/driver/matching')
@login_required_driver
def matching_page():
    return render_template('driver/matching.html')

@app.route('/update_driver_status', methods=['POST'])
def update_driver_status():
    if session.get('role') != 'driver':
        return jsonify({'success': False, 'message': '권한이 없습니다'}), 403 
    
    driver_id = session.get('loggedInDriverId') # 세션에서 드라이버 ID 가져오기
    if not driver_id:
        return jsonify({'success': False, 'message': '로그인된 드라이버 ID를 찾을 수 없습니다.'}), 401

    status = request.json.get('status') 
    if status not in [0, 1]:
        return jsonify({'success': False, 'message': '유효하지 않은 상태 값입니다. (0 또는 1만 허용)'}), 400

    try:
        success = manager.update_driver_status(driver_id, status)

        if success:
            return jsonify({'success': True, 'message': '운전자 상태가 성공적으로 업데이트되었습니다.'}), 200
        else:
            return jsonify({'success': False, 'message': '운전자 상태 업데이트에 실패했습니다.'}), 500
    except Exception as e:
        print(f"운전자 상태 업데이트 중 서버 오류 발생: {e}")
        return jsonify({'success': False, 'message': f'서버 오류: {str(e)}'}), 500

@app.route('/get_driver_status', methods=['GET'])
@login_required_driver 
def get_driver_status():
    driver_id = request.args.get('driver_id')

    if not driver_id:
        return jsonify({'success': False, 'message': '드라이버 ID가 필요합니다.'}), 400

    try:
        driver_data = manager.select_driver_by_id(driver_id)

        if driver_data:
            status = driver_data.get('is_active') 

            if status is not None: # is_active 값이 존재한다면
                return jsonify({'success': True, 'status': status}), 200 # 클라이언트에는 'status'로 반환
            else:
                return jsonify({'success': False, 'message': '드라이버 상태 정보를 찾을 수 없습니다.'}), 404
        else:
            return jsonify({'success': False, 'message': '해당 드라이버를 찾을 수 없습니다.'}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': f'서버 오류: {str(e)}'}), 500
    



# -----------------------------------------------------------------------------
# 외부 API 연동 및 유틸리티 함수
# -----------------------------------------------------------------------------
def geocode(address):
    url = "https://dapi.kakao.com/v2/local/search/address.json"
    headers = {"Authorization": f"KakaoAK {KAKAO_API_KEY}"}
    params = {"query": address}
    try:
        res = requests.get(url, headers=headers, params=params)
        result = res.json()
        if 'documents' in result and result['documents']:
            return float(result['documents'][0]['y']), float(result['documents'][0]['x'])
        return None, None
    except Exception as e:
        print(f"ERROR: geocoding 에러: {e}")
        return None, None


def geocode_simple(address):
    address_map = {"서울특별시": (37.5665, 126.9780), "부산광역시": (35.1796, 129.0756)}
    for key, coords in address_map.items():
        if key in address:
            return coords
    return (37.5665, 126.9780)


@app.route("/route_process", methods=['POST'])
def route_process():
    data = request.json
    start_addr_param = data.get("start_addr") # '위도,경도' 또는 주소 문자열 (현재 위치)
    pass_addr_list = data.get("pass_addr_list", []) # 경유지 주소 리스트 (입력한 출발지)
    end_addr = data.get("end_addr") # 최종 도착지 주소 (입력한 도착지)

    if not (start_addr_param and end_addr):
        return jsonify({"error": "출발지 또는 도착지 정보 부족"}), 400

    # 1. 출발지 (현재 위치) 좌표 처리
    start_lat, start_lon = None, None
    if isinstance(start_addr_param, str) and ',' in start_addr_param:
        try:
            s_lat_str, s_lon_str = start_addr_param.split(',')
            start_lat = float(s_lat_str.strip())
            start_lon = float(s_lon_str.strip())
        except ValueError:
            start_lat, start_lon = geocode(start_addr_param) or geocode_simple(start_addr_param)
    else:
        start_lat, start_lon = geocode(start_addr_param) or geocode_simple(start_addr_param)

    if start_lat is None or start_lon is None:
        return jsonify({"error": "출발지(현재 위치) 좌표를 찾을 수 없습니다."}), 400


    # 2. 경유지 주소들 좌표로 변환 및 TMap API passList 형식 생성
    tmap_pass_list = []
    display_pass_coords = []

    for p_addr in pass_addr_list:
            p_lat, p_lon = geocode(p_addr) or geocode_simple(p_addr)
            if p_lat is not None and p_lon is not None:
                # POI_ID 부분에 주소 문자열 대신 '0'을 넣거나 아예 생략 (권장)
                tmap_pass_list.append(f"{p_lon},{p_lat}") # POI_ID를 생략
                # 또는 tmap_pass_list.append(f"{p_lon},{p_lat},0") # POI_ID를 0으로 설정
                display_pass_coords.append({"lat": p_lat, "lon": p_lon})
            else:
                print(f"WARN: 경유지 '{p_addr}'의 좌표를 찾을 수 없습니다. 건너뜁니다.")


    # 3. 최종 도착지 주소 좌표로 변환
    end_lat, end_lon = geocode(end_addr) or geocode_simple(end_addr)
    if end_lat is None or end_lon is None:
        return jsonify({"error": f"도착지 '{end_addr}'의 좌표를 찾을 수 없습니다."}), 400

    # TMap API 호출을 위한 헤더 및 바디 구성
    headers = {"appKey": TMAP_API_KEY, "Content-Type": "application/json"}
    body = {
        "startX": str(start_lon),
        "startY": str(start_lat),
        "endX": str(end_lon),
        "endY": str(end_lat),
        "reqCoordType": "WGS84GEO",
        "resCoordType": "WGS84GEO",
        "startName": "현재위치",
        "endName": "최종도착지",
        "passList": ";".join(tmap_pass_list) if tmap_pass_list else "",
        "searchOption": "0", # 추천 경로
    }

    try:
        # 보행자 경로 API 사용
        response = requests.post("https://apis.openapi.sk.com/tmap/routes/pedestrian?version=1", headers=headers, json=body)
        response.raise_for_status()

        route_data = response.json()
        coords = []

        for feature in route_data['features']:
            geometry = feature['geometry']
            if geometry['type'] == 'LineString':
                for coord_pair in geometry['coordinates']:
                    coords.append({"lat": coord_pair[1], "lon": coord_pair[0]})

        first_feature_properties = route_data['features'][0]['properties'] if route_data['features'] else {}
        total_distance_final = first_feature_properties.get("totalDistance", 0) # TMap API에서 제공하는 전체 거리
        total_time_final = first_feature_properties.get("totalTime", 0)       # TMap API에서 제공하는 전체 시간


        return jsonify({
            "coords": coords,
            "totalDistance": total_distance_final,
            "totalTime": total_time_final,
            "passCoords": display_pass_coords,
            "success": True
        })

    except requests.exceptions.HTTPError as e:
        return jsonify({"error": f"TMAP API 오류: {response.text}"}), response.status_code
    except Exception as e:
        return jsonify({"error": "경로 처리 중 오류 발생", "details": str(e)}), 500


@app.route('/send_location', methods=['POST'])
def send_location():
    data = request.json
    received_data_list.append(data)
    if kafka_enabled and producer:
        try:
            producer.send('location_topic', data)
        except Exception as e:
            print(f"Kafka 전송 에러: {e}")
    for client in clients:
        try:
            client.put(json.dumps(data))
        except:
            pass
    return jsonify({"status": "success"})


@app.route('/admin_log')
def admin_log():
    return jsonify(received_data_list)


@app.route('/start_guidance', methods=['POST'])
def start_guidance():
    data = request.json
    return jsonify({'status': 'success', 'initial_speed': data.get('speed', 60), 'guidance_active': True})


@app.route('/stream')
def stream():
    def event_stream():
        q = queue.Queue()
        clients.append(q)
        try:
            while True: yield f"data: {q.get()}\n\n"
        except GeneratorExit:
            clients.remove(q)

    return Response(event_stream(), mimetype="text/event-stream")


def kafka_consumer_thread():
    if not kafka_enabled: return
    try:
        consumer = KafkaConsumer('location_topic', bootstrap_servers=['kafka:9092'],
                                 value_deserializer=lambda m: json.loads(m.decode('utf-8')))
        for msg in consumer:
            for client in clients:
                try:
                    client.put(json.dumps(msg.value))
                except:
                    pass
    except Exception as e:
        print(f"Kafka Consumer 에러: {e}")


if kafka_enabled:
    threading.Thread(target=kafka_consumer_thread, daemon=True).start()


@app.route('/api/location/latest')
def get_latest_location():
    if received_data_list: return jsonify(received_data_list[-1])
    return jsonify({"error": "위치 데이터가 없습니다"}), 404


# [추가] 관리자 실시간 관제용 API: 기사 목록 반환
@app.route('/api/drivers')
@login_required_admin
def get_all_drivers():
    try:
        # DB에서 모든 기사 정보를 가져옵니다.
        all_drivers = manager.select_matching_driver()

        # 시뮬레이션을 위해 가상의 상태 정보를 추가합니다.
        statuses = ["운송 중", "대기 중", "휴식 중"]
        for driver in all_drivers:
            driver['status'] = random.choice(statuses)

        return jsonify(all_drivers)
    except Exception as e:
        print(f"API 오류: 기사 목록 조회 실패: {e}")
        return jsonify({"error": "데이터를 불러오는데 실패했습니다."}), 500


@app.route('/api/users')
@login_required_admin
def get_all_users():
    users = []
    try:
        # DB에서 화주, 기사, 관리자 정보를 모두 가져옵니다.
        shippers = manager.connect_and_execute("SELECT user_id, name, '화주' as role FROM shippers")
        drivers = manager.connect_and_execute("SELECT driver_id as user_id, name, '기사' as role FROM drivers")
        admins = manager.connect_and_execute(
            "SELECT admin_id as user_id, admin_name as name, '관리자' as role FROM admins")

        if shippers: users.extend(shippers)
        if drivers: users.extend(drivers)
        if admins: users.extend(admins)

        return jsonify(users)
    except Exception as e:
        print(f"API 오류: 사용자 목록 조회 실패: {e}")
        return jsonify({"error": "데이터를 불러오는데 실패했습니다."}), 500


# -----------------------------------------------------------------------------
# 앱 실행
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5555, debug=True)