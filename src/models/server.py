# src/models/server.py
import numpy as np
from typing import Dict, List, Any
from src.models.cooling import CoolingSystem
import logging

logger = logging.getLogger(__name__)

class Server:
    """Simulates a single server's thermal and power profile."""
    
    def __init__(self, server_id: int, config: Any):
        """
        Initialize the server.
        
        Args:
            server_id: Unique identifier for the server.
            config: Configuration object.
        """
        self.id = server_id
        self.config = config
        self.temperature = config.physics.ambient_temp
        self.cpu_load = 0.0
        self.power_draw = config.physics.p_idle
        self.cooling_system = CoolingSystem(mode="AIR", config=config.cooling)
        self.temp_history: List[float] = [self.temperature]
        self.power_history: List[float] = [self.power_draw]
        logger.debug(f"Server {self.id} initialized")
    
    def update_physics(self, cpu_load: float, cooling_action: float, dt: float = 1.0) -> Dict[str, float]:
        """
        Update server physical state based on load and cooling.
        
        Args:
            cpu_load: Normalized CPU load (0.0 to 1.0).
            cooling_action: Normalized cooling action (0.0 to 1.0).
            dt: Time step duration.
            
        Returns:
            Dictionary containing state update statistics.
        """
        cpu_load = np.clip(cpu_load, 0.0, 1.0)
        cooling_action = np.clip(cooling_action, 0.0, 1.0)
        
        # Calculate dynamic power consumption
        u = cpu_load
        r = self.config.physics.r_coeff
        dynamic_factor = (2 * u) - (u ** r)
        
        p_idle = self.config.physics.p_idle
        p_max = self.config.physics.p_max
        self.power_draw = p_idle + (p_max - p_idle) * dynamic_factor
        heat_generated = self.power_draw
        
        # Calculate cooling effect
        heat_removed = self.cooling_system.get_cooling_capacity(cooling_action)
        cooling_cost = self.cooling_system.get_power_consumption(cooling_action)
        
        # Thermal dynamics
        net_heat = heat_generated - heat_removed
        delta_temp = (net_heat * dt) / self.config.physics.server_thermal_mass
        
        # Clip temperature change rate
        max_delta = self.config.physics.max_temp_change_per_second
        delta_temp = np.clip(delta_temp, -max_delta, max_delta)
        
        self.temperature += delta_temp
        
        # Apply physical limits
        self.temperature = np.clip(
            self.temperature,
            self.config.physics.min_temp,
            self.config.physics.max_temp
        )
        
        self.temp_history.append(self.temperature)
        self.power_history.append(self.power_draw + cooling_cost)
        
        if self.temperature >= self.config.physics.max_temp * 0.9:
            logger.warning(f"Server {self.id} temperature critical: {self.temperature:.1f}ºC")
        
        return {
            "temp": self.temperature,
            "it_power": self.power_draw,
            "cooling_power": cooling_cost,
            "heat_generated": heat_generated,
            "heat_removed": heat_removed,
        }
    
    def reset(self) -> None:
        """Reset server state to initial values."""
        self.temperature = self.config.physics.ambient_temp
        self.cpu_load = 0.0
        self.power_draw = self.config.physics.p_idle
        self.temp_history = [self.temperature]
        self.power_history = [self.power_draw]
        logger.debug(f"Server {self.id} reset")
    
    def __repr__(self) -> str:
        return f"Server(id={self.id}, T={self.temperature:.1f}ºC, P={self.power_draw:.0f}W)"
