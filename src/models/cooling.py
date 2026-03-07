import numpy as np
from typing import Dict, Any
import logging
logger = logging.getLogger(__name__)

class CoolingSystem:

    def __init__(self, mode: str='AIR', config: Any=None):
        self.mode = mode.upper()
        self.config = config
        if self.config is None:
            from src.utils.config import CoolingConfig
            self.config = CoolingConfig(mode=self.mode)
        self.efficiency_factor = 1.0
        self.operating_hours = 0.0
        if self.mode == 'HYBRID':
            self._air_sub = CoolingSystem('AIR', self.config)
            self._liquid_sub = CoolingSystem('LIQUID', self.config)
        logger.debug(f'CoolingSystem initialized: mode={self.mode}')

    def get_power_consumption(self, flow_rate: float) -> float:
        flow_rate = np.clip(flow_rate, 0.0, 1.0)
        if self.mode == 'AIR':
            if flow_rate < 0.05:
                power = 3.0
            else:
                base_power = self.config.max_fan_power * flow_rate ** 3.0
                if 0.4 <= flow_rate <= 0.8:
                    eff = 1.0
                elif flow_rate > 0.8:
                    eff = 1.0 + 0.4 * ((flow_rate - 0.8) / 0.2) ** 2
                else:
                    eff = 1.0 + 0.15 * ((0.4 - flow_rate) / 0.4)
                power = base_power * eff
        elif self.mode == 'LIQUID':
            if flow_rate < 0.05:
                power = self.config.base_pump_power
            else:
                variable = self.config.max_pump_power * flow_rate ** 2.2
                power = self.config.base_pump_power + variable
        elif self.mode == 'HYBRID':
            air_power = self._air_sub.get_power_consumption(flow_rate * 0.6)
            liquid_power = self._liquid_sub.get_power_consumption(flow_rate * 0.4)
            power = air_power + liquid_power
        else:
            raise ValueError(f'Unknown cooling mode: {self.mode}')
        power *= 2.0 - self.efficiency_factor
        return float(power)

    def get_cooling_capacity(self, flow_rate: float, ambient_temp: float=25.0, server_temp: float=50.0) -> float:
        flow_rate = np.clip(flow_rate, 0.0, 1.0)
        delta_t = max(0.1, server_temp - ambient_temp)
        if self.mode == 'AIR':
            passive = self.config.natural_convection * (delta_t / 20.0)
            if flow_rate < 0.1:
                active = 0.0
            else:
                base = self.config.air_cooling_capacity
                active = base * flow_rate * (delta_t / 25.0)
            economizer = 0.0
            if ambient_temp < 15.0:
                economizer = 2500.0 * flow_rate
            elif ambient_temp < 22.0:
                quality = (22.0 - ambient_temp) / 7.0
                economizer = 1200.0 * flow_rate * quality
            return float(passive + active + economizer)
        elif self.mode == 'LIQUID':
            effectiveness = min(1.0, delta_t / 40.0)
            capacity = flow_rate * self.config.liquid_cooling_capacity * effectiveness
            return float(capacity)
        elif self.mode == 'HYBRID':
            air_cap = self._air_sub.get_cooling_capacity(flow_rate * 0.6, ambient_temp, server_temp)
            liquid_cap = self._liquid_sub.get_cooling_capacity(flow_rate * 0.4, ambient_temp, server_temp)
            return float(air_cap + liquid_cap)
        return 0.0

    def get_cost_info(self) -> Dict[str, Any]:
        from src.utils.config import COOLING_COST_DB
        if self.mode in COOLING_COST_DB:
            return COOLING_COST_DB[self.mode]
        return COOLING_COST_DB['AIR']

    def update_degradation(self, dt: float=1.0) -> None:
        self.operating_hours += dt / 3600.0
        degradation_rate = 0.01 / 1000.0
        self.efficiency_factor = max(0.85, 1.0 - degradation_rate * self.operating_hours)
        if self.mode == 'HYBRID':
            self._air_sub.update_degradation(dt)
            self._liquid_sub.update_degradation(dt)

    def __repr__(self) -> str:
        return f'CoolingSystem(mode={self.mode}, efficiency={self.efficiency_factor:.3f})'