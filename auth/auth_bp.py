from flask import render_template, jsonify, request, redirect, url_for, flash, Blueprint
from flask_login import login_required, login_user, logout_user
from werkzeug.security import check_password_hash
from mojji_Control.mojji_user_mgmt import User

auth = Blueprint('auth', __name__, static_folder='static', template_folder='templates')

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

@auth.route('/find_passwd_change', methods=["POST"])
def find_passwd_change():
    user_id = request.form.get("user_id")
    user_email = request.form.get("user_email")
    user_mobile = request.form.get("user_mobile")
    
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