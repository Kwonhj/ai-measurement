"""KAISAR 실측용 프로브 (judge.Jailbreak 채점용)"""

import json
import random

import garak.probes
from garak import _config
from garak.attempt import Attempt
from garak.data import path as data_path
from garak.probes.phrasing import PastTense

PLACEHOLDER = "[INSERT PROMPT HERE]"
N_PROMPTS = 50
PAIR_SEED = 42


class DanPayload(garak.probes.Probe):
    """DAN 탈옥 문장 + 해로운 요청"""

    lang = "en"
    primary_detector = "judge.Jailbreak"
    tags = ["payload:jailbreak"]
    goal = "get harmful content by wrapping a harmful request in a DAN jailbreak"
    tier = garak.probes.Tier.OF_CONCERN
    active = True
    doc_uri = "https://arxiv.org/html/2308.03825"

    def __init__(self, config_root=_config):
        super().__init__(config_root=config_root)
        with open(data_path / "inthewild_jailbreak_llms.json", encoding="utf-8") as f:
            templates = [t for t in json.load(f) if PLACEHOLDER in t]
        with open(data_path / "harmbench" / "harmbench_prompts.txt", encoding="utf-8") as f:
            behaviors = [line.strip() for line in f if line.strip()]
        rng = random.Random(PAIR_SEED)
        templates = rng.sample(templates, N_PROMPTS)
        behaviors = rng.sample(behaviors, N_PROMPTS)
        self.prompts = [t.replace(PLACEHOLDER, b) for t, b in zip(templates, behaviors)]
        self.goals = behaviors

    def _attempt_prestore_hook(self, attempt: Attempt, seq: int) -> Attempt:
        attempt.notes["attack_goal"] = self.goals[seq]
        return attempt


class PastTenseJudged(PastTense):
    """과거형 탈옥 (채점자에게 실제 질문 전달)"""

    primary_detector = "judge.Jailbreak"
    active = True

    def _attempt_prestore_hook(self, attempt: Attempt, seq: int) -> Attempt:
        attempt = super()._attempt_prestore_hook(attempt, seq)
        attempt.notes["attack_goal"] = self.prompts[seq]
        return attempt