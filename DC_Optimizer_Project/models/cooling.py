# src/models/cooling.py
import numpy as np
from typing import Tuple, Optional

class CoolingSystem:
    def __init__(self, mode: str = "AIR", config=None):
        self.mode = mode
        self.config = config
        if self.config is None:
            from src.config import CoolingConfig
            self.config = CoolingConfig()
    
    def get_power_consumption(self, flow_rate: float) -> float:
        flow_rate = np.clip(flow_rate, 0.0, 1.0)
        
        if self.mode == "AIR":
            power = self.config.max_fan_power * (flow_rate ** 3)
            power += 0.1 * self.config.max_fan_power * (1 if flow_rate > 0 else 0)
        
        elif self.mode == "LIQUID":
            power = self.config.base_pump_power
            if flow_rate > 0:
                efficiency_factor = 0.8 + 0.4 * np.sin(flow_rate * np.pi / 2)
                power += self.config.max_pump_power * (flow_rate ** 2) * efficiency_factor
        
        elif self.mode == "HYBRID":
            air_flow = 0.3 * flow_rate
            liquid_flow = 0.7 * flow_rate
            air_power = self.config.max_fan_power * (air_flow ** 3)
            liquid_power = self.config.base_pump_power
            if liquid_flow > 0:
                liquid_power += self.config.max_pump_power * (liquid_flow ** 2)
            power = air_power + liquid_power
        
        else:
            raise ValueError(f"Unknown cooling mode: {self.mode}")
        
        return float(power)
    
    def get_cooling_capacity(self, flow_rate: float) -> float:
        flow_rate = np.clip(flow_rate, 0.0, 1.0)
        
        if self.mode == "AIR":
            passive = self.config.natural_convection
            active = flow_rate * self.config.air_cooling_capacity
            return passive + active
        
        elif self.mode == "LIQUID":
            return flow_rate * self.config.liquid_cooling_capacity
        
        elif self.mode == "HYBRID":
            air_cooling = 0.3 * flow_rate * self.config.air_cooling_capacity
            liquid_cooling = 0.7 * flow_rate * self.config.liquid_cooling_capacity
            return air_cooling + liquid_cooling
        
        return 0.0
    
    def __repr__(self) -> str:
        return f"CoolingSystem(mode={self.mode}, max_power={self.config.max_fan_power}W)"
