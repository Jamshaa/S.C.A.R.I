# src/utils/greendc.py
import json
from pathlib import Path
from typing import Dict, Any

class GreenDCCalculator:
    """
    Translates technical energy metrics from S.C.A.R.I simulations
    into environmental (CO2) and economic (OPEX) impact data.
    """
    def __init__(self, 
                 electricity_price: float = 0.18, 
                 carbon_intensity: float = 0.211,
                 tree_absorption: float = 21.0):
        """
        Args:
            electricity_price: price in €/kWh
            carbon_intensity: kg CO2 per kWh
            tree_absorption: kg CO2 absorbed by one tree per year
        """
        self.price = electricity_price
        self.intensity = carbon_intensity
        self.tree_absorption = tree_absorption

    def calculate_impact(self, 
                         baseline_power_w: float, 
                         scari_power_w: float, 
                         simulation_steps: int, 
                         step_duration_s: float = 1.0) -> Dict[str, Any]:
        """
        Performs the sustainability conversion.
        Assuming power is in Watts and we want to extrapolate to a "Yearly projection"
        based on the simulated efficiency.
        """
        # 1. Calculate Energy Saved in the Simulation (kWh)
        # Power(W) * Time(s) / 3,600,000 = kWh
        duration_s = simulation_steps * step_duration_s
        energy_saved_ws = (baseline_power_w - scari_power_w) * duration_s
        energy_saved_kwh = max(0, energy_saved_ws / 3600000.0)

        # 2. Extrapolate to Yearly Savings (assuming DC runs 24/7)
        # Scaling factor = (seconds in a year) / (duration of simulation)
        seconds_per_year = 365 * 24 * 3600
        yearly_scaling = seconds_per_year / duration_s
        
        yearly_energy_saved_kwh = energy_saved_kwh * yearly_scaling
        co2_saved_kg = yearly_energy_saved_kwh * self.intensity
        money_saved_eur = yearly_energy_saved_kwh * self.price
        trees_equivalent = co2_saved_kg / self.tree_absorption

        return {
            "energy_saved_kwh_sim": round(energy_saved_kwh, 4),
            "projected_yearly_savings_eur": round(money_saved_eur, 2),
            "projected_yearly_co2_kg": round(co2_saved_kg, 2),
            "trees_equivalent": round(trees_equivalent, 1),
            "market_data": {
                "price_eur_kwh": self.price,
                "carbon_intensity_kg_kwh": self.intensity
            }
        }
