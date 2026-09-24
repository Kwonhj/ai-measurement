"""garak 리포트의 프롬프트를 그대로 다시 호출해서 응답 원문과 finish_reason 을 저장한다.
사용: py rerun_direct.py <원본 report.jsonl>
"""

import json, os, sys, time, datetime
from openai import OpenAI

MODEL = "gemini-3.8-flash"
URI = "https://generativelanguage.googleapis.com/v1beta/openai/"
PARAMS = dict(max_tokens=8000, n=1, temperature=0.7, top_p=1.0)  # garak 이 보낸 것과 동일
RUN_DIR = os.path.expanduser(r"~\.local\share\garak\garak_runs")


def call(client, text):
    for i in range(5):
        try:
            r = client.chat.completions.create(
                model=MODEL, messages=[{"role": "user", "content": text}], **PARAMS)
            c = r.choices[0] if r.choices else None
            content = (c.message.content if c and c.message else None)
            return content, (c.finish_reason if c else "no_choices"), r.usage.model_dump() if r.usage else {}
        except Exception as e:
            err = str(e)
            if "429" in err or "503" in err:
                time.sleep(5 * (i + 1)); continue
            return None, f"error: {err[:120]}", {}
    return None, "error: retry limit", {}


def main():
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        sys.exit("[중단] GEMINI_API_KEY 를 설정하세요.")
    src = sys.argv[1]
    client = OpenAI(base_url=URI, api_key=key)
    rows = [json.loads(l) for l in open(src, encoding="utf-8")]
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    tag = os.path.basename(src).split("_")[-1].replace(".report.jsonl", "")
    out = os.path.join(RUN_DIR, f"garak_{MODEL}_{stamp}_{tag}.report.jsonl")
    reasons = {}
    with open(out, "w", encoding="utf-8") as fp:
        for r in rows:
            if r.get("entry_type") == "start_run setup":
                r["rerun_note"] = f"direct API rerun of {os.path.basename(src)}"
            if r.get("entry_type") == "attempt" and r.get("status") == 2:
                text = r["prompt"]["turns"][-1]["content"]["text"]
                content, reason, usage = call(client, text)
                reasons[reason] = reasons.get(reason, 0) + 1
                r["outputs"] = [{"text": content, "lang": "en", "data_path": None, "data_type": None,
                                 "data_checksum": None, "notes": {}}] if content is not None else [None]
                r.setdefault("notes", {})
                r["notes"]["finish_reason"] = reason
                r["notes"]["usage"] = usage
                r["detector_results"] = {}
                print(f"[{r['seq']:2}] {reason:14} len={len(content or '')}  {(content or '')[:50]!r}")
            if r.get("entry_type") in ("eval", "digest"):
                continue
            if r.get("entry_type") == "attempt" and r.get("status") != 2:
                continue  # garak 은 시도마다 준비(1)/완료(2) 두 줄을 남김. 완료분만 유지
            fp.write(json.dumps(r, ensure_ascii=False) + "\n")
    print("\nfinish_reason 집계:", reasons)
    print("저장:", out)


if __name__ == "__main__":
    main()