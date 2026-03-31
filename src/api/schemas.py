from typing import Optional

from pydantic import BaseModel, field_validator

from src.api.common import (
    normalize_model_filename,
    normalize_output_name,
    resolve_config_path,
)
from src.utils.greendc import GreenDCCalculator


class TrainingParams(BaseModel):
    timesteps: int = 10000
    config: str = "configs/default.yaml"
    name: str = "scari_model"
    cooling_mode: str = "AIR"

    @field_validator("timesteps")
    @classmethod
    def validate_timesteps(cls, value: int) -> int:
        if value < 1000 or value > 10000000:
            raise ValueError("timesteps must be between 1,000 and 10,000,000")
        return value

    @field_validator("config")
    @classmethod
    def validate_config(cls, value: str) -> str:
        return str(resolve_config_path(value))

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        return normalize_output_name(value)

    @field_validator("cooling_mode")
    @classmethod
    def validate_cooling_mode(cls, value: str) -> str:
        valid = {"AIR", "LIQUID", "HYBRID"}
        normalized = value.upper()
        if normalized not in valid:
            raise ValueError(f"cooling_mode must be one of {sorted(valid)}")
        return normalized


class RenameRequest(BaseModel):
    old_name: str
    new_name: str

    @field_validator("new_name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        return normalize_model_filename(value)


class EvaluationRequest(BaseModel):
    model: str = "default_model.zip"
    models: Optional[list[str]] = None
    steps: int = 5000
    name: Optional[str] = None
    config: str = "configs/default.yaml"

    @field_validator("steps")
    @classmethod
    def validate_steps(cls, value: int) -> int:
        if value < 100 or value > 100000:
            raise ValueError("steps must be between 100 and 100,000")
        return value

    @field_validator("config")
    @classmethod
    def validate_config(cls, value: str) -> str:
        return str(resolve_config_path(value))


class DataCenterParams(BaseModel):
    num_servers: int
    topology: str = "spine_leaf"
    annual_power_kwh: float = 1000000
    baseline_pue: float = 1.67
    optimized_pue: float = 1.1
    region: str = "EU"

    @field_validator("num_servers")
    @classmethod
    def validate_servers(cls, value: int) -> int:
        if value < 1 or value > 100000:
            raise ValueError("num_servers must be between 1 and 100,000")
        return value

    @field_validator("topology")
    @classmethod
    def validate_topology(cls, value: str) -> str:
        valid_topologies = {"fat_tree", "clos", "spine_leaf", "three_tier"}
        if value not in valid_topologies:
            raise ValueError(f"topology must be one of {sorted(valid_topologies)}")
        return value

    @field_validator("region")
    @classmethod
    def validate_region(cls, value: str) -> str:
        valid_regions = set(GreenDCCalculator.REGION_DATA.keys())
        if value not in valid_regions:
            raise ValueError(f"region must be one of {sorted(valid_regions)}")
        return value


class ROIParams(BaseModel):
    num_servers: int
    investment_eur: float
    annual_savings_eur: float
    region: str = "EU"

    @field_validator("investment_eur", "annual_savings_eur")
    @classmethod
    def validate_positive(cls, value: float) -> float:
        if value < 0:
            raise ValueError("Values must be non-negative")
        return value

    @field_validator("region")
    @classmethod
    def validate_region(cls, value: str) -> str:
        valid_regions = set(GreenDCCalculator.REGION_DATA.keys())
        if value not in valid_regions:
            raise ValueError(f"region must be one of {sorted(valid_regions)}")
        return value
