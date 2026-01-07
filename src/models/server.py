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
        # Enhanced realism: CPU power isn't linear, it follows a cubic curve
        u = cpu_load
        # r = 1.8 approximates modern CPU power scaling better than linear
        dynamic_factor = 0.3 + 0.7 * (u ** 1.8) if u > 0 else 0.3 # Base 30% power even at "0" load if on
        
        p_idle = self.config.physics.p_idle
        p_max = self.config.physics.p_max
        it_dynamic_power = p_max * dynamic_factor
        
        # 2. Temperature-Dependent Leakage Power (Enhanced for S.C.A.R.I. Efficiency)
        # Stronger coupling makes thermal management more critical for energy savings
        # P_leak = P_static * exp(k * (T - T_ref))
        t_ref = 45.0 # Reference temperature (lower reference makes penalty stricter)
        k_leak = 0.03 # Leakage coefficient (3% increase per degree - significant!)
        
        # Leakage is a percentage of max power that grows exponentially
        base_leakage = p_max * 0.05 
        leakage_power = base_leakage * np.exp(k_leak * (self.temperature - t_ref))
        
        self.power_draw = it_dynamic_power + leakage_power
        heat_generated = self.power_draw
        
        # 3. Calculate cooling effect with temperature-aware capacity
        effective_ambient = self.config.physics.ambient_temp + inlet_temp_offset
        capacity_at_ambient = self.cooling_system.get_cooling_capacity(
            cooling_action, 
            ambient_temp=effective_ambient, 
            server_temp=self.temperature
        )
        
        # Cooling effectiveness based on temperature gradient
        heat_removed = capacity_at_ambient
        
        cooling_cost = self.cooling_system.get_power_consumption(cooling_action)
        
        # 4. Thermal dynamics with improved inertia
        # Net heat determines temperature change rate
        net_heat = heat_generated - heat_removed
        
        # Variable thermal mass? No, assuming constant mass for now but tuned value
        delta_temp = (net_heat * dt) / self.config.physics.server_thermal_mass
        
        # Clip temperature change rate for physical realism
        max_delta = self.config.physics.max_temp_change_per_second
        delta_temp = np.clip(delta_temp, -max_delta, max_delta)
        
        self.temperature += delta_temp
        
        # 5. Thermal Aging (Arrhenius Law)
        # Accelerating aging factors based on temperature
        # E_a/k_b ≈ 8000 for electronic components
        aging_factor = np.exp(8000 * (1/(273.15 + 40.0) - 1/(273.15 + self.temperature)))
        self.health -= (0.000002 * aging_factor * dt) # Slightly faster aging
        self.health = max(0.0, self.health)
        
        # Apply physical limits
        self.temperature = np.clip(
            self.temperature,
            self.config.physics.min_temp,
            self.config.physics.max_temp
        )
        
        self.temp_history.append(self.temperature)
        self.power_history.append(self.power_draw + cooling_cost)
        
        # Critical warning log
        if self.temperature >= self.config.physics.max_temp * 0.95:
            logger.warning(f"Server {self.id} CRITICAL TEMP: {self.temperature:.1f}ºC")
        
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
        # Start at a realistic "warm" operating temperature to avoid startup skew in metrics
        self.temperature = np.random.uniform(40.0, 50.0)
        self.cpu_load = 0.0
        self.power_draw = self.config.physics.p_idle
        self.health = 1.0
        self.temp_history = [self.temperature]
        self.power_history = [self.power_draw]
        logger.debug(f"Server {self.id} reset")
    
    def __repr__(self) -> str:
        return f"Server(id={self.id}, T={self.temperature:.1f}ºC, P={self.power_draw:.0f}W)"
