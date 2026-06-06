"""단지 1개 클릭 -> 매물 탭 -> 카드 수집 -> 파싱 검증"""
import sys
import time

# Windows 콘솔 UTF-8 출력
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from selenium.webdriver.common.by import By

from config import SELECTORS
from crawler import _click_article_tab, _collect_cards, build_driver
from parser import parse_article

driver = build_driver()
try:
    from config import TARGET_URL
    driver.get(TARGET_URL)
    print("[test] 로딩 중... (10초)")
    time.sleep(10)

    markers = driver.find_elements(By.CSS_SELECTOR, SELECTORS["complex_marker"])
    print(f"[test] 마커 {len(markers)}개")

    driver.execute_script("arguments[0].click();", markers[0])
    print(f"[test] 마커 클릭: {markers[0].text!r}")
    time.sleep(3)

    # 매물 탭 클릭
    clicked = _click_article_tab(driver)
    print(f"[test] 매물 탭 클릭: {clicked}")
    time.sleep(2)

    # 카드 수집
    cards_raw = _collect_cards(driver)
    print(f"[test] 수집된 카드 수: {len(cards_raw)}")

    if cards_raw:
        print("\n=== 첫 번째 카드 raw ===")
        for k, v in cards_raw[0].items():
            if k != "raw_text":
                print(f"  {k}: {v!r}")

        print("\n=== 파싱 결과 ===")
        parsed = parse_article(cards_raw[0])
        if parsed:
            for k, v in parsed.items():
                print(f"  {k}: {v!r}")
        else:
            print("  파싱 실패")

        ok = sum(1 for c in cards_raw if parse_article(c))
        print(f"\n=== 전체 파싱: {ok}/{len(cards_raw)} 성공 ===")
    else:
        # 패널 내 현재 내용 확인
        detail = driver.find_elements(By.CSS_SELECTOR, "#complex_detail")
        if detail:
            print("[test] #complex_detail 텍스트:", detail[0].text[:300])

        tabs = driver.find_elements(By.CSS_SELECTOR, SELECTORS["panel_tab_button"])
        print(f"[test] 탭 {len(tabs)}개:")
        for t in tabs:
            print(f"  {t.text!r}")

finally:
    driver.quit()
    print("[test] 종료")
