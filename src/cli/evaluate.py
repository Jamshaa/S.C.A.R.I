# src/cli/evaluate.py
#!/usr/bin/env python3
"""
S.C.A.R.I. v2.0 - Evaluation Module
Evaluates trained models and compares with baseline PID controller.
"""

import click
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import logging
from pathlib import Path
from typing import Dict, Tuple, List, Optional, Any
import json
import math
from dataclasses import dataclass, asdict
from tqdm import tqdm
from stable_baselines3 import PPO

from src.config import Config, DEFAULT_CONFIG
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
    average_pue: float  # Added in S.C.A.R.I. "True Physics"
    average_health: float # Added in S.C.A.R.I. "True Physics"
    convergence_time: int
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class BaselineController:
    """Conserative PID-based baseline controller."""
    
    def __init__(self, target_temp: float = 28.0): # Keeping it cold
        self.target_temp = target_temp
        self.prev_error = 0.0
        self.integral = 0.0
    
    def compute_action(self, temps: np.ndarray, num_servers: int) -> np.ndarray:
        """Compute PID-based cooling action."""
        max_temp = np.max(temps)
        error = max_temp - self.target_temp
        
        # Simple PID gains
        kp, ki, kd = 0.05, 0.002, 0.01
        
        self.integral += error
        self.integral = np.clip(self.integral, -100, 100)
        
        derivative = error - self.prev_error
        self.prev_error = error
        
        fan_speed = kp * error + ki * self.integral + kd * derivative
        fan_speed = np.clip(0.4 + fan_speed, 0.2, 1.0) # Higher floor for safety
        
        return np.ones(num_servers) * fan_speed
    
    def reset(self):
        self.prev_error = 0.0
        self.integral = 0.0

class EvaluationRunner:
    """Runs evaluation episodes and collects metrics."""
    
    def __init__(self, config: Config, env: Any):
        self.config = config
        self.env = env
        # Try to get num_servers from internal env if possible
        if hasattr(env, 'num_servers'):
            self.num_servers = env.num_servers
        elif hasattr(env, 'get_attr'):
            self.num_servers = env.get_attr('num_servers')[0]
        else:
            self.num_servers = 10 # Default
        self.baseline = BaselineController(target_temp=30.0)
    
    def evaluate_baseline(self, num_steps: int = 5000, seed: Optional[int] = None) -> Tuple[List[float], List[float], List[float], EvaluationMetrics]:
        print("\n📊 Evaluating Baseline (PID) Controller...")
        # Reset with fixed seed for fair comparison
        obs = self.env.reset()
        if hasattr(self.env, 'seed') and seed is not None:
            self.env.seed(seed)
        
        rewards, temps, powers = [], [], []
        it_powers, cooling_powers, healths, all_actions = [], [], [], []
        violations = 0
        
        for _ in tqdm(range(num_steps), desc="Baseline"):
            current_obs = obs[0]
            server_temps = current_obs[:self.num_servers] 
            num_servers = len(server_temps)
            
            action = self.baseline.compute_action(server_temps, num_servers)
            obs, reward, done, info = self.env.step([action])
            
            rewards.append(reward[0])
            temps.append(info[0]['max_temp'])
            powers.append(info[0]['total_power'])
            it_powers.append(info[0].get('it_power', info[0]['total_power'] * 0.9))
            cooling_powers.append(info[0].get('cooling_power', info[0]['total_power'] * 0.1))
            healths.append(info[0].get('avg_health', 1.0))
            all_actions.append(np.mean(action))
            
            if info[0]['max_temp'] >= self.config.reward.critical_limit:
                violations += 1
            
        metrics = self._compute_metrics(rewards, temps, powers, it_powers, cooling_powers, healths, all_actions, violations)
        return rewards, temps, powers, metrics

    def evaluate_model(self, model: PPO, num_steps: int = 5000, seed: Optional[int] = None) -> Tuple[List[float], List[float], List[float], EvaluationMetrics]:
        print("\n🤖 Evaluating Trained Model...")
        # Reset with same fixed seed
        obs = self.env.reset()
        if hasattr(self.env, 'seed') and seed is not None:
            self.env.seed(seed)
            
        rewards, temps, powers = [], [], []
        it_powers, cooling_powers, healths, all_actions = [], [], [], []
        violations = 0
       
        for _ in tqdm(range(num_steps), desc="Model"):
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, done, info = self.env.step(action)
            
            rewards.append(reward[0])
            temps.append(info[0]['max_temp'])
            powers.append(info[0]['total_power'])
            it_powers.append(info[0].get('it_power', info[0]['total_power'] * 0.9))
            cooling_powers.append(info[0].get('cooling_power', info[0]['total_power'] * 0.1))
            healths.append(info[0].get('avg_health', 1.0))
            all_actions.append(np.mean(action[0]))
            
            if info[0]['max_temp'] >= self.config.reward.critical_limit:
                violations += 1
        
        metrics = self._compute_metrics(rewards, temps, powers, it_powers, cooling_powers, healths, all_actions, violations)
        return rewards, temps, powers, metrics
    
    def _compute_metrics(self, rewards: List[float], temps: List[float], 
                         powers: List[float], it_powers: List[float],
                         cooling_powers: List[float], healths: List[float],
                         actions: List[float], violations: int) -> EvaluationMetrics:
        temps_array = np.array(temps)
        rewards_array = np.array(rewards)
        powers_array = np.array(powers)
        it_array = np.array(it_powers)
        cool_array = np.array(cooling_powers)
        
        # Stability and efficiency calculations
        temp_changes = np.abs(np.diff(temps_array))
        thermal_stability = 1.0 - (np.std(temp_changes) / (np.max(temp_changes) + 1e-6))
        
        baseline_power_idle = self.config.physics.p_idle * self.num_servers
        power_efficiency = 1.0 - (np.mean(powers_array) / (baseline_power_idle * 2))
        
        avg_fan_speed = np.mean(actions)
        
        # S.C.A.R.I. "True Physics" Metrics
        avg_pue = np.mean(powers_array / (it_array + 1e-6))
        avg_health = np.mean(healths)
        
        return EvaluationMetrics(
            total_power_consumption=float(np.sum(powers_array)),
            average_temperature=float(np.mean(temps_array)),
            max_temperature=float(np.max(temps_array)),
            min_temperature=float(np.min(temps_array)),
            std_temperature=float(np.std(temps_array)),
            safety_violations=int(violations),
            avg_fan_speed=float(avg_fan_speed),
            power_efficiency=float(np.clip(power_efficiency, 0, 1)),
            thermal_stability=float(np.clip(thermal_stability, 0, 1)),
            episode_reward=float(np.mean(rewards_array)),
            average_pue=float(avg_pue),
            average_health=float(avg_health),
            convergence_time=0, 
        )

class ComparisonVisualizer:
    """Generates comparison plots and reports."""
    
    def __init__(self, output_dir: str = 'outputs'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def plot_comparisons(self, b_data: Tuple, m_data: Tuple):
        b_rewards, b_temps, b_powers, b_metrics = b_data
        m_rewards, m_temps, m_powers, m_metrics = m_data
        
        # Create comprehensive comparison
        self.plot_main_comparison(b_metrics, m_metrics, b_powers, m_powers, b_temps, m_temps)
        self.generate_text_report(b_metrics, m_metrics)
        logger.info(f"Comparison saved to {self.output_dir}")

    def plot_main_comparison(self, b_m, m_m, b_powers, m_powers, b_temps, m_temps):
        """Create comprehensive comparison dashboard."""
        
        fig = plt.figure(figsize=(16, 10))
        fig.suptitle('S.C.A.R.I. v4.0 vs Baseline (PID)', fontsize=20, fontweight='bold', y=0.98)
        
        # Colors
        baseline_color = '#E74C3C'
        scari_color = '#2ECC71'
        
        # Calculate improvements
        power_diff = ((b_m.total_power_consumption - m_m.total_power_consumption) / b_m.total_power_consumption) * 100
        temp_diff = ((b_m.average_temperature - m_m.average_temperature) / b_m.average_temperature) * 100
        stability_diff = ((m_m.thermal_stability - b_m.thermal_stability) / max(b_m.thermal_stability, 0.01)) * 100
        
        # Row 1: Bar charts
        ax1 = fig.add_subplot(2, 3, 1)
        bars = ax1.bar(['Baseline', 'SCARI'], 
                       [b_m.total_power_consumption/1000, m_m.total_power_consumption/1000],
                       color=[baseline_color, scari_color], edgecolor='white', linewidth=2)
        ax1.set_ylabel('Energy (kWh)', fontsize=12, fontweight='bold')
        ax1.set_title(f'Power Consumption\n({power_diff:+.1f}%)', fontsize=14, fontweight='bold',
                     color=scari_color if power_diff > 0 else baseline_color)
        for bar in bars:
            ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                    f'{bar.get_height():.1f}', ha='center', va='bottom', fontsize=11, fontweight='bold')
        
        ax2 = fig.add_subplot(2, 3, 2)
        bars = ax2.bar(['Baseline', 'SCARI'],
                       [b_m.average_temperature, m_m.average_temperature],
                       color=[baseline_color, scari_color], edgecolor='white', linewidth=2)
        ax2.set_ylabel('Temperature (°C)', fontsize=12, fontweight='bold')
        ax2.set_title(f'Avg Temperature\n({temp_diff:+.1f}%)', fontsize=14, fontweight='bold',
                     color=scari_color if temp_diff > 0 else baseline_color)
        for bar in bars:
            ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                    f'{bar.get_height():.1f}°C', ha='center', va='bottom', fontsize=11, fontweight='bold')
        
        ax3 = fig.add_subplot(2, 3, 3)
        bars = ax3.bar(['Baseline', 'SCARI'],
                       [b_m.thermal_stability * 100, m_m.thermal_stability * 100],
                       color=[baseline_color, scari_color], edgecolor='white', linewidth=2)
        ax3.set_ylabel('Stability (%)', fontsize=12, fontweight='bold')
        ax3.set_title(f'System Stability\n({stability_diff:+.1f}%)', fontsize=14, fontweight='bold',
                     color=scari_color if stability_diff > 0 else baseline_color)
        ax3.set_ylim(0, 100)
        for bar in bars:
            ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                    f'{bar.get_height():.1f}%', ha='center', va='bottom', fontsize=11, fontweight='bold')
        
        # Row 2: Time series
        ax4 = fig.add_subplot(2, 2, 3)
        steps = np.arange(len(b_powers))
        ax4.plot(steps, pd.Series(b_powers).rolling(100).mean(), label='Baseline', color=baseline_color, alpha=0.8, linewidth=2)
        ax4.plot(steps, pd.Series(m_powers).rolling(100).mean(), label='SCARI', color=scari_color, linewidth=2)
        ax4.set_xlabel('Evaluation Steps', fontsize=11)
        ax4.set_ylabel('Power (W)', fontsize=11)
        ax4.set_title('Power Over Time (Rolling Avg)', fontsize=13, fontweight='bold')
        ax4.legend(loc='upper right')
        ax4.grid(True, alpha=0.3)
        
        ax5 = fig.add_subplot(2, 2, 4)
        ax5.plot(steps, pd.Series(b_temps).rolling(100).mean(), label='Baseline', color=baseline_color, alpha=0.8, linewidth=2)
        ax5.plot(steps, pd.Series(m_temps).rolling(100).mean(), label='SCARI', color=scari_color, linewidth=2)
        ax5.axhline(y=65, color='orange', linestyle='--', alpha=0.7, label='Caution')
        ax5.axhline(y=75, color='red', linestyle='--', alpha=0.7, label='Warning')
        ax5.set_xlabel('Evaluation Steps', fontsize=11)
        ax5.set_ylabel('Temperature (°C)', fontsize=11)
        ax5.set_title('Temperature Over Time (Rolling Avg)', fontsize=13, fontweight='bold')
        ax5.legend(loc='upper right')
        ax5.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'comparison.png', dpi=150, bbox_inches='tight', facecolor='white')
        plt.close()

    def generate_text_report(self, b_m: EvaluationMetrics, m_m: EvaluationMetrics):
        """Generate a simple text report."""
        
        power_diff = ((b_m.total_power_consumption - m_m.total_power_consumption) / b_m.total_power_consumption) * 100
        temp_diff = ((b_m.average_temperature - m_m.average_temperature) / b_m.average_temperature) * 100
        
        report = f"""
S.C.A.R.I. v10.5 - ADVANCED COMPARISON REPORT
=============================================

BASELINE (PID)          SCARI (Attention)    DIFFERENCE
---------------------------------------------------------------------------
Power: {b_m.total_power_consumption/1000:,.1f} Wh        {m_m.total_power_consumption/1000:,.1f} Wh          {power_diff:+.2f}%
Temp:  {b_m.average_temperature:.1f}°C            {m_m.average_temperature:.1f}°C            {temp_diff:+.2f}%
PUE:   {b_m.average_pue:.3f}                {m_m.average_pue:.3f}                {(m_m.average_pue - b_m.average_pue):+.3f}
Health: {b_m.average_health*100:.2f}%          {m_m.average_health*100:.2f}%          {(m_m.average_health - b_m.average_health)*100:+.3f}%

RESULT: {"SCARI is MORE EFFICIENT (Wins! 🎉)" if power_diff > 0 else "SCARI is currently less efficient"}
"""
        
        with open(self.output_dir / 'report.txt', 'w', encoding='utf-8') as f:
            f.write(report.strip())

@click.command()
@click.option('--config', default='configs/default.yaml', help='Config path')
@click.option('--model', default='data/trained_models/scari_v2_final.zip', help='Model path')
@click.option('--steps', default=5000, type=int, help='Evaluation steps')
@click.option('--output', default='outputs', help='Output directory')
@click.option('--seed', default=42, type=int, help='Seed')
def evaluate(config, model, steps, output, seed):
    """Evaluate and compare models."""
    from src.envs.datacenter_env import DataCenterEnv
    from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize
    np.random.seed(seed)
    
    try:
        cfg = Config.from_yaml(config)
    except Exception:
        cfg = DEFAULT_CONFIG
        
    def make_env():
        return DataCenterEnv(cfg)
        
    env = DummyVecEnv([make_env])
    
    # Load normalization stats if they exist
    stats_path = Path(model).parent / 'vec_normalize.pkl'
    if stats_path.exists():
        env = VecNormalize.load(str(stats_path), env)
        env.training = False # Don't update stats during evaluation
        env.norm_reward = False # Don't normalize rewards during evaluation for metrics
        logger.info(f"Loaded normalization stats from {stats_path}")
    
    try:
        trained_model = PPO.load(model)
    except Exception:
        print(f"❌ Model not found at {model}. Please train first.")
        return
    
    runner = EvaluationRunner(cfg, env)
    b_results = runner.evaluate_baseline(steps, seed=seed)
    m_results = runner.evaluate_model(trained_model, steps, seed=seed)
    
    # Use legacy visualizer
    viz = ComparisonVisualizer(output)
    viz.plot_comparisons(b_results, m_results)
    
    # Use advanced visualizer
    print("\n📊 Creating advanced visualizations...")
    adv_viz = PerformanceVisualizer(output)
    
    # Prepare data for advanced visualizations
    b_rewards, b_temps, b_powers, b_metrics = b_results
    m_rewards, m_temps, m_powers, m_metrics = m_results
    
    # Get IT and cooling power data
    b_it_powers = []
    b_cooling_powers = []
    m_it_powers = []
    m_cooling_powers = []
    
    # Re-run quick evaluation to get detailed data
    obs = env.reset()
    for _ in range(min(steps, len(b_powers))):
        action = runner.baseline.compute_action(obs[0][:runner.num_servers], runner.num_servers)
        obs, reward, done, info = env.step([action])
        b_it_powers.append(info[0].get('it_power', info[0]['total_power'] * 0.85))
        b_cooling_powers.append(info[0].get('cooling_power', info[0]['total_power'] * 0.15))
    
    obs = env.reset()
    for _ in range(min(steps, len(m_powers))):
        action, _ = trained_model.predict(obs, deterministic=True)
        obs, reward, done, info = env.step(action)
        m_it_powers.append(info[0].get('it_power', info[0]['total_power'] * 0.85))
        m_cooling_powers.append(info[0].get('cooling_power', info[0]['total_power'] * 0.15))
    
    baseline_data = {
        'temps': b_temps,
        'powers': b_powers,
        'it_powers': b_it_powers,
        'cooling_powers': b_cooling_powers
    }
    
    model_data = {
        'temps': m_temps,
        'powers': m_powers,
        'it_powers': m_it_powers,
        'cooling_powers': m_cooling_powers
    }
    
    # Create comprehensive dashboard
    adv_viz.create_comprehensive_dashboard(
        b_metrics.to_dict(), 
        m_metrics.to_dict(),
        baseline_data,
        model_data
    )
    
    # Create power breakdown chart
    adv_viz.create_power_breakdown_chart(baseline_data, model_data)
    
    # Save metrics
    with open(Path(output) / 'metrics.json', 'w', encoding='utf-8') as f:
        json.dump({'baseline': b_metrics.to_dict(), 'model': m_metrics.to_dict()}, f, indent=2)
    
    # Print summary
    power_savings = ((b_metrics.total_power_consumption - m_metrics.total_power_consumption) / 
                     b_metrics.total_power_consumption) * 100
    
    print("\n" + "="*70)
    print("✅ Evaluation Complete!")
    print("="*70)
    print(f"Energy Savings: {power_savings:+.2f}%")
    print(f"SCARI PUE: {m_metrics.average_pue:.3f}")
    print(f"Baseline PUE: {b_metrics.average_pue:.3f}")
    print(f"Max Temperature: {m_metrics.max_temperature:.1f}°C")
    print(f"Safety Violations: {m_metrics.safety_violations}")
    print(f"\n📊 Results saved to '{output}' directory")
    print("="*70)

if __name__ == '__main__':
    evaluate()
