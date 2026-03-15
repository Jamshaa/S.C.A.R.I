import pytest
import numpy as np
from src.envs.datacenter_env import DataCenterEnv
from src.utils.config import Config, DEFAULT_CONFIG

def test_env_initialization():
    env = DataCenterEnv(DEFAULT_CONFIG)
    assert env.num_servers == DEFAULT_CONFIG.environment.num_racks * DEFAULT_CONFIG.environment.servers_per_rack
    obs, _ = env.reset()
    assert obs.shape == env.observation_space.shape
    assert isinstance(obs, np.ndarray)

def test_env_step():
    env = DataCenterEnv(DEFAULT_CONFIG)
    env.reset()
    action = env.action_space.sample()
    obs, reward, terminated, truncated, info = env.step(action)
    assert obs.shape == env.observation_space.shape
    assert isinstance(reward, float)
    assert isinstance(terminated, bool)
    assert 'total_power' in info
    assert 'avg_temp' in info

def test_raw_observations():
    env = DataCenterEnv(DEFAULT_CONFIG)
    env.reset()
    raw_obs = env.get_raw_observations()
    assert 'temps' in raw_obs
    assert 'power' in raw_obs
    assert len(raw_obs['temps']) == env.num_servers


def test_env_terminates_on_hard_limit():
    cfg = Config()
    cfg.environment.safety_override = False
    cfg.environment.terminate_on_hard_limit = True
    env = DataCenterEnv(cfg)
    env.reset(seed=7)
    for server in env.rack.servers:
        server.temperature = cfg.reward.hard_limit + 3.0
    obs, reward, terminated, truncated, info = env.step(np.zeros(env.num_servers, dtype=np.float32))
    assert obs.shape == env.observation_space.shape
    assert terminated is True
    assert truncated is False
    assert info['hard_limit_violation'] is True


def test_safety_override_raises_actions_near_limit():
    cfg = Config()
    cfg.environment.safety_override = True
    cfg.environment.safety_override_temp = 55.0
    env = DataCenterEnv(cfg)
    env.reset(seed=11)
    env.current_loads = np.ones(env.num_servers, dtype=np.float32)
    env.prev_raw_temps = np.full(env.num_servers, 57.5, dtype=np.float32)
    for server in env.rack.servers:
        server.temperature = 59.0
    safe_action, meta = env._apply_safety_override(np.zeros(env.num_servers, dtype=np.float32))
    assert meta['active'] is True
    assert meta['fraction'] > 0.0
    assert np.all(safe_action >= cfg.environment.safety_min_action)


def test_reward_weights_shift_tradeoff_toward_energy_savings():
    conservative_cfg = Config()
    conservative_cfg.environment.num_racks = 1
    conservative_cfg.environment.servers_per_rack = 1
    conservative_cfg.reward.safe_threshold = 58.0
    conservative_cfg.reward.hard_limit = 60.0
    conservative_cfg.reward.critical_limit = 59.5
    conservative_cfg.reward.energy_weight = 1.0
    conservative_cfg.reward.safety_weight = 2.0

    aggressive_cfg = Config()
    aggressive_cfg.environment.num_racks = 1
    aggressive_cfg.environment.servers_per_rack = 1
    aggressive_cfg.reward.safe_threshold = 58.0
    aggressive_cfg.reward.hard_limit = 60.0
    aggressive_cfg.reward.critical_limit = 59.5
    aggressive_cfg.reward.energy_weight = 5.5
    aggressive_cfg.reward.safety_weight = 0.6

    conservative_env = DataCenterEnv(conservative_cfg)
    aggressive_env = DataCenterEnv(aggressive_cfg)
    conservative_env.reset(seed=3)
    aggressive_env.reset(seed=3)

    stats = [{'it_power': 500.0, 'cooling_power': 24.0, 'temp': 58.8, 'health': 1.0}]
    action = np.array([0.08], dtype=np.float32)

    conservative_reward = conservative_env._calculate_reward(stats, action)
    aggressive_reward = aggressive_env._calculate_reward(stats, action)

    assert aggressive_reward > conservative_reward


def test_facility_overhead_is_included_in_total_power():
    cfg = Config()
    cfg.cooling.facility_base_power = 120.0
    cfg.cooling.facility_power_ratio = 0.1
    env = DataCenterEnv(cfg)
    env.reset(seed=5)
    _, _, _, _, info = env.step(np.zeros(env.num_servers, dtype=np.float32))
    assert info['facility_power'] >= 120.0
    assert info['total_power'] >= info['it_power'] + info['cooling_power'] + 120.0
