# AI 품질 측정 실측

AI 품질 측정 도구를 하나씩 직접 설치하고 돌려서, 화면과 숫자를 남기는 기록입니다.
글은 링크드인 아티클로 연재하고, 코드, 골든셋, 측정 결과, 코퍼스는 여기에 둡니다.

## 연재

| 도구 | 무엇을 측정하나 | 폴더 | 상태 |
| --- | --- | --- | --- |
| RAGAS | RAG의 신뢰성. 검색이 맞았는지, 근거로만 답했는지 | `ragas/` | 연재 완료 |
| Garak | 강건성. 인젝션과 탈옥 공격에 뚫리는지 | `garak/` | 연재 중 |
| Langfuse | 추적성. 호출 체인이 기록되는지 | `langfuse/` | 예정 |
| AgentDojo | 통제성. Agent가 유발 상황에서 멈추는지 | `agentdojo/` | 예정 |

## RAGAS 사용법

나라장터 RFP 9건으로 미니 RAG를 만들고, 골든셋 27문항으로 측정하고 개선한 7편.

1. [좋은 RAG란?](https://lnkd.in/p/gpSNdZGs)
2. [미니 RAG 구축](https://lnkd.in/p/gA28JRGe)
3. [골든셋 작성](https://lnkd.in/p/ggvwrGHJ)
4. [RAGAS 설치와 실행](https://lnkd.in/p/gwZaNYXH) 
5. [측정결과 분석](https://lnkd.in/p/gjGh8ZWt) 
- [번외. 채점방식을 알면 보이는 것](https://lnkd.in/p/gGVeAktr) 
6. [RAG 개선](https://lnkd.in/p/gpgDD5y3)

재료는 [`ragas/`](ragas/)에 있습니다.

## Garak 사용법

GPT 두 모델에 탈옥 공격 200발을 쏘고, 판정이 맞는지 끝까지 확인한 4편.

1. .[강건한 LLM이란](https://lnkd.in/p/gqcs2w7U).
2. .[설치와 구조](https://lnkd.in/p/gpmbw3ch).
3. .[탄약 일발 장전](https://lnkd.in/p/g_MbBfp6).
4. .[1차 공격, GPT 탈옥](https://lnkd.in/p/gQwQx7wy).

재료는 [`garak/`](garak/)에 있습니다.

## 저자

권혁재. 정보관리기술사. [LinkedIn](https://www.linkedin.com/in/jacekwon)
