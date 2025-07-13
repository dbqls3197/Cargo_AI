from flask import Flask, render_template, request, jsonify
from models import DBManager
import json
import requests
# Flask 앱을 생성합니다.
app = Flask(__name__)
manager = DBManager()

manager.create_shipper_requests_table()
# 루트 URL ('/')에 접속했을 때 index.html 파일을 렌더링합니다.
@app.route('/')
def index():
    return render_template('public/index.html')

@app.route('/login')
def login():
    pass
    
    # if admin :
    #     return render_template('admin/dashboard')

    # elif shipper :
    #     return render_template('shipper/dashboard')
    # elif driver :
    #     return render_template('driver/admin/dashboard')
    
@app.route('/register')
def register():
    pass 

#데코레이터

# 화주 페이지
## 화주 대시보드
@app.route('/shipper/dashboard')
def shipper_dashboard():
    return render_template('shipper/dashboard.html')

## 화주 운송 내역 페이지
@app.route('/shipper/my_shipments')
def shipper_my_shipments():
    return render_template('shipper/my_shipments.html')

## 화주 화물 의뢰 페이지
@app.route('/shipper/shipper_request')
def shipper_request():
    return render_template('shipper/shipper_request.html')

## 화주 화물 의뢰 정보 DB 저장
@app.route('/shipper/request/submit', methods=['POST'])
def submit_shipper_request():
    try:
        data = request.get_json()
        manager.insert_shipper_request(data)
        return jsonify({"success": True})
    except Exception as e:
        print(f"에러 발생: {e}")
        return jsonify({"success": False, "message": str(e)})
    
## 화주 의뢰 매칭
@app.route('/shipper/matching')
def shipper_matching():
    return render_template('shipper/shipper_matching.html')


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