# src/cli/evaluate.py
#!/usr/bin/env python3
"""
S.C.A.R.I. - Evaluation Module
Evaluates trained models and compares with baseline PID controller.
"""

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

logger = logging.getLogger(__name__)

@dataclass
class EvaluationMetrics:
    """Container for high-fidelity performance metrics."""
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

class BaselineController:
    """Realistic PID-based baseline controller representing modern datacenter operations."""
    
    def __init__(self, target_temp: float = 30.0):
        self.target_temp = target_temp  # Industry standard: 27-32°C
        self.prev_error = 0.0
        self.integral = 0.0
    
    def compute_action(self, temps: np.ndarray, num_servers: int) -> np.ndarray:
        """Compute realistic PID-based cooling action."""
        max_temp = np.max(temps)
        error = max_temp - self.target_temp
        
        kp, ki, kd = 0.05, 0.002, 0.01
        self.integral += error
        self.integral = np.clip(self.integral, -100, 100)
        
        derivative = error - self.prev_error
        self.prev_error = error
        
        fan_speed = kp * error + ki * self.integral + kd * derivative
        # Modern datacenter: 40% minimum for airflow, up to 100% max
        fan_speed = np.clip(0.4 + fan_speed, 0.4, 1.0)
        
        return np.ones(num_servers) * fan_speed
    
    def reset(self):
        self.prev_error = 0.0
        self.integral = 0.0

class EvaluationRunner:
    """Runs evaluation episodes and collects metrics for SCARI-v2."""
    
    def __init__(self, config: Config, env: Any):
        self.config = config
        self.env = env
        # Get num_servers from env attributes
        if hasattr(env, 'get_attr'):
            self.num_servers = env.get_attr('num_servers')[0]
        else:
            self.num_servers = 10
        self.baseline = BaselineController(target_temp=25.0)
    
    def evaluate_baseline(self, num_steps: int = 5000) -> Tuple[List[float], List[float], List[float], EvaluationMetrics]:
        print("\n📊 Evaluating Baseline (Legacy PID) Controller...")
        obs = self.env.reset()
        
        rewards, temps, powers = [], [], []
        it_powers, cooling_powers, healths, all_actions = [], [], [], []
        violations = 0
        
        for _ in tqdm(range(num_steps), desc="Baseline"):
            # Observations for Baseline are un-normalized (from env internally or slice them)
            # In SCARI-v2 env returns normalized, so we might need a way to get raw temps
            # OR we assuming baseline sees normalized too? Legacy doesn't.
            # For simplicity in this sim, we use the raw values if env provides them in info
            # or we reverse normalization. 
            # Actually, the BaselineController here expects raw temps.
            
            # Since evaluate.py is for the user, let's ensure we get metrics from info
            action = self.baseline.compute_action(np.array([25.0]*self.num_servers), self.num_servers) # Dummy start
            
            # Re-stepping to get real temps from info
            obs, reward, done, info = self.env.step([action])
            
            # Actual temps from info (reliable)
            server_temps = np.array([s['temp'] for s in info[0].get('stats', [{'temp': info[0]['avg_temp']}]*self.num_servers)])
            action = self.baseline.compute_action(server_temps, self.num_servers)
            
            rewards.append(reward[0])
            temps.append(info[0]['max_temp'])
            powers.append(info[0]['total_power'])
            it_powers.append(info[0].get('it_power', info[0]['total_power'] * 0.9))
            cooling_powers.append(info[0].get('cooling_power', info[0]['total_power'] * 0.1))
            healths.append(info[0].get('avg_health', 1.0))
            all_actions.append(np.mean(action))
            
            if info[0]['max_temp'] >= self.config.physics.max_temp:
                violations += 1
            
        metrics = self._compute_metrics(rewards, temps, powers, it_powers, cooling_powers, healths, all_actions, violations)
        return rewards, temps, powers, metrics

    def evaluate_model(self, model: PPO, num_steps: int = 5000) -> Tuple[List[float], List[float], List[float], EvaluationMetrics]:
        print("\n🤖 Evaluating SCARI-v2 Model...")
        obs = self.env.reset()
            
        rewards, temps, powers = [], [], []
        it_powers, cooling_powers, healths, all_actions = [], [], [], []
        violations = 0
       
        for _ in tqdm(range(num_steps), desc="Model"):
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, done, info = self.env.step(action)
            
            rewards.append(reward[0])
            temps.append(info[0].get('max_temp', info[0]['avg_temp']))
            powers.append(info[0]['total_power'])
            it_powers.append(info[0].get('it_power', info[0]['total_power'] * 0.9))
            cooling_powers.append(info[0].get('cooling_power', info[0]['total_power'] * 0.1))
            healths.append(info[0].get('avg_health', 1.0))
            all_actions.append(np.mean(action[0]))
            
            if info[0]['max_temp'] >= self.config.physics.max_temp:
                violations += 1
        
        metrics = self._compute_metrics(rewards, temps, powers, it_powers, cooling_powers, healths, all_actions, violations)
        return rewards, temps, powers, metrics
    
    def _compute_metrics(self, rewards, temps, powers, it_powers, cooling_powers, healths, actions, violations) -> EvaluationMetrics:
        powers_array = np.array(powers)
        it_array = np.array(it_powers)
        
        thermal_stability = 1.0 - (np.std(temps) / (np.max(temps) - np.min(temps) + 1e-6))
        
        return EvaluationMetrics(
            total_power_consumption=float(np.sum(powers_array)),
            average_temperature=float(np.mean(temps)),
            max_temperature=float(np.max(temps)),
            min_temperature=float(np.min(temps)),
            std_temperature=float(np.std(temps)),
            safety_violations=int(violations),
            avg_fan_speed=float(np.mean(actions)),
            power_efficiency=float(np.clip(1.0 - (np.mean(powers_array)/5000), 0, 1)),
            thermal_stability=float(np.clip(thermal_stability, 0, 1)),
            episode_reward=float(np.mean(rewards)),
            average_pue=float(np.mean(powers_array / (it_array + 1e-6))),
            average_health=float(np.mean(healths)),
            convergence_time=0, 
        )

def run_evaluation():
    parser = argparse.ArgumentParser(description="SCARI-v2 Performance Evaluation")
    parser.add_argument('--config', type=str, default='configs/default.yaml', help='Config path')
    parser.add_argument('--model', type=str, default='data/models/scari_v2_final.zip', help='Model path')
    parser.add_argument('--steps', type=int, default=5000, help='Evaluation steps')
    parser.add_argument('--output', type=str, default='outputs/eval', help='Output directory')
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
    
    # Load model
    try:
        trained_model = PPO.load(args.model)
        print(f"✅ Loaded model from {args.model}")
    except Exception as e:
        print(f"❌ Failed to load model: {e}")
        return
    
    runner = EvaluationRunner(cfg, env)
    b_rewards, b_temps, b_powers, b_metrics = runner.evaluate_baseline(args.steps)
    m_rewards, m_temps, m_powers, m_metrics = runner.evaluate_model(trained_model, args.steps)
    
    # Save results
    metrics_path = output_dir / 'metrics.json'
    with open(metrics_path, 'w') as f:
        json.dump({
            'baseline': b_metrics.to_dict(),
            'scari_v2': m_metrics.to_dict()
        }, f, indent=4)
    
    # Generate visualization
    print("\n📈 Generating Performance Visualizations...")
    viz = PerformanceVisualizer(str(output_dir))
    
    baseline_history = {
        'temps': b_temps,
        'powers': b_powers,
    }
    model_history = {
        'temps': m_temps,
        'powers': m_powers,
    }
    
    viz.create_comprehensive_dashboard(
        b_metrics.to_dict(),
        m_metrics.to_dict(),
        baseline_history,
        model_history
    )
    
    print(f"\n✅ Evaluation complete. Results saved to {output_dir}")
    print(f"   - Energy Savings: {((b_metrics.total_power_consumption - m_metrics.total_power_consumption)/b_metrics.total_power_consumption)*100:.1f}%")
    print(f"   - SCARI PUE: {m_metrics.average_pue:.3f}")

if __name__ == '__main__':
    run_evaluation()
