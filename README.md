# S.C.A.R.I. 🤖❄️  
### Sustainable Cooling & Autonomous Resource Intelligence

**S.C.A.R.I.** is an advanced **Artificial Intelligence agent** based on **Reinforcement Learning (RL)**, purpose-built to optimize **energy efficiency in Data Centers**.

Powered by **PPO (Proximal Policy Optimization)**, S.C.A.R.I. learns to **dynamically control air and liquid cooling systems**, significantly reducing electrical consumption **without compromising server thermal safety**.

---

## 🌍 Why S.C.A.R.I.?

Modern data centers waste enormous amounts of energy due to conservative, static cooling strategies.  
**S.C.A.R.I. changes the paradigm** by learning *when* and *how much* to cool — applying only the cooling strictly necessary to remain within safe thermal limits.

> Less energy. Same safety. Smarter decisions.

---

## 🚀 Key Features

- **Custom Simulation Environment**  
  Built on the **Gymnasium** standard for reinforcement learning research.

- **Realistic Physical Modeling**  
  Thermodynamic equations inspired by *Jin et al. (2020)*, including:
  - CPU utilization dynamics  
  - Thermal inertia  
  - Air density and heat capacity  
  - Heat dissipation constraints  

- **State-of-the-Art Reinforcement Learning**  
  Uses **PPO via Stable-Baselines3** for stable, efficient, and reproducible training.

- **Benchmarking & Baselines**  
  Direct comparison between:
  - Traditional controllers (PID / heuristic)
  - Autonomous AI-driven cooling control

- **Professional Visualization**  
  Automatically generates publication-ready plots for:
  - Power consumption  
  - Thermal safety margins  
  - Economic and energy impact  

---

## 🧱 Project Structure

```text
S.C.A.R.I/
├── agents/
│   └── train_ppo.py       # PPO agent training script
├── envs/
│   └── datacenter_env.py  # Gymnasium environment (the rules of the game)
├── models/
│   ├── server.py          # Server physics (heat, CPU, safety limits)
│   ├── rack.py            # Rack-level aggregation logic
│   ├── cooling.py         # Fan and pump physical models
│   └── ppo_scari/         # Trained models (.zip)
├── outputs/               # Generated plots and figures
├── results/               # Raw simulation CSV data
├── config.py              # Physical constants and tunable parameters
└── run_comparison.py      # AI vs Baseline evaluation script
```

---

## ⚙️ Installation

Clone the repository:
```bash
git clone https://github.com/your-username/S.C.A.R.I.git
cd S.C.A.R.I
```

Install dependencies (Python 3.8+ required):
```bash
pip install gymnasium stable-baselines3 pandas matplotlib numpy shimmy
```

---

## 🧠 Training the Agent

To train S.C.A.R.I. from scratch, run the PPO training script.  
The agent learns through **trial and error** over millions of steps:

- Saving energy is rewarded  
- Overheating servers is heavily penalized  

```bash
# Train for 1 million steps (recommended)
python agents/train_ppo.py --timesteps 1000000 --checkpoint-interval 100000
```

**Output model:**  
`models/ppo_scari/scari_v1.zip`

**Monitoring (optional):**
```bash
tensorboard --logdir=logs
```

---

## 📊 Evaluation & Benchmarking

Once trained, S.C.A.R.I. can be evaluated against a traditional baseline controller:

```bash
# Run a 5000-second comparison simulation
python run_comparison.py \
  --steps 5000 \
  --model-path models/ppo_scari/scari_v1.zip
```

**Generated outputs (`outputs/`):**

1. `1_analisis_potencia.png`  
   Highlights (in green) where the AI consumes less power than the baseline.

2. `2_analisis_temperatura.png`  
   Comparison of thermal strategies.  
   The AI often maintains higher — yet safe — temperatures to maximize efficiency.

3. `3_impacto_factura.png`  
   Cumulative energy consumption (Wh), representing the electricity bill.

---

## 🔬 Physical Model & Science

The simulator is governed by simplified but realistic thermodynamic equations.

**CPU Heat Generation:**
```math
P_{cpu} = P_{idle} + (P_{max} - P_{idle}) · (2u - u_r)
```

Where:
- `u`  = CPU utilization  
- `u_r` = reference utilization  

**Heat Dissipation:**  
Depends on flow rate (`f`), coolant heat capacity (`C_p`), and temperature difference (`ΔT`).

**Cooling Power Consumption:**

- **Air Cooling:**  
  Cubic relationship:
  ```math
  P ∝ f³
  ```
  Small reductions in fan speed yield massive energy savings.

- **Liquid Cooling:**  
  Quadratic or linear behavior depending on the pump curve.

---

## 📝 Configuration

All physical parameters can be adjusted in `config.py`, including:

- `AMBIENT_TEMP`  
  Air intake temperature (default: 22 °C)

- `SERVER_THERMAL_MASS`  
  Thermal inertia of servers (heating/cooling speed)

- `P_MAX`  
  Maximum power draw per server node (Watts)

---

## 🧪 Research Context

S.C.A.R.I. was developed as part of a **research project on Data Center Optimization using Deep Reinforcement Learning**, combining:

- Sustainable computing  
- Control theory  
- Applied artificial intelligence  
- Energy-aware system design  

---

> **S.C.A.R.I. doesn’t just cool servers — it learns how to think thermally.**
