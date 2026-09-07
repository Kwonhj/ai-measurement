# run_ragas.py — 골든셋·메타모픽 실행 + RAGAS 0.4.x 채점 (RAGAS 실측용)
# 사용법:
#   python run_ragas.py                          # 골든셋 27문항 1회
#   python run_ragas.py --repeat 3               # 반복 측정 (비결정성 확인)
#   python run_ragas.py --sheet 메타모픽          # 메타모픽 20건
#   set TOP_K=2 && python run_ragas.py --tag k2  # 설정 바꿔 재측정 (mini_rag.py 환경변수 공유)
# 준비물: 같은 폴더에 mini_rag.py, RAGAS_골든셋_RFP9건.xlsx, docs/, OPENAI_API_KEY
# 결과: results/ 아래에 실행별 CSV + 콘솔 요약. 심판·임베딩은 gpt-4o-mini + text-embedding-3-small.

import os, sys, csv, time, argparse, asyncio, statistics
import openpyxl

from ragas.llms import llm_factory
from ragas.embeddings import embedding_factory
from ragas.metrics.collections import (
    Faithfulness, AnswerRelevancy, ContextPrecision, ContextRecall,
)

import mini_rag

MODEL_JUDGE = os.environ.get("MODEL_JUDGE", "gpt-4o-mini")
XLSX = os.environ.get("GOLDEN_XLSX", "RAGAS_골든셋_RFP9건.xlsx")


def load_sheet(name):
    wb = openpyxl.load_workbook(XLSX, read_only=True)
    ws = wb[name]
    rows = list(ws.iter_rows(values_only=True))
    head, body = rows[0], rows[1:]
    if name == "골든셋":
        # ID, 유형, 질문, 정답, 근거 문서, 근거 위치, 비고
        return [{"id": r[0], "type": r[1], "q": r[2], "ref": r[3]} for r in body if r and r[0]]
    else:
        # ID, 기준 문항, 변형 유형, 변형 질문, 기대, 기대 답
        return [{"id": r[0], "type": r[2], "q": r[3], "ref": r[5], "expect": r[4]} for r in body if r and r[0]]


async def score_one(metrics, q, ans, ctxs, ref):
    fa, ar, cp, cr = metrics
    out = {}
    out["faithfulness"] = (await fa.ascore(user_input=q, response=ans, retrieved_contexts=ctxs)).value
    out["answer_relevancy"] = (await ar.ascore(user_input=q, response=ans)).value
    out["context_precision"] = (await cp.ascore(user_input=q, reference=ref, retrieved_contexts=ctxs)).value
    out["context_recall"] = (await cr.ascore(user_input=q, retrieved_contexts=ctxs, reference=ref)).value
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sheet", default="골든셋")
    ap.add_argument("--repeat", type=int, default=1)
    ap.add_argument("--tag", default="")
    args = ap.parse_args()

    items = load_sheet(args.sheet)
    from openai import AsyncOpenAI
    aclient = AsyncOpenAI()
    llm = llm_factory(MODEL_JUDGE, client=aclient)
    from ragas.embeddings import OpenAIEmbeddings
    emb = OpenAIEmbeddings(client=aclient, model=mini_rag.MODEL_EMB)
    metrics = (Faithfulness(llm=llm), AnswerRelevancy(llm=llm, embeddings=emb),
               ContextPrecision(llm=llm), ContextRecall(llm=llm))

    os.makedirs("results", exist_ok=True)
    cfg = f"cs{mini_rag.CHUNK_SIZE}_k{mini_rag.TOP_K}_{mini_rag.MODEL_GEN}"
    stamp = time.strftime("%m%d_%H%M")

    for run in range(1, args.repeat + 1):
        path = f"results/{args.sheet}_{cfg}{('_'+args.tag) if args.tag else ''}_r{run}_{stamp}.csv"
        rows, agg = [], {m: [] for m in ("faithfulness", "answer_relevancy", "context_precision", "context_recall")}
        for it in items:
            ans, ctxs, docs = mini_rag.ask(it["q"])
            try:
                sc = asyncio.run(score_one(metrics, it["q"], ans, ctxs, str(it["ref"])))
            except Exception as e:
                print(f"[채점 실패] {it['id']}: {e}")
                sc = {m: None for m in agg}
            for m, v in sc.items():
                if v is not None:
                    agg[m].append(v)
            row = {"id": it["id"], "type": it["type"], "question": it["q"],
                   "answer": ans, "reference": it["ref"], "docs": "|".join(dict.fromkeys(docs)), **sc}
            if "expect" in it:
                row["expect"] = it["expect"]
            rows.append(row)
            print(f"{it['id']}  F={sc['faithfulness']}  AR={sc['answer_relevancy']}  "
                  f"CP={sc['context_precision']}  CR={sc['context_recall']}  | {ans[:40]}")
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
        print(f"\n[{run}회차 저장] {path}")
        for m, vals in agg.items():
            if vals:
                print(f"  {m}: 평균 {statistics.mean(vals):.3f}  최소 {min(vals):.3f}  최대 {max(vals):.3f}")
        print()


if __name__ == "__main__":
    main()
