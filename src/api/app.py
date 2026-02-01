import os
import subprocess
import threading
from pathlib import Path
from typing import List, Optional
import json

from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from src.utils.greendc import GreenDCCalculator
from pydantic import BaseModel, validator
import logging

# Configure Structured Logging
class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_obj = {
            "time": self.formatTime(record),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
        }
        return json.dumps(log_obj)

logger = logging.getLogger("SCARI_API")
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logger.addHandler(handler)
logger.setLevel(logging.INFO)

app = FastAPI(title="S.C.A.R.I API")

# Enable CORS for specific frontend origins
origins = [
    "http://localhost",
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
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

def get_python_executable():
    """Get the path to the python executable in the venv, cross-platform."""
    # Windows
    windows_path = BASE_DIR / "venv" / "Scripts" / "python.exe"
    if windows_path.exists():
        return str(windows_path)
    # Linux / Mac
    unix_path = BASE_DIR / "venv" / "bin" / "python"
    if unix_path.exists():
        return str(unix_path)
    # Fallback
    return "python"

@app.get("/")
async def root():
    """Root endpoint providing basic info."""
    return {
        "name": "S.C.A.R.I API",
        "version": "2.0.0",
        "status": "online",
        "endpoints": ["/models", "/status", "/results", "/outputs", "/health"]
    }

@app.get("/health")
async def health_check():
    """Detailed health check for the SCARI ecosystem."""
    import torch
    return {
        "status": "operating",
        "compute": {
            "device": "cuda" if torch.cuda.is_available() else "cpu",
            "torch_version": torch.__version__
        },
        "storage": {
            "models_count": len(list(MODELS_DIR.glob("*.zip"))),
            "evaluations_count": len(list(OUTPUTS_DIR.glob("*.json")))
        }
    }

class TrainingParams(BaseModel):
    timesteps: int = 10000
    config: str = "configs/optimized.yaml"
    name: str = "scari_model"

    @validator('timesteps')
    def validate_timesteps(cls, v):
        if v < 1000 or v > 10_000_000:
            raise ValueError("timesteps must be between 1,000 and 10,000,000")
        return v

class RenameRequest(BaseModel):
    old_name: str
    new_name: str

    @validator('new_name')
    def validate_name(cls, v):
        if not v.endswith('.zip'):
            return f"{v}.zip"
        return v


class TrainingStatus:
    is_training = False
    progress = 0
    current_step = 0
    total_steps = 0
    last_log = ""

class EvaluationStatus:
    is_evaluating = False
    last_log = ""
    error = ""
    result = None

status = TrainingStatus()
eval_status = EvaluationStatus()
greendc = GreenDCCalculator() # Default industrial rates

@app.get("/models")
async def get_models():
    """List all available models."""
    models = []
    # Avoid listing hidden files and ensure we only get .zip
    for f in MODELS_DIR.glob("*.zip"):
        if f.is_file() and not f.name.startswith('.'):
            models.append(f.name)
    return {"models": models}

def sanitize_model_name(name: str) -> str:
    """Basic sanitization to prevent path traversal."""
    return os.path.basename(name)

@app.post("/models/rename")
async def rename_model(request: RenameRequest):
    """Rename an existing model."""
    old_name = sanitize_model_name(request.old_name)
    new_name = sanitize_model_name(request.new_name)
    
    old_path = MODELS_DIR / old_name
    new_path = MODELS_DIR / new_name
    
    if not old_path.exists():
        logger.warning(f"Rename failed: Model {request.old_name} not found")
        raise HTTPException(status_code=404, detail="Model not found")
        
    if new_path.exists():
        logger.warning(f"Rename failed: Target {request.new_name} already exists")
        raise HTTPException(status_code=400, detail="New name already exists")
    
    try:
        old_path.rename(new_path)
        logger.info(f"Renamed model {request.old_name} to {request.new_name}")
        return {"message": f"Renamed {request.old_name} to {request.new_name}", "new_name": request.new_name}
    except Exception as e:
        logger.error(f"Rename error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to rename: {str(e)}")

@app.delete("/models")
async def delete_all_models():
    """Delete all model files."""
    try:
        count = 0
        deleted_files = []
        for f in MODELS_DIR.glob("*.zip"):
            try:
                os.remove(f)
                count += 1
                deleted_files.append(f.name)
            except Exception as e:
                logger.error(f"Failed to delete {f.name}: {e}")
                
        logger.info(f"Deleted all models ({count} files)")
        return {"message": f"Deleted {count} models", "deleted": deleted_files}
    except Exception as e:
        logger.error(f"Delete all error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete all: {str(e)}")


def run_train_task(params: TrainingParams):
    global status
    status.is_training = True
    status.progress = 0
    status.current_step = 0
    status.total_steps = params.timesteps
    try:
        venv_python = get_python_executable()
            
        # Construct command
        cmd = [
            venv_python, "-m", "src.train",
            "--timesteps", str(params.timesteps),
            "--config", params.config,
            "--output-name", params.name
        ]
        
        # Set UTF-8 encoding for Windows
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONUNBUFFERED"] = "1"
        
        # Run process
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            cwd=str(BASE_DIR),
            env=env
        )
        for line in process.stdout:
            status.last_log = line.strip()
            # Parse progress from SB3 logs
            if "total_timesteps" in line:
                try:
                    # Line format matches: |    total_timesteps     | 1234        |
                    parts = line.split('|')
                    if len(parts) >= 3:
                        timesteps = int(parts[2].strip())
                        status.current_step = timesteps
                        status.progress = min(100, int((timesteps / params.timesteps) * 100))
                except:
                    pass
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
        "last_log": status.last_log,
        "progress": status.progress
    }

def run_eval_task(model_path: Path, steps: int, output_dir: Path):
    global eval_status
    eval_status.is_evaluating = True
    eval_status.error = ""
    eval_status.result = None
    
    venv_python = get_python_executable()

    cmd = [
        venv_python, "-m", "src.evaluate",
        "--model", str(model_path),
        "--output", str(output_dir),
        "--steps", str(steps)
    ]
    
    try:
        # Set UTF-8 encoding for Windows
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            cwd=str(BASE_DIR),
            env=env
        )
        for line in process.stdout:
            eval_status.last_log = line.strip()
            
        process.wait()
        if process.returncode == 0:
            # Load results
            metrics_path = output_dir / "metrics.json"
            if metrics_path.exists():
                with open(metrics_path, "r") as f:
                    eval_status.result = json.load(f)
        else:
            eval_status.error = f"Evaluation process exited with code {process.returncode}"
    except Exception as e:
        eval_status.error = str(e)
    finally:
        eval_status.is_evaluating = False

@app.post("/evaluate")
async def run_evaluation(model_name: str, background_tasks: BackgroundTasks, steps: int = 5000):
    """Run evaluation for a specific model in background."""
    safe_name = sanitize_model_name(model_name)
    model_path = MODELS_DIR / safe_name
    if not model_path.exists():
        raise HTTPException(status_code=404, detail="Model not found")
    
    if eval_status.is_evaluating:
        raise HTTPException(status_code=400, detail="Evaluation already in progress")
    
    background_tasks.add_task(run_eval_task, model_path, steps, OUTPUTS_DIR)
    return {"message": "Evaluation started"}

@app.get("/evaluation-status")
async def get_evaluation_status():
    """Get the current evaluation status."""
    return {
        "is_evaluating": eval_status.is_evaluating,
        "last_log": eval_status.last_log,
        "error": eval_status.error,
        "has_result": eval_status.result is not None
    }

@app.get("/results")
async def get_results():
    """Get the results of the last evaluation with safety checks."""
    metrics_path = OUTPUTS_DIR / "metrics.json"
    if not metrics_path.exists():
        logger.warning("Attempted to fetch results but metrics.json is missing")
        return {"error": "No results available. Please run an evaluation first."}
    
    try:
        with open(metrics_path, "r") as f:
            metrics = json.load(f)
    except Exception as e:
        logger.error(f"Error reading metrics.json: {e}")
        return {"error": "Failed to parse evaluation results."}
    
    # List available images in outputs/eval
    images = []
    try:
        for f in sorted(OUTPUTS_DIR.glob("*.png")):
            # Only include valid images
            if f.stat().st_size > 0:
                images.append(f"/outputs/eval/{f.name}")
    except Exception as e:
        logger.error(f"Error listing output images: {e}")
        # Continue without images if there's an error
        images = []
    
    # Calculate sustainability impact
    green_impact = greendc.calculate_impact(
        baseline_power_w=metrics['baseline']['total_power_consumption'],
        scari_power_w=metrics['scari']['total_power_consumption'],
        simulation_steps=metrics['scari'].get('total_steps', 5000)
    )
        
    return {
        "metrics": metrics,
        "images": images,
        "sustainability": green_impact
    }

@app.get("/explain")
async def get_explanations():
    """Get decision explanations for demo."""
    from src.api.sample_decisions import SAMPLE_DECISIONS
    return {"decisions": SAMPLE_DECISIONS}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
