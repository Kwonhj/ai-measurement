# mini_rag.py — RFP 9건 미니 RAG (RAGAS 실측용)
# 사용법:
#   1) 이 파일과 같은 폴더에 docs/ 를 만들고 RFP PDF·TXT 9건을 넣는다
#   2) set OPENAI_API_KEY=sk-...   (PowerShell: $env:OPENAI_API_KEY="sk-...")
#   3) python mini_rag.py "2026년 사업의 예산은 얼마인가"
# 설정은 환경변수로 바꾼다: CHUNK_SIZE(기본 800), CHUNK_OVERLAP(150), TOP_K(4), MODEL_GEN(gpt-4o-mini)
# 인덱스는 .cache/ 에 저장되고, CHUNK_SIZE·CHUNK_OVERLAP이 바뀌면 자동 재구축한다.

import os, sys, json, glob, hashlib
import numpy as np
from openai import OpenAI

DOCS_DIR = os.environ.get("DOCS_DIR", "docs")
CHUNK_SIZE = int(os.environ.get("CHUNK_SIZE", "800"))
CHUNK_OVERLAP = int(os.environ.get("CHUNK_OVERLAP", "150"))
TOP_K = int(os.environ.get("TOP_K", "4"))
MODEL_GEN = os.environ.get("MODEL_GEN", "gpt-4o-mini")
MODEL_EMB = os.environ.get("MODEL_EMB", "text-embedding-3-small")
CACHE = ".cache"

client = OpenAI()

SYSTEM = (
    "너는 제안요청서(RFP) 문서만을 근거로 답하는 조수다. "
    "아래 문맥에 근거가 있으면 그 내용만으로 간결하게 답한다. "
    "문맥에 근거가 없으면 반드시 '문서에 없음'이라고만 답한다. "
    "문맥 밖의 지식으로 추측하지 않는다."
)


def read_text(path: str) -> str:
    if path.lower().endswith(".pdf"):
        from pypdf import PdfReader
        try:
            return "\n".join((p.extract_text() or "") for p in PdfReader(path).pages)
        except Exception as e:
            print(f"[경고] PDF 추출 실패, 텍스트로 재시도: {path} ({e})")
    # PDF가 아니거나 추출 실패 시 텍스트로 읽는다 (09번 대비)
    with open(path, "rb") as f:
        return f.read().decode("utf-8", "ignore")


def chunk(text: str, size: int, overlap: int):
    text = " ".join(text.split())
    out, i = [], 0
    while i < len(text):
        out.append(text[i:i + size])
        i += size - overlap
    return out


def embed(texts, batch=100):
    vecs = []
    for i in range(0, len(texts), batch):
        r = client.embeddings.create(model=MODEL_EMB, input=texts[i:i + batch])
        vecs += [d.embedding for d in r.data]
    v = np.array(vecs, dtype=np.float32)
    return v / np.linalg.norm(v, axis=1, keepdims=True)


def build_index():
    files = sorted(glob.glob(os.path.join(DOCS_DIR, "*")))
    if not files:
        sys.exit(f"[오류] {DOCS_DIR}/ 에 문서가 없다.")
    key = hashlib.md5(f"{CHUNK_SIZE}-{CHUNK_OVERLAP}-{MODEL_EMB}-{'|'.join(files)}".encode()).hexdigest()[:10]
    os.makedirs(CACHE, exist_ok=True)
    npz, meta = os.path.join(CACHE, f"idx_{key}.npz"), os.path.join(CACHE, f"idx_{key}.jsonl")
    if os.path.exists(npz):
        chunks = [json.loads(l) for l in open(meta, encoding="utf-8")]
        return np.load(npz)["v"], chunks
    chunks = []
    for f in files:
        for c in chunk(read_text(f), CHUNK_SIZE, CHUNK_OVERLAP):
            chunks.append({"doc": os.path.basename(f), "text": c})
    print(f"[인덱스] 문서 {len(files)}건 → 청크 {len(chunks)}개 임베딩 중...")
    v = embed([c["text"] for c in chunks])
    np.savez_compressed(npz, v=v)
    with open(meta, "w", encoding="utf-8") as f:
        for c in chunks:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    return v, chunks


def retrieve(query: str, v, chunks, k=TOP_K):
    q = embed([query])[0]
    idx = np.argsort(v @ q)[::-1][:k]
    return [chunks[i] for i in idx]


def answer(query: str, contexts):
    ctx = "\n\n".join(f"[{c['doc']}]\n{c['text']}" for c in contexts)
    r = client.chat.completions.create(
        model=MODEL_GEN,
        temperature=0,
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": f"문맥:\n{ctx}\n\n질문: {query}"},
        ],
    )
    return r.choices[0].message.content.strip()


def ask(query: str):
    v, chunks = build_index()
    ctxs = retrieve(query, v, chunks)
    return answer(query, ctxs), [c["text"] for c in ctxs], [c["doc"] for c in ctxs]


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit('사용법: python mini_rag.py "질문"')
    ans, ctxs, docs = ask(sys.argv[1])
    print("\n[검색 문서]", ", ".join(dict.fromkeys(docs)))
    print("[답변]", ans)
