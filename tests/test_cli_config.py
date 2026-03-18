from types import SimpleNamespace

import src.evaluate as evaluate_module
import src.train as train_module
from src.utils.config import Config


class _FakeTTY:
    def __init__(self, interactive: bool):
        self._interactive = interactive

    def isatty(self) -> bool:
        return self._interactive


def test_evaluate_uses_default_config_when_stdout_is_not_interactive(monkeypatch):
    monkeypatch.setattr(evaluate_module.sys, "stdin", _FakeTTY(True))
    monkeypatch.setattr(evaluate_module.sys, "stdout", _FakeTTY(False))
    config_path = evaluate_module.choose_config_path(None)
    assert config_path.name == "default.yaml"


def test_train_uses_default_config_when_stdout_is_not_interactive(monkeypatch):
    monkeypatch.setattr(train_module.sys, "stdin", _FakeTTY(True))
    monkeypatch.setattr(train_module.sys, "stdout", _FakeTTY(False))
    config_path = train_module.choose_config_path(None)
    assert config_path.name == "default.yaml"


def test_apply_training_overrides_preserves_yaml_profile_when_not_provided():
    cfg = Config.from_yaml("configs/default.yaml")
    args = SimpleNamespace(timesteps=None, profile=None, cooling_mode="AIR")
    updated = train_module.apply_training_overrides(cfg, args)
    assert updated.reward.profile == "TOTAL_POWER_TARGET_20"


def test_apply_training_overrides_can_override_profile_label():
    cfg = Config.from_yaml("configs/default.yaml")
    args = SimpleNamespace(timesteps=None, profile="EXPERIMENT_A", cooling_mode="AIR")
    updated = train_module.apply_training_overrides(cfg, args)
    assert updated.reward.profile == "EXPERIMENT_A"


def test_default_profile_loads_evaluation_baseline_settings():
    cfg = Config.from_yaml("configs/default.yaml")
    assert cfg.evaluation.baseline_profile == "TRADITIONAL_ENTERPRISE"
    assert cfg.evaluation.baseline_target_temp == 47.0
    assert cfg.evaluation.baseline_min_action == 0.52
