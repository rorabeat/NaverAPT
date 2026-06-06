# 네이버 부동산 아파트 실거래가 크롤링 설계

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
   4-1. 매매만 필터 → 낮은가격순 정렬 → 4층↑ 첫 카드 가격 = 매매 최저가
   4-2. 전세만 필터 → 높은가격순 정렬 → 4층↑ 첫 카드 가격 = 전세 최고가
5. output/summary_<동이름>.csv 저장
```

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

## 수집 데이터 항목 (예상)

| 필드 | 설명 |
|------|------|
| complex_name | 아파트 단지명 |
| address | 주소 |
| area_m2 | 전용면적 (㎡) |
| floor | 층수 |
| deal_type | 거래 유형 (매매/전세/월세) |
| price | 거래금액 |
| deal_date | 거래일 |
| dong | 동 |

---

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
    └── summary_<동이름>.csv  # 동 검색 결과
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
