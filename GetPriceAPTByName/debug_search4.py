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

    # JS로 placeholder로 검색 input 찾기
    el = driver.execute_script("""
        let inputs = Array.from(document.querySelectorAll('input'));
        return inputs.find(el => el.placeholder && el.placeholder.includes('검색'));
    """)
    if el:
        print(f"[debug] JS로 찾음: placeholder='{el.get_attribute('placeholder')}' class='{el.get_attribute('class')}'")
        rect = driver.execute_script("return arguments[0].getBoundingClientRect();", el)
        print(f"[debug] rect: {rect}")
        print(f"[debug] offsetParent: {driver.execute_script('return arguments[0].offsetParent !== null', el)}")
        
        # JS로 클릭 및 값 설정
        driver.execute_script("arguments[0].focus(); arguments[0].click();", el)
        time.sleep(0.5)
        
        # ActionChains로 클릭
        ActionChains(driver).move_to_element(el).click().send_keys("망포동").perform()
        time.sleep(2)
        
        driver.save_screenshot("output/debug_after_type.png")
        print("[debug] 타이핑 후 스크린샷 저장")
        
        # 드롭다운 결과 확인
        time.sleep(1)
        all_els = driver.find_elements(By.XPATH, "//*[contains(text(), '망포동')]")
        print(f"[debug] '망포동' 텍스트 포함 요소 {len(all_els)}개:")
        for el2 in all_els[:10]:
            print(f"  tag={el2.tag_name} text='{el2.text[:60]}' class='{el2.get_attribute('class')[:60]}'")
    else:
        print("[debug] JS로 검색 input 못 찾음")
        driver.save_screenshot("output/debug_no_input.png")

    time.sleep(3)
finally:
    driver.quit()
