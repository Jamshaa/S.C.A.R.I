# S.C.A.R.I — Smart Cooling & AI-driven Resource Infrastructure

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=black)
![PPO](https://img.shields.io/badge/Algorithm-PPO-orange)
![License](https://img.shields.io/badge/License-MIT-green)
![CI](https://github.com/Jamshaa/S.C.A.R.I/actions/workflows/test.yml/badge.svg)

**S.C.A.R.I** is a Reinforcement Learning framework for **autonomous thermal management** of data-centre infrastructure. A PPO agent with a custom attention-based policy learns to optimise cooling in real time — reducing energy consumption while maintaining safe operating temperatures.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    React + Vite UI (5173)                    │
│  ┌──────────┐  ┌──────────────┐  ┌───────────────────────┐  │
│  │ Training  │  │  Evaluation  │  │ Sustainability Calc.  │  │
│  │ Monitor   │  │ Dashboard    │  │ ROI · CO₂ · PUE       │  │
│  └─────┬─────┘  └──────┬───────┘  └──────────┬────────────┘  │
│        └───────────────┼──────────────────────┘              │
└─────────────────────────┼────────────────────────────────────┘
                          │ REST API
┌─────────────────────────┼────────────────────────────────────┐
│              FastAPI Backend (8000)                           │
│  ┌──────────┐  ┌──────────────┐  ┌───────────────────────┐  │
│  │ Training  │  │  Evaluation  │  │ GreenDC Calculator    │  │
│  │ Runner    │  │  Runner      │  │ (CO₂, ROI, topology)  │  │
│  └─────┬─────┘  └──────┬───────┘  └───────────────────────┘  │
│        └───────────────┼─────────────────────────────────────│
│              ┌─────────┴──────────┐                          │
│              │ Gymnasium Env      │                          │
│              │ (Physics Sim)      │                          │
│              └─────────┬──────────┘                          │
│              ┌─────────┴──────────┐                          │
│              │ PPO Agent (SB3)    │                          │
│              │ Attention Policy   │                          │
│              └────────────────────┘                          │
└──────────────────────────────────────────────────────────────┘
```

---

## Features

| Area                          | Detail                                                     |
| ----------------------------- | ---------------------------------------------------------- |
| **Thermal RL Agent**          | PPO with attention policy, thermally-aware state space     |
| **Physics Simulation**        | Multi-rack server environment with realistic heat transfer |
| **Telemetry Dashboard**       | Live training progress, evaluation metrics, decision trace |
| **Sustainability Calculator** | CO₂ offset, annual savings (EUR), PUE analysis by region   |
| **Explainability**            | Per-step reasoning, feature attribution, confidence scores |
| **Evaluation History**        | Named runs, side-by-side comparison, chart downloads       |

---

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- Git

### Setup

```bash
# 1. Clone
git clone https://github.com/Jamshaa/S.C.A.R.I.git
cd S.C.A.R.I

# 2. Environment config
cp .env.example .env

# 3. Python environment
python -m venv venv
.\venv\Scripts\activate        # Windows
# source venv/bin/activate     # Linux / macOS
pip install -r requirements.txt

# 4. Frontend
cd ui && npm install && cd ..
```

### Run

**Backend** (Terminal 1):

```bash
python -m uvicorn src.api.app:app --host 127.0.0.1 --port 8000 --reload
```

**Frontend** (Terminal 2):

```bash
cd ui && npm run dev
```

Open **http://localhost:5173**

### Shutdown

Press `Ctrl+C` in each terminal. Alternatively:

```bash
# Kill backend by port (Windows)
python src/scripts/cleanup_server.py

# Or manually
taskkill /F /IM python.exe
taskkill /F /IM node.exe
```

---

## Project Structure

```
S.C.A.R.I/
├── configs/
│   ├── default.yaml            # Base training profile
│   └── optimized.yaml          # Tuned thermal-safe profile
├── data/models/                # Trained model checkpoints (.zip)
├── src/
│   ├── api/
│   │   ├── app.py              # FastAPI backend (all endpoints)
│   │   └── sample_decisions.py # Demo explainability data
│   ├── envs/
│   │   └── datacenter_env.py   # Gymnasium environment (thermal sim)
│   ├── models/
│   │   ├── server.py           # Server thermal model
│   │   ├── rack.py             # Rack aggregation model
│   │   ├── cooling.py          # Cooling system model
│   │   └── policy.py           # Attention-based policy network
│   ├── utils/
│   │   ├── config.py           # Configuration loader
│   │   ├── visualization.py    # Chart generation
│   │   ├── explainability.py   # Decision explanation engine
│   │   └── greendc.py          # Sustainability calculator
│   ├── scripts/
│   │   └── cleanup_server.py   # Port cleanup utility
│   ├── train.py                # CLI training entry-point
│   └── evaluate.py             # CLI evaluation entry-point
├── ui/                         # React + Vite dashboard
│   └── src/
│       ├── App.jsx             # Main application UI
│       ├── DataCenterCalculator.jsx
│       ├── index.css           # Design system
│       └── config.js           # API base URL
├── tests/                      # pytest suite
│   ├── test_api.py             # API endpoint tests
│   ├── test_env.py             # Environment tests
│   └── test_greendc.py         # Sustainability calculator tests
├── .github/workflows/test.yml  # CI pipeline
├── Dockerfile                  # Backend container
├── docker-compose.yml          # Full-stack orchestration
├── Makefile                    # Common tasks
├── requirements.txt            # Python dependencies
└── .env.example                # Environment template
```

---

## API Reference

Once the backend is running, interactive docs are at:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Core Endpoints

| Method   | Path                  | Description              |
| -------- | --------------------- | ------------------------ |
| `GET`    | `/`                   | API info and status      |
| `GET`    | `/health`             | System health check      |
| `GET`    | `/models`             | List trained models      |
| `POST`   | `/models/rename`      | Rename a model           |
| `DELETE` | `/models/{name}`      | Delete a single model    |
| `DELETE` | `/models`             | Clear all models         |
| `POST`   | `/train`              | Start training run       |
| `GET`    | `/status`             | Training progress        |
| `POST`   | `/evaluate`           | Start evaluation run     |
| `GET`    | `/evaluation-status`  | Evaluation progress      |
| `GET`    | `/evaluation-results` | Latest evaluation data   |
| `GET`    | `/history`            | List all evaluation runs |
| `GET`    | `/history/{id}`       | Get specific evaluation  |
| `DELETE` | `/history/{id}`       | Delete an evaluation run |
| `GET`    | `/explain`            | AI decision explanations |

### Sustainability Calculator Endpoints

| Method | Path                              | Description                      |
| ------ | --------------------------------- | -------------------------------- |
| `POST` | `/calculator/embodied-carbon`     | Hardware embodied CO₂            |
| `POST` | `/calculator/network-topology`    | Network topology analysis        |
| `POST` | `/calculator/scenario-comparison` | Baseline vs optimised comparison |
| `POST` | `/calculator/roi-analysis`        | Financial ROI analysis           |
| `POST` | `/calculator/comprehensive`       | Full sustainability report       |
| `GET`  | `/calculator/info`                | Available calculators info       |

---

## Docker

```bash
docker compose up -d
```

Backend → `http://localhost:8000` · Frontend → `http://localhost:5173`

---

## Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test module
python -m pytest tests/test_greendc.py -v

# With coverage
python -m pytest tests/ --cov=src --cov-report=html
```

---

## Configuration

Training profiles live in `configs/`. The `optimized.yaml` profile includes:

- **Physics**: Realistic thermal mass, power ranges, temperature limits
- **Cooling**: Industrial fan/pump power, air and liquid cooling capacities
- **Reward**: Safety-first weighting with energy efficiency as secondary objective
- **Training**: PPO hyperparameters tuned for thermal stability convergence

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Run the test suite (`python -m pytest tests/ -v`)
4. Submit a pull request

---

## License

MIT — see [LICENSE](LICENSE)
