from pathlib import Path

import pytest

from src.evaluate import EvaluationRunner, build_realistic_baseline, find_vecnormalize_stats_path
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


def test_find_vecnormalize_stats_path_prefers_model_specific_file(monkeypatch):
    model_path = Path("C:/fake/models/scari_liquid.zip")
    shared_stats = model_path.parent / "vec_normalize.pkl"
    model_stats = model_path.with_name("scari_liquid_vec_normalize.pkl")

    def fake_exists(self):
        return self in {shared_stats, model_stats}

    monkeypatch.setattr(type(model_path), "exists", fake_exists)

    assert find_vecnormalize_stats_path(model_path) == model_stats


def test_find_vecnormalize_stats_path_falls_back_to_shared_file(monkeypatch):
    model_path = Path("C:/fake/models/scari_default.zip")
    shared_stats = model_path.parent / "vec_normalize.pkl"

    def fake_exists(self):
        return self == shared_stats

    monkeypatch.setattr(type(model_path), "exists", fake_exists)

    assert find_vecnormalize_stats_path(model_path) == shared_stats


def test_compute_metrics_reports_safety_override_usage():
    runner = EvaluationRunner(Config(), FakeVecEnv(), evaluation_seed=42)

    metrics = runner._compute_metrics(
        controller_name="SCARI",
        rewards=[1.0, 0.5, 0.2],
        temps=[50.0, 51.0, 52.0],
        powers=[900.0, 910.0, 920.0],
        it_powers=[700.0, 705.0, 710.0],
        cooling_powers=[120.0, 118.0, 116.0],
        healths=[1.0, 0.99, 0.98],
        actions=[0.2, 0.25, 0.3],
        violations=0,
        override_steps=2,
        override_fractions=[0.0, 0.1, 0.2],
    )

    assert metrics.safety_override_steps == 2
    assert metrics.safety_override_rate_percent == pytest.approx(66.66666666666666)
    assert metrics.safety_override_avg_fraction == pytest.approx(0.1)
    assert metrics.safety_override_avg_fraction_active == pytest.approx(0.15)
    assert metrics.safety_override_max_fraction == pytest.approx(0.2)
