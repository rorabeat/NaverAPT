import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By

options = uc.ChromeOptions()
options.add_argument("--window-size=1400,900")
driver = uc.Chrome(options=options, version_main=148)

try:
    driver.get("https://fin.land.naver.com")
    time.sleep(7)

    # 스크린샷 저장
    driver.save_screenshot("output/debug_screenshot.png")
    print("[debug] 스크린샷 저장 완료")

    # 모든 visible input 찾기
    inputs = driver.find_elements(By.TAG_NAME, "input")
    print(f"\n[debug] 전체 input {len(inputs)}개 중 visible:")
    for i, inp in enumerate(inputs):
        if inp.is_displayed():
            ph = inp.get_attribute("placeholder") or ""
            cls = inp.get_attribute("class") or ""
            typ = inp.get_attribute("type") or ""
            print(f"  [{i}] type='{typ}' placeholder='{ph}' class='{cls[:80]}'")

    # JS로 페이지 내 검색 관련 텍스트 찾기
    result = driver.execute_script("""
        let inputs = Array.from(document.querySelectorAll('input'));
        return inputs.map(el => ({
            tag: el.tagName,
            type: el.type,
            placeholder: el.placeholder,
            cls: el.className.substring(0,100),
            visible: el.offsetParent !== null,
            rect: JSON.stringify(el.getBoundingClientRect())
        }));
    """)
    print(f"\n[debug] JS로 찾은 input {len(result)}개:")
    for r in result:
        if r['visible']:
            print(f"  visible={r['visible']} type={r['type']} ph='{r['placeholder']}' cls='{r['cls'][:60]}'")
            print(f"    rect={r['rect']}")

    time.sleep(2)
finally:
    driver.quit()
