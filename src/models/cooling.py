# src/models/cooling.py
import numpy as np
from typing import Tuple, Optional, Any
import logging

logger = logging.getLogger(__name__)

class CoolingSystem:
    """Advanced cooling physics with economizer mode and efficiency optimization."""
    
    def __init__(self, mode: str = "AIR", config: Any = None):
        """
        Initialize the cooling system.
        
        Args:
            mode: Cooling mode ("AIR", "LIQUID", or "HYBRID").
            config: Cooling configuration object.
        """
        self.mode = mode
        self.config = config
        if self.config is None:
            from src.config import CoolingConfig
            self.config = CoolingConfig()
        
        # Track efficiency degradation over time
        self.efficiency_factor = 1.0
        self.operating_hours = 0.0
        
        logger.debug(f"CoolingSystem initialized with {self.mode} mode")
    
    def get_power_consumption(self, flow_rate: float) -> float:
        """
        Calculate power consumption with realistic efficiency curves.
        
        Args:
            flow_rate: Normalized flow rate (0.0 to 1.0).
            
        Returns:
            Power consumption in Watts.
        """
        flow_rate = np.clip(flow_rate, 0.0, 1.0)
        
        if self.mode == "AIR":
            # Realistic fan power: includes deadband and efficiency sweet spot
            if flow_rate < 0.1:
                # Deadband - minimal power for monitoring only (electronics)
                power = 5.0
            else:
                # Cubic relationship for fans: P ~ flow^3
                # But actual mechanical efficiency drops at extremes
                
                # Base cubic power
                base_power = self.config.max_fan_power * (flow_rate ** 3.0)
                
                # Efficiency curve: Fans are most efficient around 60-80% speed
                # Penalty for running at 100% (turbulence, backpressure) or very low (motor slip)
                if 0.4 <= flow_rate <= 0.8:
                    efficiency_factor = 1.0 # Optimal
                elif flow_rate > 0.8:
                    # Exponential penalty near max speed
                    efficiency_factor = 1.0 + 0.5 * ((flow_rate - 0.8) / 0.2) ** 2
                else: 
                     # Low speed inefficiency
                    efficiency_factor = 1.0 + 0.2 * ((0.4 - flow_rate) / 0.4)
                
                power = base_power * efficiency_factor
        
        elif self.mode == "LIQUID":
            # Pump power
            if flow_rate < 0.1:
                power = self.config.base_pump_power
            else:
                # Pump power ~ flow^2 (less geometric increase than fans)
                variable_power = self.config.max_pump_power * (flow_rate ** 2.2)
                power = self.config.base_pump_power + variable_power
        
        elif self.mode == "HYBRID":
             # Simplified hybrid logic
            air_part = self.get_power_consumption(flow_rate * 0.7) # Assume split load
            liquid_part = CoolingSystem("LIQUID", self.config).get_power_consumption(flow_rate * 0.3)
            power = air_part + liquid_part
        
        else:
            raise ValueError(f"Unknown cooling mode: {self.mode}")
        
        # Apply degradation factor
        power *= (2.0 - self.efficiency_factor) # Lower efficiency = Higher power
        
        return float(power)
    
    def get_cooling_capacity(self, flow_rate: float, ambient_temp: float = 22.0, server_temp: float = 50.0) -> float:
        """
        Calculate cooling capacity with economizer mode and temperature-dependent efficiency.
        
        Args:
            flow_rate: Normalized flow rate (0.0 to 1.0).
            ambient_temp: Outside air temperature.
            server_temp: Server inlet temperature.
            
        Returns:
            Cooling capacity in Watts.
        """
        flow_rate = np.clip(flow_rate, 0.0, 1.0)
        
        # Temperature delta affects cooling effectiveness
        # Heat transfer Q = m * Cp * DeltaT
        delta_t = max(0.1, server_temp - ambient_temp)
        
        if self.mode == "AIR":
            # Natural convection (always some heat loss)
            passive = self.config.natural_convection * (delta_t / 20.0)
            
            # Economizer mode: Massive free cooling when ambient is low
            economizer_bonus = 0.0
            if ambient_temp < 15.0:
                # Full free cooling available
                economizer_bonus = 2000.0 * flow_rate
            elif ambient_temp < 20.0:
                # Partial free cooling
                quality = (20.0 - ambient_temp) / 5.0
                economizer_bonus = 1000.0 * flow_rate * quality
            
            # Active cooling capacity
            # Scales linearly with flow but depends heavily on Delta T
            base_capacity = self.config.air_cooling_capacity
            active = base_capacity * flow_rate * (delta_t / 25.0) # Normalized at 25C delta
            
            return passive + active + economizer_bonus
        
        elif self.mode == "LIQUID":
            # Liquid cooling
            effectiveness = min(1.0, delta_t / 40.0)
            base_capacity = flow_rate * self.config.liquid_cooling_capacity
            return base_capacity * effectiveness
            
        return 0.0
    
    def update_degradation(self, dt: float = 1.0) -> None:
        """
        Update cooling system efficiency degradation over time.
        
        Args:
            dt: Time step in seconds.
        """
        self.operating_hours += dt / 3600.0
        # Efficiency degrades 1% per 1000 hours (realistic for industrial equipment)
        degradation_rate = 0.01 / 1000.0
        self.efficiency_factor = max(0.8, 1.0 - (degradation_rate * self.operating_hours))
    
    def __repr__(self) -> str:
        return f"CoolingSystem(mode={self.mode}, efficiency={self.efficiency_factor:.3f})"
