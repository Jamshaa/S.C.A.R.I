# src/models/rack.py
import numpy as np
from typing import List, Dict
from src.models.server import Server

class Rack:
    def __init__(self, rack_id: int, num_servers: int, config):
        self.id = rack_id
        self.num_servers = num_servers
        self.servers = [Server(i, config) for i in range(num_servers)]
        self.config = config
        self.last_cooling_power = 0.0
    
    def update(self, loads: np.ndarray, actions: np.ndarray) -> List[Dict]:
        loads = np.clip(loads, 0, 1)
        actions = np.clip(actions, 0, 1)
        
        assert len(loads) == self.num_servers
        assert len(actions) == self.num_servers
        
        stats = []
        total_cooling_power = 0.0
        
        for i, server in enumerate(self.servers):
            stat = server.update_physics(loads[i], actions[i])
            stats.append(stat)
            total_cooling_power += stat['cooling_power']
        
        self.last_cooling_power = total_cooling_power
        return stats
    
    def get_total_power(self) -> float:
        it_power = sum(s.power_draw for s in self.servers)
        return it_power + self.last_cooling_power
    
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
    
    def reset(self) -> None:
        for server in self.servers:
            server.reset()
        self.last_cooling_power = 0.0
    
    def __repr__(self) -> str:
        max_temp = self.get_max_temperature()
        total_power = self.get_total_power()
        return f"Rack(id={self.id}, servers={self.num_servers}, T_max={max_temp:.1f}ºC, P={total_power:.0f}W)"
