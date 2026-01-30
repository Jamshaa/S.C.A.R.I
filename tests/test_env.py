
import pytest
import numpy as np
from src.envs.datacenter_env import DataCenterEnv
from src.utils.config import DEFAULT_CONFIG

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
    assert "total_power" in info
    assert "avg_temp" in info

def test_raw_observations():
    env = DataCenterEnv(DEFAULT_CONFIG)
    env.reset()
    raw_obs = env.get_raw_observations()
    assert "temps" in raw_obs
    assert "power" in raw_obs
    assert len(raw_obs['temps']) == env.num_servers
