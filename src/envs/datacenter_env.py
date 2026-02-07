# src/envs/datacenter_env.py
import gymnasium as gym
from gymnasium import spaces
import numpy as np
from typing import Tuple, Dict, Any, List, Optional
from pathlib import Path
from src.utils.config import Config, DEFAULT_CONFIG
from src.models.rack import Rack
import logging

logger = logging.getLogger(__name__)

class DataCenterEnv(gym.Env):
    """Gymnasium environment for datacenter thermal management RL."""
    
    metadata = {'render_modes': []}
    
    def __init__(self, config: Optional[Config] = None):
        """
        Initialize the environment.
        
        Args:
            config: Configuration object.
        """
        if config is None:
            config = DEFAULT_CONFIG
        
        self.config = config
        self.num_servers = (
            config.environment.num_racks * 
            config.environment.servers_per_rack
        )
        
        self.rack = Rack(0, self.num_servers, config)
        self.current_loads = np.zeros(self.num_servers)
        self.step_count = 0
        self.episode_count = 0
        
        # SCARI: Normalized observation space [0, 1]
        # [Normalized Temps, Loads, Health, Temp Trends]
        self.observation_space = spaces.Box(
            low=0.0, high=1.0,
            shape=(4 * self.num_servers,),
            dtype=np.float32
        )
        
        self.prev_temps = None # For calculating trends
        
        # Action: [Cooling actions per server...]
        self.action_space = spaces.Box(
            low=0.0, high=1.0,
            shape=(self.num_servers,),
            dtype=np.float32
        )
        
        self.episode_rewards: List[float] = []
        self.episode_temps: List[float] = []
        self.episode_powers: List[float] = []
        
        logger.info(f"DataCenterEnv initialized with {self.num_servers} servers (Normalized v2)")
    
    def reset(self, seed: Optional[int] = None, options: Optional[Dict[str, Any]] = None) -> Tuple[np.ndarray, Dict[str, Any]]:
        """Reset the environment."""
        super().reset(seed=seed)
        
        self.rack.reset()
        self.prev_temps = self.rack.get_temperatures()
        
        # Ensure we use the seed provided by gymnasium
        self.current_loads = self.np_random.uniform(
            self.config.environment.min_initial_load,
            self.config.environment.max_initial_load,
            self.num_servers
        ).astype(np.float32)
        
        self.step_count = 0
        self.episode_count += 1
        self.episode_rewards = []
        self.episode_temps = []
        self.episode_powers = []
        
        return self._get_obs(), {}
    
    def step(self, action: np.ndarray) -> Tuple[np.ndarray, float, bool, bool, Dict[str, Any]]:
        """Step through environment physics."""
        action = np.clip(action, 0.0, 1.0).astype(np.float32)
        
        # Update workload loads
        load_std = self.config.environment.load_std
        # Random walk for loads
        load_noise = self.np_random.normal(0, load_std, self.num_servers)
        self.current_loads = np.clip(
            self.current_loads + load_noise,
            0.0, 1.0
        ).astype(np.float32)
        
        # Update server physics
        stats = self.rack.update(self.current_loads, action)
        
        # Calculate reward
        reward = self._calculate_reward(stats, action)
        
        # Termination conditions
        temps = self.rack.get_temperatures()
        max_temp = np.max(temps)
        
        terminated = bool(max_temp >= self.config.physics.max_temp)
        truncated = bool(self.step_count >= self.config.environment.max_steps)
        
        self.episode_rewards.append(reward)
        self.episode_temps.append(max_temp)
        self.episode_powers.append(self.rack.get_total_power())
        self.step_count += 1
        
        info = {
            "total_power": self.rack.get_total_power(),
            "max_temp": float(max_temp),
            "avg_temp": self.rack.get_avg_temperature(),
            "avg_health": self.rack.get_avg_health(),
            "it_power": float(sum(s['it_power'] for s in stats)),
            "cooling_power": float(sum(s['cooling_power'] for s in stats)),
            "stats": stats # Added for evaluate.py stability
        }
        
        return self._get_obs(), float(reward), terminated, truncated, info
    
    def _get_obs(self) -> np.ndarray:
        """
        Produce NORMALIZED observations [0, 1].
        """
        temps = self.rack.get_temperatures()
        loads = self.current_loads
        health = np.array([s.health for s in self.rack.servers])
        
        # Calculate trends (Normalized change per step)
        if self.prev_temps is None:
            trends = np.zeros_like(temps)
        else:
            # Add Sensor Noise (Enterprise-Grade Realism)
            # +/- 0.5°C jitter simulates real-world thermistors
            obs_noise = self.np_random.normal(0, 0.5, self.num_servers)
            noisy_temps = temps + obs_noise
            
            # Scale trend so that a 1.0 degree increase per step is "high" (0.5 + 0.5)
            # We use the previous noisy temps for trend to simulate sequential jitter
            trends = (noisy_temps - self.prev_temps) / 10.0 
            trends = np.clip(trends * 0.5 + 0.5, 0, 1) 
            
            # Use noisy temps for main observation too
            temps_for_obs = noisy_temps
        
        # Normalize temperatures between min and max allowed
        t_min = self.config.physics.min_temp
        t_max = self.config.physics.max_temp
        norm_temps = (temps_for_obs - t_min) / (t_max - t_min + 1e-6)
        norm_temps = np.clip(norm_temps, 0, 1)
        
        self.prev_temps = temps_for_obs.copy()
        
        # Loads and Health are already roughly [0, 1]
        return np.concatenate([norm_temps, loads, health, trends]).astype(np.float32)

    def get_raw_observations(self) -> Dict[str, np.ndarray]:
        """
        Return raw, un-normalized observations for analysis or legacy controllers.
        """
        return {
            'temps': self.rack.get_temperatures(),
            'loads': self.current_loads.copy(),
            'health': np.array([s.health for s in self.rack.servers]),
            'power': self.rack.get_total_power()
        }

    
    def _calculate_reward(self, stats: List[Dict[str, Any]], actions: np.ndarray) -> float:
        """
        Improved Reward Function prioritizing thermal safety (< 60°C).
        Conservative cooling to prevent temperature spikes.
        """
        it_power = sum(s['it_power'] for s in stats)
        cooling_power = sum(s['cooling_power'] for s in stats)
        total_power = it_power + cooling_power
        
        avg_temp = np.mean([s['temp'] for s in stats])
        max_temp = np.max([s['temp'] for s in stats])
        avg_health = np.mean([s['health'] for s in stats])
        pue = total_power / (it_power + 1e-6)
        
        # ---------------------------------------------------------
        # CONSERVATIVE THERMAL CONTROL STRATEGY
        # Priority: NEVER exceed 60°C (hard safety limit)
        # Target: Keep temps around 45-50°C for optimal efficiency & longevity
        # ---------------------------------------------------------
        
        # 1. SOFT THERMAL ZONE (preferred operating range: 45-55°C)
        soft_lower = 45.0
        soft_upper = 55.0
        target_temp = 50.0
        
        soft_thermal_reward = 0.0
        if soft_lower <= max_temp <= soft_upper:
            # Reward for being in the sweet spot
            deviation = abs(max_temp - target_temp)
            soft_thermal_reward = 5.0 * (1.0 - deviation / 10.0)
        elif max_temp < soft_lower:
            # Slightly overcooled but safe
            soft_thermal_reward = 2.0
        
        # 2. WARNING ZONE (55-60°C): Escalating penalties
        warning_penalty = 0.0
        if 55.0 < max_temp < 60.0:
            excess = max_temp - 55.0
            # Quadratic growth: starts small at 55°C, becomes severe as we approach 60°C
            warning_penalty = 20.0 * (excess ** 2.0)
        
        # 3. CRITICAL HARD LIMIT (>= 60°C): Maximum penalty
        critical_penalty = 0.0
        if max_temp >= 60.0:
            # Severe penalty - this should almost never happen with proper training
            excess_critical = max_temp - 60.0
            critical_penalty = 300.0 + (100.0 * excess_critical)
        
        # 4. ABSOLUTE FAIL CONDITION (>= 65°C): Emergency termination
        if max_temp >= self.config.physics.max_temp:
            return float(-2000.0)  # Game over
        
        # 5. ENERGY EFFICIENCY REWARD (secondary to thermal)
        # Only reward PUE improvements if thermal is under control
        pue_reward = 0.0
        if max_temp <= 55.0:  # Only optimize energy when thermally safe
            pue_baseline = 1.35
            pue_improvement = max(0, pue_baseline - pue)
            pue_reward = 3.0 * (pue_improvement * 20.0)
        
        # 6. HEALTH PRESERVATION
        # Reward for maintaining component health (exponential decay penalty when low)
        health_penalty = 0.0
        if avg_health < 0.95:
            health_penalty = 50.0 * (1.0 - avg_health)
        
        # 7. STABILITY REWARD (smooth actions)
        # Prevent jittery cooling that creates thermal oscillations
        action_jitter_penalty = 0.0
        if hasattr(self, 'last_action') and self.last_action is not None:
            smooth_factor = np.mean(np.abs(actions - self.last_action))
            action_jitter_penalty = 2.0 * smooth_factor  # Encourage smooth transitions
        self.last_action = actions.copy()
        
        # 8. DEMAND MANAGEMENT
        demand_limit = self.config.physics.p_max * self.num_servers * 0.8
        demand_penalty = 0.0
        if total_power > demand_limit:
            demand_penalty = 0.01 * (total_power - demand_limit)
        
        # 9. LOAD AWARENESS
        # If IT load is high but cooling is barely active, penalize (neglect of duty)
        neglect_penalty = 0.0
        it_load_mean = np.mean([s['it_power'] for s in stats]) / self.config.physics.p_max
        if it_load_mean > 0.75 and np.mean(actions) < 0.20:
            neglect_penalty = 15.0
        
        # ========== TOTAL REWARD CALCULATION ==========
        # Thermal safety is ALWAYS priority #1
        reward = (
            soft_thermal_reward +           # Want to be in optimal range
            pue_reward -                    # Energy efficiency (if safe)
            warning_penalty -               # Escalating penalty as we approach 60°C
            critical_penalty -              # Severe penalty if we hit/exceed 60°C
            health_penalty -                # Long-term reliability
            action_jitter_penalty -         # Smooth operation
            demand_penalty -                # Power management
            neglect_penalty                 # Don't ignore high loads
        )
        
        return float(reward)

    def render(self, mode='human'):
        pass
