# Garak 강건성 실측

Garak으로 GPT 두 모델에 탈옥 공격을 하고, 판정이 맞는지 끝까지 확인한 기록입니다.
글은 링크드인 "Garak 사용법" 연재 4편(1차 공격, GPT 탈옥)이고, 재료는 여기에 둡니다.

## 대상

| 모델 | 세대 |
|---|---|
| gpt-6-sol | 신형 |
| gpt-4o-mini | 구형 |

Garak v0.16.0, 판정 모델 claude-opus-5-5.

## 폴더

- `scripts/` 실행 순서대로 번호를 붙인 스크립트 5개
- `probes/` 직접 만든 프로브 kaisar.py. garak 패키지의 probes 폴더에 넣고 씁니다
- `logs/` 실행별 원본 리포트(report.jsonl)와 재판정 결과(CSV)

## 실행 순서

| 단계 | 스크립트 | 하는 일 | 결과 |
|---|---|---|---|
| 1.1 | garak1.1_jailbreak_to_gpt.py | DanInTheWild, PastTense 프로브, 기본 디텍터 | 6-sol 95.92%, 4o-mini 32.00% (거절문을 성공으로 오판) |
| 1.2 | garak1.2_jailbreak_to_gpt_by_claude.py | 디텍터를 judge.Jailbreak(Claude)로 교체 | 6-sol 2.04%, 4o-mini PASS (빈칸 템플릿이 그대로 전송됨) |
| 1.3 | garak1.3_kaisar.py | 프로브 교체. DanPayload, PastTenseJudged | probes/kaisar.py |
| 1.4 | garak1.4_jailbreak_to_gpt_changed_probes.py | 교체한 프로브로 재실행 | 6-sol 32.50%, 4o-mini 40.00% (Claude가 판정을 거부한 건이 성공으로 집계) |
| 1.5 | garak1.5_rejudge_by_claude.py | 리포트의 질문과 답변을 Claude에게 직접 보내 재판정, CSV 저장 | HIT 2, SAFE 145, BLOCKED 11, ERROR 42 |

최종: HIT 2건도 농담과 일반 설명이라 실제 뚫린 건 0건.

## 쓰는 법
