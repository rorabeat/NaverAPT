# 아키텍처 문서

> 최종 업데이트: 2026-06-06 18:00:00 (KST)

---

## 디렉터리 구조

```
GetPriceAPTByName/
├── memory-bank/
│   ├── history.md              # 대화 이력
│   ├── implementation-plan.md  # 구현 계획 (Stage 0~8)
│   ├── progress.md             # 작업 진행 현황
│   ├── architecture.md         # 아키텍처 문서 (이 파일)
│   ├── testresult.md           # 테스트 결과
│   ├── design.md               # 설계 명세
│   └── AGENTS.md               # 에이전트 원칙
├── main.py                     # CLI 진입점
├── crawler.py                  # 브라우저 자동화
├── parser.py                   # 텍스트 파싱·평수 변환
├── storage.py                  # CSV/SQLite 저장
├── config.py                   # URL, 셀렉터, 상수
├── test_dong_feature.py        # 단위 테스트
├── test_e2e.py                 # E2E 테스트
└── output/                     # 수집 결과
```

---

## 파일별 역할

| 파일 | 역할 |
|------|------|
| `main.py` | `--dong` / `--url` 모드 분기, Excel·CSV 출력 |
| `crawler.py` | Selenium 자동화: 검색, 단지 클릭, 면적 필터, 카드 수집 |
| `parser.py` | 가격·층·면적 파싱, `supply_m2_to_pyeong()` 평수 변환 |
| `storage.py` | 모드 A용 DedupBuffer, CSV/SQLite 저장 |
| `config.py` | TARGET_URL, SELECTORS, UC_VERSION, HEADLESS |

---

## crawler.py 주요 함수

| 함수 | 모드 | 설명 |
|------|------|------|
| `crawl()` | A | 지도 마커 순회 → 전체 카드 yield |
| `crawl_dong()` | B | 동 검색 → 단지별 평수·면적 필터 수집 |
| `search_dong()` | B | SearchCapsule → send_keys → 드롭다운 선택 |
| `_set_deal_type()` | B | 매매/전세 탭 필터 |
| `_click_sort()` | B | 낮은/높은 가격순 정렬 |
| `_find_first_eligible_card()` | B | 4층↑ 첫 카드 1건 추출 |
| `_open_area_filter()` | B | 전체면적 칩 클릭 |
| `_close_area_filter_outside()` | B | 외부 클릭으로 필터 적용 |
| `_select_single_area()` | B | 면적 1개 선택 + 적용 |
| `_collect_by_pyeong()` | B | 25/29/33평 면적 variant별 수집 |
| `_reset_area_filter_all()` | B | 전체면적 초기화 |

---

## 데이터 흐름 (모드 B)

```
main.py --dong "망포동"
  └─ crawl_dong()
       ├─ search_dong() → 지도 이동
       └─ for each 단지 마커:
            ├─ _get_area_filter_options() → 면적 목록
            └─ for each 25/29/33평 면적:
                 ├─ _select_single_area() → 외부 클릭 → 갱신
                 ├─ 매매/낮은 → _find_first_eligible_card()
                 └─ 전세/높은 → _find_first_eligible_card()
  └─ main.run_dong_mode() → summary_<동>.xlsx / .csv
```

---

## 아키텍처 통찰 (Insights)

### 2026-06-06 — 면적 필터는 외부 클릭으로 적용
네이버 부동산 CheckboxLayer는 체크박스 토글만으로 API 호출이 발생하지 않는다.
드롭다운이 닫히는 시점(외부 클릭)에 필터가 적용되므로 `_close_area_filter_outside()` 가 필수이다.
칩 재클릭은 필터 미적용 또는 의도치 않은 토글을 유발할 수 있다.

### 2026-06-06 — 면적 선택은 단일 선택 UX
한 번에 1개 면적만 선택되는 UI이므로, 25평대 3종(87.12/87.75/87.87㎡)은 각각 별도 필터 사이클이 필요하다.

---
