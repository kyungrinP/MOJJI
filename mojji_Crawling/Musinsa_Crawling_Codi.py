import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import cv2
import pytesseract
from PIL import Image
import requests
from io import BytesIO
import numpy as np

# Tesseract-OCR 설치 경로를 설정
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Windows 경로

# Chrome 옵션 설정
options = webdriver.ChromeOptions()
options.binary_location = "/usr/bin/google-chrome"
options.add_argument("--disable-extensions")  # 확장 프로그램 비활성화
options.add_argument("--headless")  # 창을 띄우지 않고 백그라운드에서 실행

# ChromeDriver 자동 설치 및 업데이트
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

def preprocess_image(image):
    # 이미지 크기 조정
    image = cv2.resize(image, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    
    # 그레이스케일 변환
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # 대비 조정
    gray = cv2.convertScaleAbs(gray, alpha=1.5, beta=0)
    
    # 적응형 이진화 처리
    binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)
    
    # 잡음 제거
    kernel = np.ones((1, 1), np.uint8)
    binary = cv2.dilate(binary, kernel, iterations=1)
    binary = cv2.erode(binary, kernel, iterations=1)
    
    return binary

def detect_text_in_image(img_src):
    try:
        response = requests.get(img_src)
        img = Image.open(BytesIO(response.content))
        text = pytesseract.image_to_string(img)
        return bool(text.strip())
    except Exception as e:
        print(f"텍스트 감지 중 오류 발생: {e}")
        return False

def style_links(style_image):
    codimap_list = []
    shopstaff_list = []
    style_list = []
    
    # Chrome 옵션 설정
    options = webdriver.ChromeOptions()
    options.binary_location = "/usr/bin/google-chrome"
    options.add_argument("--start-maximized")
    options.add_argument("--disable-extensions")
    options.add_argument("--headless")

    # ChromeDriver 자동 설치 및 업데이트
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    for style in style_image:
        href = style['href']
        # 마지막 '/' 이후의 문자열 추출
        number = href.split('/')[-1]
        snap_link = f"https://www.musinsa.com/snap/goods?goodsNo={number}&goodsPlatform=MUSINSA"
        driver.get(snap_link)
        print("페이지로 이동:", snap_link)
        
        # WebDriverWait을 사용해 페이지가 로드될 때까지 대기
        try:
            WebDriverWait(driver, 1).until(EC.presence_of_element_located((By.CLASS_NAME, 'object-cover')))
        except TimeoutException:
            print("페이지 로드 시간이 초과되었습니다.")
            continue

        # 페이지 소스를 가져와서 BeautifulSoup으로 파싱
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # <img> 태그 중 class 속성 값이 "object-cover"인 태그들을 모두 찾음
        img_tags = soup.find_all('img', class_='object-cover')
        
        # 모든 img 태그에서 src 속성 추출
        img_src_list = []
        for img_tag in img_tags:
            if 'src' in img_tag.attrs:
                img_src = img_tag['src']
                if not img_src.startswith('https:'):
                    img_src = 'https:' + img_src
                img_src_list.append(img_src)

        # 이미지의 src에 따라 분류하고 텍스트가 없는 이미지만 추가
        for img_src in img_src_list:
            print(f"스타일 이미지 src 확인: {img_src}")
            if '/codimap/list/' in img_src and not detect_text_in_image(img_src):
                codimap_list.append(img_src)
                print("코디맵 저장완료")
            elif '/style/list/' in img_src and not detect_text_in_image(img_src):
                style_list.append(img_src)
                print("코디샵 저장완료")
            elif '/_shopstaff/' in img_src and not detect_text_in_image(img_src):
                shopstaff_list.append(img_src)
                print("스태프 저장완료")

        # 리스트 개수가 2개 이상인 경우 해당 리스트 반환
        if len(codimap_list) >= 2:
            print("코디맵 리스트 개수가 2 이상, 실행 종료")
            driver.quit()
            return codimap_list
        if len(style_list) >= 2:
            print("코디샵 리스트 개수가 2 이상, 실행 종료")
            driver.quit()
            return style_list
        if len(shopstaff_list) >= 2:
            print("스태프 리스트 개수가 2 이상, 실행 종료")
            driver.quit()
            return shopstaff_list

    # 2개 이상의 항목을 가진 리스트가 없는 경우, 모든 리스트를 병합하여 반환
    combined_list = codimap_list + style_list + shopstaff_list
    print("2개 이상의 항목을 가진 리스트가 없음, 병합된 리스트 반환")
    driver.quit()
    return combined_list