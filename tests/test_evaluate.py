from src.evaluate import EvaluationRunner
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
