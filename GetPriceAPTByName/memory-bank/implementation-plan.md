# implementation-plan.md — 단계별 구현 계획

> **원칙**: 작업을 스스로 시작하지 않는다. 사용자의 명시적 요청이 있을 때만 해당 Stage를 진행한다.
> **최종 업데이트**: 2026-06-06 (KST, 2차 업데이트)
> 상태 아이콘: ⬜ 대기 | 🔄 진행 중 | ✅ 완료 | ❌ 실패

---

## 전체 진행 현황

| Stage | 이름 | 상태 | 완료일 |
|-------|------|------|--------|
| Stage 0 | 프로젝트 설계 및 문서화 | ✅ 완료 | 2026-06-06 |
| Stage 1 | 프로젝트 초기화 및 환경 구성 | ✅ 완료 | 2026-06-06 |
| Stage 2 | 브라우저 자동화 기반 구현 | ✅ 완료 | 2026-06-06 |
| Stage 3 | 데이터 파싱 및 추출 구현 | ✅ 완료 | 2026-06-06 |
| Stage 4 | 데이터 저장 구현 | ✅ 완료 | 2026-06-06 |
| Stage 5 | 통합 테스트 및 CLI 완성 | ✅ 완료 | 2026-06-06 |
| Stage 6 | 동 이름 검색 기능 구현 | ✅ 완료 | 2026-06-06 |
| Stage 7 | 평수별 면적 필터 + 최저/최고가 1건 수집 | ✅ 완료 | 2026-06-06 |
| Stage 8 | 면적 필터 외부 클릭 적용 (개별 사이즈 순회) | ✅ 완료 | 2026-06-06 |

---

## Stage 8 — 면적 필터 외부 클릭 적용 ✅ 완료

### 목표
체크박스만 토글하던 문제 해결 — 면적 1개 선택 후 외부 클릭으로 필터 적용, 개별 공급면적별 수집

### 작업 항목
- [x] 8.1 `_close_area_filter_outside()` — 드롭다운 외부 클릭으로 필터 적용 — 완료: 2026-06-06
- [x] 8.2 `_select_single_area()` + `_wait_for_filter_reload()` — 선택→적용→갱신 대기 — 완료: 2026-06-06
- [x] 8.3 `_collect_by_pyeong()` — 평수 그룹 → **개별 공급면적** 순회로 변경 — 완료: 2026-06-06
- [x] 8.4 `_reset_area_filter_all()` — 단지 처리 후 전체면적 초기화 — 완료: 2026-06-06
- [x] 8.5 `main.py` — `공급면적` 컬럼 추가 — 완료: 2026-06-06
- [x] 8.6 E2E 검증 — `망포동` 22단지, 매매 40건/전세 30건 — 완료: 2026-06-06

### 결과
- 네이버 UI 특성: **면적 1개 선택 → 메뉴 외부 클릭 시** 목록 갱신
- 단지당 면적 variant 수 × 2(매매/전세) 건 수집 (25/29/33평 해당 면적만)

---

## Stage 7 — 평수별 면적 필터 + 최저/최고가 1건 수집 ✅ 완료

### 목표
전체면적 필터를 활용해 25/29/33평 해당 면적의 매매최저가·전세최고가 1건씩 수집

### 작업 항목
- [x] 7.1 `parser.py` — 공급면적→평수 변환 (`supply_m2_to_pyeong`) — 완료: 2026-06-06
- [x] 7.2 `config.py` — 면적 필터 셀렉터 추가 — 완료: 2026-06-06
- [x] 7.3 `crawler.py` — `_collect_by_pyeong` 면적 필터 자동화 — 완료: 2026-06-06
- [x] 7.4 `main.py` — `평수` 컬럼 출력 — 완료: 2026-06-06
- [x] 7.5 `test_dong_feature.py` — 평수 변환 테스트 추가 — 완료: 2026-06-06

### 결과
공급면적(㎡) → 25/29/33평 버킷 변환 기반 필터링. (Stage 8에서 개별 사이즈 순회로 확장)

---

## Stage 0 — 프로젝트 설계 및 문서화 ✅ 완료

### 목표
설계 문서 및 에이전트 관리 파일 정비

### 작업 항목
- [x] `design_original.md` 분석
- [x] `design.md` 작성 (기술 스택, 흐름, 셀렉터, 디렉토리 구조)
- [x] `AGENTS.md` 생성
- [x] `history.md` 생성
- [x] `implementation-plan.md` 생성

### 결과
모든 기반 문서 생성 완료.

---

## Stage 1 — 프로젝트 초기화 및 환경 구성 ✅ 완료

### 목표
Python 프로젝트 구조 생성 및 의존성 설치

### 작업 항목
- [ ] 디렉토리 구조 생성
  ```
  GetPriceAPTByName/
  ├── main.py
  ├── crawler.py
  ├── parser.py
  ├── storage.py
  ├── config.py
  ├── requirements.txt
  └── output/
  ```
- [x] `requirements.txt` 작성
  - `playwright`
  - `playwright-stealth`
  - `pandas`
  - `sqlite3` (내장)
- [x] `config.py` 작성 — URL, 셀렉터 상수, 딜레이 설정

### 선행 조건
Stage 0 완료 ✅

### 결과
- `requirements.txt` 생성 (playwright, playwright-stealth, pandas)
- `config.py` 생성 (TARGET_URL, SELECTORS, random_delay, OUTPUT 경로, HEADLESS 설정)
- `output/` 디렉토리 생성

---

## Stage 2 — 브라우저 자동화 기반 구현 ✅ 완료

### 목표
Playwright로 네이버 부동산 지도 접속 및 단지 마커 클릭 자동화

### 작업 항목
- [x] `crawler.py` 구현
  - 브라우저 실행 (undetected-chromedriver, headless=False)
  - 목표 URL 접속 및 지도 로딩 대기
  - 아파트 단지 마커 목록 수집
  - 각 마커 클릭 → 상세 패널 열림 대기
  - `ArticleListWrapper` 내 `li` 전체 순회
  - 페이지네이션 처리

### 선행 조건
Stage 1 완료

### 결과
- `crawler.py` 생성: `build_driver()`, `crawl()` 제너레이터, `_collect_articles()` 구현

---

## Stage 3 — 데이터 파싱 및 추출 구현 ✅ 완료

### 목표
단지 상세 패널에서 실거래 데이터 파싱

### 작업 항목
- [x] `parser.py` 구현
  - 단지명, 주소 추출
  - 전용면적, 층수, 거래유형, 금액, 거래일, 동 추출
  - 데이터 정제 (금액 단위 통일 → 만원, 날짜 파싱 → YYYY-MM)

### 수집 필드
| 필드 | 설명 |
|------|------|
| complex_name | 아파트 단지명 |
| address | 주소 |
| area_m2 | 전용면적 (㎡) |
| floor | 층수 |
| deal_type | 거래 유형 (매매/전세/월세) |
| price | 거래금액 (만원) |
| deal_date | 거래일 (YYYY-MM) |
| dong | 동 |

### 선행 조건
Stage 2 완료

### 결과
- `parser.py` 생성: `parse_article()`, `_clean_price()`, `_extract_text()` 구현

---

## Stage 4 — 데이터 저장 구현 ✅ 완료

### 목표
수집 데이터를 CSV 및 SQLite에 저장

### 작업 항목
- [x] `storage.py` 구현
  - CSV 저장 (`output/apt_prices.csv`) — 저장 전 `drop_duplicates()` 적용
  - SQLite 저장 (`output/apt_prices.db`) — `UNIQUE(complex_name, area_m2, floor, deal_type, price, deal_date)` 제약 조건
  - 수집 중 메모리 내 `set` 으로 실시간 중복 키 체크

### 선행 조건
Stage 3 완료

### 결과
- `storage.py` 생성: `DedupBuffer`, `save_to_csv()`, `save_to_db()`, `_init_db()` 구현

---

## Stage 5 — 통합 테스트 및 CLI 완성 ✅ 완료

### 목표
전체 파이프라인 통합 및 CLI 인터페이스 완성

### 작업 항목
- [x] `main.py` 구현 — CLI 인자 파싱 (`--url`, `--output-csv`, `--output-db`)
- [x] 전체 파이프라인 통합 (crawl → parse → dedup → flush)
- [x] 예외 처리 (KeyboardInterrupt, 일반 예외)

```bash
python main.py --url "<NAVER_MAP_URL>" --output-csv output/apt_prices.csv
```

### 선행 조건
Stage 4 완료

### 결과
- `main.py` 생성: CLI 파싱, crawl→parse→DedupBuffer→flush 파이프라인 구현
- 전체 Stage 완료

---

---

## 실제 DOM 검증 결과 (2026-06-06)

실제 네이버 부동산 사이트에서 테스트하여 확인된 셀렉터:

| 항목 | 설계 시 셀렉터 | 실제 셀렉터 |
|------|--------------|------------|
| 단지 마커 | `[class*='ComplexSummary_article']` | `button[class*='ComplexMarkerDefault_article']` |
| 매물 탭 버튼 | (없음) | `button[class*='LineTab-module_link']` (텍스트='매물') |
| 목록 UL | `ArticleListWrapper_article__fpLy3` | `[class*='ComplexArticleTab_article']` |
| 카드 LI | `li:nth-child(n)` | `li[class*='ArticleCard_item']` |
| 단지명 | (HTML 파싱) | `[class*='ArticleCard_name']` |
| 가격 | (정규식) | `[class*='ArticleCard_area-price']` |
| 요약 항목 | (정규식) | `[class*='ArticleCard_item-summary']` [0]유형 [1]면적 [2]층 [3]향 |

**테스트 결과**: 마커 34개, 76건 수집, 파싱 100%, 중복 2건 제거, 74건 CSV/DB 저장 확인

---

## Stage 6 — 동 이름 검색 기능 구현 ✅ 완료

### 목표
사용자가 동 이름을 입력하면 해당 동의 각 단지별 **매매 최저가(4층↑)** 와 **전세 최고가(4층↑)** 를 수집한다.

### 작업 항목
- [x] `crawler.py` 신규 함수 추가
  - `_is_floor_eligible(floor_text, min_floor)` — 층수 조건 판단
  - `_click_sort(driver, label)` — JS 텍스트 매칭 정렬 버튼 클릭
  - `_set_deal_type(driver, deal_type)` — 거래유형 필터 설정
  - `_find_first_eligible_card(driver, min_floor)` — 조건 만족 첫 카드 가격 반환
  - `_get_complex_name(driver)` — 패널에서 단지명 추출
  - `search_dong(driver, dong_name)` — 검색창 입력 → 드롭다운 선택 → 지도 이동
  - `crawl_dong(dong_name, min_floor)` — 전체 흐름 오케스트레이션
- [x] `main.py` 수정 — `--dong`, `--min-floor` 인자 추가, 모드 분기
- [x] `parser.py` 수정 — `_parse_floor` 중/고/저 prefix 지원
- [x] `test_dong_feature.py` 생성 — 22개 단위 테스트 (TC1~TC5), 전체 통과

### 실행 방법
```bash
python main.py --dong "망포동"
python main.py --dong "망포동" --min-floor 5
```

### 출력
- 콘솔: 단지별 매매 최저가 / 전세 최고가 표
- 파일: `output/summary_망포동.csv`

### 테스트 결과
- `test_dong_feature.py` 22/22 통과 (2026-06-06)
- 엔드투엔드 실행 검증 완료 (2026-06-06): 26개 단지, 매매↔전세 필터 정상, CSV 저장 확인

---

## 실제 DOM 검증 결과 (2026-06-06, 동 검색 기능)

| 항목 | 기존 코드 | 실제 동작 |
|------|----------|----------|
| 검색창 | `input[placeholder*='검색']` | `button[class*='SearchCapsule']` 클릭 → `input[class*='HeaderSearch_search-input']` |
| 검색 결과 | `li[class*='SearchResult']` | `[class*='SearchResultList_name']` span 직접 클릭 |
| 거래유형 버튼 | `button` textContent 정확 매칭 | `button[class*='ButtonBox']` + `startsWith('매매'/'전세')` |
| 정렬 버튼 | `button` textContent 매칭 | `label[for='filterOrder2']` 클릭 + detail span(`낮은`/`높은`) 감지 토글 |

**실행 시 필수**: `PYTHONUTF8=1 python main.py --dong "망포동"` (Windows 콘솔 인코딩 문제)

*이 파일은 각 Stage 진행 시 자동으로 업데이트됩니다.*
