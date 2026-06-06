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

    # iframe 확인
    iframes = driver.find_elements(By.TAG_NAME, "iframe")
    print(f"[debug] iframe {len(iframes)}개:")
    for i, iframe in enumerate(iframes):
        src = iframe.get_attribute("src") or ""
        cls = iframe.get_attribute("class") or ""
        print(f"  [{i}] src='{src[:80]}' class='{cls[:60]}'")

    # iframe 안으로 들어가서 input 찾기
    for i, iframe in enumerate(iframes):
        try:
            driver.switch_to.frame(iframe)
            inputs = driver.find_elements(By.TAG_NAME, "input")
            visible_inputs = [(inp.get_attribute("placeholder"), inp.get_attribute("class")) for inp in inputs if inp.is_displayed()]
            if visible_inputs:
                print(f"\n[debug] iframe[{i}] 내 visible input:")
                for ph, cls in visible_inputs:
                    print(f"  placeholder='{ph}' class='{cls[:80]}'")
            driver.switch_to.default_content()
        except Exception as e:
            driver.switch_to.default_content()
            print(f"[debug] iframe[{i}] 접근 오류: {e}")

    # 현재 URL 확인
    print(f"\n[debug] 현재 URL: {driver.current_url}")
    
    # 페이지 소스에서 '검색' 관련 input 찾기
    source_snippet = driver.execute_script("""
        let html = document.documentElement.outerHTML;
        let idx = html.indexOf('검색');
        return html.substring(Math.max(0, idx-200), idx+200);
    """)
    print(f"\n[debug] '검색' 주변 HTML:\n{source_snippet}")

    time.sleep(2)
finally:
    driver.quit()
