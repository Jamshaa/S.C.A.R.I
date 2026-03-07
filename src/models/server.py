import numpy as np
from typing import Dict, List, Any
from src.models.cooling import CoolingSystem
import logging
logger = logging.getLogger(__name__)

class Server:

    def __init__(self, server_id: int, config: Any):
        self.id = server_id
        self.config = config
        self.temperature = config.physics.ambient_temp
        self.cpu_load = 0.0
        self.power_draw = config.physics.p_idle
        self.cooling_system = CoolingSystem(mode=config.cooling.mode, config=config.cooling)
        self.temp_history: List[float] = [self.temperature]
        self.power_history: List[float] = [self.power_draw]
        self.health = 1.0
        logger.debug(f'Server {self.id} init (cooling={config.cooling.mode})')

    def update_physics(self, cpu_load: float, cooling_action: float, dt: float=1.0, inlet_temp_offset: float=0.0) -> Dict[str, float]:
        cpu_load = np.clip(cpu_load, 0.0, 1.0)
        cooling_action = np.clip(cooling_action, 0.0, 1.0)
        u = cpu_load
        dynamic_factor = 0.3 + 0.7 * u ** 1.8 if u > 0 else 0.3
        p_idle = self.config.physics.p_idle
        p_max = self.config.physics.p_max
        it_dynamic_power = p_max * dynamic_factor
        t_ref = 45.0
        k_leak = 0.025
        base_leakage = p_max * 0.04
        leakage_power = base_leakage * np.exp(k_leak * (self.temperature - t_ref))
        self.power_draw = it_dynamic_power + leakage_power
        heat_generated = self.power_draw
        effective_ambient = self.config.physics.ambient_temp + inlet_temp_offset
        capacity = self.cooling_system.get_cooling_capacity(cooling_action, ambient_temp=effective_ambient, server_temp=self.temperature)
        heat_removed = capacity
        cooling_cost = self.cooling_system.get_power_consumption(cooling_action)
        net_heat = heat_generated - heat_removed
        delta_temp = net_heat * dt / self.config.physics.server_thermal_mass
        max_delta = self.config.physics.max_temp_change_per_second
        delta_temp = np.clip(delta_temp, -max_delta, max_delta)
        self.temperature += delta_temp
        aging_factor = np.exp(8000 * (1 / (273.15 + 40.0) - 1 / (273.15 + self.temperature)))
        self.health -= 1.5e-06 * aging_factor * dt
        self.health = max(0.0, self.health)
        self.temperature = np.clip(self.temperature, self.config.physics.min_temp, self.config.physics.max_temp)
        self.temp_history.append(self.temperature)
        self.power_history.append(self.power_draw + cooling_cost)
        return {'temp': self.temperature, 'it_power': self.power_draw, 'cooling_power': cooling_cost, 'heat_generated': heat_generated, 'heat_removed': heat_removed, 'health': self.health, 'leakage_power': leakage_power}

    def reset(self) -> None:
        self.temperature = np.random.uniform(35.0, 45.0)
        self.cpu_load = 0.0
        self.power_draw = self.config.physics.p_idle
        self.health = 1.0
        self.temp_history = [self.temperature]
        self.power_history = [self.power_draw]
        logger.debug(f'Server {self.id} reset')

    def __repr__(self) -> str:
        return f'Server(id={self.id}, T={self.temperature:.1f}°C, P={self.power_draw:.0f}W)'