from flask import Flask, render_template, request, jsonify, session, url_for, redirect
from models import DBManager
import json
import requests
# Flask 앱을 생성합니다.
app = Flask(__name__)

app.secret_key = "your_super_secret_key"

manager = DBManager()

manager.create_shipper_requests_table()
manager.create_driver_table()
manager.create_shipper_table()
# 루트 URL ('/')에 접속했을 때 index.html 파일을 렌더링합니다.
@app.route('/')
def index():
    return render_template('public/index.html')

# 로그인 페이지
@app.route('/login', methods=['POST'])
def login():
    session['id'] = request.form['user_id']
    session['pw'] = request.form['password']
    return redirect(url_for('shipper_dashboard'))
    
    # if admin :
    #     return render_template('admin/dashboard')

    # elif shipper :
    #     return render_template('shipper/dashboard')
    # elif driver :
    #     return render_template('driver/admin/dashboard')

@app.route('/logout')
def logout():
    session.clear()  # 또는 session.pop('id', None) 등으로 개별 제거 가능
    return redirect(url_for('/'))

#회원가입페이지    
@app.route('/register')
def register():
    return render_template('public/register.html') 

#데코레이터

# 화주 페이지
## 화주 대시보드
@app.route('/shipper/dashboard')
def shipper_dashboard():
    return render_template('shipper/dashboard.html')

## 화주 화물 의뢰 페이지
@app.route('/shipper/shipper_request')
def shipper_request():
    return render_template('shipper/shipper_request.html')

## 화주 화물 의뢰 정보 DB 저장
@app.route("/shipper/request/submit", methods=["POST"])
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
def shipper_my_requests():
    my_requests = manager.select_shipper_requests()
    print(my_requests)
    return render_template("shipper/my_requests.html", my_requests=my_requests)


# 기사 매칭 페이지 
@app.route('/shipper/driver_matching')
def driver_matching():
    request_id = request.args.get('id')
    drivers = manager.select_matching_driver()
    return render_template('shipper/driver_matching.html', drivers=drivers, request_id=request_id)

# 매칭 결과 페이지 
@app.route('/shipper/matching_result', methods=['POST'])
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
    my_matchings = manager.select_driver_my_request(user_id)
    print(my_matchings)
    return render_template("shipper/driver_matching_result.html", my_request=my_request, driver=driver, my_matchings=my_matchings)

## 화주 운송 내역 페이지
@app.route('/shipper/my_shipments')
def shipper_my_shipments():
    user_id = session['id']
    my_matchings = manager.select_driver_my_request(user_id)
    return render_template('shipper/my_shipments.html', my_matchings = my_matchings)

# 화물기사 대시보드
@app.route('/driver/dashboard')
def driver_dashboard():
    return render_template('driver/dashboard.html')

# 관리자 대시보드
@app.route('/admin/dashboard')
def admin_dashboard():
    return render_template('admin/dashboard.html')
# 이 파일이 직접 실행될 때 Flask 개발 서버를 실행합니다.



if __name__ == '__main__':
    # debug=True 모드로 실행하면 코드 변경 시 서버가 자동으로 재시작됩니다.
    # host와 port를 지정하여 'localhost:4321'로 접속하게 합니다.
    app.run(host='0.0.0.0', port=4321, debug=True)