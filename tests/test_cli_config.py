from types import SimpleNamespace

import src.evaluate as evaluate_module
import src.train as train_module


class _FakeTTY:
    def __init__(self, interactive: bool):
        self._interactive = interactive

    def isatty(self) -> bool:
        return self._interactive


def test_evaluate_uses_default_config_when_stdout_is_not_interactive(monkeypatch):
    monkeypatch.setattr(evaluate_module.sys, "stdin", _FakeTTY(True))
    monkeypatch.setattr(evaluate_module.sys, "stdout", _FakeTTY(False))
    config_path = evaluate_module.choose_config_path(None)
    assert config_path.name == "optimized.yaml"


def test_train_uses_default_config_when_stdout_is_not_interactive(monkeypatch):
    monkeypatch.setattr(train_module.sys, "stdin", _FakeTTY(True))
    monkeypatch.setattr(train_module.sys, "stdout", _FakeTTY(False))
    config_path = train_module.choose_config_path(None)
    assert config_path.name == "optimized.yaml"
