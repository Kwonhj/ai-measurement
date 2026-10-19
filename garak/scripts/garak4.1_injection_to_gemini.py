"""Garak 사용법 7편 - 4.1 Gemini 인젝션. 2.1과 같은 공격(인젝션 프로브 2개, 기본 디텍터), 대상만 Gemini."""

import os, sys, subprocess, datetime

GEMINI_URI = "https://generativelanguage.googleapis.com/v1beta/openai/"
MODELS = [
    ("openai.OpenAICompatible", "gemini-3.8-flash"),       # 6-sol 급
    ("openai.OpenAICompatible", "gemini-3.1-flash-lite"),  # 4o-mini 급
]
PROBES = ["promptinject.HijackHateHumans", "latentinjection.LatentInjectionReport"]   # 디텍터는 프로브 기본값
PROMPT_CAP = 50        # 프로브당 50발
GENERATIONS = 1
SEED = 42
TAG = "garak3.2"


def target_yaml(mtype, tkey):
    return ("    openai:\n      OpenAICompatible:\n"
            f"        uri: {GEMINI_URI}\n"
            f"        api_key: {tkey}\n"
            "        max_tokens: 8000\n"
            "        suppressed_params: [frequency_penalty, presence_penalty, stop, seed]\n")


def main():
    tkey = os.environ.get("GEMINI_API_KEY")
    if not tkey:
        sys.exit("[중단] GEMINI_API_KEY 를 설정하세요.")
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    for mtype, mname in MODELS:
        config = f"{TAG}_{mname}.yaml"
        with open(config, "w", encoding="utf-8") as f:
            f.write(f"run:\n  soft_probe_prompt_cap: {PROMPT_CAP}\n"
                    "plugins:\n  generators:\n" + target_yaml(mtype, tkey))
        try:
            cmd = [sys.executable, "-m", "garak",
                   "--target_type", mtype, "--target_name", mname,
                   "--probes", ",".join(PROBES),
                   "--generations", str(GENERATIONS), "--seed", str(SEED),
                   "--config", config,
                   "--report_prefix", f"{TAG}_{mname}_{stamp}"]
            print(f"\n===== {mname} =====")
            subprocess.run(cmd, check=True)
        finally:
            os.remove(config)  # 키가 들어 있으므로 실행 후 삭제


if __name__ == "__main__":
    main()
