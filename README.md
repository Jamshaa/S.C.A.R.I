# S.C.A.R.I — Smart Cooling & AI-driven Resource Infrastructure

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black)
![PPO](https://img.shields.io/badge/Algorithm-PPO-orange)
![License](https://img.shields.io/badge/License-MIT-green)

**S.C.A.R.I** is a Reinforcement Learning framework for **autonomous thermal management** of data-centre infrastructure. It uses a PPO agent with a custom attention-based policy to optimise cooling in real time, reducing energy consumption while maintaining safe operating temperatures.

---

## Features

| Area                          | Detail                                                     |
| ----------------------------- | ---------------------------------------------------------- |
| **Thermal RL Agent**          | PPO with attention policy, thermally-aware state space     |
| **Physics Simulation**        | Multi-rack server environment with realistic heat transfer |
| **Telemetry Dashboard**       | Live training progress, evaluation metrics, decision trace |
| **Sustainability Calculator** | CO₂ offset, annual savings (EUR), PUE analysis by region   |
| **Explainability**            | Per-step reasoning, feature attribution, confidence scores |

---

## Quick Start

```bash
# 1. Clone and enter
git clone https://github.com/Jamshaa/S.C.A.R.I.git
cd S.C.A.R.I

# 2. Python environment
python -m venv venv
.\venv\Scripts\activate        # Windows
source venv/bin/activate       # Linux / macOS
pip install -r requirements.txt

# 3. Frontend
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

---

## Project Structure

```
S.C.A.R.I/
├── configs/                # Training profiles (default, optimised)
├── data/models/            # Trained model checkpoints (.zip)
├── src/
│   ├── api/                # FastAPI backend & endpoints
│   │   ├── app.py          # Main API server
│   │   └── sample_decisions.py
│   ├── envs/               # Gymnasium environment (thermal sim)
│   ├── models/             # Server, rack, cooling, policy networks
│   ├── utils/              # Config, visualisation, explainability, GreenDC calculator
│   ├── train.py            # CLI training entry-point
│   └── evaluate.py         # CLI evaluation entry-point
├── ui/                     # React + Vite dashboard
│   └── src/
│       ├── App.jsx         # Main application UI
│       ├── DataCenterCalculator.jsx
│       ├── index.css       # Design system
│       └── config.js       # API base URL
├── tests/                  # pytest test suite
├── Dockerfile              # Container build
├── docker-compose.yml      # Full-stack orchestration
└── Makefile                # Common tasks
```

---

## API Reference

Once the backend is running, interactive docs are at:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

Key endpoints:

| Method   | Path                  | Description            |
| -------- | --------------------- | ---------------------- |
| `GET`    | `/models`             | List trained models    |
| `POST`   | `/train`              | Start training run     |
| `POST`   | `/evaluate`           | Evaluate a model       |
| `GET`    | `/evaluation-results` | Latest evaluation data |
| `DELETE` | `/models/{name}`      | Delete single model    |
| `DELETE` | `/models`             | Clear all models       |

---

## Docker

```bash
docker-compose up -d
```

Backend → `http://localhost:8000` · Frontend → `http://localhost:5173`

---

## License

MIT — see [LICENSE](LICENSE)
