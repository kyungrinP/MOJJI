import os
from io import BytesIO
from PIL import Image, ImageFile
from rembg import remove
from mojji_Model.connection import mojji_s3

ImageFile.LOAD_TRUNCATED_IMAGES = True

def show_rembg(file_path, s3_folder):
    # 파일명과 확장자를 분리
    filename_with_ext = os.path.basename(file_path)
    filename, ext = os.path.splitext(filename_with_ext)
    print(f"사용자 업로드 파일 이름 (확장자 제거): {filename}")

    # S3에서 파일 불러오기
    bucket_name = 'mojji-bucket'
    s3_file_path = f'{s3_folder}/{filename_with_ext}'
    print(f"S3에서 파일을 불러옵니다: {s3_file_path}")

    # S3에서 이미지를 다운로드하여 BytesIO 객체에 저장
    s3_manager = mojji_s3()  # mojji_s3 클래스 인스턴스 생성
    try:
        obj = s3_manager.s3.get_object(Bucket=bucket_name, Key=s3_file_path)
        image = Image.open(BytesIO(obj['Body'].read())).convert('RGBA')
        print("이미지 로드 성공")
    except Exception as e:
        print(f"S3에서 이미지를 불러오는 중 오류 발생: {e}")
        return None

    # 배경 제거
    try:
        result_data = remove(image)
        print("배경 제거 성공")
    except Exception as e:
        print(f"배경 제거 중 오류 발생: {e}")
        return None

    # 배경 제거된 이미지를 BytesIO 객체에 저장
    output_image_io = BytesIO()
    try:
        result_data.save(output_image_io, format='PNG')
        output_image_io.seek(0)  # 파일 포인터를 처음으로 이동
    except Exception as e:
        print(f"이미지 저장 중 오류 발생: {e}")
        return None

    # S3에 업로드할 파일 이름
    output_image_key = f"{filename}_rembg.png"
    print(f"Output image key: {output_image_key}")
    
    # 배경 제거된 이미지를 S3에 업로드
    try:
        output_image_path = s3_manager.upload_file_to_s3(output_image_io, output_image_key, bucket_name, s3_folder)
        if output_image_path:
            print(f"배경 제거된 이미지가 S3에 업로드되었습니다: {output_image_path}")
        else:
            print("S3 업로드 실패")
            return None
    except Exception as e:
        print(f"S3 업로드 중 오류 발생: {e}")
        return None

    # 최종 경로 리턴
    return output_image_path