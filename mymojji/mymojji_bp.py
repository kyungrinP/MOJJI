from flask import render_template, jsonify, request, redirect, url_for, Blueprint
from flask_login import current_user, login_required
from mojji_Control.mojji_user_mgmt import User
from mojji_Model.mojji_mongodb import conn_mongodb
from bson.objectid import ObjectId
from mojji_Control.mojji_user_clothes import Closet
from mojji_Control.mojji_favorite import Favorite
from mojji_Crawling.Musinsa_Crawling_recommend import click_button_by_type
from mojji_Crawling.Musinsa_Crawling_Codi import style_links
from mojji_ML.Mojji_CLIP import mojji_recommend
from urllib.parse import urlparse

mymojji = Blueprint('mymojji', __name__, static_folder='static', template_folder='templates')

@mymojji.route('/modify')
@login_required
def modify():
    member_id = current_user.get_id()
    user = User.get(member_id)
    user_data = user.to_dict()
    return render_template('modify.html', member_id=member_id, user=user_data)

@mymojji.route('/update', methods=["GET", "POST"])
def update():
    if request.method == "GET":
        member_id = request.args.get('member_id')
        mobile = request.args.get('mobile')
        email = request.args.get('email')

        # 사용자 찾기 및 mobile 검사
        user = User.get(member_id)
        if user.member_id == member_id:
            if user.mobile == mobile:
                if user.email == email:
                    return jsonify({'success': True})
                else:
                    if User.checkemail(email):
                        return jsonify({'success': 'emailFalse'})
            else:
                if User.checkmobile(mobile):
                    return jsonify({'success': 'mobileFalse'})

        # email을 다시 검사하는 부분
        user = User.get(member_id)
        if user.member_id == member_id:
            if user.email == email:
                return jsonify({'success': True})
            else:
                if User.checkemail(email):
                    return jsonify({'success': 'emailFalse'})

        return jsonify({'success': 'updateFailed'})  # 모든 조건이 실패하면 실패 메시지 반환
    
    if request.method == "POST":
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

        User.update(member_id, name, passwd, hint, hint_answer, postcode1, addr1, addr2, extraAddress, mobile, email)
        return redirect(url_for('main_bp.main_page'))

    return jsonify({'success': 'invalidRequest'})

@mymojji.route('/favorite', methods=['GET', 'POST'])
@login_required
def favorite():
    userID = current_user.member_id
    user_favorite = Favorite.heart_find(userID)
    print(f"추천페이지 href 확인: {user_favorite}")
    if request.method == 'POST':
        data = request.get_json()
        
        action = data.get('action')
        image = data.get('image')
        userID = data.get('userID')
        file_name = data.get('file_name')
        href = data.get('href')

        print(f"Received form data: action={action}, image={image}, userID={userID}, file_name={file_name}, href={href}")
    
        if action == 'save':
            file_name = Favorite.heart_save(userID, image, href)
            return jsonify(success=True, file_name=file_name)
        elif action == 'delete':
            for fav in user_favorite:
                if fav['shop'] == href or fav['image'] == file_name:
                    print(f"추천페이지 하트 저장 확인: {fav}")
                    Favorite.heart_delete(userID, fav['image'])
                    return jsonify(success=True)
            return jsonify(success=False, message="Item not found")
    return render_template('favorite.html', userID=userID, items=user_favorite)

@mymojji.route('/closet')
@login_required
def closet():
    userID = current_user.member_id
    user_closet = Closet.user_closet(userID)
    print(f"옷장 데이터: {user_closet}")
    return render_template('closet.html', items=user_closet)

@mymojji.route('/closet_save', methods=['POST'])
@login_required
def closet_save():
    userID = current_user.member_id
    item_id = request.form.get('item_id')
    Cgname = request.form.get('Cgname')
    item_name = request.form.get('item_name')
    item_name_KR = request.form.get('item_name_KR')
    color = request.form.get('color')
    color_KR = request.form.get('color_KR')
    image_url = request.form.get('image_url')
    action = request.form.get('action')
    
    print(f"Received form data: item_id={item_id}, Cgname={Cgname}, item_name={item_name}, item_name_KR={item_name_KR}, color={color}, color_KR={color_KR}, image_url={image_url}, action={action}")  # 폼 데이터 로그

    if action == 'delete':
        if item_id and Closet.delete_item(item_id):
            print("Item deleted successfully")
        else:
            print("Item deletion failed")
    elif action == 'edit':
        new_category = request.form.get('Cgname')
        new_item = request.form.get('item_name')
        new_color = request.form.get('color')
        if item_id and Closet.edit_item(item_id, new_category, new_item, new_color):
            print("Item edited successfully")
        else:
            print("Item edit failed")
    elif action == 'research':
        goods_lists = click_button_by_type(item_name, color)
        query_image_path = image_url.lstrip('/')
        print(f"쿼리 이미지 경로: {query_image_path}")
        # URL에서 S3 파일 경로 추출
        parsed_url = urlparse(query_image_path)
        image_url = parsed_url.path.lstrip('/')  # 경로 부분만 추출
        print(f"삭제 파일 경로: {image_url}")
        top_15_image_urls = mojji_recommend(goods_lists, image_url)
        codi_lists = style_links(top_15_image_urls)
        favorites = Favorite.heart_find(userID)
        saved_favorites = [fav['shop'] for fav in favorites]
        print(f"Favorite: {saved_favorites}")
        print(f"코디 병합 리스트: {codi_lists}")
        
        return render_template('recommend.html', color=color_KR, item_name=item_name_KR, top_15_elements=top_15_image_urls, random_styles=codi_lists, saved_favorites=saved_favorites)

    image_urls = conn_mongodb().find({})

    return render_template('closet.html', items=image_urls)

@mymojji.route('/closet_img/<item_id>')
@login_required
def closet_img(item_id):
    mojji_ab = conn_mongodb()
    item = mojji_ab.find_one({'_id': ObjectId(item_id)})
    print(item)
    item['_id'] = str(item['_id'])
    return render_template('closet_img.html', item=item)