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
            if flow_rate < 0.05:
                # Deadband - minimal power for monitoring only
                power = 2.0
            else:
                # Cubic relationship for fans, but with efficiency curve
                # Peak efficiency at 70-80% speed
                efficiency_loss = 1.0 + 0.15 * abs(0.75 - flow_rate)
                base_power = self.config.max_fan_power * (flow_rate ** 3)
                # Static pressure losses
                static_power = 0.05 * self.config.max_fan_power * flow_rate
                power = (base_power + static_power) * efficiency_loss
        
        elif self.mode == "LIQUID":
            # Pump power: base power + variable power with efficiency curve
            if flow_rate < 0.1:
                # Minimum circulation
                power = self.config.base_pump_power * 0.5
            else:
                # Pumps are more efficient than fans but still have losses
                # Best efficiency point (BEP) around 60-70% flow
                bep_flow = 0.65
                efficiency_factor = 1.0 + 0.2 * ((flow_rate - bep_flow) ** 2)
                variable_power = self.config.max_pump_power * (flow_rate ** 2.5)
                power = self.config.base_pump_power + (variable_power * efficiency_factor)
        
        elif self.mode == "HYBRID":
            # Hybrid system: switch based on efficiency
            # Prefer liquid cooling at high loads, air at low loads
            if flow_rate < 0.4:
                # Air cooling dominant
                air_flow = flow_rate * 1.5
                liquid_flow = 0.2
            else:
                # Liquid cooling dominant
                air_flow = 0.3
                liquid_flow = flow_rate
            
            # Recursive call for each subsystem
            air_system = CoolingSystem("AIR", self.config)
            liquid_system = CoolingSystem("LIQUID", self.config)
            power = air_system.get_power_consumption(air_flow) + liquid_system.get_power_consumption(liquid_flow)
        
        else:
            logger.error(f"Unknown cooling mode: {self.mode}")
            raise ValueError(f"Unknown cooling mode: {self.mode}")
        
        # Apply degradation factor
        power *= self.efficiency_factor
        
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
        
        # Temperature delta affects cooling efficiency
        delta_t = max(0.1, server_temp - ambient_temp)
        
        if self.mode == "AIR":
            # Natural convection always present
            passive = self.config.natural_convection
            
            # Economizer mode: free cooling when ambient is cool
            if ambient_temp < 18.0 and flow_rate > 0.1:
                # Free cooling bonus (outside air economizer)
                economizer_bonus = 1.5 * self.config.air_cooling_capacity * flow_rate * (18.0 - ambient_temp) / 10.0
            else:
                economizer_bonus = 0.0
            
            # Active cooling scales with flow and temperature delta
            active = flow_rate * self.config.air_cooling_capacity * (delta_t / 30.0)
            
            return passive + active + economizer_bonus
        
        elif self.mode == "LIQUID":
            # Liquid cooling more consistent but sensitive to flow
            # Effectiveness increases with delta-T
            effectiveness = min(1.0, delta_t / 40.0)
            base_capacity = flow_rate * self.config.liquid_cooling_capacity
            return base_capacity * effectiveness
        
        elif self.mode == "HYBRID":
            # Combine both modes intelligently
            air_capacity = 0.3 * flow_rate * self.config.air_cooling_capacity
            liquid_capacity = 0.7 * flow_rate * self.config.liquid_cooling_capacity
            return air_capacity + liquid_capacity
        
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
