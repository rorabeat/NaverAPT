import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

options = uc.ChromeOptions()
options.add_argument("--window-size=1400,900")
driver = uc.Chrome(options=options, version_main=148)
driver.set_window_size(1400, 900)

try:
    driver.get("https://fin.land.naver.com")
    print("[debug] 페이지 로드 완료")
    time.sleep(6)

    # 모든 input 요소 확인
    inputs = driver.find_elements(By.TAG_NAME, "input")
    print(f"[debug] input 요소 {len(inputs)}개:")
    for i, inp in enumerate(inputs):
        ph = inp.get_attribute("placeholder") or ""
        cls = inp.get_attribute("class") or ""
        print(f"  [{i}] placeholder='{ph}' class='{cls[:60]}'")

    # 검색 관련 요소 탐색
    print("\n[debug] 검색창 후보 요소:")
    for sel in ["[class*='search'] input", "[class*='Search'] input", "input[type='search']", "input[type='text']"]:
        els = driver.find_elements(By.CSS_SELECTOR, sel)
        if els:
            print(f"  {sel}: {len(els)}개")
            for el in els[:2]:
                print(f"    placeholder='{el.get_attribute('placeholder')}' class='{el.get_attribute('class')[:60]}'")

    time.sleep(3)
finally:
    driver.quit()
