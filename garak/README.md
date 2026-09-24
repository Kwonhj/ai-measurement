# garak 강건성 실측

garak 으로 상용 LLM 4종의 강건성을 실측한 기록입니다.
공격은 탈옥(DAN, 과거형), 간접 인젝션, 직접 인젝션 네 가지이고,
채점은 claude-opus-5-5 를 심판으로 세워 다시 했습니다.

## 대상

| 모델 | 세대 |
|---|---|
| gpt-6-sol | 신형 |
| gpt-4o-mini | 구형 |
| gemini-3.8-flash | 신형 |
| gemini-3.1-flash-lite | 구형 |

## 폴더

- `scripts/` 실행기와 재채점 도구
- `probes/` 직접 만든 프로브. garak 의 probes 폴더에 넣고 씁니다
- `generators/` 생성기 설정 샘플과 garak 수정분
- `logs/` 모델별 원본 리포트와 채점 결과

## 쓰는 법
set GEMINI_API_KEY=...
set ANTHROPIC_API_KEY=...
py scripts/gemini_garak.py
py scripts/rejudge.py gemini-3.8-flash_*


## 주의

측정에 쓴 질문은 HarmBench 와 공개 DAN 템플릿에서 가져왔습니다.
로그에 유해한 요청 원문이 그대로 들어 있습니다. 측정 목적 외에 쓰지 마십시오.
