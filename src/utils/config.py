from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Union, List
from pathlib import Path
import yaml
import json
import logging
logger = logging.getLogger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CONFIGS_DIR = PROJECT_ROOT / 'configs'
PREFERRED_CONFIG_NAME = 'optimized.yaml'
PREFERRED_CONFIG_PATH = CONFIGS_DIR / PREFERRED_CONFIG_NAME


def get_available_config_paths() -> List[Path]:
    configs = sorted(CONFIGS_DIR.glob('*.yaml')) + sorted(CONFIGS_DIR.glob('*.yml'))
    deduped = []
    seen = set()
    for config_path in configs:
        resolved = config_path.resolve()
        if resolved not in seen and config_path.is_file():
            deduped.append(resolved)
            seen.add(resolved)
    return deduped


def resolve_config_file(config_value: Optional[Union[str, Path]]=None) -> Path:
    if config_value:
        candidate = Path(config_value)
        if candidate.is_absolute():
            resolved = candidate.resolve()
        else:
            project_candidate = (PROJECT_ROOT / candidate).resolve()
            configs_candidate = (CONFIGS_DIR / candidate.name).resolve()
            if project_candidate.exists():
                resolved = project_candidate
            else:
                resolved = configs_candidate
        if not resolved.exists():
            raise FileNotFoundError(f'Config file not found: {config_value}')
        return resolved
    if PREFERRED_CONFIG_PATH.exists():
        return PREFERRED_CONFIG_PATH.resolve()
    available = get_available_config_paths()
    if available:
        return available[0]
    raise FileNotFoundError('No YAML configs were found in configs/')


def prompt_for_config_selection(default_config: Optional[Union[str, Path]]=None) -> Path:
    available = get_available_config_paths()
    if not available:
        raise FileNotFoundError('No YAML configs were found in configs/')
    default_path = resolve_config_file(default_config) if default_config else resolve_config_file()
    print('\nAvailable configuration profiles:')
    for idx, config_path in enumerate(available, start=1):
        marker = ' (default)' if config_path == default_path else ''
        print(f'  {idx}. {config_path.name}{marker}')
    while True:
        try:
            choice = input(f"Choose config [Enter={default_path.name}]: ").strip()
        except EOFError:
            return default_path
        if not choice:
            return default_path
        if choice.isdigit():
            index = int(choice) - 1
            if 0 <= index < len(available):
                return available[index]
        for config_path in available:
            if choice.lower() in {config_path.name.lower(), config_path.stem.lower()}:
                return config_path
        print('Invalid selection. Enter the number or filename shown above.')
COOLING_COST_DB = {'AIR': {'label': 'Air Cooling', 'description': 'Traditional CRAC/CRAH forced-air cooling', 'capex_per_server_eur': 150, 'opex_per_server_year_eur': 55, 'typical_pue': 1.4, 'max_density_kw_per_rack': 8}, 'LIQUID': {'label': 'Direct Liquid Cooling', 'description': 'Cold-plate or immersion liquid cooling', 'capex_per_server_eur': 850, 'opex_per_server_year_eur': 120, 'typical_pue': 1.05, 'max_density_kw_per_rack': 100}, 'HYBRID': {'label': 'Hybrid Cooling', 'description': 'Liquid for CPUs/GPUs + air for memory/storage', 'capex_per_server_eur': 500, 'opex_per_server_year_eur': 90, 'typical_pue': 1.15, 'max_density_kw_per_rack': 40}}

@dataclass
class PhysicsConfig:
    ambient_temp: float = 25.0
    server_thermal_mass: float = 12000
    p_idle: float = 180.0
    p_max: float = 750.0
    r_coeff: float = 0.5
    max_temp: float = 85.0
    min_temp: float = 15.0
    max_temp_change_per_second: float = 5.0

@dataclass
class CoolingConfig:
    mode: str = 'AIR'
    max_fan_power: float = 120.0
    max_pump_power: float = 60.0
    base_pump_power: float = 8.0
    air_cooling_capacity: float = 1200.0
    liquid_cooling_capacity: float = 15000.0
    natural_convection: float = 8.0
    air_idle_power: float = 12.0
    liquid_idle_power: float = 8.0
    distribution_power: float = 8.0
    auxiliary_power_ratio: float = 0.24
    hybrid_coordination_power: float = 4.0
    facility_base_power: float = 0.0
    facility_power_ratio: float = 0.0
    capex_per_server: float = 150.0
    opex_per_server_year: float = 55.0

    def __post_init__(self):
        if self.mode in COOLING_COST_DB:
            db = COOLING_COST_DB[self.mode]
            if self.capex_per_server == 150.0 and self.mode != 'AIR':
                self.capex_per_server = db['capex_per_server_eur']
            if self.opex_per_server_year == 55.0 and self.mode != 'AIR':
                self.opex_per_server_year = db['opex_per_server_year_eur']

    def get_cost_summary(self, num_servers: int, years: int=5) -> Dict[str, Any]:
        capex_total = self.capex_per_server * num_servers
        opex_annual = self.opex_per_server_year * num_servers
        tco = capex_total + opex_annual * years
        return {'mode': self.mode, 'num_servers': num_servers, 'capex_total_eur': round(capex_total, 2), 'opex_annual_eur': round(opex_annual, 2), 'tco_eur': round(tco, 2), 'tco_years': years, 'capex_per_server_eur': self.capex_per_server, 'opex_per_server_year_eur': self.opex_per_server_year}

@dataclass
class RewardConfig:
    critical_limit: float = 45.0
    energy_weight: float = 3.0
    safety_weight: float = 1.5
    stability_weight: float = 0.3
    profile: str = 'TOTAL_POWER_FIRST'
    energy_coefficient: float = 25.0
    thermal_penalty_coefficient: float = 8.0
    safe_threshold: float = 35.0
    emergency_penalty: float = 500.0
    hard_limit: float = 60.0
    warning_margin: float = 6.0
    preemptive_penalty_coefficient: float = 30.0
    hard_limit_penalty: float = 2000.0

@dataclass
class TrainingConfig:
    timesteps: int = 600000
    learning_rate: float = 0.0003
    n_steps: int = 2048
    batch_size: int = 64
    gamma: float = 0.995
    gae_lambda: float = 0.95
    ent_coef: float = 0.005
    vf_coef: float = 0.5
    max_grad_norm: float = 0.5
    n_epochs: int = 10
    clip_range: float = 0.2
    normalize_advantage: bool = True
    normalize_observation: bool = True

@dataclass
class EnvironmentConfig:
    num_servers: int = 10
    max_steps: int = 2000
    num_racks: int = 1
    servers_per_rack: int = 10
    max_load_change_per_step: float = 0.08
    min_initial_load: float = 0.3
    max_initial_load: float = 0.85
    load_std: float = 0.08
    terminate_on_hard_limit: bool = True
    safety_override: bool = True
    safety_override_temp: float = 56.0
    safety_min_action: float = 0.2
    safety_max_action: float = 1.0
    safety_lookahead_weight: float = 0.35
    safety_load_weight: float = 0.18

@dataclass
class Config:
    physics: PhysicsConfig = field(default_factory=PhysicsConfig)
    cooling: CoolingConfig = field(default_factory=CoolingConfig)
    reward: RewardConfig = field(default_factory=RewardConfig)
    training: TrainingConfig = field(default_factory=TrainingConfig)
    environment: EnvironmentConfig = field(default_factory=EnvironmentConfig)

    @classmethod
    def from_yaml(cls, path: Union[str, Path]) -> 'Config':
        path = Path(path)
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            env_data = data.get('environment', data.get('env', {}))
            return cls(physics=PhysicsConfig(**data.get('physics', {})), cooling=CoolingConfig(**data.get('cooling', {})), reward=RewardConfig(**data.get('reward', {})), training=TrainingConfig(**data.get('training', {})), environment=EnvironmentConfig(**env_data))
        except Exception as e:
            logger.error(f'Error loading config from {path}: {e}')
            raise

    def to_dict(self) -> Dict[str, Any]:
        return {'physics': self.physics.__dict__, 'cooling': self.cooling.__dict__, 'reward': self.reward.__dict__, 'training': self.training.__dict__, 'environment': self.environment.__dict__}

    def to_json(self, path: Union[str, Path]) -> None:
        path = Path(path)
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(self.to_dict(), f, indent=2)
        except Exception as e:
            logger.error(f'Error saving config to {path}: {e}')
            raise
DEFAULT_CONFIG = Config()
