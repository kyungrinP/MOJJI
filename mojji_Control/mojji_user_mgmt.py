from flask_login import UserMixin
from mojji_Model.mojji_mysql import conn_mysqldb
from mojji_Model.mojji_mongodb import conn_mongodb, like_mongodb
from werkzeug.security import generate_password_hash
from flask import current_app
import jwt
import datetime
import os
import shutil
from mojji_Model.connection import mojji_s3

class User(UserMixin):
    
    def __init__(self, id, member_id, passwd, hint, hint_answer, name, postcode1, addr1, addr2, extraAddress, mobile, email):
        self.id = id
        self.member_id = member_id
        self.passwd = passwd
        self.hint = hint
        self.hint_answer = hint_answer
        self.name = name
        self.postcode1 = postcode1
        self.addr1 = addr1
        self.addr2 = addr2
        self.extraAddress = extraAddress
        self.mobile = mobile
        self.email = email
        
    def get_id(self):
        return str(self.member_id)
    
    @staticmethod
    def get(user_id):
        mysql_db = conn_mysqldb()
        db_cursor = mysql_db.cursor()
        sql = "SELECT * FROM users WHERE member_id = %s"
        db_cursor.execute(sql, (user_id))
        user = db_cursor.fetchone()
        if not user:
            return None
        return User(
            id=user['id'], 
            member_id=user['member_id'], 
            passwd=user['passwd'],
            hint=user['hint'],
            hint_answer=user['hint_answer'],
            name=user['name'],
            postcode1=user['postcode1'],
            addr1=user['addr1'],
            addr2=user['addr2'],
            extraAddress=user['extraAddress'],
            mobile=user['mobile'],
            email=user['email']
        )

    def to_dict(self):
        return {
            'id': self.id,
            'member_id': self.member_id,
            'passwd': self.passwd,
            'hint': self.hint,
            'hint_answer': self.hint_answer,
            'name': self.name,
            'postcode1': self.postcode1,
            'addr1': self.addr1,
            'addr2': self.addr2,
            'extraAddress': self.extraAddress,
            'mobile': self.mobile,
            'email': self.email
        }

    @staticmethod
    def find(user_name, user_email, user_mobile):
        mysql_db = conn_mysqldb()
        db_cursor = mysql_db.cursor()
        sql = "SELECT member_id FROM users WHERE name = %s AND (email = %s OR mobile = %s)"
        db_cursor.execute(sql, (user_name,user_email,user_mobile))
        user = db_cursor.fetchone()
        
        if not user:
            return None

        return user
    
    @staticmethod
    def register(member_id, passwd, hint, hint_answer, name, postcode1, addr1, addr2, extraAddress, mobile, email):
        mysql_db = conn_mysqldb()
        db_cursor = mysql_db.cursor()
        
        hashed_password = generate_password_hash(passwd, method='pbkdf2:sha256')

        sql = """
        INSERT INTO users (member_id, passwd, hint, hint_answer, name, postcode1, addr1, addr2, extraAddress, mobile, email)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        register = db_cursor.execute(sql, (member_id, hashed_password, hint, hint_answer, name, postcode1, addr1, addr2, extraAddress, mobile, email))
        mysql_db.commit()
        print(f"register 결과값: {register}")
        return register
    
    @staticmethod
    def checkid(member_id):
        mysql_db = conn_mysqldb()
        db_cursor = mysql_db.cursor()
        sql = "SELECT COUNT(*) AS count FROM users WHERE member_id = %s"
        db_cursor.execute(sql, (member_id,))
        user = db_cursor.fetchone()
        exists = user['count'] > 0
        return exists
    
    @staticmethod
    def checkmobile(mobile):
        mysql_db = conn_mysqldb()
        db_cursor = mysql_db.cursor()
        sql = "SELECT COUNT(*) AS count FROM users WHERE mobile = %s"
        db_cursor.execute(sql, (mobile,))
        user = db_cursor.fetchone()
        exists = user['count'] > 0
        return exists
    
    @staticmethod
    def checkemail(email):
        mysql_db = conn_mysqldb()
        db_cursor = mysql_db.cursor()
        sql = "SELECT COUNT(*) AS count FROM users WHERE email = %s"
        db_cursor.execute(sql, (email,))
        user = db_cursor.fetchone()
        exists = user['count'] > 0
        return exists
    
    @staticmethod
    def updatecheck(mobile, email, member_id):
        mysql_db = conn_mysqldb()
        db_cursor = mysql_db.cursor()
        sql = "SELECT COUNT(*) AS count FROM users WHERE mobile = %s AND email = %s AND member_id = %s"
        db_cursor.execute(sql, (mobile, email, member_id))
        user = db_cursor.fetchone()
        exists = user['count'] > 0
        return exists

    @staticmethod
    def is_valid_password(password):
        import re
        # 비밀번호 조건: 8자에서 16자, 대소문자, 숫자, 특수문자 조합
        if len(password) < 8 or len(password) > 16:
            return False
        if not re.search(r"[A-Z]", password):
            return False
        if not re.search(r"[a-z]", password):
            return False
        if not re.search(r"\d", password):
            return False
        if not re.search(r"[~`!@#\$%\^&\*\(\)_\-\=\{\}\[\]\|;:<>,\.?/]", password):
            return False
        if re.search(r"\s", password):  # 공백 포함 여부
            return False
        if re.search(r"(.)\1\1", password):  # 동일 문자 반복 여부
            return False
        if re.search(r"(012|123|234|345|456|567|678|789|890|abc|bcd|cde|def|efg|fgh|ghi|hij|ijk|jkl|klm|lmn|mno|nop|opq|pqr|qrs|rst|stu|tuv|uvw|vwx|wxy|xyz)", password.lower()):  # 연속 문자 사용 여부
            return False
        return True
    
    @staticmethod
    def change_pw(user_id, user_email, user_mobile, new_password):
        mysql_db = conn_mysqldb()
        db_cursor = mysql_db.cursor()
        
        hashed_password = generate_password_hash(new_password)
        
        sql = "UPDATE users SET passwd = %s WHERE member_id = %s AND (email = %s OR mobile = %s)"

        ex = db_cursor.execute(sql, (hashed_password, user_id, user_email, user_mobile))
        print(ex, user_id, user_email, user_mobile)
        
        # 변경 사항을 커밋합니다.
        mysql_db.commit()
        
        user = db_cursor.fetchone()

        return user
    
    @staticmethod
    def update(member_id, name, passwd, hint, hint_answer, postcode1, addr1, addr2, extraAddress, mobile, email):
        mysql_db = conn_mysqldb()
        db_cursor = mysql_db.cursor()
        
        hashed_password = generate_password_hash(passwd)
        
        sql = "UPDATE users SET passwd = %s, hint = %s, hint_answer = %s, postcode1 = %s, addr1 = %s, addr2 = %s, extraAddress = %s, mobile = %s, email = %s WHERE member_id = %s AND name = %s"
        
        user_update = db_cursor.execute(sql, (hashed_password, hint, hint_answer, postcode1, addr1, addr2, extraAddress, mobile, email, member_id, name))
        mysql_db.commit()
        return user_update

    @staticmethod
    def delete(user_id):
        print(f"{user_id}님이 탈퇴를 원합니다.")
        mysql_db = conn_mysqldb()
        db_cursor = mysql_db.cursor()
        sql = "DELETE FROM users WHERE member_id = %s"
        deleted = db_cursor.execute(sql, (user_id,))
        mysql_db.commit()
        
        # `mojji_ab` 컬렉션에서 userID에 해당하는 데이터 삭제
        mojji_ab = conn_mongodb()
        delete_ab_result = mojji_ab.delete_many({'userID': user_id})
        print(f"{delete_ab_result.deleted_count} document(s) deleted from mojji_ab collection")
        
        # `mojji_like` 컬렉션에서 userID에 해당하는 데이터 삭제
        mojji_like = like_mongodb()
        delete_like_result = mojji_like.delete_many({ "userID": user_id })
        print(f"{delete_like_result.deleted_count} document(s) deleted from mojji_like collection")

        # S3에서 폴더 삭제
        try:
            s3_manager = mojji_s3()  # s3 매니저 객체 가져오기
            bucket_name = 'mojji-bucket'
            s3_folder = f'main/static/img/uploads/{user_id}/'

            # 폴더 안의 모든 객체(파일)를 삭제
            s3_objects = s3_manager.s3.list_objects_v2(Bucket=bucket_name, Prefix=s3_folder)
            
            if 'Contents' in s3_objects:
                for obj in s3_objects['Contents']:
                    s3_manager.s3.delete_object(Bucket=bucket_name, Key=obj['Key'])
                    print(f"파일 삭제: {obj['Key']}")
            else:
                print(f"S3 폴더 내에 삭제할 파일이 없습니다: {s3_folder}")
            
            print(f"폴더 내 모든 파일이 S3에서 성공적으로 삭제되었습니다: {s3_folder}")
        except Exception as e:
            print(f"S3 폴더 삭제 중 오류가 발생했습니다: {e}")
            return False
        
        return deleted, delete_ab_result, delete_like_result

    @staticmethod
    def create_jwt():
        payload = {
            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)
        }
        return jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256')