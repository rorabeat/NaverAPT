# history.md — 대화 및 처리 이력

> 형식: 각 항목은 `[날짜 시간]` 헤더 → **사용자 프롬프트** → **처리 결과 요약** 순으로 기록한다.

---

## 2026-06-06 (Excel 2시트 출력 + 카드 상세 정보 수집)

### [2026-06-06] 요청 11
**사용자 프롬프트**
> 매매와 전세를 시트로 구분해서 표시해줘 각 물건의 동호수.특징들을 세부적으로 표시해줘

**처리 결과**
- `crawler.py`: `_find_first_eligible_card` → `_collect_eligible_cards` 로 전면 교체
  - 첫 카드 가격만 반환하던 방식 → 모든 적격 카드의 상세 정보(동호, 면적, 층, 향, 건물유형, 가격) 수집
  - `crawl_dong` 반환 타입 변경: `list[dict]` → `{"매매": [...], "전세": [...]}`
- `main.py`: Excel 2시트 출력 (`openpyxl` 엔진)
  - 시트: **매매** (낮은가격순) / **전세** (높은가격순)
  - 컬럼: 단지명, 동, 동호, 거래유형, 가격, 면적, 층, 향, 건물유형, 기준층
  - 컬럼 너비 자동 조정
  - CSV도 병행 저장 (매매+전세 합본)
- `search_dong` 안정화: JS입력 방식 → send_keys 방식 복구 (React 검색 트리거용)

**최종 실행 결과**
- 매매 129건 / 전세 21건 수집
- `output/summary_망포동.xlsx` 저장 완료 (매매 / 전세 시트 분리)

---

## 2026-06-06 (엔드투엔드 검증 및 버그 수정)

### [2026-06-06] 요청 10
**사용자 프롬프트**
> Chrome 실행 → 네이버 부동산 검색창에 "망포동" 입력 → 지도 이동 / 각 단지 클릭 → 매물 탭 → 매매/낮은가격순 → 첫 4층↑ 카드 가격 수집 / 전세/높은가격순 → 첫 4층↑ 카드 가격 수집 / output/summary_망포동.csv 출력 확인 === 직접 수행해서 정상 작동하는지 확인해줘

**처리 결과 (다중 버그 수정 사이클)**

| 사이클 | 문제 | 수정 내용 |
|--------|------|-----------|
| 1 | `input[placeholder*='검색']` 셀렉터 불일치 — 검색창이 `<button>` 으로 구현됨 | `SearchCapsule` 버튼 클릭 후 `HeaderSearch_search-input` input에 타이핑하도록 `search_dong` 재작성 |
| 2 | 드롭다운 첫 결과 클릭 안 됨 | `[class*='SearchResultList_name']` span을 직접 클릭 |
| 3 | Windows cp949 콘솔 인코딩 오류 (em dash `—`) | `main.py` 상단에 `sys.stdout` UTF-8 강제 설정 추가 |
| 4 | 매매↔전세 필터 전환 안 됨 — `_set_deal_type` JS가 `매매` vs `매매11` 텍스트 불일치 | `startsWith` 매칭으로 변경, `ButtonBox` 버튼 직접 클릭 |
| 5 | 정렬 (`낮은가격순`/`높은가격순`) 미작동 — 정렬이 `<label>` (라디오 패턴) 구현 | `label[for='filterOrder2']` 클릭 + detail span (`낮은`/`높은`) 감지하여 방향 맞춤 |
| 6 | 가격 텍스트에 `\n상승내역 보기` 포함 | `splitlines()[0]` 으로 첫 줄만 사용 |
| 7 | 검색 간헐적 실패 | `search_dong`에 재시도(2회) + 페이지 새로고침 로직 추가 |

**최종 실행 결과** (`PYTHONUTF8=1 python main.py --dong "망포동"`)
- 단지 마커 34개 발견, 26개 단지 수집
- 매매 최저가 / 전세 최고가 정상 분리 확인
- `output/summary_망포동.csv` 26행 저장 완료

---

## 2026-06-06

### [2026-06-06] 요청 1
**사용자 프롬프트**
> design_original.md 을 리뷰하고 수정된 결과를 design.md 에 저장해줘

**처리 결과**
- `memory-bank/design_original.md` 내용 분석 (URL, CSS 셀렉터, Python + undetected-playwright 메모)
- `memory-bank/design.md` 신규 생성
  - 추가 항목: 기술 스택 표, 크롤링 흐름 단계, 수집 데이터 필드 목록, 봇 탐지 우회 전략, 디렉토리 구조, 실행 CLI, 주의사항

---

### [2026-06-06] 요청 2
**사용자 프롬프트**
> design.md 파일을 토대로 memory-bank 폴더 하위에 AGENTS.md 파일을 생성하고 아래 파일을 생성하되 지속적으로 업데이트 한다.
> 1. history.md : 시간별로 사용자가 입력한 프롬프트를 그대로 저장한다. 그리고 AI 가 처리한 결과를 요약해서 표시한다.
> 2. implementation-plan.md : design.md 와 Agents.md 를 분석하여 작업계획을 stage 별로 작성한다. 작업을 스스로 시작하지 말고 사용자의 요청에 따라 순서에 맞게 진행한다. 그리고 진행 여부및 결과를 각각 표시한다.

**처리 결과**
- `memory-bank/AGENTS.md` 생성 — 에이전트 역할 원칙, 관리 파일 목록, 행동 흐름 정의
- `memory-bank/history.md` 생성 — 현재 파일 (이력 누적 관리)
- `memory-bank/implementation-plan.md` 생성 — Stage 0~5 구현 계획, 각 Stage 상태 표시

---

### [2026-06-06] 요청 3
**사용자 프롬프트**
> 시작해줘

**처리 결과**
- Stage 1 — 프로젝트 초기화 및 환경 구성 진행
  - `output/` 디렉토리 생성
  - `requirements.txt` 생성 (playwright → 이후 변경)
  - `config.py` 생성 (TARGET_URL, SELECTORS, random_delay, OUTPUT 경로, HEADLESS)
  - `implementation-plan.md` Stage 1 → ✅ 완료

---

### [2026-06-06] 요청 4
**사용자 프롬프트**
> undetected-chromedriver 를 이용해줘

**처리 결과**
- 기술 스택 playwright → undetected-chromedriver + Selenium 으로 변경
  - `requirements.txt` 수정: undetected-chromedriver==3.5.5, selenium==4.21.0, pandas==2.2.2
  - `config.py` 수정: WINDOW_SIZE, UC_VERSION 상수 추가
  - `design.md` 수정: 기술 스택 표, 봇 탐지 우회 전략, 크롤링 흐름 설명 업데이트

---

### [2026-06-06] 요청 6
**사용자 프롬프트**
> 완료까지 진행해줘

**처리 결과**
- Stage 2~5 구현 완료 (crawler.py, parser.py, storage.py, main.py)

---

### [2026-06-06] 요청 7
**사용자 프롬프트**
> 실제 웹사이트에서 정상 동작할때까지 테스트-구현 반복해줘

**처리 결과 (반복 테스트 사이클)**

| 사이클 | 문제 | 수정 |
|--------|------|------|
| 1 | ChromeDriver 149 vs Chrome 148 버전 불일치 | `UC_VERSION=148` 고정 |
| 2 | `ComplexSummary_article` 셀렉터 0건 | 실제 마커: `button[class*='ComplexMarkerDefault_article']` |
| 3 | 마커 클릭 후 카드 0건 — 기본 탭이 "시세/실거래가" | `매물` 탭 클릭 로직 `_click_article_tab()` 추가 |
| 4 | 전체 파이프라인 검증 | 마커 3개 × 76건 수집, 파싱 76/76, 중복 2건 제거, CSV/DB 74건 저장 확인 |

- `config.py`: 셀렉터 전면 교체 (`ComplexMarkerDefault_article`, `LineTab-module_link`, `ComplexArticleTab_article` 등)
- `crawler.py`: `_click_article_tab()` 추가, `driver.quit()` 안전 처리
- `parser.py`: Selenium WebElement 직접 추출 방식으로 전면 재작성
- `storage.py`: 중복 키 필드 업데이트 (매물 기준)
- `test_single.py`, `test_e2e.py` 생성 (검증용)

**최종 검증 결과**
- 마커 34개 탐지, 30건/13건/33건 수집
- 파싱 성공률 100% (76/76)
- 중복 제거 2건, CSV/DB 74건 저장 정상

---

### [2026-06-06] 요청 6
**사용자 프롬프트**
> 완료까지 진행해줘

**처리 결과**
- Stage 2 ✅: `crawler.py` 생성 — `build_driver()` (undetected-chromedriver), `crawl()` 제너레이터, 페이지네이션 처리
- Stage 3 ✅: `parser.py` 생성 — HTML 텍스트 파싱, 정규식 기반 필드 추출, 금액 만원 단위 정제
- Stage 4 ✅: `storage.py` 생성 — `DedupBuffer`(메모리 set), `save_to_csv()`(drop_duplicates), `save_to_db()`(UNIQUE 제약)
- Stage 5 ✅: `main.py` 생성 — CLI (`--url`, `--output-csv`, `--output-db`), 전체 파이프라인 통합
- `implementation-plan.md` 전 Stage ✅ 완료 업데이트

---

### [2026-06-06] 요청 9
**사용자 프롬프트**
> 프롬프트 명령 입력하고 수행할때마다 업데이트 하도록 claude.md 및 agents.md 업데이트 해줘

**처리 결과**
- `CLAUDE.md` 신규 생성 (프로젝트 루트)
  - 핵심 규칙: 매 요청 후 memory-bank 4개 파일 업데이트 순서 명시
  - 프로젝트 개요, 실행/테스트 명령, 파일 역할 요약, 주의사항 포함
- `memory-bank/AGENTS.md` 수정
  - 원칙 6번 추가: "매 요청 후 memory-bank 동기화 필수" + 파일별 업데이트 조건
  - CLAUDE.md 와의 우선순위 관계 명시 (충돌 시 CLAUDE.md 우선)

---

### [2026-06-06] 요청 8
**사용자 프롬프트**
> 테스트케이스 작성해줘 5개

**처리 결과**
- `test_dong_feature.py` 생성 — 5개 테스트 클래스, 22개 케이스
  - TC1 `TestIsFloorEligible`: `_is_floor_eligible` 층수 판단 (숫자/고/중/저, 경계값) 7케이스
  - TC2 `TestParseFloor`: `_parse_floor` 층 텍스트 파싱 (중/고 prefix 포함) 5케이스
  - TC3 `TestParseDealPrice`: 가격 파싱 (범위/단일/억만원/거래유형/월세) 5케이스
  - TC4 `TestCrawlDongStructure`: 결과 dict 구조 검증 3케이스
  - TC5 `TestRunDongModeCsv`: CSV 저장 경로/빈 결과 처리 2케이스
- `parser.py` 버그 수정: `_parse_floor` 가 "중/25층" 등 한글 prefix 처리 못하던 문제 해결
- 전체 22/22 통과 확인

---

### [2026-06-06] 요청 5
**사용자 프롬프트**
> 동일 매물은 제거하도록 요청을 추가해줘

**처리 결과**
- `design.md` 에 "중복 매물 제거 정책" 섹션 추가
  - 중복 판단 기준 필드: complex_name, area_m2, floor, deal_type, price, deal_date
  - 처리 방식: 메모리 내 set 실시간 체크 / SQLite UNIQUE 제약 / CSV drop_duplicates()
- `implementation-plan.md` Stage 4 저장 항목에 중복 제거 로직 명세 추가

---
