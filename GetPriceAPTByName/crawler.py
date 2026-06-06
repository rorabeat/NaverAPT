import time
from typing import Generator

import undetected_chromedriver as uc
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from config import HEADLESS, SELECTORS, TARGET_URL, UC_VERSION, WINDOW_SIZE, random_delay
from parser import STANDARD_PYEONG, parse_area_option

BASE_URL = "https://fin.land.naver.com"


def build_driver() -> uc.Chrome:
    options = uc.ChromeOptions()
    if HEADLESS:
        options.add_argument("--headless=new")
    options.add_argument(f"--window-size={WINDOW_SIZE[0]},{WINDOW_SIZE[1]}")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = uc.Chrome(options=options, version_main=UC_VERSION)
    driver.set_window_size(*WINDOW_SIZE)
    return driver


def _wait_for(driver: uc.Chrome, css: str, timeout: int = 15):
    return WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, css))
    )


def _safe_text(el, css: str) -> str:
    try:
        return el.find_element(By.CSS_SELECTOR, css).text.strip()
    except (NoSuchElementException, StaleElementReferenceException):
        return ""


def _extract_card(card) -> dict:
    """매물 카드 WebElement에서 데이터를 직접 추출한다."""
    name_text = _safe_text(card, SELECTORS["card_name"])      # "힐스테이트영통 105동"
    price_text = _safe_text(card, SELECTORS["card_price"])    # "매매 13억 5,000 ~ 14억"

    summary_els = card.find_elements(By.CSS_SELECTOR, SELECTORS["card_summary_items"])
    # [0]=건물유형  [1]=면적  [2]=층  [3]=향
    summary = [el.text.strip() for el in summary_els]

    return {
        "name_text": name_text,     # 단지명+동
        "price_text": price_text,   # 거래유형+가격
        "building_type": summary[0] if len(summary) > 0 else "",
        "area_text": summary[1] if len(summary) > 1 else "",   # "111A㎡ (전용84A)"
        "floor_text": summary[2] if len(summary) > 2 else "",  # "21/27층"
        "direction": summary[3] if len(summary) > 3 else "",
        "raw_text": card.text,
    }


def _click_article_tab(driver: uc.Chrome):
    """패널에서 '매물' 탭을 찾아 클릭한다."""
    try:
        tabs = driver.find_elements(By.CSS_SELECTOR, SELECTORS["panel_tab_button"])
        for tab in tabs:
            if tab.text.strip() == "매물":
                driver.execute_script("arguments[0].click();", tab)
                time.sleep(1.5)
                return True
    except Exception:
        pass
    return False


def _collect_cards(driver: uc.Chrome) -> list[dict]:
    """단지 패널이 열린 상태에서 모든 매물 카드를 수집한다."""
    records: list[dict] = []

    # 매물 탭으로 이동
    _click_article_tab(driver)

    # 매물 목록 UL 대기
    try:
        _wait_for(driver, SELECTORS["article_list_ul"], timeout=10)
    except TimeoutException:
        return records

    time.sleep(1)

    # 더보기 버튼이 있으면 클릭해서 전체 펼치기
    try:
        expand_btns = driver.find_elements(By.CSS_SELECTOR, SELECTORS["expand_button"])
        for btn in expand_btns:
            try:
                driver.execute_script("arguments[0].click();", btn)
                time.sleep(0.5)
            except Exception:
                pass
    except Exception:
        pass

    # 패널 스크롤로 모든 카드 로드
    panel = driver.find_elements(By.CSS_SELECTOR, SELECTORS["panel_scroll"])
    scroll_target = panel[0] if panel else None

    prev_count = 0
    for _ in range(20):
        cards = driver.find_elements(By.CSS_SELECTOR, SELECTORS["article_items"])
        if len(cards) == prev_count:
            break
        prev_count = len(cards)
        if scroll_target:
            driver.execute_script(
                "arguments[0].scrollTop += 1000;", scroll_target
            )
        else:
            driver.execute_script("window.scrollBy(0, 1000);")
        time.sleep(0.8)

    # 최종 카드 목록에서 데이터 추출
    cards = driver.find_elements(By.CSS_SELECTOR, SELECTORS["article_items"])
    for card in cards:
        try:
            data = _extract_card(card)
            if data["name_text"] or data["price_text"]:
                records.append(data)
        except StaleElementReferenceException:
            continue

    return records


def _is_floor_eligible(floor_text: str, min_floor: int = 4) -> bool:
    """층 텍스트로 min_floor 이상 여부 판단. "21/27층"→True, "중/25층"→True, "저/25층"→False"""
    t = floor_text.strip()
    prefix = t.split("/")[0] if "/" in t else t.replace("층", "")
    if prefix in ("고", "중"):
        return True
    if prefix == "저":
        return False
    try:
        return int(prefix) >= min_floor
    except ValueError:
        return False


def _click_sort(driver: uc.Chrome, direction: str):
    """가격순 정렬 label을 클릭하여 원하는 방향으로 설정한다.
    direction: '낮은' (매매 최저가용) 또는 '높은' (전세 최고가용)
    - 가격순 label 클릭 시 1차=낮은가격순, 2차=높은가격순으로 토글됨
    """
    try:
        price_label = driver.find_element(By.CSS_SELECTOR, "label[for='filterOrder2']")
    except NoSuchElementException:
        return

    for _ in range(3):
        driver.execute_script("arguments[0].click();", price_label)
        time.sleep(1.0)
        try:
            detail_els = price_label.find_elements(By.CSS_SELECTOR, "[class*='ArticleSorter_detail']")
            current = detail_els[0].text.strip() if detail_els else ""
            if current == direction:
                break
        except StaleElementReferenceException:
            break


def _set_deal_type(driver: uc.Chrome, deal_type: str):
    """거래유형 필터 버튼을 클릭한다. 버튼 텍스트가 '매매30', '전세5' 형태여서 startsWith로 매칭."""
    btns = driver.find_elements(By.CSS_SELECTOR, "button[class*='ButtonBox']")
    for btn in btns:
        try:
            if btn.text.strip().startswith(deal_type):
                driver.execute_script("arguments[0].click();", btn)
                time.sleep(1.5)
                return
        except StaleElementReferenceException:
            continue


def _find_first_eligible_card(driver: uc.Chrome, complex_name: str, dong_name: str,
                               deal_type: str, min_floor: int = 4,
                               pyeong: int | None = None) -> dict | None:
    """정렬된 카드 목록에서 층수 조건을 만족하는 첫 번째 카드 1건만 반환한다."""
    try:
        cards = driver.find_elements(By.CSS_SELECTOR, SELECTORS["article_items"])
        for card in cards[:50]:
            try:
                summary_els = card.find_elements(By.CSS_SELECTOR, SELECTORS["card_summary_items"])
                floor_text = summary_els[2].text.strip() if len(summary_els) > 2 else ""
                if not floor_text or not _is_floor_eligible(floor_text, min_floor):
                    continue

                try:
                    price_raw = card.find_element(By.CSS_SELECTOR, SELECTORS["card_price"]).text.strip()
                    price = price_raw.splitlines()[0].strip()
                except (NoSuchElementException, StaleElementReferenceException):
                    price = ""

                try:
                    unit_text = card.find_element(By.CSS_SELECTOR, SELECTORS["card_name"]).text.strip()
                except (NoSuchElementException, StaleElementReferenceException):
                    unit_text = complex_name

                area_text = summary_els[1].text.strip() if len(summary_els) > 1 else ""
                record = {
                    "단지명":   complex_name,
                    "동":      dong_name,
                    "동호":     unit_text,
                    "거래유형":  deal_type,
                    "가격":     price,
                    "평수":     f"{pyeong}평" if pyeong else "",
                    "면적":     area_text,
                    "층":      floor_text,
                    "향":      summary_els[3].text.strip() if len(summary_els) > 3 else "",
                    "건물유형":  summary_els[0].text.strip() if len(summary_els) > 0 else "",
                    "기준층":   f"{min_floor}층 이상",
                }
                return record
            except (StaleElementReferenceException, IndexError):
                continue
    except Exception:
        pass
    return None


def _is_area_filter_open(driver: uc.Chrome) -> bool:
    """면적 필터 드롭다운이 열려 있는지 확인한다."""
    try:
        layers = driver.find_elements(By.CSS_SELECTOR, SELECTORS["area_filter_layer"])
        return any(layer.is_displayed() for layer in layers)
    except Exception:
        return False


def _open_area_filter(driver: uc.Chrome) -> bool:
    """전체면적 칩을 클릭하여 면적 필터 드롭다운을 연다."""
    if _is_area_filter_open(driver):
        return True
    try:
        chip = driver.find_element(By.CSS_SELECTOR, SELECTORS["area_filter_chip"])
        driver.execute_script("arguments[0].click();", chip)
        time.sleep(0.8)
        _wait_for(driver, SELECTORS["area_filter_layer"], timeout=5)
        return True
    except (NoSuchElementException, TimeoutException):
        return False


def _close_area_filter_outside(driver: uc.Chrome):
    """드롭다운 외부를 클릭해 메뉴를 닫고 필터를 적용한다."""
    if not _is_area_filter_open(driver):
        return

    outside_targets = [
        "[class*='ComplexSummary_name']",
        "[class*='ComplexArticleTab_article']",
        "[class*='LineTab-module_list']",
        "#complex_detail",
    ]
    for sel in outside_targets:
        try:
            el = driver.find_element(By.CSS_SELECTOR, sel)
            driver.execute_script("arguments[0].click();", el)
            time.sleep(0.5)
            if not _is_area_filter_open(driver):
                break
        except NoSuchElementException:
            continue

    if _is_area_filter_open(driver):
        try:
            driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
            time.sleep(0.5)
        except Exception:
            pass

    if _is_area_filter_open(driver):
        try:
            chip = driver.find_element(By.CSS_SELECTOR, SELECTORS["area_filter_chip"])
            driver.execute_script("arguments[0].click();", chip)
            time.sleep(0.5)
        except NoSuchElementException:
            pass


def _wait_for_filter_reload(driver: uc.Chrome, timeout: int = 12):
    """면적 필터 적용 후 매물 목록 갱신을 기다린다."""
    time.sleep(0.8)
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, SELECTORS["article_list_ul"]))
        )
    except TimeoutException:
        pass

    # 카드 DOM 교체 대기 (stale 방지)
    prev_sig = ""
    for _ in range(8):
        cards = driver.find_elements(By.CSS_SELECTOR, SELECTORS["article_items"])
        sig = "|".join(c.text[:40] for c in cards[:3])
        if sig and sig == prev_sig:
            break
        prev_sig = sig
        time.sleep(0.6)


def _area_label_key(text: str) -> str:
    """label 텍스트에서 면적 식별 키를 추출한다."""
    supply, _ = parse_area_option(text)
    return str(supply) if supply is not None else text.strip()


def _read_area_filter_options(driver: uc.Chrome) -> list[dict]:
    """열린 면적 필터 드롭다운에서 항목을 파싱한다."""
    options = []
    labels = driver.find_elements(By.CSS_SELECTOR, SELECTORS["area_filter_items"])
    for label in labels:
        text = label.text.strip()
        if not text or "전체면적" in text:
            continue
        supply, pyeong = parse_area_option(text)
        if supply is None:
            continue
        options.append({
            "key": _area_label_key(text),
            "text": text,
            "supply_m2": supply,
            "pyeong": pyeong,
        })
    return options


def _get_area_filter_options(driver: uc.Chrome) -> list[dict]:
    """면적 필터 드롭다운을 열어 옵션 목록을 읽고 닫는다."""
    if not _open_area_filter(driver):
        return []
    options = _read_area_filter_options(driver)
    _close_area_filter_outside(driver)
    _wait_for_filter_reload(driver)
    return options


def _select_single_area(driver: uc.Chrome, target_key: str) -> bool:
    """면적 1개만 선택 → 외부 클릭으로 적용 → 목록 갱신 대기."""
    if not _open_area_filter(driver):
        return False

    labels = driver.find_elements(By.CSS_SELECTOR, SELECTORS["area_filter_items"])
    clicked = False
    for label in labels:
        text = label.text.strip()
        if "전체면적" in text:
            continue
        if _area_label_key(text) == target_key:
            driver.execute_script("arguments[0].click();", label)
            clicked = True
            time.sleep(0.4)
            break

    if not clicked:
        _close_area_filter_outside(driver)
        return False

    _close_area_filter_outside(driver)
    _wait_for_filter_reload(driver)
    return True


def _reset_area_filter_all(driver: uc.Chrome):
    """전체면적(모든 면적)으로 필터를 초기화한다."""
    if not _open_area_filter(driver):
        return
    labels = driver.find_elements(By.CSS_SELECTOR, SELECTORS["area_filter_items"])
    for label in labels:
        if "전체면적" in label.text:
            driver.execute_script("arguments[0].click();", label)
            time.sleep(0.4)
            break
    _close_area_filter_outside(driver)
    _wait_for_filter_reload(driver)


def _collect_by_pyeong(driver: uc.Chrome, complex_name: str, dong_name: str,
                        min_floor: int) -> tuple[list[dict], list[dict]]:
    """단지별 면적(25/29/33평 해당)마다 1개씩 선택 → 매매최저가·전세최고가 1건씩 수집."""
    mae_records: list[dict] = []
    jeon_records: list[dict] = []

    area_options = _get_area_filter_options(driver)
    target_options = [opt for opt in area_options if opt["pyeong"] in STANDARD_PYEONG]

    if not target_options:
        print("  [면적필터] 옵션 없음 — 전체 면적 기준 1건씩 수집")
        _set_deal_type(driver, "매매")
        _click_sort(driver, "낮은")
        card = _find_first_eligible_card(driver, complex_name, dong_name, "매매", min_floor)
        if card:
            mae_records.append(card)
        _set_deal_type(driver, "전세")
        _click_sort(driver, "높은")
        card = _find_first_eligible_card(driver, complex_name, dong_name, "전세", min_floor)
        if card:
            jeon_records.append(card)
        return mae_records, jeon_records

    for opt in target_options:
        pyeong = opt["pyeong"]
        label = f"{opt['supply_m2']}㎡ ({pyeong}평)"
        print(f"  [면적선택] {label}")

        if not _select_single_area(driver, opt["key"]):
            print(f"    → 면적 선택 실패, 건너뜀")
            continue

        _set_deal_type(driver, "매매")
        _click_sort(driver, "낮은")
        mae_card = _find_first_eligible_card(
            driver, complex_name, dong_name, "매매", min_floor, pyeong=pyeong
        )
        if mae_card:
            mae_card["공급면적"] = f"{opt['supply_m2']}㎡"
            mae_records.append(mae_card)
            print(f"    매매: {mae_card['가격']}")
        else:
            print("    매매: (해당 없음)")

        _set_deal_type(driver, "전세")
        _click_sort(driver, "높은")
        jeon_card = _find_first_eligible_card(
            driver, complex_name, dong_name, "전세", min_floor, pyeong=pyeong
        )
        if jeon_card:
            jeon_card["공급면적"] = f"{opt['supply_m2']}㎡"
            jeon_records.append(jeon_card)
            print(f"    전세: {jeon_card['가격']}")
        else:
            print("    전세: (해당 없음)")

    _reset_area_filter_all(driver)
    return mae_records, jeon_records


def _get_complex_name(driver: uc.Chrome) -> str:
    """현재 열린 단지 패널의 단지명을 반환한다."""
    try:
        el = driver.find_element(By.CSS_SELECTOR, "[class*='ComplexSummary_name']")
        return el.text.strip()
    except Exception:
        pass
    try:
        el = driver.find_element(By.CSS_SELECTOR, "[class*='PanelTitle_title']")
        return el.text.strip()
    except Exception:
        pass
    return ""


def search_dong(driver: uc.Chrome, dong_name: str) -> bool:
    """검색창에 동 이름을 입력하고 해당 동으로 지도를 이동한다."""
    try:
        # 1단계: SearchCapsule 버튼 클릭 → 검색 입력창 활성화
        search_capsule = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "button[class*='SearchCapsule']"))
        )
        driver.execute_script("arguments[0].click();", search_capsule)
        time.sleep(2.0)

        # 2단계: 활성화된 input에 send_keys로 타이핑 (React 검색 트리거용)
        search_input = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "input[class*='HeaderSearch_search-input'], input[class*='search-input']")
            )
        )
        search_input.click()
        time.sleep(0.3)
        search_input.send_keys(dong_name)
        time.sleep(2.5)

        # 3단계: 드롭다운 첫 번째 결과 클릭
        first_result = WebDriverWait(driver, 8).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "[class*='SearchResultList_name']"))
        )
        driver.execute_script("arguments[0].click();", first_result)
        time.sleep(4)
        return True

    except Exception as e:
        print(f"[search_dong] 오류: {type(e).__name__}")

    return False


def crawl_dong(dong_name: str, min_floor: int = 4) -> dict[str, list[dict]]:
    """동 이름으로 검색하여 각 단지의 25/29/33평별 매매최저가·전세최고가 1건씩 수집.
    반환: {"매매": [...], "전세": [...]}
    """
    driver = build_driver()
    mae_records: list[dict] = []
    jeon_records: list[dict] = []

    try:
        driver.get(BASE_URL)
        print(f"[crawl_dong] 로딩 중...")
        time.sleep(5)

        print(f"[crawl_dong] '{dong_name}' 검색 중...")
        ok = search_dong(driver, dong_name)
        if not ok:
            print(f"[crawl_dong] '{dong_name}' 검색 실패")
            return {"매매": mae_records, "전세": jeon_records}

        time.sleep(3)

        markers = driver.find_elements(By.CSS_SELECTOR, SELECTORS["complex_marker"])
        print(f"[crawl_dong] 단지 마커 {len(markers)}개 발견")

        processed = set()
        for idx in range(len(markers)):
            try:
                markers = driver.find_elements(By.CSS_SELECTOR, SELECTORS["complex_marker"])
                if idx >= len(markers):
                    break
                marker = markers[idx]
                marker_id = marker.text.strip()
                if marker_id in processed:
                    continue
                processed.add(marker_id)

                driver.execute_script("arguments[0].click();", marker)
                time.sleep(2)

                complex_name = _get_complex_name(driver)
                if not complex_name:
                    complex_name = marker_id or f"단지{idx+1}"

                _click_article_tab(driver)
                time.sleep(1)

                # --- 25/29/33평별 매매최저가·전세최고가 1건씩 수집 ---
                mae_cards, jeon_cards = _collect_by_pyeong(
                    driver, complex_name, dong_name, min_floor
                )
                mae_records.extend(mae_cards)
                jeon_records.extend(jeon_cards)

                print(f"[crawl_dong] [{idx+1}] {complex_name} — 매매:{len(mae_cards)}건 / 전세:{len(jeon_cards)}건")

            except (StaleElementReferenceException, NoSuchElementException):
                continue
            except Exception as e:
                print(f"[crawl_dong] 단지 {idx+1} 오류: {e}")
                continue

    finally:
        try:
            driver.quit()
        except Exception:
            pass

    return {"매매": mae_records, "전세": jeon_records}


def crawl() -> Generator[dict, None, None]:
    """네이버 부동산 지도에서 단지별 매물 데이터를 수집한다."""
    driver = build_driver()
    try:
        driver.get(TARGET_URL)
        print("[crawler] 페이지 로딩 중...")
        time.sleep(4)

        markers = driver.find_elements(By.CSS_SELECTOR, SELECTORS["complex_marker"])
        print(f"[crawler] 단지 마커 {len(markers)}개 발견")

        processed = set()
        for idx in range(len(markers)):
            # StaleElement 방지: 매번 다시 찾기
            try:
                markers = driver.find_elements(By.CSS_SELECTOR, SELECTORS["complex_marker"])
                if idx >= len(markers):
                    break
                marker = markers[idx]
                marker_id = marker.text.strip()
                if marker_id in processed:
                    continue
                processed.add(marker_id)

                driver.execute_script("arguments[0].click();", marker)
                time.sleep(random_delay())

                cards = _collect_cards(driver)
                print(f"[crawler] [{idx+1}/{len(markers)}] {marker_id!r} — {len(cards)}건")
                yield from cards

            except (StaleElementReferenceException, NoSuchElementException):
                continue
            except Exception as e:
                print(f"[crawler] 단지 {idx+1} 오류: {e}")
                continue
    finally:
        try:
            driver.quit()
        except Exception:
            pass
