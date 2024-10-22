import os
from dotenv import load_dotenv

# .env 파일을 로드
load_dotenv()

# 환경 변수 사용
AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY')
AWS_SECRET_KEY = os.getenv('AWS_SECRET_KEY')
BUCKET_NAME = os.getenv('BUCKET_NAME')