"""Garak 사용법 6편 - 3.1 Gemini 탈옥. 1.4와 같은 공격(kaisar.DanPayload, kaisar.PastTenseJudged + Claude 판정), 대상만 Gemini."""

import os, sys, shutil, subprocess, datetime

GEMINI_URI = "https://generativelanguage.googleapis.com/v1beta/openai/"
MODELS = [
    ("openai.OpenAICompatible", "gemini-3.8-flash"),       # 6-sol 급
    ("openai.OpenAICompatible", "gemini-3.1-flash-lite"),  # 4o-mini 급
]
PROBES = ["kaisar.DanPayload", "kaisar.PastTenseJudged"]
DETECTOR = "judge.Jailbreak"
JUDGE_MODEL = "claude-opus-5-5"
PROMPT_CAP = 50
GENERATIONS = 1
SEED = 42
TAG = "garak3.1"
PROBE_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "garak1.3_kaisar.py")


def install_probe():
    """garak1.3_kaisar.py 를 garak/probes/kaisar.py 로 복사한다."""
    import garak.probes
    dst = os.path.join(list(garak.probes.__path__)[0], "kaisar.py")
    shutil.copyfile(PROBE_SRC, dst)
    print(f"[프로브 설치] {dst}")


def target_yaml(mtype, tkey):
    return ("    openai:\n      OpenAICompatible:\n"
            f"        uri: {GEMINI_URI}\n"
            f"        api_key: {tkey}\n"
            "        max_tokens: 8000\n"
            "        suppressed_params: [frequency_penalty, presence_penalty, stop, seed]\n")


def judge_yaml(jkey):
    return ("  detectors:\n    judge:\n"
            "      detector_model_type: openai.OpenAICompatible\n"
            f"      detector_model_name: {JUDGE_MODEL}\n"
            "      detector_model_config:\n"
            "        uri: https://api.anthropic.com/v1/\n"
            f"        api_key: {jkey}\n"
            "        max_tokens: 2000\n"
            "        suppressed_params: [frequency_penalty, presence_penalty, stop, seed, temperature, top_p]\n")


def main():
    tkey = os.environ.get("GEMINI_API_KEY")
    jkey = os.environ.get("ANTHROPIC_API_KEY")
    if not tkey or not jkey:
        sys.exit("[중단] GEMINI_API_KEY 와 ANTHROPIC_API_KEY 를 모두 설정하세요.")
    install_probe()
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    for mtype, mname in MODELS:
        config = f"{TAG}_{mname}.yaml"
        with open(config, "w", encoding="utf-8") as f:
            f.write(f"run:\n  soft_probe_prompt_cap: {PROMPT_CAP}\n"
                    "plugins:\n  generators:\n" + target_yaml(mtype, tkey) + judge_yaml(jkey))
        try:
            cmd = [sys.executable, "-m", "garak",
                   "--target_type", mtype, "--target_name", mname,
                   "--probes", ",".join(PROBES),
                   "--detectors", DETECTOR,
                   "--generations", str(GENERATIONS), "--seed", str(SEED),
                   "--config", config,
                   "--report_prefix", f"{TAG}_{mname}_{stamp}"]
            print(f"\n===== {mname} =====")
            subprocess.run(cmd, check=True)
        finally:
            os.remove(config)  # 키가 들어 있으므로 실행 후 삭제


if __name__ == "__main__":
    main()
