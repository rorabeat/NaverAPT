"""엔드-투-엔드 테스트: 마커 3개 수집 후 CSV/DB 저장"""
import sys, io
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import time
from selenium.webdriver.common.by import By
from config import SELECTORS
from crawler import _click_article_tab, _collect_cards, build_driver
from parser import parse_article
from storage import DedupBuffer

MAX_MARKERS = 3

driver = build_driver()
buffer = DedupBuffer()
total_raw = total_parsed = total_dup = 0

try:
    from config import TARGET_URL
    driver.get(TARGET_URL)
    print("[e2e] 로딩 중... (10초)")
    time.sleep(10)

    markers = driver.find_elements(By.CSS_SELECTOR, SELECTORS["complex_marker"])
    print(f"[e2e] 마커 {len(markers)}개 발견, {MAX_MARKERS}개만 처리")

    for idx in range(min(MAX_MARKERS, len(markers))):
        try:
            markers = driver.find_elements(By.CSS_SELECTOR, SELECTORS["complex_marker"])
            marker = markers[idx]
            driver.execute_script("arguments[0].click();", marker)
            time.sleep(2)

            cards = _collect_cards(driver)
            print(f"[e2e] 마커 {idx+1}: {len(cards)}건 수집")
            total_raw += len(cards)

            for raw in cards:
                record = parse_article(raw)
                if record is None:
                    continue
                total_parsed += 1
                if not buffer.add(record):
                    total_dup += 1

        except Exception as e:
            print(f"[e2e] 마커 {idx+1} 오류: {e}")

finally:
    try:
        driver.quit()
    except Exception:
        pass

print(f"\n[e2e] 결과: 수집 {total_raw} / 파싱 {total_parsed} / 중복 {total_dup} / 저장 {len(buffer.records)}")
buffer.flush(csv_path="output/test_prices.csv", db_path="output/test_prices.db")

# CSV 확인
import pandas as pd
df = pd.read_csv("output/test_prices.csv")
print(f"\n[e2e] CSV 저장 확인: {len(df)}행")
print(df.head(3).to_string())
