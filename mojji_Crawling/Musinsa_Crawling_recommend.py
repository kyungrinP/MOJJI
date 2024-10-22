import json
from selenium import webdriver
import time
from bs4 import BeautifulSoup
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

def scroll_down(driver, times):
    for _ in range(times):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)  # 스크롤 후 로드 시간을 줌

def get_links(driver):
    html_content = driver.page_source
    soup = BeautifulSoup(html_content, 'html.parser')
    codi_elements = soup.select('div.sc-hzhKNl.lmHEaa > div')
    links = []
    for element in codi_elements:
        a_tag = element.find('a', class_='sc-eldOKa eYuOFs gtm-view-item-list gtm-select-item')
        img_tag = element.find('img', class_='max-w-full w-full absolute m-auto inset-0 h-auto z-0 visible object-cover')
        if a_tag and img_tag:
            href = a_tag.get('href')
            src = img_tag.get('src')
            links.append({'src': src, 'href': href})
    return links

def click_button_by_type(item_type, color):
    # Chrome 옵션 설정
    options = webdriver.ChromeOptions()
    options.binary_location = "/usr/bin/google-chrome"
    options.add_argument("--start-maximized")
    options.add_argument("--disable-extensions")
    options.add_argument("--headless")

    # ChromeDriver 자동 설치 및 업데이트
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    try:
        driver.get("https://www.musinsa.com/menu?storeCode=musinsa")
        time.sleep(2)

        # Load item types from JSON with UTF-8 encoding
        with open('mojji-renewal/mojji_Crawling/item_types.json', 'r', encoding='utf-8') as f:
            item_types = json.load(f)
        
        with open('mojji-renewal/mojji_Crawling/item_color.json', 'r', encoding='utf-8') as f:
            item_color = json.load(f)

        # Get alt value based on item_type
        alt_value = item_types[item_type]
        color_value = item_color[color]
        
        driver.get(alt_value)

        current_url = driver.current_url
        url_with_color = f"{current_url}&color={color_value}"
        driver.get(url_with_color)
        time.sleep(2)

        # 초기 링크 리스트 가져오기
        element_list = get_links(driver)

        # 스크롤 반복
        for _ in range(20):
            scroll_down(driver, 1)
            new_elements = get_links(driver)
            element_list.extend(new_elements)
            if len(element_list) >= 100:
                break

        # 중복 제거
        unique_elements = [dict(t) for t in {tuple(d.items()) for d in element_list}]
        
        print("링크 리스트:", unique_elements)
        print("리스트 개수:", len(unique_elements))

        return unique_elements

    finally:
        driver.quit()