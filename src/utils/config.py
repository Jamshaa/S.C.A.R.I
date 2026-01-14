# src/utils/config.py
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Union
from pathlib import Path
import yaml
import json
import logging

logger = logging.getLogger(__name__)

@dataclass
class PhysicsConfig:
    """Configuration for server and datacenter physics."""
    ambient_temp: float = 22.0
    server_thermal_mass: float = 15000
    p_idle: float = 200.0
    p_max: float = 800.0
    r_coeff: float = 0.5
    max_temp: float = 95.0
    min_temp: float = 22.0
    max_temp_change_per_second: float = 5.0

@dataclass
class CoolingConfig:
    """Configuration for the cooling system parameters."""
    mode: str = "AIR"
    max_fan_power: float = 1000.0
    max_pump_power: float = 50.0
    base_pump_power: float = 10.0
    air_cooling_capacity: float = 3000.0
    liquid_cooling_capacity: float = 12000.0
    natural_convection: float = 50.0

@dataclass
class RewardConfig:
    """Configuration for reward calculation parameters."""
    target_temp_min: float = 50.0
    target_temp_max: float = 60.0
    safety_limit: float = 75.0
    critical_limit: float = 85.0
    energy_weight: float = 0.8
    safety_weight: float = 2.0
    stability_weight: float = 0.2
    # Keep legacy names as optional or defaults if needed for compatibility
    energy_coefficient: float = 15.0
    thermal_penalty_coefficient: float = 10.0

@dataclass
class TrainingConfig:
    """Configuration for RL training parameters."""
    timesteps: int = 500000
    learning_rate: float = 0.0001
    n_steps: int = 4096
    batch_size: int = 128
    gamma: float = 0.99
    gae_lambda: float = 0.95
    ent_coef: float = 0.001
    vf_coef: float = 0.5
    max_grad_norm: float = 0.5
    n_epochs: int = 10
    clip_range: float = 0.2
    normalize_advantage: bool = True
    normalize_observation: bool = True

@dataclass
class EnvironmentConfig:
    """Configuration for the datacenter environment structure."""
    num_servers: int = 10
    max_steps: int = 1000
    num_racks: int = 1
    servers_per_rack: int = 10
    max_load_change_per_step: float = 0.05
    min_initial_load: float = 0.6
    max_initial_load: float = 0.9
    load_std: float = 0.1
    episode_length: int = 1000

@dataclass
class Config:
    """Main configuration container for S.C.A.R.I."""
    physics: PhysicsConfig = field(default_factory=PhysicsConfig)
    cooling: CoolingConfig = field(default_factory=CoolingConfig)
    reward: RewardConfig = field(default_factory=RewardConfig)
    training: TrainingConfig = field(default_factory=TrainingConfig)
    environment: EnvironmentConfig = field(default_factory=EnvironmentConfig)
    
    @classmethod
    def from_yaml(cls, path: Union[str, Path]) -> 'Config':
        """Load configuration from a YAML file."""
        path = Path(path)
        try:
            with open(path, 'r') as f:
                data = yaml.safe_load(f)
            return cls(
                physics=PhysicsConfig(**data.get('physics', {})),
                cooling=CoolingConfig(**data.get('cooling', {})),
                reward=RewardConfig(**data.get('reward', {})),
                training=TrainingConfig(**data.get('training', {})),
                environment=EnvironmentConfig(**data.get('environment', {})),
            )
        except Exception as e:
            logger.error(f"Error loading config from {path}: {e}")
            raise
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to a dictionary."""
        return {
            'physics': self.physics.__dict__,
            'cooling': self.cooling.__dict__,
            'reward': self.reward.__dict__,
            'training': self.training.__dict__,
            'environment': self.environment.__dict__,
        }
    
    def to_json(self, path: Union[str, Path]) -> None:
        """Save configuration to a JSON file."""
        path = Path(path)
        try:
            with open(path, 'w') as f:
                json.dump(self.to_dict(), f, indent=2)
        except Exception as e:
            logger.error(f"Error saving config to {path}: {e}")
            raise

DEFAULT_CONFIG = Config()
