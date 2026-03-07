import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import logging
from pathlib import Path
from typing import Dict, Tuple, List, Optional, Any
import json
from dataclasses import dataclass, asdict
from tqdm import tqdm
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize
from src.utils.config import Config, DEFAULT_CONFIG
from src.utils.visualization import PerformanceVisualizer
from src.utils.explainability import DecisionExplainer
logger = logging.getLogger(__name__)

@dataclass
class EvaluationMetrics:
    total_power_consumption: float
    average_temperature: float
    max_temperature: float
    min_temperature: float
    std_temperature: float
    safety_violations: int
    avg_fan_speed: float
    power_efficiency: float
    thermal_stability: float
    episode_reward: float
    average_pue: float
    average_health: float
    convergence_time: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
BASE_DIR = Path(__file__).resolve().parent

class BaselineController:

    def __init__(self, target_temp: float=45.0):
        self.target_temp = target_temp
        self.prev_error = 0.0
        self.integral = 0.0

    def compute_action(self, temps: np.ndarray, num_servers: int) -> np.ndarray:
        max_temp = np.max(temps)
        error = max_temp - self.target_temp
        kp, ki, kd = (0.05, 0.002, 0.01)
        self.integral += error
        self.integral = np.clip(self.integral, -100, 100)
        derivative = error - self.prev_error
        self.prev_error = error
        fan_speed = kp * error + ki * self.integral + kd * derivative
        fan_speed = np.clip(0.1 + fan_speed, 0.1, 1.0)
        return np.ones(num_servers) * fan_speed

    def reset(self):
        self.prev_error = 0.0
        self.integral = 0.0

class EvaluationRunner:

    def __init__(self, config: Config, env: Any):
        self.config = config
        self.env = env
        if hasattr(env, 'get_attr'):
            self.num_servers = env.get_attr('num_servers')[0]
        else:
            self.num_servers = 10
        self.baseline = BaselineController(target_temp=25.0)
        self.baseline_it_powers: List[float] = []
        self.baseline_cooling_powers: List[float] = []
        self.model_it_powers: List[float] = []
        self.model_cooling_powers: List[float] = []

    def evaluate_baseline(self, num_steps: int=5000) -> Tuple[List[float], List[float], List[float], EvaluationMetrics]:
        print('\n📊 Evaluating Baseline (Legacy PID) Controller...')
        obs = self.env.reset()
        rewards, temps, powers = ([], [], [])
        it_powers, cooling_powers, healths, all_actions = ([], [], [], [])
        violations = 0
        initial_temps = np.ones(self.num_servers) * self.config.physics.ambient_temp
        action = self.baseline.compute_action(initial_temps, self.num_servers)
        for _ in tqdm(range(num_steps), desc='Baseline'):
            obs, reward, done, info = self.env.step([action])
            server_temps = np.array([s['temp'] for s in info[0].get('stats', [{'temp': info[0].get('avg_temp', 25.0)}] * self.num_servers)])
            action = self.baseline.compute_action(server_temps, self.num_servers)
            rewards.append(reward[0])
            temps.append(info[0].get('max_temp', 25.0))
            powers.append(info[0].get('total_power', 0.0))
            it_powers.append(info[0].get('it_power', info[0].get('total_power', 0.0) * 0.9))
            cooling_powers.append(info[0].get('cooling_power', info[0].get('total_power', 0.0) * 0.1))
            healths.append(info[0].get('avg_health', 1.0))
            all_actions.append(np.mean(action))
            if info[0]['max_temp'] >= self.config.physics.max_temp:
                violations += 1
        metrics = self._compute_metrics(rewards, temps, powers, it_powers, cooling_powers, healths, all_actions, violations)
        self.baseline_it_powers = it_powers
        self.baseline_cooling_powers = cooling_powers
        return (rewards, temps, powers, metrics)

    def evaluate_model(self, model: PPO, num_steps: int=5000) -> Tuple[List[float], List[float], List[float], EvaluationMetrics, List[Dict]]:
        print('\n🤖 Evaluating SCARI Model...')
        obs = self.env.reset()
        t_min = self.config.physics.min_temp
        t_max = self.config.physics.max_temp
        explainer = DecisionExplainer(t_min=t_min, t_max=t_max, max_history=num_steps)
        rewards, temps, powers = ([], [], [])
        it_powers, cooling_powers, healths, all_actions = ([], [], [], [])
        decisions_log = []
        violations = 0
        for step in tqdm(range(num_steps), desc='Model'):
            action, _ = model.predict(obs, deterministic=True)
            if step % 50 == 0:
                explanation = explainer.explain_action(obs, action[0], step)
                decisions_log.append(explanation)
            obs, reward, done, info = self.env.step(action)
            rewards.append(reward[0])
            temps.append(info[0].get('max_temp', info[0].get('avg_temp', 25.0)))
            powers.append(info[0].get('total_power', 0.0))
            it_powers.append(info[0].get('it_power', info[0].get('total_power', 0.0) * 0.9))
            cooling_powers.append(info[0].get('cooling_power', info[0].get('total_power', 0.0) * 0.1))
            healths.append(info[0].get('avg_health', 1.0))
            all_actions.append(np.mean(action[0]))
            if info[0]['max_temp'] >= self.config.physics.max_temp:
                violations += 1
        metrics = self._compute_metrics(rewards, temps, powers, it_powers, cooling_powers, healths, all_actions, violations)
        self.model_it_powers = it_powers
        self.model_cooling_powers = cooling_powers
        return (rewards, temps, powers, metrics, decisions_log)

    def _compute_metrics(self, rewards, temps, powers, it_powers, cooling_powers, healths, actions, violations) -> EvaluationMetrics:
        powers_array = np.array(powers)
        it_array = np.array(it_powers)
        temps_array = np.array(temps)
        thermal_stability = 1.0 - np.std(temps_array) / (np.ptp(temps_array) + 1e-06)
        window = min(100, len(rewards) // 5)
        if window > 0:
            rolling = np.convolve(rewards, np.ones(window) / window, mode='valid')
            diffs = np.abs(np.diff(rolling))
            converged_mask = diffs < 0.01 * (np.max(np.abs(rolling)) + 1e-06)
            conv_time = int(np.argmax(converged_mask)) if converged_mask.any() else len(rewards)
        else:
            conv_time = len(rewards)
        return EvaluationMetrics(total_power_consumption=float(np.sum(powers_array)), average_temperature=float(np.mean(temps_array)), max_temperature=float(np.max(temps_array)), min_temperature=float(np.min(temps_array)), std_temperature=float(np.std(temps_array)), safety_violations=int(violations), avg_fan_speed=float(np.mean(actions)), power_efficiency=float(np.clip(1.0 - np.mean(powers_array) / 5000, 0, 1)), thermal_stability=float(np.clip(thermal_stability, 0, 1)), episode_reward=float(np.mean(rewards)), average_pue=float(np.mean(powers_array / (it_array + 1e-06))), average_health=float(np.mean(healths)), convergence_time=conv_time)

def run_evaluation():
    BASE_DIR = Path(__file__).parent.parent
    parser = argparse.ArgumentParser(description='SCARI Performance Evaluation')
    parser.add_argument('--config', type=str, default=str(BASE_DIR / 'configs/default.yaml'), help='Config path')
    parser.add_argument('--models', type=str, default=str(BASE_DIR / 'data/models/scari_final.zip'), help='Comma-separated paths to models')
    parser.add_argument('--steps', type=int, default=5000, help='Evaluation steps')
    parser.add_argument('--output', type=str, default=str(BASE_DIR / 'outputs/eval'), help='Output directory')
    parser.add_argument('--seed', type=int, default=42, help='Seed')
    args = parser.parse_args()
    from src.envs.datacenter_env import DataCenterEnv
    np.random.seed(args.seed)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    try:
        cfg = Config.from_yaml(args.config)
    except Exception:
        cfg = DEFAULT_CONFIG

    def make_env():
        return DataCenterEnv(cfg)
    env = DummyVecEnv([make_env])
    runner = EvaluationRunner(cfg, env)
    b_rewards, b_temps, b_powers, b_metrics = runner.evaluate_baseline(args.steps)
    baseline_history = {'temps': b_temps, 'powers': b_powers, 'it_powers': runner.baseline_it_powers, 'cooling_powers': runner.baseline_cooling_powers}
    model_paths = [p.strip() for p in args.models.split(',') if p.strip()]
    model_metrics_dict = {}
    model_data_dict = {}
    decisions_dict = {}
    print(f'\n🚀 Evaluating {len(model_paths)} model(s) against Baseline...')
    for m_path in model_paths:
        path = Path(m_path)
        if not path.exists():
            print(f'⚠️ Model not found: {path}')
            continue
        m_name = path.stem.replace('scari_', '').replace('_final', '').upper()
        if not m_name:
            m_name = 'SCARI'
        try:
            trained_model = PPO.load(str(path))
            print(f'\n🤖 Evaluating Model: {m_name}')
            m_r, m_t, m_p, m_m, m_d = runner.evaluate_model(trained_model, args.steps)
            model_metrics_dict[m_name] = m_m.to_dict()
            model_data_dict[m_name] = {'temps': m_t, 'powers': m_p, 'it_powers': runner.model_it_powers, 'cooling_powers': runner.model_cooling_powers}
            decisions_dict[m_name] = m_d
        except Exception as e:
            print(f'❌ Failed to evaluate model {m_name}: {e}')
    metrics_path = output_dir / 'metrics.json'
    with open(metrics_path, 'w') as f:
        json.dump({'baseline': b_metrics.to_dict(), 'models': model_metrics_dict, 'decisions': decisions_dict}, f, indent=4)
    if model_metrics_dict:
        print('\n📈 Generating Multi-Model Performance Visualizations...')
        viz = PerformanceVisualizer(str(output_dir))
        viz.create_comprehensive_dashboard(b_metrics.to_dict(), model_metrics_dict, baseline_history, model_data_dict)
        print(f"\n{'=' * 60}")
        print(f'  ✅ Evaluation complete — results in {output_dir}')
        print(f"{'=' * 60}")
        for k, v in model_metrics_dict.items():
            sav_pct = (b_metrics.total_power_consumption - v['total_power_consumption']) / b_metrics.total_power_consumption * 100
            print(f'  [{k}] Energy Savings : {sav_pct:+.1f}%')
            print(f"  [{k}] SCARI PUE      : {v.get('average_pue', 1.0):.3f}")
            print(f"  [{k}] Max Temperature: {v['max_temperature']:.1f}°C")
            print(f"  [{k}] Violations     : {v.get('safety_violations', 0)}")
            print('-' * 60)
    else:
        print('❌ No models were successfully evaluated.')
if __name__ == '__main__':
    run_evaluation()