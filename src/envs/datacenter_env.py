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
        S.C.A.R.I. "Thermal Intelligence" - Aggressive Energy Optimization Reward
        
        GOAL: Achieve 15-25% energy savings through intelligent thermal management.
        Strongly incentivizes operating at higher safe temperatures with minimal cooling.
        """
        # 1. TOTAL POWER PENALTY (Primary Fixed)
        total_it_power = sum(s['it_power'] for s in stats)
        total_cooling_power = sum(s['cooling_power'] for s in stats)
        total_power = total_it_power + total_cooling_power

        normalized_power = total_power / 4000.0
        power_penalty = 500.0 * (normalized_power ** 2) 
        
        power_bonus = 200.0 * (1.0 - min(1.0, normalized_power))
        
        # 2. COOLING POWER - Direct penalty (cooling is pure waste)
        # Penalize cooling quadratically to discourage ANY unnecessary cooling
        cooling_ratio = total_cooling_power / (total_it_power + 1e-6)
        cooling_penalty = 800.0 * (cooling_ratio ** 2)
        
        # 3. PUE OPTIMIZATION - Industry-leading target
        current_pue = total_power / (total_it_power + 1e-6)
        # Target PUE < 1.08 for best-in-class efficiency
        if current_pue < 1.08:
            pue_bonus = 600.0 * (1.08 - current_pue) ** 0.5
        else:
            pue_penalty = 400.0 * ((current_pue - 1.08) ** 2)
            pue_bonus = -pue_penalty
        
        # 4. THERMAL UTILIZATION - Reward operating at specific EFFICIENT SETPOINT
        temps = np.array([s['temp'] for s in stats])
        avg_temp = np.mean(temps)
        
        # Target Setpoint: 50.0ºC (The Golden Mean)
        target_setpoint = 50.0
        temp_diff = abs(avg_temp - target_setpoint)
        
        # Gaussian bell curve: Balanced to allow slight drift to ~60C
        temp_utilization_bonus = 1200.0 * np.exp(-0.15 * (temp_diff ** 2))
        
        if avg_temp < 30.0:
            temp_utilization_bonus -= 300.0

        # 5. SAFETY CONSTRAINTS
        safety_penalty = 0.0
        danger_threshold = self.config.physics.max_temp - 10.0
        max_temp = np.max(temps)
        if max_temp > danger_threshold:
             danger_ratio = (max_temp - danger_threshold) / 10.0
             safety_penalty = 2000.0 * (danger_ratio ** 3)

        # 6. ACTION EFFICIENCY
        avg_action = np.mean(actions)
        if avg_action > 0.1:
            action_waste_penalty = 200.0 * ((avg_action - 0.1) ** 2)
        else:
            action_waste_penalty = -100.0 * (0.1 - avg_action)

        # 7. ACTION SMOOTHNESS
        smoothness_penalty = 0.0
        if hasattr(self, 'last_actions'):
            action_diff = np.mean(np.abs(actions - self.last_actions))
            smoothness_penalty = 50.0 * (action_diff ** 2)
        self.last_actions = actions.copy()
        
        # 8. THERMAL STABILITY
        temp_std = np.std(temps)
        if temp_std < 2.5:
            stability_bonus = 200.0 * (2.5 - temp_std)
        else:
            stability_bonus = -100.0 * ((temp_std - 2.5) ** 2)
        
        # 9. SYSTEM HEALTH
        avg_health = np.mean([s['health'] for s in stats])
        if avg_health > 0.98:
            health_bonus = 150.0 * (avg_health - 0.98) / 0.02
        else:
            health_bonus = -300.0 * (0.98 - avg_health)
        
        # TOTAL REWARD COMPOSITION
        total_reward = (
            power_bonus +
            pue_bonus +
            temp_utilization_bonus +
            stability_bonus +
            health_bonus -
            power_penalty -
            cooling_penalty -
            safety_penalty -
            action_waste_penalty -
            smoothness_penalty
        )
        
        # CRITICAL FAILURE - Catastrophic penalty
        if max_temp >= self.config.physics.max_temp:
            total_reward -= 10000.0
            
        return float(total_reward)
    
    def render(self) -> None:
        """Standard Gymnasium render implementation."""
        pass
