# Data Center Calculator - Integration Guide

## Overview

S.C.A.R.I has been significantly enhanced with a comprehensive **Data Center Calculator** that provides enterprise-grade sustainability analysis for datacenter operations. This integration brings together:

- **Embodied Carbon Analysis** - Manufacturing and production footprint
- **Network Topology Optimization** - Architecture-specific carbon calculations
- **Operational Carbon Comparison** - Baseline vs. SCARI-optimized scenarios
- **ROI & Financial Analysis** - Investment payback and economic projections

## Architecture

### Backend (Python/FastAPI)

#### Enhanced GreenDC Calculator (`src/utils/greendc.py`)

The core calculator has been expanded from a simple operational impact tool to a comprehensive sustainability suite:

```python
from src.utils.greendc import GreenDCCalculator

calculator = GreenDCCalculator(
    electricity_price=0.18,      # €/kWh
    carbon_intensity=0.211,      # kg CO2/kWh
    tree_absorption=21.0         # kg CO2/tree/year
)
```

#### Key Features

##### 1. Embodied Carbon Calculation
Calculate manufacturing emissions from datacenter hardware:

```python
result = calculator.calculate_embodied_carbon(
    num_servers=1000,
    topology="spine_leaf"
)
# Returns: datacenter_size, total_embodied_co2_kg, hardware_breakdown, etc.
```

**Supported Topologies:**
- `spine_leaf` - Modern 2-tier architecture
- `clos` - 3-tier Clos networking
- `fat_tree` - Full bisection bandwidth
- `three_tier` - Traditional Core-Aggregation-Access

**Hardware Tracked:**
- Servers: 800 kg CO₂ per unit
- Network Switches: 150 kg CO₂ per 48-port
- PDUs: 80 kg CO₂ per unit
- CRAC Units: 300 kg CO₂ per unit
- UPS Systems: 400 kg CO₂ per unit
- Cabling: 50 kg CO₂ per 100m

##### 2. Network Topology Analysis
Analyze architecture requirements and their carbon footprint:

```python
result = calculator.calculate_network_topology(
    num_servers=500,
    topology="spine_leaf"
)
# Returns: total_switches, oversubscription_ratio, embodied_carbon, etc.
```

##### 3. Scenario Comparison
Compare baseline vs. SCARI-optimized operations:

```python
result = calculator.compare_scenarios(
    num_servers=500,
    baseline_pue=1.67,           # Industry average
    optimized_pue=1.1,           # With SCARI optimization
    annual_power_kwh=1000000
)
# Returns: carbon savings, cost reduction, breakeven analysis
```

##### 4. ROI Analysis
Financial return on investment calculations:

```python
result = calculator.roi_analysis(
    num_servers=500,
    investment_eur=500000,
    annual_savings_eur=100000
)
# Returns: ROI%, payback period, 10-year benefit
```

### API Endpoints

#### `/calculator/embodied-carbon` (POST)
Calculate hardware manufacturing emissions.

**Request:**
```json
{
  "num_servers": 500,
  "topology": "spine_leaf"
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "datacenter_size": "medium",
    "total_embodied_co2_kg": 542000,
    "annual_amortized_co2_kg": 108400,
    "hardware_breakdown": {...},
    "switch_count": 12,
    "cracs_count": 5,
    "ups_count": 1
  }
}
```

#### `/calculator/network-topology` (POST)
Analyze network architecture carbon impact.

**Request:**
```json
{
  "num_servers": 500,
  "topology": "spine_leaf"
}
```

#### `/calculator/scenario-comparison` (POST)
Compare operational efficiency scenarios.

**Request:**
```json
{
  "num_servers": 500,
  "baseline_pue": 1.67,
  "optimized_pue": 1.1,
  "annual_power_kwh": 1000000
}
```

#### `/calculator/roi-analysis` (POST)
Calculate financial returns.

**Request:**
```json
{
  "num_servers": 500,
  "investment_eur": 500000,
  "annual_savings_eur": 100000
}
```

#### `/calculator/comprehensive` (POST)
Full datacenter sustainability analysis (all metrics combined).

#### `/calculator/info` (GET)
Get information about available calculators.

### Frontend (React/Vite)

#### DataCenterCalculator Component (`ui/src/DataCenterCalculator.jsx`)

New comprehensive UI component with:

**Tabs:**
- **Overview** - Feature descriptions and quick analysis
- **Parameters** - Input configuration
- **ROI** - Financial analysis inputs
- **Results** - Detailed analysis results

**Features:**
- Real-time form validation
- Interactive parameter adjustment
- Color-coded results visualization
- Support for all network topologies
- Responsive design with dark/light themes

## Usage Examples

### Command Line

```bash
# Backend service
uvicorn src.api.app:app --host 0.0.0.0 --port 8000

# Frontend
cd ui && npm run dev
```

### Python Integration

```python
from src.utils.greendc import GreenDCCalculator

# Create calculator
calc = GreenDCCalculator(
    electricity_price=0.15,  # Regional pricing
    carbon_intensity=0.38,   # Regional grid mix
    region="US"
)

# Analyze a 2000-server hyperscale datacenter
embodied = calc.calculate_embodied_carbon(2000, "spine_leaf")
network = calc.calculate_network_topology(2000, "spine_leaf")
scenarios = calc.compare_scenarios(
    num_servers=2000,
    baseline_pue=1.67,
    optimized_pue=1.05,  # SCARI achieves even better PUE at scale
    annual_power_kwh=5000000
)

# Financial analysis
roi = calc.roi_analysis(
    num_servers=2000,
    investment_eur=2000000,  # SCARI deployment cost
    annual_savings_eur=500000  # Energy + maintenance savings
)

print(f"Payback period: {roi['payback_period_years']} years")
print(f"10-year benefit: €{roi['ten_year_net_benefit_eur']:,.0f}")
```

### API Usage

```bash
# Comprehensive analysis
curl -X POST http://localhost:8000/calculator/comprehensive \
  -H "Content-Type: application/json" \
  -d '{
    "num_servers": 500,
    "topology": "spine_leaf",
    "annual_power_kwh": 1000000,
    "baseline_pue": 1.67,
    "optimized_pue": 1.1
  }'

# ROI Analysis
curl -X POST http://localhost:8000/calculator/roi-analysis \
  -H "Content-Type: application/json" \
  -d '{
    "num_servers": 500,
    "investment_eur": 500000,
    "annual_savings_eur": 100000
  }'
```

## Data Center Classifications

The calculator automatically categorizes datacenters:

| Size | Server Count | Typical Use |
|------|-------------|------------|
| **Small** | < 100 | Edge, regional |
| **Medium** | 100-500 | Regional, enterprise |
| **Large** | 500-2000 | National, hyperscale prep |
| **Hyperscale** | > 2000 | Global, cloud provider |

## Sustainability Metrics

### Carbon Footprint Components

1. **Embodied Carbon** - Manufacturing & production (amortized over 5 years)
2. **Operational Carbon** - Energy consumption (annual)
3. **Network Carbon** - Infrastructure & switching systems

### Key Performance Indicators

- **PUE (Power Usage Effectiveness)** - Total Power / IT Power
  - Industry average: 1.67
  - SCARI optimized: 1.1
  - Hyperscale optimized: 1.05

- **Breakeven Period** - Years to offset embodied carbon through operational gains

- **ROI Payback** - Years until investment cost is recovered

## Testing

Comprehensive test suite included in `tests/test_greendc.py`:

```bash
# Run all tests
python -m pytest tests/test_greendc.py -v

# Run specific test class
python -m pytest tests/test_greendc.py::TestGreenDCCalculator -v

# Run with coverage
python -m pytest tests/test_greendc.py --cov=src.utils.greendc
```

**Test Coverage:**
- ✅ Calculator initialization
- ✅ Operational impact calculation
- ✅ Embodied carbon (small, medium, large, hyperscale)
- ✅ Network topology analysis (spine_leaf, clos, fat_tree)
- ✅ Scenario comparison
- ✅ ROI analysis (positive return, zero investment, no savings)
- ✅ Datacenter size classification
- ✅ Switch calculation consistency

## Customization

### Regional Settings

```python
calculator = GreenDCCalculator(
    electricity_price=0.12,      # €/kWh (varies by region)
    carbon_intensity=0.50,       # kg CO2/kWh (grid mix dependent)
    tree_absorption=20.0,        # kg CO2/tree/year
    region="US"
)
```

### Regional Electricity Prices
- **EU**: €0.18-0.22/kWh
- **USA**: €0.12-0.18/kWh (varies by state)
- **Asia**: €0.10-0.15/kWh

### Carbon Intensity (Grid Mix)
- **France**: 0.05 kg CO₂/kWh (hydroelectric heavy)
- **Germany**: 0.38 kg CO₂/kWh (renewable transition)
- **Poland**: 0.70 kg CO₂/kWh (coal heavy)
- **USA**: 0.42 kg CO₂/kWh (average)

## Integration with Existing Features

The calculator seamlessly integrates with S.C.A.R.I's existing capabilities:

1. **Neural Policy Training** - SCARI policies optimize for lower PUE
2. **Evaluation** - Performance metrics now include sustainability data
3. **Explainability** - AI decisions linked to CO₂ impact
4. **Visualization** - Charts showing embodied vs. operational carbon

## Performance Notes

- Calculations complete in < 50ms
- Supports datacenter sizes from 1 to 100,000+ servers
- Network topology calculations use efficient algorithms
- Suitable for real-time dashboard updates

## Future Enhancements

- [ ] Water usage footprint (WUE - Water Usage Effectiveness)
- [ ] Scope 3 emissions (supply chain)
- [ ] Real-time electricity price feeds
- [ ] Machine learning-powered optimization suggestions
- [ ] Multi-region comparison dashboards
- [ ] Carbon credit market pricing integration
- [ ] Renewable energy procurement impact analysis

## Support & Documentation

For more information:
- API Docs: Available at `http://localhost:8000/docs` (FastAPI Swagger UI)
- Code: `src/utils/greendc.py` and `src/api/app.py`
- Tests: `tests/test_greendc.py`
- UI: `ui/src/DataCenterCalculator.jsx`

---

**Version**: 2.0.0
**Last Updated**: February 7, 2026
**Status**: Production Ready
