# CLAUDE.md — AI 에이전트 행동 지침

이 파일은 Claude Code 가 이 프로젝트에서 작업할 때 반드시 따라야 하는 규칙을 정의합니다.

---

## 핵심 규칙: 매 요청마다 memory-bank 업데이트

**모든 사용자 프롬프트를 처리한 후, 반드시 아래 파일들을 업데이트한다.**
작업 규모와 무관하게, 단 한 줄을 수정했더라도 해당 파일들을 동기화한다.

### 업데이트 순서

1. **`memory-bank/history.md`** — 가장 먼저, 항상
   - 사용자 프롬프트 원문 기록
   - 처리 결과 요약 (수정 파일, 핵심 변경사항, 테스트 결과)

2. **`memory-bank/implementation-plan.md`** — 작업 상태가 바뀐 경우
   - Stage 상태 아이콘 갱신: ⬜ → 🔄 → ✅ / ❌
   - 새 기능/Stage 추가 시 해당 항목 신설

3. **`memory-bank/design.md`** — 설계(구조/흐름/셀렉터)가 바뀐 경우
   - 기술 스택, 크롤링 흐름, 디렉토리 구조, 실행 방법 최신화

4. **`memory-bank/AGENTS.md`** — 에이전트 원칙이나 관리 파일 목록이 바뀐 경우

---

## 프로젝트 개요

- **목적**: 네이버 부동산(fin.land.naver.com) 아파트 매물 크롤러
- **주요 기능**:
  - 모드 A: 지도 URL 기반 전체 매물 수집 → CSV/SQLite 저장
  - 모드 B: 동 이름 입력 → 단지별 매매 최저가(4층↑) / 전세 최고가(4층↑) 수집

## 실행

```bash
python main.py                        # 모드 A: 지도 전체 수집
python main.py --dong "망포동"         # 모드 B: 동 이름 검색
python main.py --dong "망포동" --min-floor 5
```

## 테스트

```bash
python -m pytest test_dong_feature.py -v   # 단위 테스트 22케이스
python test_e2e.py                          # 엔드투엔드 테스트 (브라우저 필요)
```

---

## 파일 역할 요약

| 파일 | 역할 |
|------|------|
| `main.py` | CLI 진입점, 모드 분기 |
| `crawler.py` | 브라우저 자동화 (crawl, crawl_dong) |
| `parser.py` | 텍스트 파싱 및 데이터 정제 |
| `storage.py` | CSV / SQLite 저장, 중복 제거 |
| `config.py` | URL, CSS 셀렉터, Chrome 설정 상수 |
| `memory-bank/` | 설계 문서 및 작업 이력 관리 |

---

## 주의사항

- Chrome 버전과 `UC_VERSION` 을 일치시켜야 한다 (현재 `UC_VERSION = 148`)
- 거래유형 필터(`_set_deal_type`) 와 검색 드롭다운 셀렉터는 실제 DOM 확인 후 수정이 필요할 수 있다
- `headless=False` 권장 — 네이버 부동산 봇 탐지 우회
