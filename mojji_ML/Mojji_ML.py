def mojji_ml(image_path, image_dir):
    # Some basic setup:
    # Setup detectron2 logger
    from detectron2.utils.logger import setup_logger
    # Detectron2의 로깅 설정을 초기화
    setup_logger()

    # import some common libraries
    import numpy as np
    import os, cv2
    import requests
    from io import BytesIO
    from mojji_Model.connection import mojji_s3

    # import some common detectron2 utilities
    from detectron2 import model_zoo
    from detectron2.engine import DefaultPredictor
    from detectron2.config import get_cfg

    #모델 불러오기
    cfg = get_cfg()
    cfg.merge_from_file(model_zoo.get_config_file("COCO-InstanceSegmentation/mask_rcnn_R_50_FPN_3x.yaml"))
    cfg.DATALOADER.NUM_WORKERS = 8
    cfg.MODEL.ROI_HEADS.BATCH_SIZE_PER_IMAGE = 128   # faster (default: 512)
    cfg.MODEL.ROI_HEADS.NUM_CLASSES = 13
    cfg.MODEL.DEVICE = "cpu"

    cfg.MODEL.WEIGHTS = "https://mojji-bucket.s3.ap-northeast-2.amazonaws.com/mojji_ML/model_final.pth"  # path to the model we just trained
    cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = 0.7   # set a custom testing threshold
    predictor = DefaultPredictor(cfg)

    def load_image_from_url(url):
        try:
            # URL에서 이미지 다운로드
            response = requests.get(url)
            if response.status_code == 200:
                # 이미지 데이터를 NumPy 배열로 변환
                image_array = np.frombuffer(response.content, np.uint8)
                # NumPy 배열을 이미지로 디코딩
                img = cv2.imdecode(image_array, cv2.IMREAD_UNCHANGED)
                if img is not None:
                    print(f"Image loaded successfully from {url}")
                return img
            else:
                print(f"Error: Could not retrieve image from {url}, status code: {response.status_code}")
        except Exception as e:
            print(f"Exception occurred while loading image from URL: {e}")
        return None

    # 이미지 불러오기
    im = load_image_from_url(image_path)
    print(f"Output Image Path: {image_path}")

    if im is None:
        print(f"Error: Could not load image at {image_path}")
    else:
        print(f"Image loaded successfully from {image_path}")

    # 알파 채널을 추가한 후 다시 RGB로 변환하여 알파 채널 제거
    if im.shape[2] == 4:  # RGBA 이미지인지 확인
        im = cv2.cvtColor(im, cv2.COLOR_BGRA2BGR)  # 다시 RGB로 변환

    # 추론 수행
    outputs = predictor(im)

    # 추론 결과에서 인스턴스 추출
    instances = outputs["instances"].to("cpu")
    pred_classes = instances.pred_classes.numpy()
    pred_masks = instances.pred_masks.numpy()
    
    # DeepFashion2 클래스 이름 리스트
    class_names = [
        "short_sleeve_top", "long_sleeve_top", "short_sleeve_outer", "long_sleeve_outer", 
        "vest", "sling", "shorts", "trousers", "skirt", "short_sleeve_dress", 
        "long_sleeve_dress", "vest_dress", "sling_dress"
    ]

    detected_items = []
    # 이미지에 각 마스크를 적용하여 개별 의상 이미지 생성 및 저장
    for i in range(len(pred_classes)):
        mask = pred_masks[i]
        masked_img = cv2.cvtColor(im.copy(), cv2.COLOR_BGR2BGRA)  # 알파 채널 추가

        # 투명 배경 설정
        masked_img[mask == 0] = [0, 0, 0, 0]

        # 잘려진 이미지 크기 계산
        x, y, w, h = cv2.boundingRect(mask.astype(np.uint8))

        # 잘린 이미지 추출
        cropped_img = masked_img[y:y+h, x:x+w]

        # 정사각형 크기 계산
        max_side = max(w, h)
        square_img = np.zeros((max_side, max_side, 4), dtype=np.uint8)

        # 정사각형 이미지에 잘린 이미지 삽입
        if w > h:
            y_offset = (max_side - h) // 2
            square_img[y_offset:y_offset+h, :w] = cropped_img
        else:
            x_offset = (max_side - w) // 2
            square_img[:h, x_offset:x_offset+w] = cropped_img

        # 클래스 이름 가져오기
        class_name = class_names[pred_classes[i]]
        
        # 이미지를 메모리 버퍼에 저장
        is_success, buffer = cv2.imencode(".png", square_img)
        if is_success:
            file_obj = BytesIO(buffer)

            # S3에 파일 업로드
            file_key = f"{class_name}_{i}.png"
            bucket_name = 'mojji-bucket'  # S3 버킷 이름
            # S3에 파일 업로드
            s3_manager = mojji_s3()  # 인스턴스 생성
            s3_url = s3_manager.upload_file_to_s3(file_obj, file_key, bucket_name, image_dir)
            
            if s3_url:
                detected_items.append((class_name, s3_url))
                print(f"Uploaded {class_name}_{i} to {s3_url}")
        else:
            print(f"Failed to encode {class_name}_{i} as PNG")

    # S3에 업로드된 파일 목록과 파일명 추출
    if detected_items:
        # S3 URL 목록 생성
        detect_img_urls = [item[1] for item in detected_items]
        
        # 파일 이름 목록 생성 (S3 URL에서 파일 이름만 추출)
        detect_img_names = [os.path.basename(url) for url in detect_img_urls]
    else:
        detect_img_urls = []
        detect_img_names = []

    # 결과 출력
    print(f"detect_img_urls: {detect_img_urls}")
    print(f"detect_img_names: {detect_img_names}")

    # 옷 카테고리 추출
    import pandas as pd
    from PIL import Image, ImageEnhance
    from extcolors import extract_from_image
    import json
    import colorgram
    import math

    def euclidean_distance(color1, color2):
        return math.sqrt(sum((e1-e2)**2 for e1, e2 in zip(color1, color2)))
    
    # 의류 색상 기준 RGB 값
    clothing_colors = {
        'black': (0, 0, 0),
        'white': (255, 255, 255),
        'red': (255, 0, 0),
        'orange': (255, 69, 0),
        'yellow': (255, 215, 0),
        'green': (34, 139, 34),
        'sky': (135, 206, 235),
        'blue': (0, 0, 205),
        'denim': (47, 79, 79),
        'navy': (25, 25, 112),
        'khaki': (60, 60, 30),
        'pink': (255, 163, 185),
        'purple': (148, 0, 211),
        'camel': (195, 39, 0),
        'beige': (222, 184, 135),
        'brown': (45, 27, 23),
        'ivory': (200, 200, 200),
        'grey': (128, 128, 128)
    }

    def match_color(rgb):
        min_distance = float('inf')
        matched_color = "etc"
        for color_name, color_rgb in clothing_colors.items():
            distance = euclidean_distance(rgb, color_rgb)
            if distance < min_distance:
                min_distance = distance
                matched_color = color_name
        return matched_color
    
    def rgb_to_hex(rgb_tuple):
        r = int(rgb_tuple[0])
        g = int(rgb_tuple[1])
        b = int(rgb_tuple[2])
        return '#' + hex(r)[2:].zfill(2) + hex(g)[2:].zfill(2) + hex(b)[2:].zfill(2)

    def load_colors_dict(file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            colors_dict = json.load(file)
        return colors_dict

    def get_color_code(rgb, color_ranges):
        for color in color_ranges:
            if all(color["rgb_range"]["min"][i] <= rgb[i] <= color["rgb_range"]["max"][i] for i in range(3)):
                return color["color_code"]
        return "etc"

    # JSON 객체 초기화
    clothing_info = {
        "상 의": "",
        "상의 색상": "",
        "하 의": "",
        "하의 색상": "",
        "아우터": "",
        "아우터 색상": "",
        "드레스": "",
        "드레스 색상": ""
    }

    # detected_items를 사용하여 class_name과 S3 URL을 가져옵니다
    for class_name, detect_img_url in detected_items:
        # S3에서 이미지를 다운로드하여 처리
        response = requests.get(detect_img_url)
        img_data = BytesIO(response.content)
        converted_image = Image.open(img_data)

        # 색상 및 채도 조정
        converted_image = ImageEnhance.Color(converted_image).enhance(2.0)
        converted_image = ImageEnhance.Sharpness(converted_image).enhance(2.0)

        # 색상 추출
        colors, pixel_count = extract_from_image(converted_image, tolerance=10, limit=3)
        # colors = colorgram.extract(detect_img_path, 2)
        # color_palette = [(color.rgb.r, color.rgb.g, color.rgb.b) for color in colors]

        most_colors = {}

        pixel_output = 0
        for idx, color in enumerate(colors):
            pixel_output += color[1]
            color_rgb = list(color[0])
            color_ratio = round((color[1] / pixel_count) * 100, 2)
            color_pixels = color[1]

            most_colors[idx] = {}
            most_colors[idx]["RGB"] = color_rgb
            most_colors[idx]["HEX"] = rgb_to_hex(color_rgb)
            most_colors[idx]["RATIO"] = f'{color_ratio}%'
            most_colors[idx]["PIXELS"] = color_pixels

        # json_file_path = 'mojji_ML/RGB_Color_Codes_Chart.json'
        # color_ranges = load_colors_dict(json_file_path)["colors"]
        # dominant_color_code = get_color_code(most_colors[0]["RGB"], color_ranges)
        # print(f"Color: {most_colors}")
        
        matched_color = match_color(most_colors[0]["RGB"])
        print(f'추출된 색상 {most_colors[0]["RGB"]}는 의류 색상 {matched_color}에 매칭됩니다.')

        if 'short_sleeve_top' == class_name or 'long_sleeve_top' == class_name or 'vest' == class_name or 'sling' == class_name:
            if class_name == 'vest':
                class_name = 'sling'
            clothing_info["상 의"] = class_name
            clothing_info["상의 색상"] = matched_color
        elif 'shorts' == class_name or 'trousers' == class_name or 'skirt' == class_name:
            clothing_info["하 의"] = class_name
            clothing_info["하의 색상"] = matched_color
        elif 'short_sleeve_outer' == class_name or 'long_sleeve_outer' == class_name:
            clothing_info["아우터"] = class_name
            clothing_info["아우터 색상"] = matched_color
        elif 'short_sleeve_dress' == class_name or 'long_sleeve_dress' == class_name or 'vest_dress' == class_name or 'sling_dress' == class_name:
            clothing_info["드레스"] = class_name
            clothing_info["드레스 색상"] = matched_color

    # Save results as CSV in memory
    df = pd.DataFrame([clothing_info])
    csv_buffer = BytesIO()  # 메모리 버퍼에 CSV 파일 저장
    df.to_csv(csv_buffer, index=False, encoding='utf-8-sig')
    csv_buffer.seek(0)  # 버퍼 포인터를 처음으로 되돌림

    # S3에 CSV 파일 업로드
    csv_key = "output_result.csv"
    # S3에 파일 업로드
    s3_manager = mojji_s3()  # 인스턴스 생성
    csv_s3_url = s3_manager.upload_file_to_s3(csv_buffer, csv_key, bucket_name, image_dir)
    if csv_s3_url:
        print(f"CSV 파일이 S3에 업로드되었습니다: {csv_s3_url}")
    else:
        print("CSV 파일 업로드 실패")

    return detect_img_names