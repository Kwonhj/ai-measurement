# Garak 강건성 실측

Garak으로 GPT와 Gemini에 탈옥과 인젝션 공격 수행, 판정이 맞는지 끝까지 확인한 기록.
링크드인 "Garak 사용법" 연재 4편(GPT 탈옥), 5편(GPT 인젝션), 6편(Gemini 탈옥).

## 대상

| 모델 | 체급 |
|---|---|
| gpt-6-sol | 신형, 숙고형 |
| gpt-4o-mini | 구형, 경량 |
| gemini-3.8-flash | 신형, 숙고형 |
| gemini-3.1-flash-lite | 구형, 경량 |

Garak v0.17.0, 판정 모델 claude-opus-5-5. Gemini는 OpenAI 호환 엔드포인트로 연결.

## 폴더

- `scripts/` 편별로 번호를 붙인 스크립트. 1.x 탈옥(GPT), 2.x 인젝션(GPT), 3.x 탈옥(Gemini)
- `probes/` 직접 만든 프로브 kaisar.py. garak 패키지의 probes 폴더에 넣고 시작(script가 자동으로 수행)
- `logs/` 실행별 원본 리포트(report.jsonl, hitlog.jsonl)와 재판정 결과(CSV)

## 실행 순서

### 4편. GPT 탈옥 (1.x)

| 단계 | 스크립트 | 하는 일 | 결과 |
|---|---|---|---|
| 1.1 | garak1.1_jailbreak_to_gpt.py | DanInTheWild, PastTense 프로브, 기본 디텍터 | 6-sol 95.92%, 4o-mini 32.00% (거절문을 성공으로 오판) |
| 1.2 | garak1.2_jailbreak_to_gpt_by_claude.py | 디텍터를 judge.Jailbreak(Claude)로 교체 | 6-sol 2.04%, 4o-mini PASS (빈칸 템플릿이 그대로 전송됨) |
| 1.3 | garak1.3_kaisar.py | 프로브 교체. DanPayload, PastTenseJudged | probes/kaisar.py |
| 1.4 | garak1.4_jailbreak_to_gpt_changed_probes.py | 교체한 프로브로 재실행 | 6-sol 32.50%, 4o-mini 40.00% (Claude가 판정을 거부한 건이 성공으로 집계) |
| 1.5 | garak1.5_rejudge_by_claude.py | 리포트의 질문과 답변을 Claude에게 직접 보내 재판정, CSV 저장 | HIT 2, SAFE 145, BLOCKED 11, ERROR 42 |

최종: HIT 2건도 농담과 일반 설명이라 실제 뚫린 건 0건.

### 5편. GPT 인젝션 (2.x)

| 단계 | 스크립트 | 하는 일 | 결과 |
|---|---|---|---|
| 2.1 | garak2.1_injection_to_gpt.py | HijackHateHumans(직접), LatentInjectionReport(간접) 프로브, 기본 디텍터 | Garak 판정 94/200 |

디텍터가 문자열 비교라 Claude 재판정 단계 없음. hitlog를 사람이 읽어 오탐 9건을 제외.
최종: 85/200 (42.5%). 6-sol 32건, 4o-mini 53건.

### 6편. Gemini 탈옥 (3.x)

| 단계 | 스크립트 | 하는 일 | 결과 |
|---|---|---|---|
| 3.1 | garak3.1_jailbreak_to_gemini.py | 1.4와 같은 프로브(DanPayload, PastTenseJudged)와 Claude 판정으로 Gemini 공격 | Garak 판정 59/200 |
| 1.5 | garak1.5_rejudge_by_claude.py | 3.1 리포트를 같은 방식으로 재판정 | HIT 17, SAFE 110, BLOCKED 31, ERROR 42 |

재판정 결과를 Claude 채팅과 사람이 다시 확인.
최종: 7/200 (3.5%). 3.8-flash 0건, 3.1-flash-lite 7건(전부 DanPayload).

## 쓰는 법
set OPENAI_API_KEY=...
set ANTHROPIC_API_KEY=...
set GEMINI_API_KEY=...
py scripts/garak1.1_jailbreak_to_gpt.py
py scripts/garak1.2_jailbreak_to_gpt_by_claude.py
py scripts/garak1.4_jailbreak_to_gpt_changed_probes.py
py scripts/garak1.5_rejudge_by_claude.py
py scripts/garak2.1_injection_to_gpt.py
py scripts/garak3.1_jailbreak_to_gemini.py

1.2, 1.4, 3.1은 Claude 키가 든 yaml을 만들었다가 실행이 끝나면 스스로 지움.

## 주의

공격 질문은 HarmBench와 공개 DAN 템플릿에서 가져옴.
로그에 유해한 요청 원문과 모델의 답변 원문이 그대로 들어 있음. 측정 목적 외에 사용 불허.
