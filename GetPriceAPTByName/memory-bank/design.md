# 네이버 부동산 아파트 실거래가 크롤링 설계

> 최종 업데이트: 2026-06-06 18:00:00 (KST)

## 개요

네이버 부동산(fin.land.naver.com) 지도 화면에서 특정 지역 아파트 단지 목록 및 실거래가 데이터를 수집하는 크롤러.

---

## 목표 URL

```
https://fin.land.naver.com/map?center=3zkle5-2Ayvzo&layer=NobwRAlgJmBcYGMD2BbADgGwKYA8D6UWALgIYQZgA0YaJATiSgM5zjLrY4CSM8AjAAYAnABY%2BAJjABfakyz0EACwAK9Ri1jgITAGrkMJOADMSGOdVIAjOABUGhDwE80WBpgAIJ80tR0xACudAB2JJZOsER0UVhSALpAA&zoom=14.400225253300547
```

---

## 기술 스택

| 항목 | 선택 |
|------|------|
| 언어 | Python 3.10+ |
| 브라우저 자동화 | undetected-chromedriver + Selenium (봇 탐지 우회) |
| 데이터 저장 | CSV / SQLite |
| 스케줄링 | cron 또는 수동 실행 |

---

## 타겟 셀렉터

```css
#complex_detail > div > div.ArticleListWrapper_article__fpLy3 > ul > li:nth-child(n) > div > button
```

- 단지 상세 패널 내 거래 목록의 각 항목 버튼
- `nth-child(n)` 을 반복하거나 `ul > li` 전체를 순회하여 모든 항목 수집

---

## 크롤링 흐름

### 모드 A — 지도 전체 수집 (`python main.py`)
```
1. 브라우저 실행 (undetected-chromedriver, headless=False 권장)
2. 목표 URL 접속 및 지도 로딩 대기
3. 지도 위 아파트 단지 마커 목록 수집
4. 각 단지 마커 클릭 → 매물 탭 클릭 → 카드 전체 수집
5. 수집 데이터 저장 (CSV / SQLite)
```

### 모드 B — 동 이름 검색 (`python main.py --dong "망포동"`)
```
1. 브라우저 실행 → fin.land.naver.com 접속
2. 검색창에 동 이름 입력 → 드롭다운 결과 선택 → 지도 이동
3. 지도 위 단지 마커 수집
4. 각 단지 클릭 → 매물 탭 클릭
   4-1. 전체면적 필터 드롭다운 파싱 → 공급면적을 25/29/33평으로 그룹핑
   4-2. 각 면적(87.12A㎡, 96.45㎡ 등) **1개씩** 선택 → **드롭다운 외부 클릭**으로 필터 적용 → 목록 갱신 대기
   4-3. 매매/낮은가격순 → 4층↑ 첫 카드 = 매매 최저가 1건
   4-4. 전세/높은가격순 → 4층↑ 첫 카드 = 전세 최고가 1건
   4-5. 다음 면적로 반복 → 마지막에 전체면적으로 초기화
5. output/summary_<동이름>.xlsx 저장 (매매/전세 시트, 평수 컬럼 포함)
```

**평수 변환 기준** (공급면적 ÷ 3.305785, ±1.5평 허용)
| 표준 평수 | 예시 공급면적 (힐스테이트영통) |
|----------|-------------------------------|
| 25평 | 87.12A㎡, 87.75B㎡, 87.87C㎡ |
| 29평 | 96.45㎡ |
| 33평 | 110.94B㎡, 111.31A㎡ |

**면적 필터 UI 동작 (중요)**
- 체크박스만 클릭해도 **필터가 적용되지 않음**
- 면적 **1개** 선택 후 **드롭다운 외부 클릭** 시 메뉴가 닫히며 목록 갱신
- 칩 텍스트: `전체면적` → 선택 후 `87A㎡` 등으로 변경
- 외부 클릭 대상: 단지명 헤더, 매물 목록, 탭 바 (실패 시 ESC)

**면적 필터 셀렉터**
| 요소 | CSS |
|------|-----|
| 전체면적 칩 | `button#면적` |
| 체크박스 레이어 | `[class*='ComplexArticleFilter_area-filter'] [class*='CheckboxLayer']` |
| 면적 항목 | `[class*='ComplexArticleFilter_area-filter'] [class*='CheckboxLayer'] ul li label` |

**면적 필터 관련 함수 (`crawler.py`)**
| 함수 | 역할 |
|------|------|
| `_open_area_filter` | 전체면적 칩 클릭 → 드롭다운 열기 |
| `_close_area_filter_outside` | 외부 클릭으로 드롭다운 닫기 + 필터 적용 |
| `_select_single_area` | 면적 1개 선택 → 외부 클릭 → 갱신 대기 |
| `_wait_for_filter_reload` | 매물 목록 DOM 갱신 대기 |
| `_collect_by_pyeong` | 25/29/33평 해당 면적 variant별 매매·전세 1건씩 수집 |
| `_reset_area_filter_all` | 전체면적으로 필터 초기화 |

**층수 판단 기준**
| 텍스트 | 포함 여부 |
|--------|----------|
| `21/27층` (숫자 >= 4) | 포함 |
| `고/25층` | 포함 (고층) |
| `중/25층` | 포함 (중층) |
| `저/25층` | **제외** (저층) |

---

## 중복 매물 제거 정책

동일 매물 판단 기준: 아래 필드가 모두 일치하는 경우 중복으로 간주하고 제거한다.

| 기준 필드 | 설명 |
|-----------|------|
| `complex_name` | 단지명 |
| `area_m2` | 전용면적 |
| `floor` | 층수 |
| `deal_type` | 거래 유형 |
| `price` | 거래금액 |
| `deal_date` | 거래일 |

**처리 방식**
- 수집 중 메모리 내 `set` 으로 중복 키 실시간 체크
- 저장 시 SQLite `UNIQUE` 제약 조건으로 이중 방지
- CSV 저장 전 `pandas.DataFrame.drop_duplicates()` 적용

---

## 수집 데이터 항목

### 모드 A (지도 전체)
| 필드 | 설명 |
|------|------|
| complex_name | 아파트 단지명 |
| dong | 동호 |
| deal_type | 거래 유형 (매매/전세/월세) |
| price_min / price_max | 거래금액 (만원) |
| area_m2 | 전용면적 (㎡) |
| floor | 층수 |
| total_floors | 총층 |
| direction | 향 |
| building_type | 건물유형 |
| listing_date | 등록일 |

### 모드 B (동 검색 — summary 출력)
| 필드 | 설명 |
|------|------|
| 단지명 | 아파트 단지명 |
| 동 | 검색 동 이름 |
| 동호 | 단지명+동호 (예: 힐스테이트영통 105동) |
| 거래유형 | 매매 / 전세 |
| 평수 | 25평 / 29평 / 33평 (공급면적 기준 변환) |
| 공급면적 | 필터에서 선택한 공급면적 (예: 96.45㎡) |
| 가격 | 거래금액 텍스트 |
| 면적 | 카드 표시 면적 (전용면적 포함) |
| 층 | 층 정보 |
| 향 | 방향 |
| 건물유형 | 아파트 등 |
| 기준층 | min_floor 기준 (예: 4층 이상) |

**출력 파일**
- `output/summary_<동이름>.xlsx` — 시트: 매매 / 전세
- `output/summary_<동이름>.csv` — 매매+전세 합본

## 봇 탐지 우회 전략

- `undetected-chromedriver` 사용 — ChromeDriver 패치로 navigator.webdriver 플래그 제거
- 각 액션 사이 랜덤 딜레이 (`time.sleep(random.uniform(1.5, 3.5))`)
- `headless=False` 모드로 실사용자 환경 모방
- Chrome 버전 자동 감지 (필요 시 `UC_VERSION` 고정)

---

## 디렉토리 구조

```
GetPriceAPTByName/
├── main.py                  # 진입점 (--dong / --url 모드 분기)
├── crawler.py               # 브라우저 자동화 (crawl, crawl_dong)
├── parser.py                # 데이터 파싱 및 정제
├── storage.py               # CSV / SQLite 저장
├── config.py                # URL, 셀렉터, 딜레이 상수
├── requirements.txt
├── test_dong_feature.py     # 단위 테스트 22케이스
├── test_e2e.py              # 엔드투엔드 테스트
└── output/
    ├── apt_prices.csv       # 전체 수집 결과
    ├── apt_prices.db
    └── summary_<동이름>.xlsx  # 동 검색 결과 (매매/전세 시트)
    └── summary_<동이름>.csv
```

---

## 실행 방법

```bash
pip install -r requirements.txt

# 모드 A: 지도 URL 기반 전체 수집
python main.py

# 모드 B: 동 이름 기반 단지별 최저/최고가 수집
python main.py --dong "망포동"
python main.py --dong "망포동" --min-floor 5
```

---
