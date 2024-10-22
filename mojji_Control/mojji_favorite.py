from mojji_Model.mojji_mongodb import like_mongodb
from botocore.exceptions import ClientError
from flask_login import current_user
from mojji_Model.connection import mojji_s3
import requests
from io import BytesIO

class Favorite:
    
    def __init__(self, userID, image):
        self.userID = userID
        self.image_url = image

    @staticmethod
    def heart_save(userID, image_url, href):
        # S3 매니저 인스턴스 생성
        s3_manager = mojji_s3()
        bucket_name = 'mojji-bucket'

        # S3에서 저장될 경로 설정
        s3_folder = f'main/static/img/uploads/{userID}/favorite'

        # favorite_1, favorite_2, ... 식으로 파일명 생성
        file_number = 1
        file_extension = image_url.split('.')[-1].split('?')[0]  # 쿼리 매개변수 제거
        file_name = f"favorite_{file_number}.{file_extension}"

        # 파일이 중복되면 번호를 증가시키며 새로운 이름을 생성
        while True:
            s3_file_path = f"{s3_folder}/{file_name}"
            try:
                s3_manager.s3.head_object(Bucket=bucket_name, Key=s3_file_path)
                file_number += 1
                file_name = f"favorite_{file_number}.{file_extension}"
                s3_file_path = f"{s3_folder}/{file_name}"
            except ClientError as e:
                # 객체가 존재하지 않는 경우, 반복을 종료하고 파일을 저장
                if e.response['Error']['Code'] == '404':
                    break
                else:
                    print(f"예상치 못한 오류 발생: {e}")
                    return None
        
        # 파일 업로드 처리
        try:
            # 이미지 URL에서 이미지를 다운로드
            response = requests.get(image_url)
            response.raise_for_status()  # 요청 오류가 발생하면 예외를 발생시킴

            # 이미지를 BytesIO로 변환
            file_obj = BytesIO(response.content)
            
            # S3에 파일 업로드
            s3_manager.upload_file_to_s3(file_obj, file_name, bucket_name, s3_folder)
            print(f"파일이 S3에 성공적으로 업로드되었습니다: {s3_file_path}")
        except Exception as e:
            print(f"S3에 파일 업로드 중 오류 발생: {e}")
            return None
        
        # 데이터베이스에 정보 저장
        if current_user.is_authenticated:
            mojji_like = like_mongodb()
            preference = {
                'userID': userID,
                'image': s3_file_path,  # 저장된 파일 경로를 저장
                'shop': href
            }
            mojji_like.insert_one(preference)
            print(f"데이터베이스에 항목이 성공적으로 저장되었습니다: {preference}")
        else:
            print(f"로그인 후 이용할 수 있습니다. 로그인 페이지로 이동하시겠습니까?")

        return file_name
    
    @staticmethod
    def heart_delete(userID, image):
        mojji_like = like_mongodb()
        query = {'userID': userID, 'image': image}
        print(f"Attempting to delete item with query: {query}")  # 쿼리 조건을 출력
        
        # 데이터베이스에서 항목 삭제 시도
        result = mojji_like.delete_one(query)
        if result.deleted_count > 0:
            print(f"Deleted {result.deleted_count} item(s) successfully.")
            
            # S3에서 원본 파일 삭제
            try:
                s3_manager = mojji_s3()  # s3 매니저 객체 가져오기
                bucket_name = 'mojji-bucket'

                # S3에서 파일 삭제
                s3_manager.s3.delete_object(Bucket=bucket_name, Key=image)
                print(f"원본 파일이 S3에서 성공적으로 삭제되었습니다: {image}")
            except Exception as e:
                print(f"S3 파일 삭제 중 오류가 발생했습니다: {e}")
                return False
        else:
            print("No items matched the query. Deletion failed.")
            return False

    @staticmethod
    def heart_find(userID):
        mojji_like = like_mongodb()
        myquery = {'userID': userID}
        heart_find = list(mojji_like.find(myquery))
        return heart_find

    @staticmethod
    def heart_find_recommend(userID, href):
        mojji_like = like_mongodb()
        myquery = {'userID': userID, 'shop': href}
        heart_find_recommend = list(mojji_like.find(myquery))
        return heart_find_recommend