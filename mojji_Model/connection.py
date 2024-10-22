from mojji_Model.config import AWS_ACCESS_KEY, AWS_SECRET_KEY
import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError, ClientError
from io import StringIO
import csv

class mojji_s3:

    def __init__(self):
        """
        초기화 메서드로 S3 연결을 설정
        """
        self.s3 = self.s3_connection()

    def s3_connection(self):
        """
        s3 bucket에 연결
        :return: 연결된 s3 객체
        """
        try:
            s3 = boto3.client(
                service_name='s3',
                aws_access_key_id=AWS_ACCESS_KEY,
                aws_secret_access_key=AWS_SECRET_KEY
            )
        except NoCredentialsError:
            print("Credentials not available")
            exit(1)  # 적절한 오류 코드를 반환
        except PartialCredentialsError:
            print("Incomplete credentials provided")
            exit(1)
        except Exception as e:
            print(f"An error occurred: {e}")
            exit(1)  # 적절한 오류 코드를 반환
        else:
            print("s3 bucket connected!")
            return s3

    def get_s3_images(self, bucket_name, folder):
        """
        S3 버킷에서 이미지 파일 목록을 가져오는 함수
        :param bucket_name: S3 버킷 이름
        :param folder: 이미지가 저장된 폴더 경로
        :return: 이미지 파일 목록
        """
        try:
            response = self.s3.list_objects_v2(Bucket=bucket_name, Prefix=folder)
            if 'Contents' in response:
                images = [content['Key'] for content in response.get('Contents', []) if content['Key'].endswith(('jpg', 'jpeg', 'png', 'gif'))]
                return images
            else:
                print("No images found in the specified folder.")
                return []
        except Exception as e:
            print(f"Error fetching images from S3: {e}")
            return []

    def upload_file_to_s3(self, file_obj, file_key, bucket_name, s3_folder):
        """
        파일을 S3에 업로드하는 함수
        :param file_obj: 업로드할 파일 객체
        :param file_key: 파일의 이름 또는 경로
        :param bucket_name: S3 버킷 이름
        :param s3_folder: S3에 저장할 폴더 경로
        :return: 업로드된 파일의 S3 URL
        """
        s3_file_path = f"{s3_folder}/{file_key}"  # S3에 저장할 경로 설정

        try:
            # S3에 파일 업로드
            self.s3.upload_fileobj(file_obj, bucket_name, s3_file_path)
            print(f"파일이 S3에 업로드되었습니다: {s3_file_path}")

            # 업로드된 파일의 S3 URL 생성
            s3_url = f"https://{bucket_name}.s3.ap-northeast-2.amazonaws.com/{s3_file_path}"
            return s3_url
        except Exception as e:
            print(f"S3에 파일 업로드 중 오류 발생: {e}")
            return None

    def get_s3_csv(self, file_key):
        """
        S3에서 CSV 파일을 불러오는 함수
        :param file_key: S3에 저장된 CSV 파일의 경로
        :return: CSV 데이터를 담은 리스트
        """
        bucket_name = 'mojji-bucket'
        
        # S3 연결
        s3_manager = mojji_s3()  # mojji_s3 클래스 인스턴스 생성
        try:
            # S3에서 파일 가져오기
            obj = s3_manager.s3.get_object(Bucket=bucket_name, Key=file_key)
            csv_data = obj['Body'].read().decode('utf-8-sig')  # 바이트 데이터를 UTF-8로 디코딩
            print(f"S3에서 파일을 불러옵니다: {file_key}")
            
            # CSV 데이터를 메모리에서 읽기
            csv_file = StringIO(csv_data)  # StringIO 객체를 사용하여 텍스트로 변환
            reader = csv.reader(csv_file)
            data = [row for row in reader]  # CSV 데이터를 리스트로 변환
            return data
        
        except Exception as e:
            print(f"S3에서 CSV 파일을 불러오는 중 오류 발생: {e}")
            return None

    def move_s3_file(self, bucket_name, source_key, destination_key):
        """
        S3 버킷에서 파일을 복사한 후 원본 파일을 삭제하는 함수
        :param bucket_name: S3 버킷 이름
        :param source_key: 원본 파일 경로 (파일 이동 전 경로)
        :param destination_key: 대상 파일 경로 (파일 이동 후 경로)
        """
        try:
            # 파일 복사
            copy_source = {
                'Bucket': bucket_name,
                'Key': source_key
            }
            self.s3.copy_object(CopySource=copy_source, Bucket=bucket_name, Key=destination_key)
            print(f"파일이 복사되었습니다: {destination_key}")
            
            # 원본 파일 삭제
            self.s3.delete_object(Bucket=bucket_name, Key=source_key)
            print(f"원본 파일이 삭제되었습니다: {source_key}")
            
        except ClientError as e:
            print(f"파일 이동 중 오류 발생: {e}")
            return False
        
        return True