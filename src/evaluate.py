import argparse
import json
import logging
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize
from tqdm import tqdm

from src.utils.config import (
    Config,
    DEFAULT_CONFIG,
    PREFERRED_CONFIG_PATH,
    get_available_config_paths,
    prompt_for_config_selection,
    resolve_config_file,
)
from src.utils.explainability import DecisionExplainer
from src.utils.visualization import PerformanceVisualizer

logger = logging.getLogger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parent.parent


def find_vecnormalize_stats_path(model_path: Path) -> Optional[Path]:
    candidates = [
        model_path.with_name(f"{model_path.stem}_vec_normalize.pkl"),
        model_path.parent / "vec_normalize.pkl",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def build_evaluation_env(config: Config, vecnormalize_path: Optional[Path] = None) -> Any:
    from src.envs.datacenter_env import DataCenterEnv

    env = DummyVecEnv([lambda: DataCenterEnv(config)])
    if vecnormalize_path is None:
        return env
    try:
        wrapped_env = VecNormalize.load(str(vecnormalize_path), env)
        wrapped_env.training = False
        wrapped_env.norm_reward = False
        logger.info("Loaded VecNormalize stats from %s", vecnormalize_path)
        return wrapped_env
    except Exception as exc:
        logger.warning("Failed to load VecNormalize stats from %s: %s", vecnormalize_path, exc)
        return env


@dataclass
class EvaluationMetrics:
    controller_name: str
    total_power_consumption: float
    total_it_power_consumption: float
    total_cooling_power_consumption: float
    average_temperature: float
    max_temperature: float
    min_temperature: float
    std_temperature: float
    safety_violations: int
    safety_override_steps: int
    safety_override_rate_percent: float
    safety_override_avg_fraction: float
    safety_override_avg_fraction_active: float
    safety_override_max_fraction: float
    avg_fan_speed: float
    power_efficiency: float
    thermal_stability: float
    episode_reward: float
    average_pue: float
    average_health: float
    convergence_time: int
    total_steps: int
    average_it_power: float
    average_cooling_power: float
    average_cooling_share: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class BaselineController:
    def __init__(
        self,
        target_temp: float = 50.0,
        min_action: float = 0.14,
        max_action: float = 1.0,
        controller_name: str = "BASELINE",
        strategy: str = "TUNED_PID",
    ):
        self.target_temp = float(target_temp)
        self.min_action = float(min_action)
        self.max_action = float(max_action)
        self.controller_name = controller_name
        self.strategy = strategy.upper()
        self.prev_error = 0.0
        self.prev_max_temp: Optional[float] = None
        self.integral = 0.0

    def compute_action(
        self,
        temps: np.ndarray,
        loads: Optional[np.ndarray],
        num_servers: int,
    ) -> np.ndarray:
        if self.strategy == "TRADITIONAL_ENTERPRISE":
            return self._compute_traditional_action(temps, loads, num_servers)
        return self._compute_tuned_pid_action(temps, loads, num_servers)

    def _compute_tuned_pid_action(
        self,
        temps: np.ndarray,
        loads: Optional[np.ndarray],
        num_servers: int,
    ) -> np.ndarray:
        max_temp = float(np.max(temps))
        avg_temp = float(np.mean(temps))
        avg_load = float(np.mean(loads)) if loads is not None and len(loads) else 0.55
        temp_rise = 0.0 if self.prev_max_temp is None else max(0.0, max_temp - self.prev_max_temp)
        error = max_temp - self.target_temp

        kp, ki, kd = (0.05, 0.001, 0.03)
        self.integral = float(np.clip(self.integral + error, -120.0, 120.0))
        derivative = error - self.prev_error
        self.prev_error = error
        self.prev_max_temp = max_temp

        base_flow = self.min_action + np.clip((avg_load - 0.35) / 0.55, 0.0, 1.0) * 0.16
        headroom_guard = np.clip((avg_temp - (self.target_temp - 7.5)) / 7.5, 0.0, 1.0) * 0.22
        ramp_guard = np.clip(temp_rise / 1.5, 0.0, 1.0) * 0.18
        fan_speed = base_flow + headroom_guard + ramp_guard + kp * error + ki * self.integral + kd * derivative

        if max_temp > self.target_temp + 2.0:
            fan_speed = max(fan_speed, 0.52)
        if max_temp > self.target_temp + 4.0:
            fan_speed = max(fan_speed, 0.72)
        if max_temp > self.target_temp + 6.0:
            fan_speed = self.max_action

        fan_speed = float(np.clip(fan_speed, self.min_action, self.max_action))
        return np.ones(num_servers, dtype=np.float32) * fan_speed

    def _compute_traditional_action(
        self,
        temps: np.ndarray,
        loads: Optional[np.ndarray],
        num_servers: int,
    ) -> np.ndarray:
        max_temp = float(np.max(temps))
        avg_temp = float(np.mean(temps))
        avg_load = float(np.mean(loads)) if loads is not None and len(loads) else 0.55
        temp_rise = 0.0 if self.prev_max_temp is None else max(0.0, max_temp - self.prev_max_temp)
        self.prev_max_temp = max_temp

        if avg_load > 0.8:
            load_bias = 0.22
        elif avg_load > 0.65:
            load_bias = 0.18
        elif avg_load > 0.5:
            load_bias = 0.14
        else:
            load_bias = 0.10

        fan_speed = self.min_action + load_bias
        fan_speed += np.clip((avg_temp - (self.target_temp - 5.5)) / 4.0, 0.0, 1.0) * 0.26
        fan_speed += np.clip((max_temp - (self.target_temp - 1.5)) / 3.0, 0.0, 1.0) * 0.34
        fan_speed += np.clip(temp_rise / 1.0, 0.0, 1.0) * 0.14

        if max_temp < self.target_temp - 2.5:
            fan_speed = max(fan_speed, self.min_action + 0.06)
        if max_temp > self.target_temp + 1.0:
            fan_speed = max(fan_speed, 0.82)
        if max_temp > self.target_temp + 2.5:
            fan_speed = max(fan_speed, 0.94)
        if max_temp > self.target_temp + 4.0:
            fan_speed = self.max_action

        fan_speed = float(np.clip(fan_speed, self.min_action, self.max_action))
        return np.ones(num_servers, dtype=np.float32) * fan_speed

    def reset(self) -> None:
        self.prev_error = 0.0
        self.prev_max_temp = None
        self.integral = 0.0


def choose_config_path(config_argument: str | None) -> Path:
    if config_argument:
        return resolve_config_file(config_argument)
    if sys.stdin.isatty() and sys.stdout.isatty():
        print(f"\nNo --config specified. Press Enter to use {PREFERRED_CONFIG_PATH.name} or choose another profile.")
        return prompt_for_config_selection(PREFERRED_CONFIG_PATH)
    return resolve_config_file(PREFERRED_CONFIG_PATH)


def print_available_configs() -> None:
    for config_path in get_available_config_paths():
        marker = " (default)" if config_path.resolve() == PREFERRED_CONFIG_PATH.resolve() else ""
        print(f"- {config_path.name}{marker}")


def build_realistic_baseline(config: Config) -> BaselineController:
    profile = getattr(config.evaluation, "baseline_profile", "TUNED_PID").upper()
    conservative_target = min(config.reward.safe_threshold - 2.5, config.reward.hard_limit - 10.0)
    conservative_target = max(config.physics.ambient_temp + 15.0, conservative_target)
    conservative_target = min(conservative_target, config.reward.hard_limit - 5.0)
    if profile in {"TRADITIONAL_ENTERPRISE", "ENTERPRISE_CRAC", "LEGACY_CRAC"}:
        default_target = min(config.reward.safe_threshold - 5.5, config.reward.hard_limit - 11.0)
        default_target = max(config.physics.ambient_temp + 12.0, default_target)
        cooling_mode = config.cooling.mode.upper()
        default_floor = {
            "AIR": 0.48,
            "LIQUID": 0.28,
            "HYBRID": 0.34,
        }.get(cooling_mode, 0.24)
        baseline_target = config.evaluation.baseline_target_temp if config.evaluation.baseline_target_temp > 0 else default_target
        baseline_min_action = config.evaluation.baseline_min_action if config.evaluation.baseline_min_action > 0 else max(default_floor, config.environment.safety_min_action + 0.18)
        baseline_max_action = max(baseline_min_action, float(config.evaluation.baseline_max_action))
        return BaselineController(
            target_temp=baseline_target,
            min_action=baseline_min_action,
            max_action=baseline_max_action,
            controller_name="TRADITIONAL_ENTERPRISE",
            strategy="TRADITIONAL_ENTERPRISE",
        )

    baseline_target = config.evaluation.baseline_target_temp if config.evaluation.baseline_target_temp > 0 else conservative_target
    baseline_min_action = config.evaluation.baseline_min_action if config.evaluation.baseline_min_action > 0 else max(0.12, config.environment.safety_min_action)
    baseline_max_action = max(baseline_min_action, float(config.evaluation.baseline_max_action))
    controller_name = "REAL_WORLD_PID" if profile == "REAL_WORLD_PID" else "BASELINE"
    return BaselineController(
        target_temp=baseline_target,
        min_action=baseline_min_action,
        max_action=baseline_max_action,
        controller_name=controller_name,
        strategy="TUNED_PID",
    )


class EvaluationRunner:
    def __init__(self, config: Config, env: Any, evaluation_seed: Optional[int] = None):
        self.config = config
        self.env = env
        self.evaluation_seed = evaluation_seed
        self.num_servers = env.get_attr("num_servers")[0] if hasattr(env, "get_attr") else 10
        self.baseline = build_realistic_baseline(config)
        self.baseline_it_powers: List[float] = []
        self.baseline_cooling_powers: List[float] = []
        self.model_it_powers: List[float] = []
        self.model_cooling_powers: List[float] = []

    def _reset_env(self) -> Any:
        if self.evaluation_seed is not None and hasattr(self.env, "seed"):
            self.env.seed(self.evaluation_seed)
        return self.env.reset()

    def _get_current_loads(self) -> Optional[np.ndarray]:
        if hasattr(self.env, "get_attr"):
            try:
                return np.array(self.env.get_attr("current_loads")[0], dtype=np.float32)
            except Exception:
                return None
        return None

    def _get_explainer_observation(self, obs: Any) -> Any:
        if hasattr(self.env, "unnormalize_obs"):
            try:
                return self.env.unnormalize_obs(np.array(obs, copy=True))
            except Exception:
                return obs
        return obs

    def evaluate_baseline(self, num_steps: int = 5000) -> Tuple[List[float], List[float], List[float], EvaluationMetrics]:
        print(
            f"\nEvaluating baseline controller: {self.baseline.controller_name} "
            f"(target={self.baseline.target_temp:.1f}C)"
        )
        self.baseline.reset()
        self._reset_env()
        return self._run_baseline_loop(num_steps)

    def _run_baseline_loop(self, num_steps: int) -> Tuple[List[float], List[float], List[float], EvaluationMetrics]:
        rewards, temps, powers, it_powers, cooling_powers = [], [], [], [], []
        healths, all_actions = [], []
        violations = 0
        override_steps = 0
        override_fractions: List[float] = []
        initial_temps = np.ones(self.num_servers, dtype=np.float32) * self.config.physics.ambient_temp
        action = self.baseline.compute_action(initial_temps, self._get_current_loads(), self.num_servers)

        for _ in tqdm(range(num_steps), desc="Baseline", leave=False):
            _, reward, _, info = self.env.step([action])
            step_info = info[0]
            server_temps = np.array(
                [s["temp"] for s in step_info.get("stats", [{"temp": step_info.get("avg_temp", 25.0)}] * self.num_servers)],
                dtype=np.float32,
            )
            action = self.baseline.compute_action(server_temps, self._get_current_loads(), self.num_servers)
            rewards.append(float(reward[0]))
            temps.append(float(step_info.get("max_temp", 25.0)))
            powers.append(float(step_info.get("total_power", 0.0)))
            it_powers.append(float(step_info.get("it_power", step_info.get("total_power", 0.0) * 0.9)))
            cooling_powers.append(float(step_info.get("cooling_power", step_info.get("total_power", 0.0) * 0.1)))
            healths.append(float(step_info.get("avg_health", 1.0)))
            all_actions.append(float(np.mean(action)))
            override_fraction = float(step_info.get("safety_override_fraction", 0.0))
            override_fractions.append(max(0.0, override_fraction))
            if step_info.get("safety_override_active", False):
                override_steps += 1
            if step_info.get("hard_limit_violation", step_info.get("max_temp", 0.0) >= self.config.reward.hard_limit):
                violations += 1

        metrics = self._compute_metrics(
            "BASELINE",
            rewards,
            temps,
            powers,
            it_powers,
            cooling_powers,
            healths,
            all_actions,
            violations,
            override_steps,
            override_fractions,
        )
        self.baseline_it_powers = it_powers
        self.baseline_cooling_powers = cooling_powers
        return rewards, temps, powers, metrics

    def evaluate_model(
        self,
        model: PPO,
        model_name: str,
        num_steps: int = 5000,
    ) -> Tuple[List[float], List[float], List[float], EvaluationMetrics, List[Dict[str, Any]]]:
        print(f"\nEvaluating trained model: {model_name}")
        obs = self._reset_env()
        explainer = DecisionExplainer(
            t_min=self.config.physics.min_temp,
            t_max=self.config.physics.max_temp,
            max_history=num_steps,
        )
        rewards, temps, powers, it_powers, cooling_powers = [], [], [], [], []
        healths, all_actions = [], []
        decisions_log: List[Dict[str, Any]] = []
        violations = 0
        override_steps = 0
        override_fractions: List[float] = []

        for step in tqdm(range(num_steps), desc=model_name, leave=False):
            action, _ = model.predict(obs, deterministic=True)
            if step % 50 == 0:
                explainer_obs = self._get_explainer_observation(obs)
                decisions_log.append(explainer.explain_action(explainer_obs, action[0], step))
            obs, reward, _, info = self.env.step(action)
            step_info = info[0]
            rewards.append(float(reward[0]))
            temps.append(float(step_info.get("max_temp", step_info.get("avg_temp", 25.0))))
            powers.append(float(step_info.get("total_power", 0.0)))
            it_powers.append(float(step_info.get("it_power", step_info.get("total_power", 0.0) * 0.9)))
            cooling_powers.append(float(step_info.get("cooling_power", step_info.get("total_power", 0.0) * 0.1)))
            healths.append(float(step_info.get("avg_health", 1.0)))
            all_actions.append(float(np.mean(action[0])))
            override_fraction = float(step_info.get("safety_override_fraction", 0.0))
            override_fractions.append(max(0.0, override_fraction))
            if step_info.get("safety_override_active", False):
                override_steps += 1
            if step_info.get("hard_limit_violation", step_info.get("max_temp", 0.0) >= self.config.reward.hard_limit):
                violations += 1

        metrics = self._compute_metrics(
            model_name,
            rewards,
            temps,
            powers,
            it_powers,
            cooling_powers,
            healths,
            all_actions,
            violations,
            override_steps,
            override_fractions,
        )
        self.model_it_powers = it_powers
        self.model_cooling_powers = cooling_powers
        return rewards, temps, powers, metrics, decisions_log

    def _compute_metrics(
        self,
        controller_name: str,
        rewards: List[float],
        temps: List[float],
        powers: List[float],
        it_powers: List[float],
        cooling_powers: List[float],
        healths: List[float],
        actions: List[float],
        violations: int,
        override_steps: int,
        override_fractions: List[float],
    ) -> EvaluationMetrics:
        powers_arr = np.array(powers, dtype=np.float64)
        temps_arr = np.array(temps, dtype=np.float64)
        it_arr = np.array(it_powers, dtype=np.float64)
        cool_arr = np.array(cooling_powers, dtype=np.float64)
        override_arr = np.array(override_fractions, dtype=np.float64)
        active_override_arr = override_arr[override_arr > 1e-6]

        thermal_stability = 1.0 - np.std(temps_arr) / (np.ptp(temps_arr) + 1e-6)
        power_efficiency = 1.0 - np.mean(cool_arr) / (np.mean(powers_arr) + 1e-6)
        convergence_time = self._estimate_convergence(rewards)
        total_steps = len(rewards)

        return EvaluationMetrics(
            controller_name=controller_name,
            total_power_consumption=float(np.sum(powers_arr)),
            total_it_power_consumption=float(np.sum(it_arr)),
            total_cooling_power_consumption=float(np.sum(cool_arr)),
            average_temperature=float(np.mean(temps_arr)),
            max_temperature=float(np.max(temps_arr)),
            min_temperature=float(np.min(temps_arr)),
            std_temperature=float(np.std(temps_arr)),
            safety_violations=int(violations),
            safety_override_steps=int(override_steps),
            safety_override_rate_percent=float((override_steps / max(total_steps, 1)) * 100.0),
            safety_override_avg_fraction=float(np.mean(override_arr) if override_arr.size else 0.0),
            safety_override_avg_fraction_active=float(np.mean(active_override_arr) if active_override_arr.size else 0.0),
            safety_override_max_fraction=float(np.max(override_arr) if override_arr.size else 0.0),
            avg_fan_speed=float(np.mean(actions)),
            power_efficiency=float(np.clip(power_efficiency, 0.0, 1.0)),
            thermal_stability=float(np.clip(thermal_stability, 0.0, 1.0)),
            episode_reward=float(np.mean(rewards) if rewards else 0.0),
            average_pue=float(np.mean(powers_arr / (it_arr + 1e-6))),
            average_health=float(np.mean(healths) if healths else 1.0),
            convergence_time=convergence_time,
            total_steps=total_steps,
            average_it_power=float(np.mean(it_arr)),
            average_cooling_power=float(np.mean(cool_arr)),
            average_cooling_share=float(np.mean(cool_arr / (powers_arr + 1e-6))),
        )

    @staticmethod
    def _estimate_convergence(rewards: List[float]) -> int:
        window = min(100, max(1, len(rewards) // 5))
        if len(rewards) <= 1 or window <= 1:
            return len(rewards)
        rolling = np.convolve(rewards, np.ones(window) / window, mode="valid")
        diffs = np.abs(np.diff(rolling))
        threshold = 0.01 * (np.max(np.abs(rolling)) + 1e-6)
        converged = diffs < threshold
        return int(np.argmax(converged)) if converged.any() else len(rewards)


def run_evaluation() -> None:
    parser = argparse.ArgumentParser(description="SCARI Performance Evaluation")
    parser.add_argument("--config", type=str, help="Config path; if omitted, default.yaml is used by default")
    parser.add_argument("--list-configs", action="store_true", help="List available YAML configs and exit")
    parser.add_argument(
        "--models",
        type=str,
        default=str(PROJECT_ROOT / "data/models/scari_final.zip"),
        help="Comma-separated paths to models",
    )
    parser.add_argument("--steps", type=int, default=5000, help="Evaluation steps")
    parser.add_argument(
        "--output",
        type=str,
        default=str(PROJECT_ROOT / "outputs/eval"),
        help="Output directory",
    )
    parser.add_argument("--seed", type=int, default=42, help="Seed")
    args = parser.parse_args()

    if args.list_configs:
        print_available_configs()
        return

    np.random.seed(args.seed)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    config_path = choose_config_path(args.config)
    try:
        cfg = Config.from_yaml(config_path)
    except Exception as exc:
        logger.error("Failed to load config %s: %s", config_path, exc)
        try:
            config_path = resolve_config_file(PREFERRED_CONFIG_PATH)
            cfg = Config.from_yaml(config_path)
        except Exception:
            cfg = DEFAULT_CONFIG

    baseline_env = build_evaluation_env(cfg)
    baseline_runner = EvaluationRunner(cfg, baseline_env, evaluation_seed=args.seed)
    _, baseline_temps, baseline_powers, baseline_metrics = baseline_runner.evaluate_baseline(args.steps)
    baseline_history = {
        "temps": baseline_temps,
        "powers": baseline_powers,
        "it_powers": baseline_runner.baseline_it_powers,
        "cooling_powers": baseline_runner.baseline_cooling_powers,
    }
    if hasattr(baseline_env, "close"):
        baseline_env.close()

    model_paths = [item.strip() for item in args.models.split(",") if item.strip()]
    model_metrics_dict: Dict[str, Dict[str, Any]] = {}
    model_data_dict: Dict[str, Dict[str, List[float]]] = {}
    decisions_dict: Dict[str, List[Dict[str, Any]]] = {}

    print(f"\nEvaluating {len(model_paths)} model(s) against {baseline_metrics.controller_name}...")
    for model_path in model_paths:
        path = Path(model_path)
        if not path.exists():
            print(f"Model not found: {path}")
            continue
        model_name = path.stem.replace("scari_", "").replace("_final", "").upper() or "SCARI"
        vecnormalize_path = find_vecnormalize_stats_path(path)
        model_env = build_evaluation_env(cfg, vecnormalize_path)
        model_runner = EvaluationRunner(cfg, model_env, evaluation_seed=args.seed)
        try:
            trained_model = PPO.load(str(path))
            model_rewards, model_temps, model_powers, model_metrics, decisions = model_runner.evaluate_model(
                trained_model, model_name=model_name, num_steps=args.steps,
            )
            model_metrics_dict[model_name] = model_metrics.to_dict()
            model_data_dict[model_name] = {
                "temps": model_temps,
                "powers": model_powers,
                "it_powers": model_runner.model_it_powers,
                "cooling_powers": model_runner.model_cooling_powers,
            }
            decisions_dict[model_name] = decisions
        except Exception as exc:
            print(f"Failed to evaluate model {model_name}: {exc}")
        finally:
            if hasattr(model_env, "close"):
                model_env.close()

    metrics_path = output_dir / "metrics.json"
    with metrics_path.open("w", encoding="utf-8") as handle:
        json.dump(
            {
                "metadata": {
                    "config": str(config_path),
                    "seed": args.seed,
                    "baseline_controller": baseline_metrics.controller_name,
                },
                "baseline": baseline_metrics.to_dict(),
                "models": model_metrics_dict,
                "decisions": decisions_dict,
            },
            handle,
            indent=4,
        )

    if not model_metrics_dict:
        print("No models were successfully evaluated.")
        return

    print("\nGenerating performance visualizations...")
    visualizer = PerformanceVisualizer(str(output_dir))
    visualizer.create_comprehensive_dashboard(
        baseline_metrics.to_dict(),
        model_metrics_dict,
        baseline_history,
        model_data_dict,
    )

    print(f"\n{'=' * 60}")
    print(f"Evaluation complete - results in {output_dir}")
    print(f"{'=' * 60}")
    print(
        f"Baseline reference : {baseline_metrics.controller_name} "
        f"(target {baseline_runner.baseline.target_temp:.1f}C, PUE {baseline_metrics.average_pue:.3f})"
    )
    for name, metrics in model_metrics_dict.items():
        energy_savings = (
            (baseline_metrics.total_power_consumption - metrics["total_power_consumption"])
            / max(baseline_metrics.total_power_consumption, 1e-6)
            * 100
        )
        print(f"  [{name}] Total savings   : {energy_savings:+.1f}%")
        print(f"  [{name}] SCARI PUE       : {metrics.get('average_pue', 1.0):.3f}")
        print(f"  [{name}] Avg / Max temp  : {metrics['average_temperature']:.1f}C / {metrics['max_temperature']:.1f}C")
        print(f"  [{name}] Violations      : {metrics.get('safety_violations', 0)}")
        print(
            f"  [{name}] Override use    : "
            f"{metrics.get('safety_override_rate_percent', 0.0):.1f}% steps, "
            f"avg +{metrics.get('safety_override_avg_fraction_active', 0.0) * 100:.1f}% when active"
        )
        print("-" * 60)


if __name__ == "__main__":
    run_evaluation()
