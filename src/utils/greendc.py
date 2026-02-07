# src/utils/greendc.py
"""
GreenDC Calculator - Comprehensive Data Center Sustainability Analysis
Combines operational carbon, embodied carbon, network topology analysis,
and financial ROI calculations.
"""

import json
import math
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum


class DataCenterSize(Enum):
    """Data center size classifications"""
    SMALL = "small"      # < 100 servers
    MEDIUM = "medium"    # 100-500 servers
    LARGE = "large"      # 500-2000 servers
    HYPERSCALE = "hyperscale"  # > 2000 servers


class NetworkTopology(Enum):
    """Network topology types"""
    FAT_TREE = "fat_tree"
    CLOS = "clos"
    SPINE_LEAF = "spine_leaf"
    THREE_TIER = "three_tier"


@dataclass
class HardwareComponent:
    """Represents a hardware component with embodied carbon"""
    name: str
    quantity: int
    embodied_co2_kg: float
    lifespan_years: float = 5.0
    
    def annual_co2(self) -> float:
        """Calculate annual amortized CO2"""
        return (self.quantity * self.embodied_co2_kg) / self.lifespan_years


class GreenDCCalculator:
    """
    Translates technical energy metrics from S.C.A.R.I simulations
    into environmental (CO2) and economic (OPEX) impact data.
    Includes embodied carbon, network topology analysis, and ROI calculations.
    """
    
    # Embodied carbon coefficients (kg CO2 per unit)
    EMBODIED_CARBON = {
        "server": 800,           # Per server
        "switch_48port": 150,    # Per switch
        "pdu": 80,               # Per PDU
        "crac": 300,             # Per CRAC unit
        "ups": 400,              # Per UPS
        "cabling_100m": 50,      # Per 100m
    }
    
    # Network switch specifications
    NETWORK_SPECS = {
        "fat_tree": {
            "ports_per_switch": 48,
            "oversubscription": 1.0,
            "description": "Full bisection bandwidth topology"
        },
        "clos": {
            "ports_per_switch": 48,
            "oversubscription": 0.67,
            "description": "3-tier Clos networking"
        },
        "spine_leaf": {
            "ports_per_switch": 48,
            "oversubscription": 1.0,
            "description": "2-tier Spine-Leaf topology"
        },
        "three_tier": {
            "ports_per_switch": 48,
            "oversubscription": 0.5,
            "description": "Traditional Core-Aggregation-Access"
        }
    }

    def __init__(self, 
                 electricity_price: float = 0.18, 
                 carbon_intensity: float = 0.211,
                 tree_absorption: float = 21.0,
                 region: str = "EU"):
        """
        Args:
            electricity_price: price in €/kWh (default EU rate)
            carbon_intensity: kg CO2 per kWh (grid mix dependent)
            tree_absorption: kg CO2 absorbed by one tree per year
            region: geographical region for climate data
        """
        self.price = electricity_price
        self.intensity = carbon_intensity
        self.tree_absorption = tree_absorption
        self.region = region

    def calculate_impact(self, 
                         baseline_power_w: float, 
                         scari_power_w: float, 
                         simulation_steps: int, 
                         step_duration_s: float = 1.0) -> Dict[str, Any]:
        """
        Calculate operational impact (energy savings, CO2, economics).
        Extrapolates simulation to yearly projections.
        """
        duration_s = simulation_steps * step_duration_s
        energy_saved_ws = (baseline_power_w - scari_power_w) * duration_s
        energy_saved_kwh = max(0, energy_saved_ws / 3600000.0)

        seconds_per_year = 365 * 24 * 3600
        yearly_scaling = seconds_per_year / duration_s
        
        yearly_energy_saved_kwh = energy_saved_kwh * yearly_scaling
        co2_saved_kg = yearly_energy_saved_kwh * self.intensity
        money_saved_eur = yearly_energy_saved_kwh * self.price
        trees_equivalent = co2_saved_kg / self.tree_absorption

        # Calculate PUE (Power Usage Effectiveness)
        pue_baseline = 1.67  # Industry average
        pue_scari = 1.1      # Estimated with SCARI optimization
        pue_improvement = ((pue_baseline - pue_scari) / pue_baseline) * 100

        return {
            "energy_saved_kwh_sim": round(energy_saved_kwh, 4),
            "projected_yearly_savings_eur": round(money_saved_eur, 2),
            "projected_yearly_co2_kg": round(co2_saved_kg, 2),
            "trees_equivalent": round(trees_equivalent, 1),
            "pue_baseline": pue_baseline,
            "pue_optimized": pue_scari,
            "pue_improvement_percent": round(pue_improvement, 1),
            "market_data": {
                "price_eur_kwh": self.price,
                "carbon_intensity_kg_kwh": self.intensity
            }
        }

    def calculate_embodied_carbon(self, 
                                 num_servers: int,
                                 topology: str = "spine_leaf") -> Dict[str, Any]:
        """
        Calculate embodied carbon from hardware manufacturing.
        Based on datacenter size and network topology.
        """
        # Determine datacenter size
        if num_servers < 100:
            size = DataCenterSize.SMALL
        elif num_servers < 500:
            size = DataCenterSize.MEDIUM
        elif num_servers < 2000:
            size = DataCenterSize.LARGE
        else:
            size = DataCenterSize.HYPERSCALE

        # Hardware inventory
        num_switches = self._calculate_switches(num_servers, topology)
        num_pdus = math.ceil(num_servers / 8)  # ~8 servers per PDU
        num_cracs = max(2, math.ceil(num_servers / 100))
        num_ups = max(1, math.ceil(num_servers / 500))
        cabling_100m = math.ceil(num_servers * 0.5)  # 50m per server

        components = [
            HardwareComponent("Servers", num_servers, self.EMBODIED_CARBON["server"]),
            HardwareComponent("Switches", num_switches, self.EMBODIED_CARBON["switch_48port"]),
            HardwareComponent("PDUs", num_pdus, self.EMBODIED_CARBON["pdu"]),
            HardwareComponent("CRAC Units", num_cracs, self.EMBODIED_CARBON["crac"]),
            HardwareComponent("UPS", num_ups, self.EMBODIED_CARBON["ups"]),
            HardwareComponent("Cabling (100m)", cabling_100m, self.EMBODIED_CARBON["cabling_100m"]),
        ]

        total_embodied_co2 = sum(c.quantity * c.embodied_co2_kg for c in components)
        total_annual_amortized = sum(c.annual_co2() for c in components)

        breakdown = {c.name: {"qty": c.quantity, "kg_co2": c.quantity * c.embodied_co2_kg} 
                    for c in components}

        return {
            "datacenter_size": size.value,
            "num_servers": num_servers,
            "topology": topology,
            "total_embodied_co2_kg": round(total_embodied_co2, 2),
            "annual_amortized_co2_kg": round(total_annual_amortized, 2),
            "hardware_breakdown": breakdown,
            "switch_count": num_switches,
            "cracs_count": num_cracs,
            "ups_count": num_ups,
        }

    def calculate_network_topology(self, 
                                  num_servers: int,
                                  topology: str = "spine_leaf") -> Dict[str, Any]:
        """
        Analyze network topology requirements and carbon footprint.
        """
        if topology not in self.NETWORK_SPECS:
            topology = "spine_leaf"

        specs = self.NETWORK_SPECS[topology]
        num_switches = self._calculate_switches(num_servers, topology)
        
        # Calculate network embodied carbon
        switch_carbon = num_switches * self.EMBODIED_CARBON["switch_48port"]
        cabling_units = math.ceil(num_servers * 0.5)
        cabling_carbon = cabling_units * self.EMBODIED_CARBON["cabling_100m"]
        total_network_carbon = switch_carbon + cabling_carbon

        # Estimate network power consumption
        watts_per_switch = 300  # Typical 48-port switch
        network_power_w = num_switches * watts_per_switch

        return {
            "topology": topology,
            "topology_description": specs["description"],
            "total_switches": num_switches,
            "total_ports": num_switches * specs["ports_per_switch"],
            "oversubscription_ratio": specs["oversubscription"],
            "estimated_network_power_w": network_power_w,
            "embodied_carbon_switches_kg": round(switch_carbon, 2),
            "embodied_carbon_cabling_kg": round(cabling_carbon, 2),
            "total_embodied_carbon_kg": round(total_network_carbon, 2),
        }

    def compare_scenarios(self,
                         num_servers: int,
                         baseline_pue: float = 1.67,
                         optimized_pue: float = 1.1,
                         annual_power_kwh: float = 1000000) -> Dict[str, Any]:
        """
        Compare operational carbon across different scenarios.
        annual_power_kwh is the IT equipment power consumption.
        Total datacenter power = IT power * PUE
        """
        # Baseline scenario: with traditional cooling
        baseline_total_power_kwh = annual_power_kwh * baseline_pue
        baseline_annual_co2 = baseline_total_power_kwh * self.intensity
        baseline_cost = baseline_total_power_kwh * self.price
        
        # Optimized scenario: with SCARI cooling
        optimized_total_power_kwh = annual_power_kwh * optimized_pue
        optimized_annual_co2 = optimized_total_power_kwh * self.intensity
        optimized_cost = optimized_total_power_kwh * self.price
        
        co2_reduction = baseline_annual_co2 - optimized_annual_co2
        reduction_percent = (co2_reduction / baseline_annual_co2) * 100
        cost_savings = baseline_cost - optimized_cost

        # Break-even analysis (embodied carbon)
        embodied = self.calculate_embodied_carbon(num_servers)
        embodied_co2 = embodied["total_embodied_co2_kg"]
        breakeven_years = embodied_co2 / co2_reduction if co2_reduction > 0 else float('inf')

        return {
            "scenario_comparison": {
                "baseline": {
                    "pue": baseline_pue,
                    "annual_energy_kwh": baseline_total_power_kwh,
                    "annual_co2_kg": round(baseline_annual_co2, 2),
                    "annual_cost_eur": round(baseline_cost, 2),
                },
                "optimized": {
                    "pue": optimized_pue,
                    "annual_energy_kwh": optimized_total_power_kwh,
                    "annual_co2_kg": round(optimized_annual_co2, 2),
                    "annual_cost_eur": round(optimized_cost, 2),
                }
            },
            "improvements": {
                "co2_reduction_kg": round(co2_reduction, 2),
                "co2_reduction_percent": round(reduction_percent, 1),
                "cost_savings_eur": round(cost_savings, 2),
                "breakeven_years": round(breakeven_years, 1) if breakeven_years != float('inf') else None,
            }
        }

    def roi_analysis(self,
                    num_servers: int,
                    investment_eur: float,
                    annual_savings_eur: float) -> Dict[str, Any]:
        """
        Financial return on investment analysis.
        """
        roi_percent = (annual_savings_eur / investment_eur) * 100 if investment_eur > 0 else 0
        payback_years = investment_eur / annual_savings_eur if annual_savings_eur > 0 else float('inf')
        ten_year_net_benefit = (annual_savings_eur * 10) - investment_eur

        return {
            "investment_eur": round(investment_eur, 2),
            "annual_savings_eur": round(annual_savings_eur, 2),
            "roi_percent_annual": round(roi_percent, 1),
            "payback_period_years": round(payback_years, 1) if payback_years != float('inf') else None,
            "ten_year_net_benefit_eur": round(ten_year_net_benefit, 2),
            "annual_carbon_avoided_kg": round(annual_savings_eur / self.price * self.intensity, 2),
        }

    def _calculate_switches(self, num_servers: int, topology: str) -> int:
        """
        Calculate required switches based on topology.
        """
        ports_per_switch = self.NETWORK_SPECS[topology]["ports_per_switch"]
        
        if topology == "fat_tree":
            # Fat-tree requires 3 * (k/2)^2 switches for k-port switches
            k = ports_per_switch
            return int(3 * (k / 2) ** 2)
        elif topology == "clos":
            # 3-tier: access + aggregation + core
            tiers = 3
            servers_per_access = ports_per_switch // 2
            num_access = math.ceil(num_servers / servers_per_access)
            num_agg = max(2, num_access // 4)
            num_core = max(2, num_agg // 4)
            return num_access + num_agg + num_core
        elif topology == "spine_leaf":
            # 2-tier: leaves + spines
            servers_per_leaf = ports_per_switch // 2
            num_leaves = math.ceil(num_servers / servers_per_leaf)
            num_spines = max(2, num_leaves // 2)
            return num_leaves + num_spines
        else:  # three_tier
            # Traditional 3-tier
            servers_per_access = ports_per_switch // 2
            num_access = math.ceil(num_servers / servers_per_access)
            return num_access + max(2, num_access // 4) + max(1, num_access // 12)
