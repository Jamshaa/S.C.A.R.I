# 🚀 S.C.A.R.I — Smart Cooling & Agentic Reinforcement Infrastructure

[![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.11-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688.svg?style=flat&logo=FastAPI)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18%2B-61DAFB.svg?style=flat&logo=React)](https://react.dev/)
[![Docker](https://img.shields.io/badge/Docker-Supported-2496ED.svg?style=flat&logo=Docker)](https://www.docker.com/)

**S.C.A.R.I** is an advanced Reinforcement Learning framework and interactive dashboard designed to optimize **Data Center cooling efficiency** and calculate comprehensive sustainability metrics. It uses **PPO (Proximal Policy Optimization)** agents to learn real-time, thermal-safe cooling policies that dramatically reduce operational carbon footprints and energy expenditure.

---

## 🌟 Key Features

### 🧠 1. Agentic Thermal Control (Reinforcement Learning)
* **Custom Environment:** A robust physics-based environment replicating server loads, heat generation, rack thermodynamics, and cooling inertia.
* **PPO Agents:** State-of-the-art training pipelines built on **Stable-Baselines3** and **Gymnasium** to choose optimal cooling operations dynamically.
* **Safety Override:** Hard thermal boundary protection guarantees servers never overheat, shifting seamlessly between active AI control and traditional baselines if critical thresholds are met.

### 📊 2. Comprehensive Sustainability Calculator
* **Embodied Carbon:** Amortized manufacturing emissions calculations based on server counts and data center density.
* **Network Topology Impact:** Evaluates carbon overhead for network topologies including **Fat-Tree, Clos, Spine-Leaf, and Three-Tier** systems.
* **Operational ROI Analysis:** Instant estimation of capital expenditure (CAPEX), operational savings (OPEX), and carbon payback periods.

### 🌍 3. Global Emissions Explorer
* **Country Baselines Database:** Interactive map panel tracking **real-world country emission intensities** (CO2/kWh, fossil fuel vs. low-carbon energy mix, electricity production, population, and GDP).
* **Location-based Insights:** Compare how your data center's carbon intensity changes dynamically depending on the deployment region (e.g., France's nuclear/renewable grid vs. highly fossil-intensive grids).

### ⚡ 4. Advanced Real-time Dashboard
* **Training & Evaluation Controls:** Spin up, monitor, or terminate RL training runs directly from the UI sidebar in real time.
* **Explainability Panel:** Real-time decision trust meters, safety indexes, and micro-metric power breakdowns.

---

## 🛠️ Technology Stack

* **Backend & RL:** Python, FastAPI, Stable-Baselines3, PyTorch, Gymnasium, Pandas, NumPy.
* **Frontend:** React 18, Vite, Lucide Icons, Recharts, TailwindCSS / HSL Custom Modern Dark Theme.
* **Deployment:** Docker, Docker Compose, GNU Make.

---

## 🚀 Quick Start (Local Development)

### Prerequisites
* **Python** 3.10+
* **Node.js** 20+
* **Git**

### Installation

Clone the repository and install all components using the built-in `Makefile`:

```bash
# Clone the repository
git clone https://github.com/Jamshaa/S.C.A.R.I.git
cd S.C.A.R.I

# Install all backend (venv) & frontend dependencies
make install
```

### Running the Services

#### 1. Backend (FastAPI API)
```bash
# Activate your environment
source venv/bin/activate  # On macOS/Linux
.\.venv\Scripts\activate  # On Windows

# Run the API server
python -m uvicorn src.api.app:app --host 127.0.0.1 --port 8000 --reload
```
* **API Documentation:** Available at `http://127.0.0.1:8000/docs` (Swagger UI).

#### 2. Frontend (React Dashboard)
```bash
cd ui
npm run dev
```
* Open `http://localhost:5173` in your browser.

---

## 🐳 Docker Deployment (Recommended)

To run the entire stack in isolated Docker containers with automated health checks, simply run:

```bash
# Build and spin up containers
make deploy
```
* **Frontend:** `http://localhost:5173`
* **API Backend:** `http://localhost:8000`
* **Shutdown:** Run `make docker-down` to stop all running services safely.

---

## 📈 Training and Evaluation

S.C.A.R.I supports three main cooling system profiles: **AIR**, **LIQUID**, and **HYBRID**. Configuration templates are stored as YAML profiles under the `configs/` directory.

### Train a Model (CLI)
Train a customized thermal-safe agent with specific physics/reward presets:
```bash
python -m src.train --config configs/default.yaml --cooling-mode AIR --name my_custom_air_model
```

### Evaluate a Model (CLI)
Benchmark your trained agent against standard baselines:
```bash
python -m src.evaluate --steps 10000 --models data/models/my_custom_air_model.zip
```

---

## 📂 Project Structure

```text
├── configs/               # YAML training & environment configuration profiles
├── data/                  # Baseline models & static datasets
│   └── models/            # Stored RL models (aire.zip baseline)
├── logs/                  # Local run logs and TensorBoard records (ignored by Git)
├── outputs/               # Locally generated evaluations and models (ignored by Git)
├── src/                   # Core Python Source Code
│   ├── api/               # FastAPI backend router, state, schemas, and tasks
│   ├── envs/              # Gymnasium thermal data center simulation environment
│   ├── models/            # Stable-baselines custom policy models & physical components
│   └── utils/             # Registries, visualizers, calculators, and configurations
├── tests/                 # Comprehensive Pytest test suite
├── ui/                    # React frontend application dashboard
└── Makefile               # Multi-platform development and deployment utility
```

---

## 📝 License

This project is licensed under the **MIT License**. You are free to use, modify, and distribute it, including for commercial projects, provided the original license notice is retained.
