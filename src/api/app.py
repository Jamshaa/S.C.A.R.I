import os
import subprocess
import threading
from pathlib import Path
from typing import List, Optional
import json

from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI(title="S.C.A.R.I API")

# Enable CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent.parent
MODELS_DIR = BASE_DIR / "data" / "models"
OUTPUTS_DIR = BASE_DIR / "outputs" / "eval"

# Ensure directories exist
MODELS_DIR.mkdir(parents=True, exist_ok=True)
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

# Servir archivos estáticos para ver las gráficas (png)
app.mount("/outputs", StaticFiles(directory=str(BASE_DIR / "outputs")), name="outputs")

@app.get("/")
async def root():
    """Root endpoint providing basic info."""
    return {
        "name": "S.C.A.R.I API",
        "version": "2.0.0",
        "status": "online",
        "endpoints": ["/models", "/status", "/results", "/outputs"]
    }

class TrainingParams(BaseModel):
    timesteps: int = 10000
    config: str = "configs/default.yaml"

class TrainingStatus:
    is_training = False
    progress = 0
    last_log = ""

status = TrainingStatus()

@app.get("/models")
async def get_models():
    """List all available models."""
    models = []
    for f in MODELS_DIR.glob("*.zip"):
        models.append(f.name)
    return {"models": models}

def run_train_task(params: TrainingParams):
    global status
    status.is_training = True
    try:
        # Use full path to python in venv if it exists, otherwise use 'python'
        venv_python = str(BASE_DIR / "venv" / "Scripts" / "python.exe")
        if not os.path.exists(venv_python):
            venv_python = "python"
            
        # Construct command
        cmd = [
            venv_python, "train.py",
            "--timesteps", str(params.timesteps),
            "--config", params.config
        ]
        # Run process
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=str(BASE_DIR)
        )
        for line in process.stdout:
            status.last_log = line.strip()
            # Basic progress parsing if possible, or just log
    except Exception as e:
        status.last_log = f"Error: {str(e)}"
    finally:
        status.is_training = False

@app.post("/train")
async def start_training(params: TrainingParams, background_tasks: BackgroundTasks):
    """Start training in background."""
    if status.is_training:
        raise HTTPException(status_code=400, detail="Training already in progress")
    background_tasks.add_task(run_train_task, params)
    return {"message": "Training started"}

@app.get("/status")
async def get_status():
    """Get training status."""
    return {
        "is_training": status.is_training,
        "last_log": status.last_log
    }

@app.post("/evaluate")
async def run_evaluation(model_name: str, steps: int = 5000):
    """Run evaluation for a specific model."""
    model_path = MODELS_DIR / model_name
    if not model_path.exists():
        raise HTTPException(status_code=404, detail="Model not found")
    
    print(f"DEBUG: Evaluating {model_name} for {steps} steps")
    
    venv_python = str(BASE_DIR / "venv" / "Scripts" / "python.exe")
    if not os.path.exists(venv_python):
        venv_python = "python"

    cmd = [
        venv_python, "evaluate.py",
        "--model", str(model_path),
        "--output", str(OUTPUTS_DIR),
        "--steps", str(steps)
    ]
    
    try:
        # We run it synchronously as it usually takes ~5-10 seconds for 5000 steps
        result = subprocess.run(cmd, check=True, cwd=str(BASE_DIR), capture_output=True, text=True)
        return {"message": "Evaluation successful", "output": result.stdout}
    except subprocess.CalledProcessError as e:
        print(f"ERROR: {e.stdout}\n{e.stderr}")
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {e.stderr or e.stdout}")

@app.get("/results")
async def get_results():
    """Get the results of the last evaluation."""
    metrics_path = OUTPUTS_DIR / "metrics.json"
    if not metrics_path.exists():
        return {"error": "No results available"}
    
    with open(metrics_path, "r") as f:
        metrics = json.load(f)
    
    # List available images in outputs/eval
    images = []
    for f in OUTPUTS_DIR.glob("*.png"):
        images.append(f"/outputs/eval/{f.name}")
        
    return {
        "metrics": metrics,
        "images": images
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
