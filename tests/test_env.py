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
