from flask import render_template, jsonify, request, redirect, url_for, flash, Blueprint
from flask_login import login_required, login_user, logout_user
from werkzeug.security import check_password_hash
from mojji_Control.mojji_user_mgmt import User
import boto3
import os
from dotenv import load_dotenv
from botocore.exceptions import ClientError
import random
import string

# .env 파일을 로드
load_dotenv()

auth = Blueprint('auth', __name__, static_folder='static', template_folder='templates')

# 환경 변수에서 Cognito Pool 및 Client 정보 불러오기
client = boto3.client('cognito-idp', region_name='ap-northeast-2')
USER_POOL_ID = os.getenv('USER_POOL_ID')
CLIENT_ID = os.getenv('CLIENT_ID')

@auth.route('/register')
def register():
    return render_template('register.html')

@auth.route('/register_new', methods=['POST'])
def register_new():
    member_id = request.form['member_id']
    passwd = request.form['passwd']
    hint = request.form['hint']
    hint_answer = request.form['hint_answer']
    name = request.form['nameContents']
    postcode1 = int(request.form['postcode1'])
    addr1 = request.form['addr1']
    addr2 = request.form['addr2']
    extraAddress = request.form['extraAddress']
    mobile = "".join(request.form.getlist('mobile[]'))
    email = request.form['email1']

    User.register(member_id, passwd, hint, hint_answer, name, postcode1, addr1, addr2, extraAddress, mobile, email)

    return redirect(url_for('main_bp.main_page'))

@auth.route('/check-mobile', methods=['GET'])
def check_mobile():
    mobile = request.args.get('mobile')
    checkmb = User.checkmobile(mobile)
    print(f"mobile : {checkmb}")
    return jsonify({'valid': checkmb})

@auth.route('/check-email', methods=['GET'])
def check_email():
    email = request.args.get('email')
    checkemail = User.checkemail(email)
    print(f"email : {checkemail}")
    return jsonify({'valid': checkemail})

@auth.route('/find_id')
def find_id():
    return render_template('find_id.html')

@auth.route('/find_id_result', methods=["POST"])
def find_id_result():
    user_name = request.form.get("name")
    user_email = request.form.get("email")
    user_mobile = request.form.get("phone")

    # 휴대폰 번호 포맷팅
    formatted_mobile = f"{user_mobile[:3]}-{user_mobile[3:7]}-{user_mobile[7:]}"

    user = User.find(user_name, user_email, user_mobile)
    
    if user:
        user_id = user['member_id']
        return render_template('find_id_result.html', user_id=user_id, user_name=user_name, user_email=user_email, user_mobile=formatted_mobile)
    else:
        return render_template('find_id.html', error="입력하신 정보로 가입 된 회원 아이디는 존재하지 않습니다.")
    
@auth.route('/find_passwd_info')
def find_passwd_info():
    return render_template('find_passwd_info.html')

@auth.route('/find_passwd_auth', methods=["POST"])
def find_passwd_auth():
    user_id = request.form.get("userid")
    user_name = request.form.get("name")
    user_email = request.form.get("email")
    user_mobile = request.form.get("phone")
    selected_method = request.form.get("selected_method")
    
    print(f"비밀번호 찾기 정보: {user_id}, {user_name}, {user_email}, {user_mobile}")
    
    formatted_mobile = f"{user_mobile[:3]}-{user_mobile[3:7]}-{user_mobile[7:]}"
    user = User.get(user_id)

    if user:
        print(f"비밀번호 유저 정보: {user.member_id}, {user.name}, {user.email}, {user.mobile}")
        if user_id == user.member_id and user_name == user.name:
            if user_email == user.email or user_mobile == user.mobile:
                return render_template('find_passwd_auth.html', user_id=user_id, user_name=user_name, user_email=user_email, user_mobile=formatted_mobile, Method=selected_method)
            else:
                return render_template('find_passwd_info.html', error="입력하신 정보가 올바르지 않습니다.")
        else:
            return render_template('find_passwd_info.html', error="입력하신 정보가 올바르지 않습니다.")
    else:
        return render_template('find_passwd_info.html', error="입력하신 정보로 가입 된 회원 내역이 존재하지 않습니다.")

@auth.route('/find_passwd_change', methods=["GET", "POST"])
def find_passwd_change():
    if request.method == "POST":
        user_id = request.form.get("user_id")
        user_email = request.form.get("user_email")
        user_mobile = request.form.get("user_mobile")
    else:  # GET 요청 처리
        user_id = request.args.get("user_id")
        user_email = request.args.get("user_email")
        user_mobile = request.args.get("user_mobile")

    print(user_id, user_email, user_mobile)

    return render_template('find_passwd_change.html', user_id=user_id, user_email=user_email, user_mobile=user_mobile)

@auth.route('/changed-pw', methods=["POST"])
def changed_pw():
    user_id = request.form.get("userid")
    user_email = request.form.get("user_email")
    user_mobile = request.form.get("user_mobile")
    new_password = request.form.get('new_passwd')
    
    print(user_id, user_email, user_mobile, new_password)

    if User.is_valid_password(new_password):
        User.change_pw(user_id, user_email, user_mobile, new_password)
        return jsonify({'success': True})
    
    return jsonify({'success': False})

@auth.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        id = request.form.get("member_id")
        pw = request.form.get("member_passwd")
        user = User.get(id)
        if user and check_password_hash(user.passwd, pw):
            login_user(user)
            return redirect(url_for('main_bp.main_page'))
        else:
            flash("아이디 또는 비밀번호가 일치하지 않습니다.")
            return render_template('login.html')
    return render_template('login.html')

@auth.route('/logout', methods=['GET'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('main_bp.main_page'))

@auth.route('/delete', methods=['POST'])
@login_required
def delete():
    member_id = request.form['member_id']
    deleted = User.delete(member_id)
    if deleted:
        logout_user()
        return jsonify({'success': True})
    else:
        return jsonify({'success': False})

@auth.route('/check-id', methods=['GET'])
def check_id():
    member_id = request.args.get('member_id')
    checkid = User.checkid(member_id)
    return jsonify({'exists': checkid})

@auth.route('/check-pw', methods=['GET'])
def check_pw():
    password = request.args.get('passwd')
    checkpw = User.is_valid_password(password)
    return jsonify({'valid': checkpw})

@auth.route('/send_otp', methods=['POST'])
def send_otp():
    # AWS Cognito 클라이언트 설정
    client = boto3.client('cognito-idp', region_name='ap-northeast-2')

    try:
        # 요청 데이터 가져오기
        data = request.get_json()
        user_id = data.get('user_id')  # 사용자 ID
        method = data.get('method')   # 인증 방식 (email 또는 mobile)
        contact = data.get('contact') # 이메일 또는 전화번호

        print(f"요청 데이터: 사용자ID={user_id}, 인증 방식={method}")

        # 입력값 검증
        if not user_id or not method or not contact:
            return jsonify({"success": False, "message": "필수 입력값(user_id, method, contact)을 모두 입력해주세요."}), 400

        if method == "mobile":
            # 전화번호 형식 검증 및 변환
            phone = contact.replace("-", "").strip()  # 하이픈 제거 및 공백 제거
            if not phone.isdigit() or not phone.startswith("010"):
                return jsonify({"success": False, "message": "전화번호는 010으로 시작하는 숫자만 입력 가능합니다."}), 400
            contact = f"+82{phone[1:]}"  # 국제 형식으로 변환
            print(f"국제 형식 전화번호: {contact}")

            # 전화번호 속성 업데이트
            client.admin_update_user_attributes(
                UserPoolId='ap-northeast-2_RG8lPds2G',
                Username=user_id,
                UserAttributes=[
                    {'Name': 'phone_number', 'Value': contact},
                    {'Name': 'phone_number_verified', 'Value': 'true'}
                ]
            )
            print(f"전화번호 속성 업데이트 성공: {contact}")

        elif method == "email":
            # 이메일 검증
            if "@" not in contact:
                return jsonify({"success": False, "message": "유효한 이메일 주소를 입력하세요."}), 400

            # 이메일 속성 업데이트
            client.admin_update_user_attributes(
                UserPoolId='ap-northeast-2_RG8lPds2G',
                Username=user_id,
                UserAttributes=[
                    {'Name': 'email', 'Value': contact},
                    {'Name': 'email_verified', 'Value': 'true'}
                ]
            )
            print(f"이메일 속성 업데이트 성공: {contact}")

        else:
            return jsonify({"success": False, "message": "유효하지 않은 인증 방식입니다. (email 또는 mobile만 지원)"}), 400

        # OTP 전송 요청
        otp_response = client.forgot_password(
            ClientId='5rqlo1p0npvqu6g672sng4r74d',
            Username=user_id
        )
        print("OTP 발송 응답:", otp_response)

        return jsonify({"success": True, "message": "인증번호가 성공적으로 전송되었습니다."})

    except client.exceptions.UserNotFoundException:
        return jsonify({"success": False, "message": "입력한 사용자 정보를 찾을 수 없습니다."}), 404
    except client.exceptions.InvalidParameterException as e:
        print(f"잘못된 파라미터: {e}")
        return jsonify({"success": False, "message": "잘못된 입력값입니다. 정보를 확인해주세요."}), 400
    except ClientError as e:
        print(f"OTP 전송 실패: {e}")
        return jsonify({"success": False, "message": "인증번호 전송에 실패했습니다. 잠시 후 다시 시도해주세요.", "error": str(e)}), 500
    except Exception as e:
        print(f"예상치 못한 오류: {e}")
        return jsonify({"success": False, "message": "시스템 오류가 발생했습니다. 관리자에게 문의하세요."}), 500

@auth.route('/verify_otp', methods=['POST'])
def verify_otp():
    """
    AWS Cognito를 사용해 발송된 OTP를 검증하는 API
    """
    # 요청 데이터 가져오기
    verification_data = request.get_json()
    verification_code = verification_data.get('verification_code')
    user_id = verification_data.get('user_id')
    user_email = verification_data.get('user_email')
    user_mobile = verification_data.get('user_mobile')
    
    print(verification_code, user_id, user_email, user_mobile)

    # 입력값 검증
    if not verification_code or not user_id:
        return jsonify({"success": False, "message": "인증번호와 사용자 ID를 모두 입력해주세요."}), 400

    # AWS Cognito 클라이언트 초기화
    client = boto3.client('cognito-idp', region_name='ap-northeast-2')

    # 새 랜덤 비밀번호 생성
    new_password = generate_random_password(length=12)
    print(f"새 랜덤 비밀번호: {new_password}")

    try:
        # AWS Cognito OTP 인증
        response = client.confirm_forgot_password(
            ClientId='5rqlo1p0npvqu6g672sng4r74d',
            Username=user_id,
            ConfirmationCode=verification_code,
            Password=new_password
        )
        print("OTP 인증 성공:", response)

        # 인증 성공 시 사용자 정보를 포함하여 다음 페이지로 리다이렉트
        return jsonify({
            "success": True,
            "message": "인증을 완료하였습니다.",
            "redirect_url": url_for('auth.find_passwd_change', user_id=user_id, user_email=user_email, user_mobile=user_mobile)
        }), 200

    except client.exceptions.CodeMismatchException:
        print("잘못된 인증번호 입력")
        return jsonify({"success": False, "message": "잘못된 인증번호입니다."}), 400
    except client.exceptions.ExpiredCodeException:
        print("만료된 인증번호 사용")
        return jsonify({"success": False, "message": "인증번호가 만료되었습니다."}), 400
    except client.exceptions.UserNotFoundException:
        print("사용자 정보 없음")
        return jsonify({"success": False, "message": "사용자를 찾을 수 없습니다."}), 404
    except client.exceptions.InvalidParameterException as e:
        print(f"잘못된 입력값: {e}")
        return jsonify({"success": False, "message": "입력값을 확인해주세요."}), 400
    except Exception as e:
        print(f"OTP 인증 중 예상치 못한 오류: {e}")
        return jsonify({"success": False, "message": "시스템 오류가 발생했습니다. 관리자에게 문의하세요."}), 500

def generate_random_password(length=12):
    """
    AWS Cognito 비밀번호 정책에 맞는 랜덤 비밀번호 생성.
    - 최소 길이: 12자 (기본값)
    - 포함: 대문자, 소문자, 숫자, 특수문자
    """
    if length < 8:
        raise ValueError("비밀번호는 최소 8자 이상이어야 합니다.")

    # 비밀번호 구성 요소
    upper_case = random.choices(string.ascii_uppercase, k=2)  # 최소 2개의 대문자
    lower_case = random.choices(string.ascii_lowercase, k=4)  # 최소 4개의 소문자
    digits = random.choices(string.digits, k=2)              # 최소 2개의 숫자
    special_characters = random.choices("!@#$%^&*()-_=+", k=2)  # 최소 2개의 특수문자

    # 나머지 랜덤 문자
    remaining_length = length - len(upper_case + lower_case + digits + special_characters)
    remaining = random.choices(string.ascii_letters + string.digits + "!@#$%^&*()-_=+", k=remaining_length)

    # 모든 구성 요소를 섞어서 랜덤 비밀번호 생성
    password = upper_case + lower_case + digits + special_characters + remaining
    random.shuffle(password)
    return ''.join(password)
