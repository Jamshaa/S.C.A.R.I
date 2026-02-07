"""
Tests for the expanded GreenDC Calculator module.
Tests embodied carbon, network topology, scenario comparison, and ROI analysis.
"""

import pytest
from src.utils.greendc import (
    GreenDCCalculator, 
    DataCenterSize, 
    NetworkTopology,
    HardwareComponent
)


class TestGreenDCCalculator:
    """Test suite for GreenDCCalculator"""
    
    @pytest.fixture
    def calculator(self):
        """Create a calculator instance for testing"""
        return GreenDCCalculator(
            electricity_price=0.18,
            carbon_intensity=0.211,
            tree_absorption=21.0
        )
    
    def test_calculator_initialization(self, calculator):
        """Test calculator initializes with correct parameters"""
        assert calculator.price == 0.18
        assert calculator.intensity == 0.211
        assert calculator.tree_absorption == 21.0
        assert calculator.region == "EU"
    
    def test_operational_impact_calculation(self, calculator):
        """Test operational carbon impact calculation"""
        result = calculator.calculate_impact(
            baseline_power_w=100000,
            scari_power_w=80000,
            simulation_steps=5000,
            step_duration_s=1.0
        )
        
        assert "energy_saved_kwh_sim" in result
        assert "projected_yearly_savings_eur" in result
        assert "projected_yearly_co2_kg" in result
        assert "trees_equivalent" in result
        assert "pue_baseline" in result
        assert "pue_optimized" in result
        assert result["pue_improvement_percent"] > 0
    
    def test_embodied_carbon_calculation_small_dc(self, calculator):
        """Test embodied carbon for small datacenter"""
        result = calculator.calculate_embodied_carbon(
            num_servers=50,
            topology="spine_leaf"
        )
        
        assert result["datacenter_size"] == "small"
        assert result["num_servers"] == 50
        assert result["total_embodied_co2_kg"] > 0
        assert result["annual_amortized_co2_kg"] > 0
        assert "hardware_breakdown" in result
    
    def test_embodied_carbon_calculation_large_dc(self, calculator):
        """Test embodied carbon for large datacenter"""
        result = calculator.calculate_embodied_carbon(
            num_servers=1500,
            topology="clos"
        )
        
        assert result["datacenter_size"] == "large"
        assert result["num_servers"] == 1500
        assert result["total_embodied_co2_kg"] > 0
    
    def test_embodied_carbon_calculation_hyperscale(self, calculator):
        """Test embodied carbon for hyperscale datacenter"""
        result = calculator.calculate_embodied_carbon(
            num_servers=5000,
            topology="fat_tree"
        )
        
        assert result["datacenter_size"] == "hyperscale"
        assert result["switch_count"] > 0
        assert result["cracs_count"] > 0
    
    def test_network_topology_spine_leaf(self, calculator):
        """Test spine-leaf network topology analysis"""
        result = calculator.calculate_network_topology(
            num_servers=500,
            topology="spine_leaf"
        )
        
        assert result["topology"] == "spine_leaf"
        assert result["total_switches"] > 0
        assert result["total_ports"] > 0
        assert result["oversubscription_ratio"] == 1.0
        assert result["estimated_network_power_w"] > 0
        assert result["total_embodied_carbon_kg"] > 0
    
    def test_network_topology_clos(self, calculator):
        """Test Clos network topology analysis"""
        result = calculator.calculate_network_topology(
            num_servers=300,
            topology="clos"
        )
        
        assert result["topology"] == "clos"
        assert result["oversubscription_ratio"] == 0.67
    
    def test_network_topology_fat_tree(self, calculator):
        """Test Fat-Tree network topology analysis"""
        result = calculator.calculate_network_topology(
            num_servers=400,
            topology="fat_tree"
        )
        
        assert result["topology"] == "fat_tree"
        assert result["total_switches"] > 0
    
    def test_scenario_comparison(self, calculator):
        """Test scenario comparison between baseline and optimized"""
        result = calculator.compare_scenarios(
            num_servers=500,
            baseline_pue=1.67,
            optimized_pue=1.1,
            annual_power_kwh=1000000
        )
        
        assert "scenario_comparison" in result
        assert "baseline" in result["scenario_comparison"]
        assert "optimized" in result["scenario_comparison"]
        assert "improvements" in result
        
        baseline = result["scenario_comparison"]["baseline"]
        optimized = result["scenario_comparison"]["optimized"]
        
        assert baseline["pue"] == 1.67
        assert optimized["pue"] == 1.1
        assert optimized["annual_co2_kg"] < baseline["annual_co2_kg"]
        assert optimized["annual_cost_eur"] < baseline["annual_cost_eur"]
        
        improvements = result["improvements"]
        assert improvements["co2_reduction_kg"] > 0
        assert improvements["co2_reduction_percent"] > 0
        assert improvements["cost_savings_eur"] > 0
    
    def test_roi_analysis_positive_return(self, calculator):
        """Test ROI analysis with positive returns"""
        result = calculator.roi_analysis(
            num_servers=500,
            investment_eur=500000,
            annual_savings_eur=100000
        )
        
        assert result["investment_eur"] == 500000
        assert result["annual_savings_eur"] == 100000
        assert result["roi_percent_annual"] == 20.0
        assert result["payback_period_years"] == 5.0
        assert result["ten_year_net_benefit_eur"] == 500000
    
    def test_roi_analysis_no_investment(self, calculator):
        """Test ROI analysis with zero investment"""
        result = calculator.roi_analysis(
            num_servers=500,
            investment_eur=0,
            annual_savings_eur=100000
        )
        
        assert result["investment_eur"] == 0
        assert result["roi_percent_annual"] == 0
    
    def test_roi_analysis_no_savings(self, calculator):
        """Test ROI analysis with zero annual savings"""
        result = calculator.roi_analysis(
            num_servers=500,
            investment_eur=500000,
            annual_savings_eur=0
        )
        
        assert result["payback_period_years"] is None
    
    def test_hardware_component(self):
        """Test HardwareComponent calculation"""
        component = HardwareComponent(
            name="Test Server",
            quantity=100,
            embodied_co2_kg=800,
            lifespan_years=5.0
        )
        
        assert component.quantity * component.embodied_co2_kg == 80000
        assert component.annual_co2() == 16000
    
    def test_datacenter_size_classification(self, calculator):
        """Test datacenter size classification"""
        # Small
        result_small = calculator.calculate_embodied_carbon(50, "spine_leaf")
        assert result_small["datacenter_size"] == "small"
        
        # Medium
        result_medium = calculator.calculate_embodied_carbon(300, "spine_leaf")
        assert result_medium["datacenter_size"] == "medium"
        
        # Large
        result_large = calculator.calculate_embodied_carbon(1000, "spine_leaf")
        assert result_large["datacenter_size"] == "large"
        
        # Hyperscale
        result_hyperscale = calculator.calculate_embodied_carbon(3000, "spine_leaf")
        assert result_hyperscale["datacenter_size"] == "hyperscale"
    
    def test_switch_calculation_consistency(self, calculator):
        """Test switch calculation is consistent across calls"""
        result1 = calculator.calculate_network_topology(500, "spine_leaf")
        result2 = calculator.calculate_network_topology(500, "spine_leaf")
        
        assert result1["total_switches"] == result2["total_switches"]
    
    def test_impact_with_zero_energy_difference(self, calculator):
        """Test impact when baseline equals optimized (no savings)"""
        result = calculator.calculate_impact(
            baseline_power_w=100000,
            scari_power_w=100000,
            simulation_steps=5000
        )
        
        assert result["energy_saved_kwh_sim"] == 0
        assert result["projected_yearly_savings_eur"] == 0
        assert result["projected_yearly_co2_kg"] == 0


class TestNetworkTopologyCalculations:
    """Test network topology switch calculations"""
    
    @pytest.fixture
    def calculator(self):
        return GreenDCCalculator()
    
    def test_spine_leaf_vs_clos_switch_count(self, calculator):
        """Compare switch counts for different topologies"""
        num_servers = 1000
        
        spine_leaf = calculator.calculate_network_topology(num_servers, "spine_leaf")
        clos = calculator.calculate_network_topology(num_servers, "clos")
        fat_tree = calculator.calculate_network_topology(num_servers, "fat_tree")
        
        # All should have switches
        assert spine_leaf["total_switches"] > 0
        assert clos["total_switches"] > 0
        assert fat_tree["total_switches"] > 0
    
    def test_topology_oversubscription(self, calculator):
        """Test topology oversubscription ratios"""
        num_servers = 500
        
        spine_leaf = calculator.calculate_network_topology(num_servers, "spine_leaf")
        clos = calculator.calculate_network_topology(num_servers, "clos")
        
        assert spine_leaf["oversubscription_ratio"] == 1.0
        assert clos["oversubscription_ratio"] == 0.67


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
