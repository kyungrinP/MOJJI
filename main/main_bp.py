from flask import render_template, request, Blueprint, current_app
from werkzeug.utils import secure_filename
from flask_login import current_user
from mojji_ML.remove_bg import show_rembg  # remove_bg.py 파일에서 show_rembg 함수 가져오기
from mojji_Model.mojji_mongodb import conn_mongodb
from datetime import datetime
import random
from mojji_Control.mojji_favorite import Favorite
from mojji_Control.mojji_user_clothes import Closet
from mojji_Control.mojji_user_mgmt import User
from mojji_ML.Mojji_ML import mojji_ml
from mojji_Crawling.Musinsa_Crawling_recommend import click_button_by_type
from mojji_Crawling.Musinsa_Crawling_Codi import style_links
from mojji_ML.Mojji_CLIP import mojji_recommend
from mojji_Model.connection import mojji_s3

main_bp = Blueprint('main_bp', __name__, static_folder='static', template_folder='templates')

@main_bp.route('/')
def main_page():
    # S3 연결을 위해 mojji_s3 인스턴스 생성
    s3_manager = mojji_s3()  # mojji_s3 클래스 인스턴스 생성
    if not s3_manager:
        return "S3 connection error", 500

    # S3 버킷 및 폴더 경로 설정
    bucket_name = 'mojji-bucket'
    folder_man = 'main/static/img/codishop/MAN/'
    folder_woman = 'main/static/img/codishop/WOMAN/'

    # S3에서 이미지 파일 목록 가져오기 및 섞기
    image_files_man = s3_manager.get_s3_images(bucket_name, folder_man)
    random.shuffle(image_files_man)

    image_files_woman = s3_manager.get_s3_images(bucket_name, folder_woman)
    random.shuffle(image_files_woman)

    # S3 URL 생성
    s3_base_url = f'https://{bucket_name}.s3.ap-northeast-2.amazonaws.com/'

    # 템플릿에 이미지 URL 전달
    return render_template('main.html', 
                           image_man=[s3_base_url + img for img in image_files_man], 
                           image_woman=[s3_base_url + img for img in image_files_woman])

# 파일 이름 유효성 확인
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

@main_bp.route('/loading', methods=['POST'])
def loading():
    file = request.files['photo']
    
    if file and allowed_file(file.filename):  # 파일 형식 체크
        if current_user.is_authenticated:  # 사용자가 로그인되어 있는지 확인
            user_id = current_user.member_id
        else:
            # 로그인되지 않은 경우 JWT 토큰을 생성하여 사용자 ID로 사용
            token = User.create_jwt()
            print(f"Token: {token}")
            user_id = token

        # S3에 업로드할 폴더 설정
        formatted_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        s3_folder = f'main/static/img/uploads/{user_id}/{formatted_time}'
        bucket_name = 'mojji-bucket'  # S3 버킷 이름
        filename = secure_filename(file.filename)

        # S3에 파일 업로드
        s3_manager = mojji_s3()  # 인스턴스 생성
        s3_url = s3_manager.upload_file_to_s3(file, filename, bucket_name, s3_folder)

        if s3_url:
            print(f"S3 파일 경로: {s3_url}")
            return render_template('loading.html', user_upload=s3_url, user_id=user_id, s3_folder=s3_folder)
        else:
            return 'S3 파일 업로드에 실패했습니다.', 500
    else:
        return '허용된 파일 형식은 png, jpg, jpeg 입니다.', 400

@main_bp.route('/result', methods=['POST'])
def result():
    file_path = request.form['file_path']
    s3_folder = request.form['s3_folder']
    print(f"result request: {file_path}, {s3_folder}")

    # show_rembg 함수 실행하여 처리된 이미지 경로 가져오기
    output_image_path = show_rembg(file_path, s3_folder)
    print(f"Result: {output_image_path}")

    # 이미지 디렉토리 설정
    image_dir = f'{s3_folder}/detect_img'

    # 의류 이미지 탐지 및 결과 추출
    detect_img_names = mojji_ml(output_image_path, image_dir)

    # S3에 저장된 CSV 파일에서 결과 불러오기
    s3_manager = mojji_s3()  # mojji_s3 클래스 인스턴스 생성
    result_list = s3_manager.get_s3_csv(f"{image_dir}/output_result.csv")  # CSV 파일 경로 수정

    print(f"Detect Image FileName: {detect_img_names}")

    # 결과 페이지 렌더링
    return render_template('result.html', options=result_list, detect_img=detect_img_names, image_dir=image_dir)

@main_bp.route('/recommend', methods=['GET', 'POST'])
def recommend():
    if current_user.is_authenticated:
        userID = current_user.member_id
    else:
        userID = request.form.get('user_id')

    Cgname = request.form.get('Cgname')
    item_name = request.form.get('item_name')
    item_name_KR = request.form.get('item_name_KR')
    color = request.form.get('color')
    color_KR = request.form.get('color_KR')
    image_url = request.form.get('image_url')
    action = request.form.get('action')

    print(f"Received form data: userID={userID}, Cgname={Cgname}, item_name={item_name}, color={color}, image_url={image_url}, action={action}")  # 폼 데이터 로그

    if action == 'save':
        goods_lists = click_button_by_type(item_name, color)
        query_image_path = image_url.lstrip('/')
        print(f"쿼리 이미지 경로: {query_image_path}")
        top_15_image_urls = mojji_recommend(goods_lists, query_image_path)
        codi_lists = style_links(top_15_image_urls)
        favorites = Favorite.heart_find(userID)
        saved_favorites = [fav['shop'] for fav in favorites]
        print(f"Favorite: {saved_favorites}")
        print(f"코디 병합 리스트: {codi_lists}")

        if current_user.is_authenticated:
            if Closet.save_item(userID, Cgname, item_name, color, query_image_path):
                print("Item saved successfully")
                return render_template('recommend.html', color=color_KR, item_name=item_name_KR, top_15_elements=top_15_image_urls, random_styles=codi_lists, saved_favorites=saved_favorites)
        else:
            return render_template('recommend.html', color=color_KR, item_name=item_name_KR, top_15_elements=top_15_image_urls, random_styles=codi_lists, saved_favorites=saved_favorites)