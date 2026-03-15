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
        self.prev_raw_temps = None
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
        self.prev_raw_temps = self.prev_temps.copy()
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
        max_load_delta = self.config.environment.max_load_change_per_step
        load_noise = np.clip(load_noise, -max_load_delta, max_load_delta)
        self.current_loads = np.clip(self.current_loads + load_noise, 0.0, 1.0).astype(np.float32)
        effective_action, safety_meta = self._apply_safety_override(action)
        stats = self.rack.update(self.current_loads, effective_action)
        reward = self._calculate_reward(stats, effective_action)
        temps = self.rack.get_temperatures()
        max_temp = np.max(temps)
        hard_limit = self._get_hard_limit()
        hard_limit_violation = bool(max_temp >= hard_limit)
        terminated = bool(max_temp >= self.config.physics.max_temp or (self.config.environment.terminate_on_hard_limit and hard_limit_violation))
        truncated = bool(self.step_count >= self.config.environment.max_steps)
        self.episode_rewards.append(reward)
        self.episode_temps.append(max_temp)
        self.episode_powers.append(self.rack.get_total_power())
        self.step_count += 1
        info = {
            'total_power': self.rack.get_total_power(),
            'max_temp': float(max_temp),
            'avg_temp': self.rack.get_avg_temperature(),
            'avg_health': self.rack.get_avg_health(),
            'it_power': float(sum((s['it_power'] for s in stats))),
            'cooling_power': float(sum((s['cooling_power'] for s in stats))),
            'stats': stats,
            'hard_limit': hard_limit,
            'hard_limit_violation': hard_limit_violation,
            'safety_override_active': safety_meta['active'],
            'safety_override_fraction': safety_meta['fraction'],
            'avg_action': float(np.mean(effective_action)),
        }
        return (self._get_obs(), float(reward), terminated, truncated, info)

    def _get_hard_limit(self) -> float:
        return float(min(self.config.reward.hard_limit, self.config.physics.max_temp))

    def _apply_safety_override(self, action: np.ndarray) -> Tuple[np.ndarray, Dict[str, float]]:
        if not self.config.environment.safety_override:
            return action, {'active': False, 'fraction': 0.0}
        temps = self.rack.get_temperatures()
        prev_temps = self.prev_raw_temps if self.prev_raw_temps is not None else temps
        temp_rise = np.clip(temps - prev_temps, 0.0, 5.0)
        hard_limit = self._get_hard_limit()
        activation_temp = min(self.config.environment.safety_override_temp, hard_limit - 0.5)
        if hard_limit <= activation_temp:
            return action, {'active': False, 'fraction': 0.0}
        ramp = np.clip((temps - activation_temp) / (hard_limit - activation_temp + 1e-6), 0.0, 1.0)
        lookahead = np.clip(temp_rise / 2.5, 0.0, 1.0) * self.config.environment.safety_lookahead_weight
        load_pressure = np.clip((self.current_loads - 0.72) / 0.28, 0.0, 1.0) * self.config.environment.safety_load_weight
        required = self.config.environment.safety_min_action + ramp * (self.config.environment.safety_max_action - self.config.environment.safety_min_action)
        required = np.clip(required + lookahead + load_pressure, 0.0, self.config.environment.safety_max_action)
        safe_action = np.maximum(action, required).astype(np.float32)
        diff = np.maximum(safe_action - action, 0.0)
        return safe_action, {'active': bool(np.any(diff > 1e-4)), 'fraction': float(np.mean(diff))}

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
            raw_prev = self.prev_raw_temps if self.prev_raw_temps is not None else self.prev_temps
            trends = (temps - raw_prev) / 10.0
            trends = np.clip(trends * 0.5 + 0.5, 0, 1)
            temps_for_obs = noisy_temps
        t_min = self.config.physics.min_temp
        t_max = self.config.physics.max_temp
        norm_temps = (temps_for_obs - t_min) / (t_max - t_min + 1e-06)
        norm_temps = np.clip(norm_temps, 0, 1)
        self.prev_temps = temps_for_obs.copy()
        self.prev_raw_temps = temps.copy()
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
        cooling_ceiling = self.num_servers * max(self.config.cooling.max_fan_power, self.config.cooling.max_pump_power, 1.0)
        max_possible_power = self.config.physics.p_max * self.num_servers + cooling_ceiling
        power_fraction = total_power / max_possible_power
        cooling_fraction = cooling_power / (cooling_ceiling + 1e-06)
        energy_reward = cfg.energy_coefficient * (1.0 - power_fraction)
        if pue < 1.12:
            pue_bonus = cfg.energy_efficiency_bonus * 1.15
        elif pue < 1.24:
            pue_bonus = cfg.energy_efficiency_bonus * (1.24 - pue) / 0.12
        else:
            pue_bonus = 0.0
        sweet_spot_bonus = cfg.sweet_spot_bonus if cfg.sweet_spot_low <= max_temp <= cfg.sweet_spot_high else 0.0
        cooling_penalty = cfg.cooling_power_weight * cooling_fraction * cfg.energy_coefficient
        thermal_penalty = 0.0
        hard_limit = self._get_hard_limit()
        warning_start = max(cfg.safe_threshold, hard_limit - cfg.warning_margin)
        if max_temp > hard_limit:
            excess = max_temp - hard_limit
            thermal_penalty += cfg.hard_limit_penalty * (1.0 + excess * 2.5) ** 2
            thermal_penalty += cfg.emergency_penalty
        elif max_temp > warning_start:
            proximity = (max_temp - warning_start) / max(hard_limit - warning_start, 1e-06)
            thermal_penalty += cfg.preemptive_penalty_coefficient * proximity ** 2 * (1.0 + 4.0 * proximity)
        elif max_temp > cfg.safe_threshold:
            excess = max_temp - cfg.safe_threshold
            thermal_penalty += cfg.thermal_penalty_coefficient * excess ** 2.0
        if max_temp > cfg.critical_limit:
            thermal_penalty += cfg.emergency_penalty * max(0.0, max_temp - cfg.critical_limit + 1.0)
        if max_temp >= hard_limit and self.config.environment.terminate_on_hard_limit:
            return float(-(cfg.hard_limit_penalty + thermal_penalty))
        if max_temp >= self.config.physics.max_temp:
            return float(-10000.0)
        jitter_penalty = 0.0
        if self.last_action is not None:
            smooth = np.mean(np.abs(actions - self.last_action))
            jitter_penalty = cfg.stability_weight * smooth * 5.0
        self.last_action = actions.copy()
        health_penalty = 0.0
        if avg_health < 0.9:
            health_penalty = 8.0 * (1.0 - avg_health)
        overcooling_penalty = 0.0
        efficient_floor = max(self.config.physics.ambient_temp + 12.0, cfg.sweet_spot_low - 7.0)
        if avg_temp < efficient_floor and cooling_fraction > 0.18:
            overcooling_gap = efficient_floor - avg_temp
            overcooling_penalty = cfg.overcooling_penalty_coefficient * overcooling_gap * (1.0 + cooling_fraction)
        reward = energy_reward + pue_bonus + sweet_spot_bonus - cooling_penalty - thermal_penalty - jitter_penalty - health_penalty - overcooling_penalty
        return float(reward)

    def render(self, mode='human'):
        pass
