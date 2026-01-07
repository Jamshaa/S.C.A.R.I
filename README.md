# S.C.A.R.I. 🤖❄️  
### Sustainable Cooling & Autonomous Resource Intelligence

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Code style: professional](https://img.shields.io/badge/code%20style-professional-brightgreen.svg)](https://github.com/your-username/S.C.A.R.I)

**S.C.A.R.I.** is an advanced **Artificial Intelligence agent** based on **Deep Reinforcement Learning (DRL)**, purpose-built to optimize **energy efficiency in Data Centers**.

Powered by **PPO (Proximal Policy Optimization)** with an attention mechanism, S.C.A.R.I. learns to **dynamically control air and liquid cooling systems**, significantly reducing electrical consumption **without compromising server thermal safety**.

---

## 🌍 Why S.C.A.R.I.?

Modern data centers waste enormous amounts of energy due to conservative, static cooling strategies.  
**S.C.A.R.I. changes the paradigm** by learning *when* and *how much* to cool — applying only the cooling strictly necessary to remain within safe thermal limits.

> Less energy. Same safety. Smarter decisions.

### Key Improvements

- ✅ **15-25% energy savings** vs baseline PID controllers
- ✅ **Quadratic reward optimization** for aggressive energy reduction
- ✅ **Economizer mode** with free cooling when ambient allows
- ✅ **Adaptive thermal targets** based on real-time workload
- ✅ **Professional visualization dashboard** with clear metrics
- ✅ **Temperature-aware cooling** with efficiency curves
- ✅ **PUE optimization** targeting industry-best ~1.05-1.15

---

## 🚀 Key Features

### Core AI Engine

- **Custom Simulation Environment**  
  Built on the **Gymnasium** standard for reinforcement learning research.

- **Realistic Advanced Physics**  
  Thermodynamic equations with:
  - CPU dynamic voltage-frequency scaling (DVFS simulation)
  - Temperature-dependent leakage power
  - Thermal inertia and heat transfer modeling
  - Economizer mode for free cooling
  - Cooling system degradation over time
  - Arrhenius law for component aging

- **State-of-the-Art RL Architecture**  
  Uses **PPO with Attention Policy** via Stable-Baselines3 for:
  - Temporal pattern recognition
  - Multi-server relationship modeling
  - Stable, efficient, and reproducible training

### Optimization Features

- **Multi-Objective Reward Function**
  - Quadratic power penalty for aggressive savings
  - Adaptive thermal safety thresholds
  - PUE optimization (Power Usage Effectiveness)
  - Cooling efficiency bonuses
  - System health preservation
  - Action smoothness for mechanical longevity

- **Professional Benchmarking & Visualization**  
  Comprehensive comparison suite with:
  - Power consumption trends with savings highlighting
  - Thermal safety zone analysis
  - Cumulative energy savings tracking
  - PUE comparison charts
  - Multi-dimensional performance metrics
  - Power breakdown (IT vs cooling)
  - Statistical significance analysis

---

## 🧱 Project Structure

```text
S.C.A.R.I/
├── configs/
│   ├── default.yaml          # Standard configuration
│   └── optimized.yaml         # Enhanced config for best performance
├── src/
│   ├── envs/
│   │   └── datacenter_env.py  # Gymnasium environment
│   ├── models/
│   │   ├── server.py          # Advanced server physics
│   │   ├── rack.py            # Rack aggregation logic
│   │   ├── cooling.py         # Cooling system with economizer
│   │   └── attention_policy.py # Attention-based policy network
│   ├── cli/
│   │   ├── train.py           # Training command
│   │   └── evaluate.py        # Evaluation & comparison
│   ├── utils/
│   │   └── visualization.py   # Professional dashboards
│   └── config.py              # Configuration management
├── data/
│   ├── trained_models/        # Saved model checkpoints
│   └── verification_models/   # Verification runs
├── outputs/                   # Generated plots and reports
├── logs/                      # Training logs (TensorBoard)
├── main.py                    # Main entry point
└── requirements.txt


---

## ⚙️ Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Setup

1. Clone the repository:
```bash
git clone https://github.com/your-username/S.C.A.R.I.git
cd S.C.A.R.I


2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate


3. Install dependencies:
```bash
pip install -r requirements.txt


4. Verify installation:
```bash
python main.py --help


---

## 🧠 Training the Agent

Train S.C.A.R.I. using the optimized configuration for best results:

```bash
# Quick training (500K steps - ~30 minutes on modern CPU)
python main.py --train --config configs/default.yaml --timesteps 500000

# Optimized training (1.5M steps - recommended for best performance)
python main.py --train --config configs/optimized.yaml --timesteps 1500000

# Training with GPU acceleration
python main.py --train --config configs/optimized.yaml --device cuda

# Training with custom checkpoints
python main.py --train --timesteps 1000000 --config configs/optimized.yaml


**Training Process:**
- Agent learns through trial and error
- Saving energy is strongly rewarded (quadratic bonus)
- Overheating servers is heavily penalized
- Models auto-saved every 50,000 steps

**Output:**
- Model: `data/trained_models/scari_final.zip`
- Normalization stats: `data/trained_models/vec_normalize.pkl`
- TensorBoard logs: `logs/SCARI_*/`

**Monitor Training (optional):**
```bash
tensorboard --logdir=logs
# Navigate to http://localhost:6006


---

## 📊 Evaluation & Benchmarking

Evaluate your trained model against a traditional PID baseline:

```bash
# Standard evaluation (5000 steps - ~5 minutes)
python main.py --evaluate --eval-steps 5000

# Extended evaluation for statistical confidence
python main.py --evaluate --eval-steps 10000

# Evaluate specific model
python main.py --evaluate --model data/trained_models/scari_final.zip


**Generated Outputs (`outputs/`):**

1. **`comprehensive_dashboard.png`**  
   Multi-panel dashboard showing:
   - Power consumption comparison with savings regions
   - Temperature management with safety zones
   - Cumulative energy savings over time
   - PUE comparison bar chart
   - Multi-dimensional performance metrics
   - Performance summary card

2. **`power_breakdown.png`**  
   Stacked area charts showing IT power vs cooling power for both approaches

3. **`comparison.png`**  
   Legacy comparison plots (maintained for compatibility)

4. **`metrics.json`**  
   Detailed numerical metrics for both baseline and SCARI

5. **`report.txt`**  
   Human-readable text summary of results

---

## 🔬 Physical Model & Science

The simulator uses simplified but realistic thermodynamic equations.

### CPU Power Consumption

Dynamic power based on workload with temperature-dependent leakage:


P_cpu = P_idle + (P_max - P_idle) · (2u - u^r)
P_leak = P_static · exp(k · (T - T_ref))
P_total = P_dynamic + P_leak


Where:
- `u` = CPU utilization (0-1)
- `r` = power curve coefficient
- `k` = leakage temperature coefficient
- `T` = current temperature

### Cooling System Physics

**Air Cooling:**
- Cubic power relationship: `P ∝ f³`
- Economizer mode when ambient < 18°C
- Deadband zone for minimal operation
- Efficiency sweet spot at 70-80% speed

**Liquid Cooling:**
- Quadratic power relationship
- Best efficiency point (BEP) at ~65% flow
- Higher heat capacity than air
- Temperature-gradient dependent effectiveness

### Heat Transfer


Q_net = Q_generated - Q_removed
ΔT = (Q_net · dt) / thermal_mass


Heat removal effectiveness scales with temperature differential and cooling mode.

---

## 📝 Configuration

All parameters can be adjusted in YAML files.

### Key Parameters

**Physics (`configs/optimized.yaml`):**
- `ambient_temp`: Data center ambient (22°C default)
- `max_temp`: Critical temperature limit (95°C)
- `server_thermal_mass`: Thermal inertia (15000 J/K)
- `p_max`: Maximum server power (800W)

**Cooling:**
- `max_fan_power`: Maximum fan power (500W - realistic industrial)
- `air_cooling_capacity`: Cooling capacity (4000W)
- `liquid_cooling_capacity`: Liquid cooling (15000W)

**Training:**
- `timesteps`: Total training steps (1.5M recommended)
- `learning_rate`: PPO learning rate (0.0001)
- `n_steps`: Rollout buffer size (8192)
- `gamma`: Discount factor (0.9995 for long-term planning)

---

## 🎯 Performance Targets

Based on our research and testing, S.C.A.R.I. should achieve:

| Metric | Target | Baseline | Expected SCARI |
|--------|--------|----------|----------------|
| **Energy Savings** | 15-25% | 0% | 15-25% |
| **PUE** | < 1.15 | ~1.015 | 1.05-1.10 |
| **Max Temp** | < 85°C | ~26°C | 45-60°C |
| **Safety Violations** | 0 | 0 | 0 |
| **Thermal Stability** | > 95% | ~98% | 95-98% |

*Note: Higher operating temperatures are acceptable and energy-efficient when within safe limits*

---

## 🧪 Research Context

S.C.A.R.I. was developed as part of a **research project on Data Center Optimization using Deep Reinforcement Learning**, combining:

- Sustainable computing principles
- Advanced control theory
- Applied artificial intelligence 
- Energy-aware system design
- Multi-objective optimization

**Inspired by:**
- Jin et al. (2020) - Thermodynamic modeling
- DeepMind's data center cooling AI
- Industry best practices (ASHRAE guidelines)

---

## 🤝 Contributing

Contributions are welcome! Areas for improvement:

- Multi-rack coordination
- Real-world deployment integration
- Workload prediction models
- More cooling system types
- Cloud provider integration

---

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🔗 Citation

If you use this code in your research, please cite:

```bibtex
@software{scari2026,
  title={S.C.A.R.I.: Sustainable Cooling and Autonomous Resource Intelligence},
  author={Your Name},
  year={2026},
  url={https://github.com/your-username/S.C.A.R.I}
}


---

> **S.C.A.R.I. doesn't just cool servers — it learns how to think thermally.**

