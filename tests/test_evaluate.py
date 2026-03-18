from src.evaluate import EvaluationRunner, build_realistic_baseline
from src.utils.config import Config


class FakeVecEnv:
    def __init__(self):
        self.seed_calls = []
        self.reset_calls = 0

    def seed(self, value):
        self.seed_calls.append(value)

    def reset(self):
        self.reset_calls += 1
        return "reset-ok"


def test_evaluation_runner_reseeds_environment_for_fair_comparison():
    env = FakeVecEnv()
    runner = EvaluationRunner(Config(), env, evaluation_seed=42)

    first = runner._reset_env()
    second = runner._reset_env()

    assert first == "reset-ok"
    assert second == "reset-ok"
    assert env.seed_calls == [42, 42]
    assert env.reset_calls == 2


def test_build_realistic_baseline_uses_traditional_enterprise_profile():
    cfg = Config()
    cfg.cooling.mode = "AIR"
    cfg.reward.safe_threshold = 53.0
    cfg.reward.hard_limit = 60.0
    cfg.evaluation.baseline_profile = "TRADITIONAL_ENTERPRISE"
    cfg.evaluation.baseline_target_temp = 47.0
    cfg.evaluation.baseline_min_action = 0.35

    baseline = build_realistic_baseline(cfg)

    assert baseline.controller_name == "TRADITIONAL_ENTERPRISE"
    assert baseline.strategy == "TRADITIONAL_ENTERPRISE"
    assert baseline.target_temp == 47.0
    assert baseline.min_action == 0.35
