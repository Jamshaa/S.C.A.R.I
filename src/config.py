# src/config.py
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
import yaml
import json
import logging

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
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
    max_fan_power: float = 500.0  # Ultra-high density fans for AI hardware
    max_pump_power: float = 50.0
    base_pump_power: float = 10.0
    air_cooling_capacity: float = 3000.0
    liquid_cooling_capacity: float = 12000.0
    natural_convection: float = 50.0

@dataclass
class RewardConfig:
    """Configuration for reward calculation parameters."""
    energy_coefficient: float = 15.0
    safe_threshold: float = 70.0
    critical_limit: float = 90.0
    thermal_penalty_coefficient: float = 10.0
    emergency_penalty: float = 100.0
    energy_efficiency_bonus: float = 2.0

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
    num_racks: int = 1
    servers_per_rack: int = 10
    max_load_change_per_step: float = 0.05
    min_initial_load: float = 0.1
    max_initial_load: float = 0.3
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
    def from_yaml(cls, path: str) -> 'Config':
        """Load configuration from a YAML file."""
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
    
    def to_json(self, path: str) -> None:
        """Save configuration to a JSON file."""
        try:
            with open(path, 'w') as f:
                json.dump(self.to_dict(), f, indent=2)
        except Exception as e:
            logger.error(f"Error saving config to {path}: {e}")
            raise

DEFAULT_CONFIG = Config()
AGGRESSIVE_CONFIG = Config(
    reward=RewardConfig(
        energy_coefficient=20.0,
        safe_threshold=75.0,
        thermal_penalty_coefficient=5.0,
    )
)
CONSERVATIVE_CONFIG = Config(
    reward=RewardConfig(
        energy_coefficient=10.0,
        safe_threshold=65.0,
        thermal_penalty_coefficient=15.0,
    )
)
PRODUCTION_CONFIG = Config(
    physics=PhysicsConfig(
        ambient_temp=24.0,
        p_idle=250.0,
    ),
    training=TrainingConfig(
        timesteps=1000000,
        learning_rate=0.00005,
    ),
    reward=RewardConfig(
        energy_coefficient=15.0,
        safe_threshold=70.0,
        critical_limit=85.0,
    )
)
