# S.C.A.R.I

S.C.A.R.I is a reinforcement learning project for data center cooling optimization.
It trains a PPO agent to reduce energy consumption while keeping server temperatures within safe limits.

## What It Does

- Simulates a data center thermal environment with servers, racks, and cooling systems
- Trains an RL agent to choose cooling actions in real time
- Compares the trained model against a baseline controller
- Exposes results through a FastAPI backend and a React dashboard
- Includes sustainability and efficiency metrics such as power savings and PUE

## How It Works

1. The environment simulates server load, heat generation, and cooling response.
2. A PPO agent learns which cooling action to apply at each step.
3. The trained policy is evaluated against a baseline controller.
4. Results are shown in the UI and through the API.

## Stack

- Python
- FastAPI
- React + Vite
- Stable-Baselines3
- Gymnasium

## Quick Start

### Requirements

- Python 3.10+
- Node.js 20+

### Install

```bash
git clone https://github.com/Jamshaa/S.C.A.R.I.git
cd S.C.A.R.I

python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt

cd ui
npm install
cd ..
```

### Run

Backend:

```bash
python -m uvicorn src.api.app:app --host 127.0.0.1 --port 8000 --reload
```

Frontend:

```bash
cd ui
npm run dev
```

Open `http://localhost:5173`.

## Training

The default profile is:

```bash
configs/default.yaml
```

Train with the default config:

```bash
python -m src.train --config configs/default.yaml --cooling-mode AIR --output-name scari_target20
```

Other profiles are available in `configs/`, including `optimized.yaml`, `max_savings_safe.yaml`, `liquid.yaml`, and `hybrid.yaml`.

## Evaluation

Evaluate a trained model:

```bash
python -m src.evaluate --config configs/default.yaml --models data/models/scari_target20.zip
```

## Project Layout

```text
configs/   YAML training and evaluation profiles
src/       Backend, environment, models, training, evaluation
ui/        React dashboard
tests/     Test suite
```

## License

This project is licensed under the MIT License.

That means you can use, modify, and distribute it, including for private or commercial work, as long as you keep the license notice.
