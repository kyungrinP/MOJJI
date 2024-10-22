from mojji_Model.mojji_mongodb import conn_mongodb
from bson import ObjectId
import os
from mojji_Model.connection import mojji_s3
from urllib.parse import urlparse

class Closet:
    
    def __init__(self, userID, category, item, color, image):
        self.userID = userID
        self.Cgname = category
        self.item_name = item
        self.color = color
        self.image_url = image

    @staticmethod
    def save_item(userID, Cgname, item_name, color, image_url):
        # S3 매니저 인스턴스 생성
        s3_manager = mojji_s3()
        bucket_name = 'mojji-bucket'

        # S3에서 저장될 경로 설정
        s3_folder = f'main/static/img/uploads/{userID}/Closet'

        # image_url에서 파일명 추출 및 고유한 번호 생성
        file_name, file_extension = os.path.splitext(os.path.basename(image_url))
        file_number = 1
        new_file_name = f"{file_name}_{file_number}{file_extension}"

        # 파일이 중복되면 번호를 증가시키며 새로운 이름을 생성
        while True:
            s3_file_path = f"{s3_folder}/{new_file_name}"
            try:
                s3_manager.s3.head_object(Bucket=bucket_name, Key=s3_file_path)
                file_number += 1
                new_file_name = f"{file_name}_{file_number}{file_extension}"
            except s3_manager.s3.exceptions.ClientError:
                # 객체가 존재하지 않는 경우
                break

        # 최종 S3 파일 경로
        print(f"Final S3 file path: {s3_file_path}")

        # S3 파일을 이동 (복사 후 원본 삭제)
        try:
            s3_manager.move_s3_file(bucket_name, image_url, s3_file_path)
            s3_url = f"https://{bucket_name}.s3.ap-northeast-2.amazonaws.com/{s3_file_path}"
            print(f"Image successfully moved to S3: {s3_url}")
        except Exception as e:
            print(f"Error moving image to S3: {e}")
            return False

        # MongoDB에 데이터 저장
        mojji_ab = conn_mongodb()
        preference = {
            'userID': userID,
            'Cgname': Cgname,
            'item_name': item_name,
            'color': color,
            'image_url': s3_url  # S3 URL을 MongoDB에 저장
        }
        mojji_ab.insert_one(preference)
        print(f"Data inserted into MongoDB: {preference}")
        
        return True

    @staticmethod
    def delete_item(item_id):
        mojji_ab = conn_mongodb()
        query = {'_id': ObjectId(item_id)}
        print(f"Attempting to delete item with query: {query}")  # 쿼리 조건을 출력
        
        # 항목을 검색하여 image_url을 가져옴
        item = mojji_ab.find_one(query)
        if item is None:
            print("No items matched the query. Deletion failed.")
            return False

        # 이미지 파일 URL 추출
        image_url_get = item.get('image_url')
        if not image_url_get:
            print("Image URL is missing in the item.")
            return False

        # URL에서 S3 파일 경로 추출
        parsed_url = urlparse(image_url_get)
        image_url = parsed_url.path.lstrip('/')  # 경로 부분만 추출
        print(f"삭제 파일 경로: {image_url}")
        
        # 항목 삭제 시도
        result = mojji_ab.delete_one(query)
        if result.deleted_count > 0:
            print(f"Deleted {result.deleted_count} item(s) successfully.")
            
            # S3에서 원본 파일 삭제
            try:
                s3_manager = mojji_s3()  # s3 매니저 객체 가져오기
                bucket_name = 'mojji-bucket'

                # S3에서 파일 삭제
                s3_manager.s3.delete_object(Bucket=bucket_name, Key=image_url)
                print(f"원본 파일이 S3에서 성공적으로 삭제되었습니다: {image_url}")
            except Exception as e:
                print(f"S3 파일 삭제 중 오류가 발생했습니다: {e}")
                return False
        else:
            print("No items matched the query. Deletion failed.")
            return False

    @staticmethod
    def edit_item(item_id, new_category, new_item, new_color):
        mojji_ab = conn_mongodb()
        myquery = {'_id': ObjectId(item_id)}
        newvalues = { '$set': {'Cgname': new_category, 'item_name': new_item, 'color': new_color}}
        result = mojji_ab.update_one(myquery, newvalues)
        if result.modified_count > 0:
            print(f"Edited {result.modified_count} item(s) successfully.")
            return True
        else:
            print("No items matched the query. Update failed.")
            
    @staticmethod
    def user_closet(userID):
        mojji_ab = conn_mongodb()
        myquery = {'userID': userID}
        user_closet = list(mojji_ab.find(myquery))
        return user_closet