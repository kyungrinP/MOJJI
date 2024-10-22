from flask import Flask, render_template, redirect, url_for
from flask_login import LoginManager
from flask_cors import CORS
from mojji_Control.mojji_user_mgmt import User
import os
from auth import auth_bp
from main import main_bp
from mymojji import mymojji_bp

# https 만을 지원하는 기능을 http 에서 테스트할 때 필요한 설정
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

app = Flask(__name__, template_folder='templates')

app.register_blueprint(auth_bp.auth, url_prefix='/auth')
app.register_blueprint(main_bp.main_bp, url_prefix='/main')
app.register_blueprint(mymojji_bp.mymojji, url_prefix='/mymojji')

CORS(app)
app.config['SECRET_KEY'] = 'mojji_server'

login_manager = LoginManager()
login_manager.init_app(app)     # app 에 login_manager 연결
login_manager.login_view = 'login'
login_manager.session_protection = 'strong'

# flask_login에서 제공하는 login_required를 실행하기 전 사용자 정보 조회
@login_manager.user_loader
def load_user(member_id):
    return User.get(member_id)

# login_required로 요청된 기능에서 현재 사용자가 로그인되어 있지 않은 경우
# unauthorized 함수 실행
@login_manager.unauthorized_handler
def unauthorized():
    return render_template('login.html')

@app.route('/')
def index():
    return redirect(url_for('main_bp.main_page'))

# 업로드된 파일을 저장할 디렉토리 경로
UPLOAD_FOLDER = '/main/static/img/uploads/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# 허용된 파일 확장자 목록
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
app.config['ALLOWED_EXTENSIONS'] = ALLOWED_EXTENSIONS

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)