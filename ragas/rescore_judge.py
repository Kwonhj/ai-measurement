# rescore_judge.py — 기존 결과 CSV의 답변은 그대로 두고 심판만 바꿔 재채점 (신뢰성 Part-2 2편 실측용)
# 사용법:
#   set GEMINI_API_KEY=... && python rescore_judge.py results/골든셋_cs800_k4_gpt-4o-mini_r1_0905_2023.csv
#   python rescore_judge.py results/메타모픽_cs800_k4_gpt-4o-mini_r1_0906_1423.csv --judge gemini-2.5-flash
# 동작: 파일명에서 cs/k 설정을 읽어 같은 인덱스로 검색 청크를 복원 → CSV의 answer 그대로 → 지정 심판으로 4개 지표 재채점
# 결과: results/rescore_<원본명>_<심판>_<시각>.csv (기존 점수, 새 점수, 차이) + 콘솔 요약
# 주의: 청크는 저장돼 있지 않아 검색을 다시 돌려 복원한다. 같은 설정이면 같은 청크가 나온다. 임베딩(text-embedding-3-small)은 그대로.

import os, sys, re, csv, time, argparse, asyncio, statistics

ap = argparse.ArgumentParser()
ap.add_argument("csv")
ap.add_argument("--judge", default="gemini-2.5-flash")
ap.add_argument("--base-url", default="https://generativelanguage.googleapis.com/v1beta/openai/")
ap.add_argument("--key-env", default="GEMINI_API_KEY")
ap.add_argument("--cs", default=None)
ap.add_argument("--k", default=None)
args = ap.parse_args()

# 파일명에서 설정 복원 → mini_rag가 import 시점에 읽으므로 먼저 세팅
m = re.search(r"_cs(\d+)_k(\d+)_", os.path.basename(args.csv))
cs = args.cs or (m.group(1) if m else "800")
k  = args.k  or (m.group(2) if m else "4")
print(f"[설정] CHUNK_SIZE={cs} TOP_K={k}")
os.environ["CHUNK_SIZE"], os.environ["TOP_K"] = cs, k

import mini_rag
from openai import AsyncOpenAI
from ragas.llms import llm_factory
from ragas.embeddings import OpenAIEmbeddings
from ragas.metrics.collections import Faithfulness, AnswerRelevancy, ContextPrecision, ContextRecall

METRICS = ("faithfulness", "answer_relevancy", "context_precision", "context_recall")

judge_client = AsyncOpenAI(api_key=os.environ[args.key_env], base_url=args.base_url)
llm = llm_factory(args.judge, client=judge_client, max_tokens=4096)
emb = OpenAIEmbeddings(client=AsyncOpenAI(), model=mini_rag.MODEL_EMB)   # 임베딩은 기존 그대로
metrics = (Faithfulness(llm=llm), AnswerRelevancy(llm=llm, embeddings=emb),
           ContextPrecision(llm=llm), ContextRecall(llm=llm))


async def score_one(q, ans, ctxs, ref):
    fa, ar, cp, cr = metrics
    return {
        "faithfulness": (await fa.ascore(user_input=q, response=ans, retrieved_contexts=ctxs)).value,
        "answer_relevancy": (await ar.ascore(user_input=q, response=ans)).value,
        "context_precision": (await cp.ascore(user_input=q, reference=ref, retrieved_contexts=ctxs)).value,
        "context_recall": (await cr.ascore(user_input=q, retrieved_contexts=ctxs, reference=ref)).value,
    }


def f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


rows = list(csv.DictReader(open(args.csv, encoding="utf-8-sig")))
v, chunks = mini_rag.build_index()
tag = args.judge.replace("/", "-")
out_path = f"results/rescore_{os.path.splitext(os.path.basename(args.csv))[0]}_{tag}_{time.strftime('%m%d_%H%M')}.csv"

out, old_agg, new_agg = [], {k: [] for k in METRICS}, {k: [] for k in METRICS}
for r in rows:
    ctx_objs = mini_rag.retrieve(r["question"], v, chunks)
    ctxs = [c["text"] for c in ctx_objs]
    docs_now = "|".join(dict.fromkeys(c["doc"] for c in ctx_objs))
    if docs_now != r.get("docs", ""):
        print(f"[주의] {r['id']} 검색 문서가 원본과 다르다: {r.get('docs')} -> {docs_now}")
    sc = None
    for attempt in (1, 2):
        try:
            sc = asyncio.run(score_one(r["question"], r["answer"], ctxs, str(r["reference"])))
            break
        except Exception as e:
            print(f"[채점 실패 {attempt}회차] {r['id']}: {type(e).__name__}: {e!r}")
    if sc is None:
        sc = {k: None for k in METRICS}
    row = {"id": r["id"], "type": r["type"], "question": r["question"], "answer": r["answer"], "docs": docs_now}
    for k in METRICS:
        o, n = f(r.get(k)), sc[k]
        row[f"{k}_old"], row[f"{k}_new"] = o, n
        row[f"{k}_diff"] = (None if o is None or n is None else round(n - o, 3))
        if o is not None: old_agg[k].append(o)
        if n is not None: new_agg[k].append(n)
    if "expect" in r:
        row["expect"] = r["expect"]
    out.append(row)
    print(f"{r['id']}  F {row['faithfulness_old']}→{row['faithfulness_new']}  "
          f"AR {row['answer_relevancy_old']}→{row['answer_relevancy_new']}  "
          f"CP {row['context_precision_old']}→{row['context_precision_new']}  "
          f"CR {row['context_recall_old']}→{row['context_recall_new']}")

with open(out_path, "w", newline="", encoding="utf-8-sig") as fh:
    w = csv.DictWriter(fh, fieldnames=list(out[0].keys()))
    w.writeheader(); w.writerows(out)

print(f"\n[저장] {out_path}   심판: gpt-4o-mini → {args.judge}   문항 {len(out)}")
for k in METRICS:
    o, n = old_agg[k], new_agg[k]
    if o and n:
        flips = sum(1 for r in out if r[f"{k}_diff"] is not None and abs(r[f"{k}_diff"]) >= 0.5)
        print(f"  {k:18s} 평균 {statistics.mean(o):.3f} → {statistics.mean(n):.3f}   "
              f"0.5 이상 움직인 문항 {flips}개")
