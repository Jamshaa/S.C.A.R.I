import gymnasium as gym
from gymnasium import spaces
import numpy as np
from typing import Tuple, Dict, Any, List, Optional
from src.utils.config import Config, DEFAULT_CONFIG
from src.models.rack import Rack
import logging
logger = logging.getLogger(__name__)

class DataCenterEnv(gym.Env):
    metadata = {'render_modes': ['human']}

    def __init__(self, config: Optional[Config]=None):
        if config is None:
            config = DEFAULT_CONFIG
        self.config = config
        self.num_servers = config.environment.num_racks * config.environment.servers_per_rack
        self.rack = Rack(0, self.num_servers, config)
        self.current_loads = np.zeros(self.num_servers)
        self.step_count = 0
        self.episode_count = 0
        self.observation_space = spaces.Box(low=0.0, high=1.0, shape=(4 * self.num_servers,), dtype=np.float32)
        self.prev_temps = None
        self.last_action = None
        self.action_space = spaces.Box(low=0.0, high=1.0, shape=(self.num_servers,), dtype=np.float32)
        self.episode_rewards: List[float] = []
        self.episode_temps: List[float] = []
        self.episode_powers: List[float] = []
        logger.info(f'DataCenterEnv: {self.num_servers} servers, cooling={config.cooling.mode}, reward={config.reward.profile}')

    def reset(self, seed: Optional[int]=None, options: Optional[Dict[str, Any]]=None) -> Tuple[np.ndarray, Dict[str, Any]]:
        super().reset(seed=seed)
        self.rack.reset()
        self.prev_temps = self.rack.get_temperatures()
        self.last_action = None
        self.current_loads = self.np_random.uniform(self.config.environment.min_initial_load, self.config.environment.max_initial_load, self.num_servers).astype(np.float32)
        self.step_count = 0
        self.episode_count += 1
        self.episode_rewards = []
        self.episode_temps = []
        self.episode_powers = []
        return (self._get_obs(), {})

    def step(self, action: np.ndarray) -> Tuple[np.ndarray, float, bool, bool, Dict[str, Any]]:
        action = np.clip(action, 0.0, 1.0).astype(np.float32)
        load_std = self.config.environment.load_std
        load_noise = self.np_random.normal(0, load_std, self.num_servers)
        self.current_loads = np.clip(self.current_loads + load_noise, 0.0, 1.0).astype(np.float32)
        stats = self.rack.update(self.current_loads, action)
        reward = self._calculate_reward(stats, action)
        temps = self.rack.get_temperatures()
        max_temp = np.max(temps)
        terminated = bool(max_temp >= self.config.physics.max_temp)
        truncated = bool(self.step_count >= self.config.environment.max_steps)
        self.episode_rewards.append(reward)
        self.episode_temps.append(max_temp)
        self.episode_powers.append(self.rack.get_total_power())
        self.step_count += 1
        info = {'total_power': self.rack.get_total_power(), 'max_temp': float(max_temp), 'avg_temp': self.rack.get_avg_temperature(), 'avg_health': self.rack.get_avg_health(), 'it_power': float(sum((s['it_power'] for s in stats))), 'cooling_power': float(sum((s['cooling_power'] for s in stats))), 'stats': stats}
        return (self._get_obs(), float(reward), terminated, truncated, info)

    def _get_obs(self) -> np.ndarray:
        temps = self.rack.get_temperatures()
        loads = self.current_loads
        health = np.array([s.health for s in self.rack.servers])
        if self.prev_temps is None:
            trends = np.zeros_like(temps)
            temps_for_obs = temps.copy()
        else:
            obs_noise = self.np_random.normal(0, 0.3, self.num_servers)
            noisy_temps = temps + obs_noise
            trends = (noisy_temps - self.prev_temps) / 10.0
            trends = np.clip(trends * 0.5 + 0.5, 0, 1)
            temps_for_obs = noisy_temps
        t_min = self.config.physics.min_temp
        t_max = self.config.physics.max_temp
        norm_temps = (temps_for_obs - t_min) / (t_max - t_min + 1e-06)
        norm_temps = np.clip(norm_temps, 0, 1)
        self.prev_temps = temps_for_obs.copy()
        return np.concatenate([norm_temps, loads, health, trends]).astype(np.float32)

    def get_raw_observations(self) -> Dict[str, np.ndarray]:
        return {'temps': self.rack.get_temperatures(), 'loads': self.current_loads.copy(), 'health': np.array([s.health for s in self.rack.servers]), 'power': self.rack.get_total_power()}

    def _calculate_reward(self, stats: List[Dict[str, Any]], actions: np.ndarray) -> float:
        it_power = sum((s['it_power'] for s in stats))
        cooling_power = sum((s['cooling_power'] for s in stats))
        total_power = it_power + cooling_power
        avg_temp = np.mean([s['temp'] for s in stats])
        max_temp = np.max([s['temp'] for s in stats])
        avg_health = np.mean([s['health'] for s in stats])
        pue = total_power / (it_power + 1e-06)
        cfg = self.config.reward
        max_possible_power = self.config.physics.p_max * self.num_servers * 1.5
        power_fraction = total_power / max_possible_power
        energy_reward = cfg.energy_coefficient * 1.5 * (1.0 - power_fraction)
        pue_target = 1.1
        if pue < pue_target:
            pue_bonus = cfg.energy_efficiency_bonus * 2.0
        elif pue < 1.3:
            pue_bonus = cfg.energy_efficiency_bonus * (1.3 - pue) / 0.2
        else:
            pue_bonus = 0.0
        sweet_spot_bonus = 0.0
        if 55.0 <= max_temp <= 59.0:
            sweet_spot_bonus = 15.0
        avg_action = np.mean(actions)
        cooling_parsimony = 5.0 * (1.0 - avg_action)
        thermal_penalty = 0.0
        HARD_LIMIT = 60.0
        if max_temp > HARD_LIMIT:
            excess = max_temp - HARD_LIMIT
            thermal_penalty = 2.0 ** excess * 100.0
            if max_temp > cfg.critical_limit:
                thermal_penalty += 5000.0
        elif max_temp > cfg.safe_threshold:
            excess = max_temp - cfg.safe_threshold
            thermal_penalty = cfg.thermal_penalty_coefficient * excess ** 2.0
        if max_temp >= self.config.physics.max_temp:
            return float(-10000.0)
        jitter_penalty = 0.0
        if self.last_action is not None:
            smooth = np.mean(np.abs(actions - self.last_action))
            jitter_penalty = cfg.stability_weight * smooth * 5.0
        self.last_action = actions.copy()
        health_penalty = 0.0
        if avg_health < 0.9:
            health_penalty = 0.5 * (1.0 - avg_health)
        reward = energy_reward + pue_bonus + sweet_spot_bonus + cooling_parsimony - thermal_penalty - jitter_penalty - health_penalty
        return float(reward)

    def render(self, mode='human'):
        pass