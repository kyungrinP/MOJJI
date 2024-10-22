import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import requests
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from mojji_Model.connection import mojji_s3

# Chrome 옵션 설정
options = webdriver.ChromeOptions()
options.binary_location = "/usr/bin/google-chrome"
options.add_argument("--start-maximized")  # 최대화된 상태로 시작
options.add_argument("--disable-extensions")  # 확장 프로그램 비활성화
options.add_argument("--headless")  # 창을 띄우지 않고 백그라운드에서 실행

# ChromeDriver 자동 설치 및 업데이트
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

def click_buttons(buttons):
    for button in buttons:
        try:
            element = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, button))
            )
            element.click()
        except NoSuchElementException:
            print(f"요소를 찾을 수 없습니다: {button}")
            continue

# href 속성 리스트로 저장
def get_links():
    # 모든 a 태그를 대상으로 기다리고 추출
    elements = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.sc-nemxqz-2.gxBJhv > div > a'))
    )
    # 각 a 태그의 href 속성 추출
    element_list = [element.get_attribute('href') for element in elements]
    return element_list

def process_links(category):
    html_content = driver.page_source
    soup = BeautifulSoup(html_content, 'html.parser')
    codi_elements = soup.select('div.sc-nemxqz-2.gxBJhv img')
    codi_element_list = [element.get('src') for element in codi_elements]

    # src 속성의 값에서 스킴이 누락된 경우 https를 추가
    codi_element_list = []
    for element in codi_elements:
        src = element.get('src')
        if src.startswith('//'):
            src = 'https:' + src  # 스킴이 누락된 경우 https 추가
        codi_element_list.append(src)

    print("코디 이미지 링크 리스트:", codi_element_list)

    # S3에 저장
    bucket_name = 'mojji-bucket'  # 버킷 이름 설정
    save_image_to_s3(codi_element_list, category, bucket_name)

# 메인페이지 TODAY CURATION 크롤링 이미지 저장
def save_image_to_s3(image_urls, category, bucket_name):
    """
    이미지 URL 리스트를 S3에 저장하는 함수
    :param image_urls: 이미지 URL 리스트
    :param category: 카테고리 (이미지가 저장될 S3 폴더명)
    :param bucket_name: S3 버킷 이름
    """
    s3_manager = mojji_s3()

    # 저장 경로 설정
    s3_base_path = f"main/static/img/codishop/{category}/"

    for idx, image_url in enumerate(image_urls):
        try:
            # 이미지 다운로드
            response = requests.get(image_url)
            if response.status_code == 200:
                # 이미지 데이터를 바이너리로 읽음
                image_data = response.content

                # S3에 저장할 파일 경로 (Key)
                file_name = f"{s3_base_path}CODI_SHOP_{category}_{idx+1}.jpg"
                print(f"S3에 저장할 파일 경로: {file_name}")

                # S3에 파일 업로드
                s3_manager.s3.put_object(Bucket=bucket_name, Key=file_name, Body=image_data)
                print(f"이미지가 S3에 업로드되었습니다: {file_name}")

            else:
                print(f"이미지 다운로드 실패: {image_url}")

        except Exception as e:
            print(f"이미지를 S3에 저장하는 중 오류 발생: {e}")

# 무신사 코디 페이지로 이동
driver.get("https://www.musinsa.com/app/stylecontents/lists?sortType=RECENT&contentsTypes=CODI_SHOP")

# 페이지 필터 버튼 클릭
filter_buttons = [
    '/html/body/div[1]/div[4]/div[1]/div/div/button[1]',
    '/html/body/div[1]/div[4]/div[1]/div/div/button[2]',
    '/html/body/div[1]/div[4]/div[1]/div/div/button[3]'
]

# 첫 번째 필터 처리
click_buttons(filter_buttons[:2])
time.sleep(3)
process_links("MAN")

# 무신사 코디 페이지로 이동
driver.get("https://www.musinsa.com/app/stylecontents/lists?sortType=RECENT&contentsTypes=CODI_SHOP")
print("무신사 코디 페이지로 이동완료")

# 잠시 대기하여 페이지가 로드될 시간을 줌
time.sleep(5)

# 두 번째 필터 처리
click_buttons(filter_buttons[1:])
time.sleep(3)
process_links("WOMAN")

# 웹 드라이버 종료
driver.quit()