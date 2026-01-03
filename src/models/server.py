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
        self.health = 1.0 # New in S.C.A.R.I. "True Physics"
        logger.debug(f"Server {self.id} initialized")
    
    def update_physics(self, cpu_load: float, cooling_action: float, dt: float = 1.0, inlet_temp_offset: float = 0.0) -> Dict[str, float]:
        """
        Update server physical state based on load and cooling.
        Includes temperature-dependent leakage power and thermal aging.
        """
        cpu_load = np.clip(cpu_load, 0.0, 1.0)
        cooling_action = np.clip(cooling_action, 0.0, 1.0)
        
        # 1. Calculate dynamic power consumption (IT Load)
        u = cpu_load
        r = self.config.physics.r_coeff
        dynamic_factor = (2 * u) - (u ** r)
        p_idle = self.config.physics.p_idle
        p_max = self.config.physics.p_max
        it_dynamic_power = p_idle + (p_max - p_idle) * dynamic_factor
        
        # 2. Temperature-Dependent Leakage Power (S.C.A.R.I. v10.0 Realism)
        # Power increases as temperature rises (positive feedback loop)
        # P_leak = P_static * exp(k * (T - T_ref))
        t_ref = 50.0 # Reference temperature
        k_leak = 0.015 # Leakage coefficient (1.5% increase per degree)
        leakage_power = (p_idle * 0.1) * np.exp(k_leak * (self.temperature - t_ref))
        
        self.power_draw = it_dynamic_power + leakage_power
        heat_generated = self.power_draw
        
        # 3. Calculate cooling effect
        # The higher the inlet temperature, the lower the cooling efficiency
        # Delta_T_effective = T_server - (Ambient + Offset)
        effective_ambient = self.config.physics.ambient_temp + inlet_temp_offset
        capacity_at_ambient = self.cooling_system.get_cooling_capacity(cooling_action)
        
        # Scaling cooling capacity based on temperature gradient
        # This is a simplification of convective heat transfer
        temp_gradient_factor = (self.temperature - effective_ambient) / (self.temperature - self.config.physics.ambient_temp + 1e-6)
        heat_removed = capacity_at_ambient * max(0.1, temp_gradient_factor)
        
        cooling_cost = self.cooling_system.get_power_consumption(cooling_action)
        
        # 4. Thermal dynamics
        net_heat = heat_generated - heat_removed
        delta_temp = (net_heat * dt) / self.config.physics.server_thermal_mass
        
        # Clip temperature change rate
        max_delta = self.config.physics.max_temp_change_per_second
        delta_temp = np.clip(delta_temp, -max_delta, max_delta)
        
        self.temperature += delta_temp
        
        # 5. Thermal Aging (Arrhenius Law)
        # Accelerating aging factors based on temperature
        # E_a/k_b ≈ 8000 for electronic components
        aging_factor = np.exp(8000 * (1/(273.15 + t_ref) - 1/(273.15 + self.temperature)))
        self.health -= (0.000001 * aging_factor * dt) # Base decay rate
        self.health = max(0.0, self.health)
        
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
            "health": self.health,
            "leakage_power": leakage_power
        }
    
    def reset(self) -> None:
        """Reset server state to initial values."""
        self.temperature = self.config.physics.ambient_temp
        self.cpu_load = 0.0
        self.power_draw = self.config.physics.p_idle
        self.health = 1.0
        self.temp_history = [self.temperature]
        self.power_history = [self.power_draw]
        logger.debug(f"Server {self.id} reset")
    
    def __repr__(self) -> str:
        return f"Server(id={self.id}, T={self.temperature:.1f}ºC, P={self.power_draw:.0f}W)"
