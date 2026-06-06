import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By

options = uc.ChromeOptions()
options.add_argument("--window-size=1400,900")
driver = uc.Chrome(options=options, version_main=148)

try:
    driver.get("https://fin.land.naver.com")
    time.sleep(6)

    # [class*='search'] input 의 부모 구조 파악
    el = driver.find_element(By.CSS_SELECTOR, "[class*='search'] input")
    print(f"input class: '{el.get_attribute('class')}'")
    print(f"input type: '{el.get_attribute('type')}'")
    print(f"input name: '{el.get_attribute('name')}'")

    # 부모들 탐색
    js = """
    let el = arguments[0];
    let info = [];
    for (let i = 0; i < 5; i++) {
        el = el.parentElement;
        if (!el) break;
        info.push(el.tagName + ' class=' + (el.className || '').substring(0,80));
    }
    return info;
    """
    parents = driver.execute_script(js, el)
    for p in parents:
        print(f"  parent: {p}")

    # 클릭해서 타이핑 테스트
    print("\n[debug] 검색창 클릭 & 타이핑 테스트")
    driver.execute_script("arguments[0].click();", el)
    time.sleep(0.5)
    from selenium.webdriver.common.keys import Keys
    el.send_keys("망포동")
    time.sleep(2)

    # 드롭다운 결과 확인
    all_li = driver.find_elements(By.CSS_SELECTOR, "li")
    visible_li = [li for li in all_li if li.is_displayed() and li.text.strip()]
    print(f"[debug] 표시된 li {len(visible_li)}개:")
    for li in visible_li[:15]:
        cls = li.get_attribute("class") or ""
        print(f"  '{li.text[:60]}' class='{cls[:60]}'")

    time.sleep(3)
finally:
    driver.quit()
