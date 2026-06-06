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

def get_cards(driver, n=5):
    cards = driver.find_elements(By.CSS_SELECTOR, "li[class*='ArticleCard_item']")
    result = []
    for card in cards[:n]:
        price_els = card.find_elements(By.CSS_SELECTOR, "[class*='ArticleCard_area-price']")
        sum_els = card.find_elements(By.CSS_SELECTOR, "[class*='ArticleCard_item-summary']")
        price = price_els[0].text.splitlines()[0] if price_els else "-"
        floor = sum_els[2].text if len(sum_els) > 2 else "-"
        result.append(f"floor={floor} price={price}")
    return result

try:
    driver.get("https://fin.land.naver.com")
    time.sleep(7)
    search_and_open_panel(driver, "망포동")

    # 힐스테이트영통 마커 찾기 (매물 많은 단지)
    markers = driver.find_elements(By.CSS_SELECTOR, "button[class*='ComplexMarkerDefault_article']")
    clicked = None
    for m in markers:
        if "13.5억" in m.text or "14억" in m.text:
            clicked = m
            break
    if not clicked:
        clicked = markers[5]  # 그냥 6번째
    driver.execute_script("arguments[0].click();", clicked)
    time.sleep(2.5)

    # 매물 탭 클릭
    tabs = driver.find_elements(By.CSS_SELECTOR, "button[class*='LineTab-module_link']")
    for tab in tabs:
        if "매물" in tab.text:
            driver.execute_script("arguments[0].click();", tab)
            time.sleep(2)
            break

    # 거래유형 버튼 전체 class 확인
    print("=== 거래유형 ButtonBox 전체 class ===")
    btns = driver.find_elements(By.CSS_SELECTOR, "button[class*='ButtonBox']")
    for b in btns:
        t = b.text.strip().replace('\n', '')
        if any(t.startswith(x) for x in ['매매', '전세', '월세', '단기']):
            print(f"  text='{t}'\n  class='{b.get_attribute('class')}'")

    # 정렬 label detail span 확인
    print("\n=== 가격순 label 상세 ===")
    labels = driver.find_elements(By.CSS_SELECTOR, "label[class*='ArticleSorter']")
    for lbl in labels:
        detail = lbl.find_elements(By.CSS_SELECTOR, "[class*='ArticleSorter_detail']")
        d_text = detail[0].text if detail else "(없음)"
        full_text = lbl.text.replace('\n','')
        print(f"  for='{lbl.get_attribute('for')}' detail='{d_text}' full='{full_text}'")

    # 현재 카드 (기본 상태)
    print(f"\n=== 기본 상태 카드 (상위 3개) ===")
    for c in get_cards(driver, 3):
        print(f"  {c}")

    # 가격순 label 클릭
    price_label = driver.find_element(By.CSS_SELECTOR, "label[for='filterOrder2']")
    driver.execute_script("arguments[0].click();", price_label)
    time.sleep(1.5)

    # 클릭 후 detail 확인
    labels = driver.find_elements(By.CSS_SELECTOR, "label[class*='ArticleSorter']")
    for lbl in labels:
        if lbl.get_attribute("for") == "filterOrder2":
            detail = lbl.find_elements(By.CSS_SELECTOR, "[class*='ArticleSorter_detail']")
            d_text = detail[0].text if detail else "(없음)"
            print(f"\n[가격순 1차 클릭 후] detail='{d_text}'")

    print("=== 1차 클릭 후 카드 ===")
    for c in get_cards(driver, 3):
        print(f"  {c}")

    # 한번 더 클릭
    price_label = driver.find_element(By.CSS_SELECTOR, "label[for='filterOrder2']")
    driver.execute_script("arguments[0].click();", price_label)
    time.sleep(1.5)

    labels = driver.find_elements(By.CSS_SELECTOR, "label[class*='ArticleSorter']")
    for lbl in labels:
        if lbl.get_attribute("for") == "filterOrder2":
            detail = lbl.find_elements(By.CSS_SELECTOR, "[class*='ArticleSorter_detail']")
            d_text = detail[0].text if detail else "(없음)"
            print(f"\n[가격순 2차 클릭 후] detail='{d_text}'")

    print("=== 2차 클릭 후 카드 ===")
    for c in get_cards(driver, 3):
        print(f"  {c}")

    # 전세 버튼 클릭 테스트
    print("\n=== 전세 버튼 클릭 테스트 ===")
    btns = driver.find_elements(By.CSS_SELECTOR, "button[class*='ButtonBox']")
    for b in btns:
        if b.text.strip().startswith("전세"):
            driver.execute_script("arguments[0].click();", b)
            print(f"  '{b.text.strip()}' 클릭")
            time.sleep(1.5)
            break
    print("클릭 후 카드:")
    for c in get_cards(driver, 3):
        print(f"  {c}")

    time.sleep(2)
finally:
    driver.quit()
