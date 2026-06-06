import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

options = uc.ChromeOptions()
options.add_argument("--window-size=1400,900")
driver = uc.Chrome(options=options, version_main=148)

try:
    driver.get("https://fin.land.naver.com")
    time.sleep(7)

    # 검색
    btn = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "button[class*='SearchCapsule']")))
    driver.execute_script("arguments[0].click();", btn)
    time.sleep(1)

    inp = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[class*='HeaderSearch_search-input'], input[class*='search-input']")))
    inp.send_keys("망포동")
    time.sleep(1.5)

    first = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, "[class*='SearchResultList_name']")))
    driver.execute_script("arguments[0].click();", first)
    time.sleep(4)

    # 첫 번째 단지 마커 클릭
    markers = driver.find_elements(By.CSS_SELECTOR, "button[class*='ComplexMarkerDefault_article']")
    print(f"마커 {len(markers)}개")
    if markers:
        driver.execute_script("arguments[0].click();", markers[0])
        time.sleep(2)

        # 매물 탭 클릭
        tabs = driver.find_elements(By.CSS_SELECTOR, "button[class*='LineTab-module_link']")
        for tab in tabs:
            if tab.text.strip() == "매물":
                driver.execute_script("arguments[0].click();", tab)
                time.sleep(1.5)
                break

        driver.save_screenshot("output/debug_panel.png")

        # 패널 내 버튼 전체 출력 (거래유형 필터 확인)
        btns = driver.find_elements(By.TAG_NAME, "button")
        print("\n=== 패널 내 버튼 (텍스트 있는 것) ===")
        for b in btns:
            t = b.text.strip()
            if t and len(t) < 20:
                cls = b.get_attribute("class") or ""
                aria = b.get_attribute("aria-pressed") or b.get_attribute("aria-selected") or ""
                print(f"  '{t}' class='{cls[:80]}' aria='{aria}'")

        # 카드 price 셀렉터 확인
        print("\n=== 카드 가격 요소 ===")
        price_els = driver.find_elements(By.CSS_SELECTOR, "[class*='ArticleCard_area-price']")
        for el in price_els[:5]:
            # 첫 번째 텍스트 노드만 가져오기
            text = driver.execute_script("return arguments[0].childNodes[0] ? arguments[0].childNodes[0].textContent : arguments[0].textContent;", el)
            print(f"  full='{el.text[:60]}' first_node='{text}'")

    time.sleep(3)
finally:
    driver.quit()
