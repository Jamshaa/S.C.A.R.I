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
        
        # State: [Temperatures..., CPU Loads...]
        self.observation_space = spaces.Box(
            low=0.0, high=100.0,
            shape=(2 * self.num_servers,),
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
        
        self.current_loads = np.random.uniform(
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
        change = np.random.uniform(
            -self.config.environment.max_load_change_per_step,
            self.config.environment.max_load_change_per_step,
            self.num_servers
        )
        self.current_loads = np.clip(self.current_loads + change, 0.1, 1.0).astype(np.float32)
        
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
            "max_temp": float(max_temp),
            "avg_temp": self.rack.get_avg_temperature(),
            "avg_reward": float(np.mean(self.episode_rewards[-10:])) if self.episode_rewards else 0.0,
        }
        
        return self._get_obs(), float(reward), terminated, truncated, info
    
    def _get_obs(self) -> np.ndarray:
        """Assemble the current state observation."""
        temps = self.rack.get_temperatures()
        return np.concatenate([temps, self.current_loads]).astype(np.float32)
    
    def _calculate_reward(self, stats: List[Dict[str, float]], actions: np.ndarray) -> float:
        """
        S.C.A.R.I. v5.0 - Power-First Reward Function
        
        GOAL: Beat the PID baseline by using LESS power while staying safe.
        
        The PID baseline uses avg_fan_speed = 0.52 and total_power = 19M Wh.
        We need to MINIMIZE fan usage while maintaining safe temperatures.
        """
        # Get current state
        total_power = self.rack.get_total_power()
        temps = self.rack.get_temperatures()
        max_temp = np.max(temps)
        avg_temp = np.mean(temps)
        
        # Fan usage (0-1 scale)
        avg_fan = np.mean(actions)
        
        # ========== REWARD = EFFICIENCY - PENALTIES ==========
        
        # 1. POWER EFFICIENCY (Main reward - MAXIMIZE this)
        # The less power we use, the better. Baseline uses ~3813W average.
        # Reward for using less than baseline, penalize for using more.
        baseline_power = 3800.0  # Approximate baseline average power
        power_diff = baseline_power - total_power
        power_reward = power_diff / 100.0  # Scale appropriately
        
        # 2. FAN EFFICIENCY (Reward low fan usage)
        # Baseline uses 0.52 average fan. We want to use LESS.
        fan_reward = 20.0 * (0.6 - avg_fan)  # Max +12 at fan=0, 0 at fan=0.6
        
        # 3. TEMPERATURE PENALTY (Only if too hot)
        temp_penalty = 0.0
        if max_temp >= 80.0:  # Critical
            temp_penalty = 100.0
        elif max_temp >= 70.0:  # Warning
            temp_penalty = 10.0 * (max_temp - 70.0)
        elif max_temp >= 60.0:  # Caution
            temp_penalty = 2.0 * (max_temp - 60.0)
        # Below 60°C = no penalty (safe zone)
        
        # 4. SWEET SPOT BONUS (Optimal temperature range)
        # Operating around 40-50°C is ideal - warm enough to save energy but safe
        sweet_spot_bonus = 0.0
        if 40.0 <= avg_temp <= 55.0:
            # Peak bonus at 47.5°C (center of optimal range)
            distance_from_center = abs(avg_temp - 47.5)
            sweet_spot_bonus = 5.0 * (1.0 - distance_from_center / 7.5)
        
        # TOTAL REWARD
        total_reward = power_reward + fan_reward + sweet_spot_bonus - temp_penalty
        
        return float(total_reward)
    
    def render(self) -> None:
        """Standard Gymnasium render implementation."""
        pass
