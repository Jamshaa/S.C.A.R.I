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
        # [Normalized Temps, Loads, Health]
        self.observation_space = spaces.Box(
            low=0.0, high=1.0,
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
        
        logger.info(f"DataCenterEnv initialized with {self.num_servers} servers (Normalized v2)")
    
    def reset(self, seed: Optional[int] = None, options: Optional[Dict[str, Any]] = None) -> Tuple[np.ndarray, Dict[str, Any]]:
        """Reset the environment."""
        super().reset(seed=seed)
        
        self.rack.reset()
        
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
        }
        
        return self._get_obs(), float(reward), terminated, truncated, info
    
    def _get_obs(self) -> np.ndarray:
        """
        Produce NORMALIZED observations [0, 1].
        """
        temps = self.rack.get_temperatures()
        loads = self.current_loads
        health = np.array([s.health for s in self.rack.servers])
        
        # Normalize temperatures between min and max allowed
        t_min = self.config.physics.min_temp
        t_max = self.config.physics.max_temp
        norm_temps = (temps - t_min) / (t_max - t_min + 1e-6)
        norm_temps = np.clip(norm_temps, 0, 1)
        
        # Loads and Health are already roughly [0, 1]
        return np.concatenate([norm_temps, loads, health]).astype(np.float32)

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
        Multi-profile Reward Function for SCARI.
        Supports specialized training for different deployment scenarios.
        """
        it_power = sum(s['it_power'] for s in stats)
        cooling_power = sum(s['cooling_power'] for s in stats)
        total_power = it_power + cooling_power
        
        avg_temp = np.mean([s['temp'] for s in stats])
        max_temp = np.max([s['temp'] for s in stats])
        avg_health = np.mean([s['health'] for s in stats])
        pue = total_power / (it_power + 1e-6)
        
        profile = self.config.reward.profile
        
        if profile == "PRODUCTION_SAFE":
            # 🛡️ PRODUCTION SAFE: Priority is Thermal Stability & Safety
            pue_reward = 20.0 * max(0, 1.20 - pue) # Low priority for PUE
            
            # Narrow Gaussian centered at 45°C (Ideal ASHRAE range)
            thermal_reward = 800.0 * np.exp(-0.02 * (avg_temp - 45.0)**2)
            
            # Early and aggressive safety penalties
            safety_penalty = 0.0
            if max_temp > 55.0: # Penalty starts MUCH earlier
                safety_penalty = 1000.0 * (max_temp - 55.0)**2
            
            cooling_action_penalty = 50.0 * np.mean(actions)**2 # Low penalty to allow cooling
            health_penalty = 5000.0 * (1.0 - avg_health) # Very high priority
            
        elif profile == "MAX_EFFICIENCY":
            # 🔥 MAX EFFICIENCY: Priority is Energy Savings
            pue_reward = 150.0 * max(0, 1.15 - pue) # High priority for PUE
            
            # Broad Gaussian (don't care as much about exact temp, just stay below critical)
            thermal_reward = 200.0 * np.exp(-0.005 * (avg_temp - 55.0)**2)
            
            # Standard safety penalties
            safety_penalty = 0.0
            if max_temp > 70.0:
                safety_penalty = 500.0 * (max_temp - 70.0)**2
            
            cooling_action_penalty = 200.0 * np.mean(actions)**2 # High penalty to discourage fan use
            health_penalty = 1000.0 * (1.0 - avg_health)
            
        else: # BALANCED
            pue_reward = 80.0 * max(0, 1.15 - pue)
            thermal_reward = 400.0 * np.exp(-0.015 * (avg_temp - 45.0)**2)
            
            safety_penalty = 0.0
            if max_temp > 70.0:
                safety_penalty = 500.0 * (max_temp - 70.0)**2
                
            cooling_action_penalty = 100.0 * np.mean(actions)**2
            health_penalty = 2000.0 * (1.0 - avg_health)
        
        reward = pue_reward + thermal_reward - safety_penalty - cooling_action_penalty - health_penalty
        
        # Disaster prevention
        if max_temp >= self.config.physics.max_temp:
            reward -= 10000.0
            
        return float(reward)

    def render(self, mode='human'):
        pass
