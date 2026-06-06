import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

options = uc.ChromeOptions()
options.add_argument("--window-size=1400,900")
driver = uc.Chrome(options=options, version_main=148)

def search_and_open_panel(driver, dong_name):
    btn = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "button[class*='SearchCapsule']")))
    driver.execute_script("arguments[0].click();", btn)
    time.sleep(1)
    inp = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[class*='HeaderSearch_search-input'], input[class*='search-input']")))
    inp.send_keys(dong_name)
    time.sleep(1.5)
    first = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, "[class*='SearchResultList_name']")))
    driver.execute_script("arguments[0].click();", first)
    time.sleep(4)

try:
    driver.get("https://fin.land.naver.com")
    time.sleep(7)
    search_and_open_panel(driver, "망포동")

    # ComplexMarkerDefault 마커 클릭
    markers = driver.find_elements(By.CSS_SELECTOR, "button[class*='ComplexMarkerDefault_article']")
    print(f"마커 {len(markers)}개")
    if markers:
        driver.execute_script("arguments[0].click();", markers[2])  # 3번째 마커
        time.sleep(2.5)

        # 매물 탭 클릭
        tabs = driver.find_elements(By.CSS_SELECTOR, "button[class*='LineTab-module_link']")
        for tab in tabs:
            if "매물" in tab.text:
                driver.execute_script("arguments[0].click();", tab)
                print(f"매물 탭 클릭: '{tab.text}'")
                time.sleep(2)
                break

        driver.save_screenshot("output/debug_sort_before.png")

        # ArticleSorter label 확인
        labels = driver.find_elements(By.CSS_SELECTOR, "label[class*='ArticleSorter']")
        print(f"\n=== ArticleSorter label {len(labels)}개 ===")
        for lbl in labels:
            text = lbl.text.replace('\n', '')
            for_attr = lbl.get_attribute("for") or ""
            cls = lbl.get_attribute("class") or ""
            print(f"  text='{text}' for='{for_attr}' class='{cls[:60]}'")

        # 거래유형 버튼 확인
        print(f"\n=== 거래유형 버튼 (ButtonBox) ===")
        btns = driver.find_elements(By.CSS_SELECTOR, "button[class*='ButtonBox']")
        for b in btns:
            t = b.text.strip()
            if t:
                print(f"  '{t}' class='{b.get_attribute('class')[:80]}'")

        # 카드 확인
        cards = driver.find_elements(By.CSS_SELECTOR, "li[class*='ArticleCard_item']")
        print(f"\n=== ArticleCard {len(cards)}개 ===")
        for card in cards[:3]:
            price_els = card.find_elements(By.CSS_SELECTOR, "[class*='ArticleCard_area-price']")
            sum_els = card.find_elements(By.CSS_SELECTOR, "[class*='ArticleCard_item-summary']")
            price = price_els[0].text if price_els else "없음"
            floor = sum_els[2].text if len(sum_els) > 2 else "없음"
            print(f"  floor='{floor}' price='{price[:40]}'")

    time.sleep(3)
finally:
    driver.quit()
