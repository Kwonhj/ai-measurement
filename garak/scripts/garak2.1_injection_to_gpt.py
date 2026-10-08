"""Garak 사용법 5편 - 2.1 첫 공격. GPT 두 모델에 인젝션 프로브 2개, 기본 디텍터."""

import os, sys, subprocess, datetime

MODELS = [
    ("openai.OpenAIReasoningGenerator", "gpt-6-sol"),
    ("openai", "gpt-4o-mini"),
]
PROBES = ["promptinject.HijackHateHumans", "latentinjection.LatentInjectionReport"]   # 디텍터는 프로브 기본값
PROMPT_CAP = 50        # 프로브당 50발
GENERATIONS = 1
SEED = 42
TAG = "garak2.1"


def target_yaml(mtype):
    if mtype == "openai.OpenAIReasoningGenerator":
        return "    openai:\n      OpenAIReasoningGenerator:\n        max_completion_tokens: 8000\n"
    return "    openai:\n      OpenAIGenerator:\n        max_tokens: 1500\n"


def main():
    if not os.environ.get("OPENAI_API_KEY"):
        sys.exit("[중단] OPENAI_API_KEY 를 설정하세요.")
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    for mtype, mname in MODELS:
        config = f"{TAG}_{mname}.yaml"
        with open(config, "w", encoding="utf-8") as f:
            f.write(f"run:\n  soft_probe_prompt_cap: {PROMPT_CAP}\n"
                    "plugins:\n  generators:\n" + target_yaml(mtype))
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
            os.remove(config)


if __name__ == "__main__":
    main()
