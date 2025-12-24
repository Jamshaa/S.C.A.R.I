
# src/envs/datacenter_env.py
import gymnasium as gym
from gymnasium import spaces
import numpy as np
from typing import Tuple, Dict, Any
from src.config import Config, DEFAULT_CONFIG
from src.models.rack import Rack

class DataCenterEnv(gym.Env):
    metadata = {'render_modes': []}
    
    def __init__(self, config: Config = None):
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
        self.best_efficiency = 0.0
        
        self.observation_space = spaces.Box(
            low=0.0, high=100.0,
            shape=(2 * self.num_servers,),
            dtype=np.float32
        )
        
        self.action_space = spaces.Box(
            low=0.0, high=1.0,
            shape=(self.num_servers,),
            dtype=np.float32
        )
        
        self.episode_rewards = []
        self.episode_temps = []
        self.episode_powers = []
    
    def reset(self, seed=None, options=None) -> Tuple[np.ndarray, Dict]:
        super().reset(seed=seed)
        
        ambient = self.config.physics.ambient_temp
        for server in self.rack.servers:
            server.reset()
        
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
        
        return self._get_obs(), {}
    
    def step(self, action: np.ndarray) -> Tuple[np.ndarray, float, bool, bool, Dict]:
        action = np.clip(action, 0.0, 1.0).astype(np.float32)
        
        change = np.random.uniform(
            -self.config.environment.max_load_change_per_step,
            self.config.environment.max_load_change_per_step,
            self.num_servers
        )
        self.current_loads = np.clip(self.current_loads + change, 0.1, 1.0).astype(np.float32)
        
        stats = self.rack.update(self.current_loads, action)
        
        reward = self._calculate_reward(stats, action)
        
        temps = self.rack.get_temperatures()
        max_temp = np.max(temps)
        
        terminated = max_temp >= self.config.physics.max_temp
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
        temps = self.rack.get_temperatures()
        return np.concatenate([temps, self.current_loads]).astype(np.float32)
    
    def _calculate_reward(self, stats: list, actions: np.ndarray) -> float:
        total_power = self.rack.get_total_power()
        max_rack_power = self.num_servers * 1000.0
        normalized_power = total_power / max_rack_power
        
        reward_energy = -self.config.reward.energy_coefficient * normalized_power
        
        temps = self.rack.get_temperatures()
        max_temp = np.max(temps)
        
        thermal_penalty = 0.0
        
        if max_temp > self.config.reward.critical_limit:
            thermal_penalty = self.config.reward.emergency_penalty
        elif max_temp > self.config.reward.safe_threshold:
            ratio = (max_temp - self.config.reward.safe_threshold) / \
                    (self.config.reward.critical_limit - self.config.reward.safe_threshold)
            thermal_penalty = self.config.reward.thermal_penalty_coefficient * (ratio ** 2)
        
        avg_temp = np.mean(temps)
        if avg_temp < self.config.reward.safe_threshold:
            efficiency_bonus = self.config.reward.energy_efficiency_bonus * \
                              (1 - normalized_power)
        else:
            efficiency_bonus = 0.0
        
        total_reward = reward_energy - thermal_penalty + efficiency_bonus
        
        return float(total_reward)
    
    def render(self) -> None:
        pass
