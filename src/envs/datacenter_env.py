# src/envs/datacenter_env.py
import gymnasium as gym
from gymnasium import spaces
import numpy as np
from typing import Tuple, Dict, Any, List, Optional
from src.config import Config, DEFAULT_CONFIG
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
        
        # State: [Temperatures..., CPU Loads..., Health...]
        self.observation_space = spaces.Box(
            low=0.0, high=100.0,
            shape=(3 * self.num_servers,),
            dtype=np.float32
        )
        
        # Action: [Cooling actions per server...]
        self.action_space = spaces.Box(
            low=0.0, high=1.0,
            shape=(self.num_servers,),
            dtype=np.float32
        )
        
        self.episode_rewards: List[float] = []
        self.episode_temps: List[float] = []
        self.episode_powers: List[float] = []
        
        logger.info(f"DataCenterEnv initialized with {self.num_servers} servers")
    
    def reset(self, seed: Optional[int] = None, options: Optional[Dict[str, Any]] = None) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Reset the environment to its initial state.
        
        Args:
            seed: Random seed.
            options: Additional reset options.
            
        Returns:
            Initial observation and auxiliary information.
        """
        super().reset(seed=seed)
        
        self.rack.reset()
        
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
        
        logger.debug(f"Environment reset. Episode {self.episode_count} starting")
        return self._get_obs(), {}
    
    def step(self, action: np.ndarray) -> Tuple[np.ndarray, float, bool, bool, Dict[str, Any]]:
        """
        Step through the environment physics.
        
        Args:
            action: Cooling control actions.
            
        Returns:
            Next observation, reward, terminated, truncated, and info.
        """
        action = np.clip(action, 0.0, 1.0).astype(np.float32)
        
        # Update workload loads
        load_std = self.config.environment.load_std
        self.current_loads = np.clip(
            self.current_loads + self.np_random.normal(0, load_std, self.num_servers),
            0, 1
        ).astype(np.float32)
        
        # Update server physics
        stats = self.rack.update(self.current_loads, action)
        
        # Calculate reward
        reward = self._calculate_reward(stats, action)
        
        # Check termination criteria
        temps = self.rack.get_temperatures()
        max_temp = np.max(temps)
        
        terminated = max_temp >= self.config.physics.max_temp
        if terminated:
            logger.warning(f"Episode terminated: Temperature limit exceeded ({max_temp:.1f}ºC)")
            
        truncated = self.step_count >= self.config.environment.episode_length
        
        self.episode_rewards.append(reward)
        self.episode_temps.append(max_temp)
        self.episode_powers.append(self.rack.get_total_power())
        self.step_count += 1
        
        info = {
            "total_power": self.rack.get_total_power(),
            "it_power": self.rack.get_it_raw_power(),
            "cooling_power": self.rack.get_cooling_raw_power(),
            "max_temp": float(max_temp),
            "avg_temp": self.rack.get_avg_temperature(),
            "avg_health": self.rack.get_avg_health(),
            "avg_reward": float(np.mean(self.episode_rewards[-10:])) if self.episode_rewards else 0.0,
        }
        
        return self._get_obs(), float(reward), terminated, truncated, info
    
    def _get_obs(self) -> np.ndarray:
        """
        Assemble the current state observation.
        S.C.A.R.I. "True Physics" - Includes Health and Inlet Offsets.
        """
        temps = self.rack.get_temperatures()
        loads = self.current_loads
        health = np.array([s.health for s in self.rack.servers])
        
        # Flattened observation: [Temps..., Loads..., Health...]
        # We need to update the observation space definition in __init__
        return np.concatenate([temps, loads, health]).astype(np.float32)
    
    def _calculate_reward(self, stats: List[Dict[str, float]], actions: np.ndarray) -> float:
        """
        S.C.A.R.I. "Thermal Intelligence" - Advanced Multi-Objective Reward v11.0
        
        GOAL: Aggressively minimize TOTAL Power while maintaining thermal safety.
        Uses quadratic penalties and adaptive targets for superior energy efficiency.
        """
        # 1. TOTAL POWER PENALTY (Primary objective - quadratic for strong incentive)
        total_it_power = sum(s['it_power'] for s in stats)
        total_cooling_power = sum(s['cooling_power'] for s in stats)
        total_power = total_it_power + total_cooling_power
        
        # Baseline is ~4000W total. Using quadratic penalty to strongly discourage waste.
        # Normalized power (divide by baseline estimate)
        normalized_power = total_power / 4000.0
        # Quadratic penalty: saving 100W is worth MORE than saving 50W + 50W separately
        power_penalty = 1000.0 * (normalized_power ** 2)
        
        # 2. PUE OPTIMIZATION (Primary efficiency metric)
        current_pue = total_power / (total_it_power + 1e-6)
        # Strongly reward PUE approaching 1.0 (ideal)
        # Penalize PUE > 1.2 exponentially
        if current_pue < 1.15:
            pue_reward = 200.0 * (1.15 - current_pue)
        else:
            pue_reward = -100.0 * ((current_pue - 1.15) ** 2)
        
        # 3. ADAPTIVE THERMAL SAFETY
        temps = np.array([s['temp'] for s in stats])
        max_temp = np.max(temps)
        avg_temp = np.mean(temps)
        
        # Dynamic safe threshold based on workload
        avg_load = np.mean(self.current_loads)
        adaptive_threshold = self.config.reward.safe_threshold + (10.0 * avg_load)
        
        # Progressive penalty as temperature rises
        safety_penalty = 0.0
        if max_temp > adaptive_threshold:
            # Exponential penalty approaching limits
            temp_ratio = (max_temp - adaptive_threshold) / (self.config.physics.max_temp - adaptive_threshold)
            safety_penalty = 500.0 * (temp_ratio ** 2)
        
        # Bonus for keeping temperatures low when possible
        temp_efficiency_bonus = 0.0
        if max_temp < adaptive_threshold - 5.0:
            temp_efficiency_bonus = 50.0 * (adaptive_threshold - 5.0 - max_temp) / 10.0
        
        # 4. COOLING EFFICIENCY BONUS
        # Reward using minimal cooling while staying safe
        avg_cooling_action = np.mean(actions)
        if max_temp < adaptive_threshold:
            # Safe and using minimal cooling = excellent
            cooling_efficiency_bonus = 100.0 * (1.0 - avg_cooling_action)
        else:
            cooling_efficiency_bonus = 0.0
        
        # 5. ACTION SMOOTHNESS (Reduce mechanical wear and oscillations)
        action_penalty = 0.0
        if hasattr(self, 'last_actions'):
            action_diff = np.mean(np.abs(actions - self.last_actions))
            # Penalize rapid changes
            action_penalty = 50.0 * (action_diff ** 1.5)
        self.last_actions = actions.copy()
        
        # 6. THERMAL STABILITY BONUS
        temp_std = np.std(temps)
        stability_bonus = 20.0 * (1.0 / (1.0 + temp_std))
        
        # 7. HEALTH PRESERVATION
        avg_health = np.mean([s['health'] for s in stats])
        health_bonus = 50.0 * (avg_health - 0.95) if avg_health > 0.95 else -100.0
        
        # TOTAL REWARD COMPOSITION
        total_reward = (
            pue_reward +
            temp_efficiency_bonus +
            cooling_efficiency_bonus +
            stability_bonus +
            health_bonus -
            power_penalty -
            safety_penalty -
            action_penalty
        )
        
        # Critical failure penalty
        if max_temp >= self.config.physics.max_temp:
            total_reward -= 5000.0
            
        return float(total_reward)
    
    def render(self) -> None:
        """Standard Gymnasium render implementation."""
        pass
