import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

options = uc.ChromeOptions()
options.add_argument("--window-size=1400,900")
driver = uc.Chrome(options=options, version_main=148)

try:
    driver.get("https://fin.land.naver.com")
    time.sleep(7)

    # '검색' 텍스트 포함한 버튼 찾기
    btns = driver.find_elements(By.TAG_NAME, "button")
    search_btn = None
    for btn in btns:
        try:
            if "검색" in btn.text and btn.is_displayed():
                print(f"[debug] 검색 버튼 발견: text='{btn.text[:60]}' class='{btn.get_attribute('class')[:80]}'")
                search_btn = btn
                break
        except Exception:
            pass

    if search_btn:
        driver.execute_script("arguments[0].click();", search_btn)
        print("[debug] 검색 버튼 클릭 완료")
        time.sleep(2)
        driver.save_screenshot("output/debug_after_click_btn.png")

        # 클릭 후 나타나는 input 찾기
        inputs = driver.find_elements(By.TAG_NAME, "input")
        print(f"[debug] 클릭 후 input {len(inputs)}개:")
        for i, inp in enumerate(inputs):
            ph = inp.get_attribute("placeholder") or ""
            cls = inp.get_attribute("class") or ""
            if inp.is_displayed() or ph:
                print(f"  [{i}] placeholder='{ph}' class='{cls[:80]}' visible={inp.is_displayed()}")

        # 나타난 input에 타이핑
        for inp in inputs:
            try:
                if inp.is_displayed():
                    inp.send_keys("망포동")
                    print(f"[debug] 타이핑 성공!")
                    time.sleep(2)
                    driver.save_screenshot("output/debug_typed.png")
                    break
            except Exception as e:
                print(f"[debug] 타이핑 실패: {e}")
    else:
        print("[debug] 검색 버튼 못 찾음")
        # span이나 div로 된 검색창 확인
        all_els = driver.find_elements(By.XPATH, "//*[contains(text(), '검색')]")
        for el in all_els[:10]:
            if el.is_displayed():
                print(f"  tag={el.tag_name} text='{el.text[:60]}' class='{el.get_attribute('class')[:60]}'")

    time.sleep(3)
finally:
    driver.quit()
