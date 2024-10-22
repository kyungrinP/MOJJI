import pymongo

# MongoDB 클러스터 호스트
MONGO_HOST = 'mojji-mongodb.cpptrs0fgqae.ap-northeast-2.docdb.amazonaws.com'

# DocumentDB 인증서 파일 경로
TLS_CERT_PATH = 'global-bundle.pem'

# MongoDB 클라이언트 생성 함수
def create_mongo_client():
    return pymongo.MongoClient(
        f'mongodb://{MONGO_HOST}:27017',  # 포트 27017
        ssl=True,  # SSL 사용
        tlsCAFile=TLS_CERT_PATH,  # AWS 제공 TLS 인증서 사용
        tlsAllowInvalidCertificates=False,  # 인증서 검증 설정 (정확한 인증서 사용 시 False 설정)
        retryWrites=False,
        username='mojjiadmin',  # DocumentDB 사용자
        password='k8spass#',  # DocumentDB 사용자 비밀번호
        authSource='admin'  # 인증할 데이터베이스
    )

# 초기 MongoDB 클라이언트 생성
MONGO_CONN = create_mongo_client()

# MongoDB 연결 확인 및 재시도 함수
def ensure_mongo_connection():
    global MONGO_CONN
    try:
        # 연결 상태 확인
        MONGO_CONN.admin.command('ismaster')
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")
        # 연결 재시도
        MONGO_CONN = create_mongo_client()

# 'mojji_ab' 컬렉션 연결 함수
def conn_mongodb():
    ensure_mongo_connection()
    return MONGO_CONN.mojji_session_db.mojji_ab

# 'mojji_like' 컬렉션 연결 함수
def like_mongodb():
    ensure_mongo_connection()
    return MONGO_CONN.mojji_session_db.mojji_like