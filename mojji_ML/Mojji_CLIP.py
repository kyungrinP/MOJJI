import torch
import clip
from PIL import Image
import requests
from io import BytesIO
import requests

# CLIP 모델과 전처리기를 로드합니다.
device = "cuda" if torch.cuda.is_available() else "cpu"
model, preprocess = clip.load("ViT-B/32", device=device)

# URL 이미지를 로드하고 전처리합니다.
def load_and_preprocess_images(image_urls):
    images = []
    valid_image_urls = []
    for url in image_urls:
        try:
            response = requests.get(url)
            image = preprocess(Image.open(BytesIO(response.content))).unsqueeze(0).to(device)
            images.append(image)
            valid_image_urls.append(url)
        except Exception as e:
            print(f"Failed to load image from {url}: {e}")
    return images, valid_image_urls

# 이미지를 임베딩 공간으로 변환하는 함수입니다.
def encode_images(images):
    with torch.no_grad():
        image_features = torch.cat([model.encode_image(image) for image in images])
    image_features /= image_features.norm(dim=-1, keepdim=True)
    return image_features

def search_images_by_image(query_image_url, images, image_urls):
    # S3 URL 생성
    s3_base_url = f'https://mojji-bucket.s3.ap-northeast-2.amazonaws.com/{query_image_url}'

    # 검색 쿼리 이미지를 S3에서 가져옵니다.
    try:
        response = requests.get(s3_base_url)
        query_image = preprocess(Image.open(BytesIO(response.content))).unsqueeze(0).to(device)
    except Exception as e:
        print(f"Failed to load query image from {s3_base_url}: {e}")
        return []

    # 쿼리 이미지의 임베딩을 만듭니다.
    with torch.no_grad():
        query_image_features = model.encode_image(query_image)
    
    # 모든 이미지의 임베딩을 만듭니다.
    image_features = encode_images(images)
    
    # 유사도를 계산합니다.
    query_image_features /= query_image_features.norm(dim=-1, keepdim=True)
    similarities = (query_image_features @ image_features.T).squeeze(0)
    
    # 유사도 순으로 이미지를 정렬합니다.
    sorted_indices = similarities.argsort(descending=True).cpu().numpy()
    sorted_image_urls = [image_urls[idx] for idx in sorted_indices]
    return sorted_image_urls

def mojji_recommend(goods_lists, query_image_url):
    # goods_lists에서 src와 href를 추출하여 리스트를 만듭니다.
    image_data = [{'src': item['src'], 'href': item['href']} for item in goods_lists]

    # URL에서 이미지를 로드 및 전처리
    image_urls = [item['src'] for item in image_data]
    images, valid_image_urls = load_and_preprocess_images(image_urls)

    # 이미지 검색
    result_image_urls = search_images_by_image(query_image_url, images, valid_image_urls)

    # 유사도가 가장 높은 이미지 15개 출력 (중복 제거)
    top_15_image_data = []
    for url in result_image_urls:
        for item in image_data:
            if item['src'] == url and item not in top_15_image_data:
                top_15_image_data.append(item)
                break
        if len(top_15_image_data) >= 15:
            break
    print("top15 리스트:", top_15_image_data)
    print("top15리스트 개수:", len(top_15_image_data))

    return top_15_image_data