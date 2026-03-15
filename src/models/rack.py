import numpy as np
from typing import List, Dict, Any
from src.models.server import Server
import logging
logger = logging.getLogger(__name__)

class Rack:

    def __init__(self, rack_id: int, num_servers: int, config: Any):
        self.id = rack_id
        self.num_servers = num_servers
        self.servers = [Server(i, config) for i in range(num_servers)]
        self.config = config
        self.last_cooling_power = 0.0
        logger.debug(f'Rack {self.id} initialized with {num_servers} servers')

    def update(self, loads: np.ndarray, actions: np.ndarray, ambient_temp: float | None=None) -> List[Dict[str, float]]:
        loads = np.clip(loads, 0, 1)
        actions = np.clip(actions, 0, 1)
        if len(loads) != self.num_servers or len(actions) != self.num_servers:
            logger.error(f'Rack {self.id} input size mismatch. Expected {self.num_servers}')
            raise ValueError('Input size mismatch')
        stats = []
        total_cooling_power = 0.0
        recirculation_factor = 0.08
        extra_inlet_heat = 0.0
        for i, server in enumerate(self.servers):
            stat = server.update_physics(loads[i], actions[i], inlet_temp_offset=extra_inlet_heat, ambient_temp=ambient_temp)
            extra_inlet_heat = stat['it_power'] / 500.0 * recirculation_factor
            stats.append(stat)
            total_cooling_power += stat['cooling_power']
        self.last_cooling_power = total_cooling_power
        return stats

    def get_total_power(self) -> float:
        it_power = sum((s.power_draw for s in self.servers))
        return float(it_power + self.last_cooling_power + self.get_facility_power())

    def get_facility_power(self) -> float:
        it_power = sum((s.power_draw for s in self.servers))
        return float(self.config.cooling.facility_base_power + it_power * self.config.cooling.facility_power_ratio)

    def get_temperatures(self) -> np.ndarray:
        return np.array([s.temperature for s in self.servers])

    def get_max_temperature(self) -> float:
        temps = self.get_temperatures()
        return float(np.max(temps)) if len(temps) > 0 else self.config.physics.ambient_temp

    def get_avg_temperature(self) -> float:
        temps = self.get_temperatures()
        return float(np.mean(temps)) if len(temps) > 0 else self.config.physics.ambient_temp

    def get_avg_cooling_power(self) -> float:
        return self.last_cooling_power / self.num_servers if self.num_servers > 0 else 0.0

    def get_avg_health(self) -> float:
        return float(np.mean([s.health for s in self.servers])) if self.servers else 1.0

    def get_it_raw_power(self) -> float:
        return sum((s.power_draw for s in self.servers))

    def get_cooling_raw_power(self) -> float:
        return self.last_cooling_power

    def reset(self) -> None:
        for server in self.servers:
            server.reset()
        self.last_cooling_power = 0.0
        logger.debug(f'Rack {self.id} reset')

    def __repr__(self) -> str:
        max_temp = self.get_max_temperature()
        total_power = self.get_total_power()
        return f'Rack(id={self.id}, servers={self.num_servers}, T_max={max_temp:.1f}ºC, P={total_power:.0f}W)'
