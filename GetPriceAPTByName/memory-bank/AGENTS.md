# AGENTS.md — 에이전트 역할 정의

이 프로젝트에서 AI 에이전트가 수행하는 역할과 행동 원칙을 정의합니다.

---

## 에이전트 원칙

1. **사용자 승인 우선** — 작업은 사용자의 명시적 요청이 있을 때만 시작한다. 스스로 다음 단계를 진행하지 않는다.
2. **단계 순서 준수** — `implementation-plan.md` 의 Stage 순서를 따르며, 이전 Stage 완료 전 다음 Stage를 시작하지 않는다.
3. **기록 유지** — 모든 사용자 프롬프트와 처리 결과는 `history.md` 에 즉시 기록한다.
4. **계획 동기화** — 작업 완료/실패 시 `implementation-plan.md` 의 상태를 즉시 업데이트한다.
5. **설계 준수** — `design.md` 에 정의된 기술 스택, 디렉토리 구조, 셀렉터를 기준으로 구현한다.
6. **매 요청 후 memory-bank 동기화 필수** — 요청 처리가 끝나면 아래 순서로 반드시 업데이트한다.
   - `history.md` → 항상 (프롬프트 원문 + 결과 요약)
   - `implementation-plan.md` → 작업 상태 변경 시
   - `design.md` → 설계/구조/흐름 변경 시
   - `AGENTS.md` → 원칙 변경 시

---

## 관리 파일 목록

| 파일 | 역할 | 업데이트 시점 |
|------|------|--------------|
| `design.md` | 시스템 설계 명세 | 설계 변경 시 |
| `AGENTS.md` | 에이전트 역할 및 원칙 | 원칙 변경 시 |
| `history.md` | 대화 및 처리 이력 | **매 사용자 요청마다 (필수)** |
| `implementation-plan.md` | 단계별 구현 계획 및 진행 상태 | 작업 시작/완료마다 |

> **CLAUDE.md 와 연동**: 프로젝트 루트의 `CLAUDE.md` 가 Claude Code 의 최우선 행동 지침이다.
> `AGENTS.md` 는 그 세부 내용을 보완한다. 두 파일이 충돌하면 `CLAUDE.md` 를 따른다.

---

## 에이전트 행동 흐름

```
사용자 요청 수신
  │
  ├─ history.md 에 요청 기록
  │
  ├─ implementation-plan.md 에서 해당 Stage 확인
  │     ├─ 선행 Stage 미완료 → 사용자에게 알림 후 중단
  │     └─ 순서 정상 → 작업 진행
  │
  ├─ 작업 수행 (design.md 명세 준수)
  │
  ├─ implementation-plan.md 상태 업데이트
  │
  └─ history.md 에 결과 요약 기록
```
