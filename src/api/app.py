import os
import subprocess
import threading
from pathlib import Path
from typing import List, Optional
import json
from datetime import datetime
import shutil

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

# Enable CORS for frontend origins
# Supports: localhost, Codespaces, and production deployments
origins = [
    # Local development (explicit)
    "http://localhost",
    "http://127.0.0.1",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    # Common dev ports
    "http://localhost:5174",
    "http://localhost:3000",
]

# Allow GitHub Codespaces and similar patterns via a regex
# Use allow_origin_regex to match any subdomain that ends with .app.github.dev
origin_regex = r"^https?://[a-z0-9-]+-\d+\.app\.github\.dev(:\d+)?$"

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
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

@app.delete("/models/{model_name}")
async def delete_model(model_name: str):
    """Delete a single model file."""
    safe_name = sanitize_model_name(model_name)
    model_path = MODELS_DIR / safe_name
    
    if not model_path.exists():
        raise HTTPException(status_code=404, detail="Model not found")
    
    try:
        os.remove(model_path)
        logger.info(f"Deleted model: {safe_name}")
        return {"message": f"Deleted {safe_name}"}
    except Exception as e:
        logger.error(f"Delete error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete: {str(e)}")


def run_train_task(params: TrainingParams):
    global status
    status.is_training = True
    status.progress = 0
    status.current_step = 0
    status.total_steps = params.timesteps
    logger.info(f"STARTING training task: {params.name} for {params.timesteps} steps")
    
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
            env=env,
            bufsize=1, # Line buffered
            universal_newlines=True
        )

        # Threaded reader to avoid blocking on Windows
        def reader(pipe, queue):
            try:
                with pipe:
                    for line in iter(pipe.readline, ''):
                        queue.put(line)
            finally:
                queue.put(None)

        import queue
        q = queue.Queue()
        t = threading.Thread(target=reader, args=(process.stdout, q))
        t.daemon = True
        t.start()

        # Read from queue
        while True:
            try:
                line = q.get(timeout=1) # Non-blocking with timeout
            except queue.Empty:
                if process.poll() is not None:
                    break
                continue

            if line is None:
                break

            status.last_log = line.strip()
            
            # Explicit success detection
            if "Training complete" in line:
                status.progress = 100
                logger.info(f"DETECTED completion signature for {params.name}")
                
            # Explicit failure detection
            if "Traceback" in line or "Error:" in line:
                logger.error(f"DETECTED error in training: {line.strip()}")

            # Parse progress from SB3 logs
            if "total_timesteps" in line:
                try:
                    # Line format matches: |    total_timesteps     | 1234        |
                    parts = line.split('|')
                    if len(parts) >= 3:
                        timesteps = int(parts[2].strip())
                        status.current_step = timesteps
                        # cap at 99 until explicit finish
                        status.progress = min(99, int((timesteps / params.timesteps) * 100))
                except:
                    pass
        
        # Ensure process finishes
        process.wait()
        if process.returncode == 0:
            status.progress = 100
            status.last_log = "Training completed successfully."
            logger.info(f"COMPLETED training task: {params.name}")
        else:
            status.last_log = f"Training failed with exit code {process.returncode}"
            logger.error(f"FAILED training task: {params.name} (exit code {process.returncode})")
            
    except Exception as e:
        status.last_log = f"Error: {str(e)}"
        logger.error(f"CRASHED training task: {str(e)}")
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

@app.get("/history")
async def get_history():
    """List all available historical evaluations."""
    history = []
    try:
        # Scan OUTPUTS_DIR for timestamped directories
        for entry in sorted(OUTPUTS_DIR.iterdir(), reverse=True):
            if entry.is_dir() and (entry / "metrics.json").exists():
                try:
                    with open(entry / "metrics.json", "r") as f:
                        metrics = json.load(f)
                    
                    # Extract key summary data
                    summary = {
                        "id": entry.name,
                        "timestamp": entry.name,
                        "pue": metrics['scari'].get('average_pue'),
                        "savings": ((metrics['baseline']['total_power_consumption'] - metrics['scari']['total_power_consumption']) / metrics['baseline']['total_power_consumption']) * 100,
                        "steps": metrics['scari'].get('total_steps', 5000),
                        "model": "scari_model" # Could store this in metrics if needed
                    }
                    history.append(summary)
                except Exception as e:
                    logger.warning(f"Failed to parse history entry {entry.name}: {e}")
                    continue
        return {"history": history}
    except Exception as e:
        logger.error(f"Error listing history: {e}")
        return {"history": []}

@app.get("/history/{eval_id}")
async def get_historical_result(eval_id: str):
    """Get full results for a specific historical evaluation."""
    # Validate ID format to prevent traversal (basic check)
    if ".." in eval_id or "/" in eval_id or "\\" in eval_id:
        raise HTTPException(status_code=400, detail="Invalid evaluation ID")
        
    eval_dir = OUTPUTS_DIR / eval_id
    metrics_path = eval_dir / "metrics.json"
    
    if not eval_dir.exists() or not metrics_path.exists():
        raise HTTPException(status_code=404, detail="Evaluation not found")
        
    try:
        with open(metrics_path, "r") as f:
            metrics = json.load(f)
    except Exception as e:
        logger.error(f"Error reading historical metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to parse results")
        
    # List images for this specific run
    images = []
    try:
        for f in sorted(eval_dir.glob("*.png")):
            if f.stat().st_size > 0:
                # Need to mount this specific directory or serve dynamically
                # Ideally, we serve static files from OUTPUTS_DIR and include the subdir in path
                images.append(f"/outputs/eval/{eval_id}/{f.name}")
    except Exception:
        pass
        
    # Calculate sustainability impact
    green_impact = greendc.calculate_impact(
        baseline_power_w=metrics['baseline']['total_power_consumption'],
        scari_power_w=metrics['scari']['total_power_consumption'],
        simulation_steps=metrics['scari'].get('total_steps', 5000)
    )
    
    return {
        "id": eval_id,
        "metrics": metrics,
        "images": images,
        "sustainability": green_impact
    }

@app.delete("/history/{eval_id}")
async def delete_historical_result(eval_id: str):
    """Delete a single historical evaluation run."""
    if ".." in eval_id or "/" in eval_id or "\\" in eval_id:
        raise HTTPException(status_code=400, detail="Invalid evaluation ID")
    
    eval_dir = OUTPUTS_DIR / eval_id
    if not eval_dir.exists() or not eval_dir.is_dir():
        raise HTTPException(status_code=404, detail="Evaluation not found")
    
    try:
        shutil.rmtree(eval_dir)
        logger.info(f"Deleted historical evaluation: {eval_id}")
        return {"message": f"Deleted evaluation {eval_id}"}
    except Exception as e:
        logger.error(f"Failed to delete evaluation {eval_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete: {str(e)}")

def run_eval_task(model_path: Path, steps: int, output_dir: Path):
    global eval_status
    eval_status.is_evaluating = True
    eval_status.error = ""
    eval_status.result = None
    
    # Generate timestamped subdirectory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = output_dir / timestamp
    run_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Starting evaluation task in {run_dir}")
    
    venv_python = get_python_executable()

    cmd = [
        venv_python, "-m", "src.evaluate",
        "--model", str(model_path),
        "--output", str(run_dir),
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
            metrics_path = run_dir / "metrics.json"
            if metrics_path.exists():
                with open(metrics_path, "r") as f:
                    eval_status.result = json.load(f)
                    
                # OPTIONAL: Create/Update 'latest' symlink or copy for backward comp
                # copying explicitly to 'latest' folder or root might be easier on Windows than symlinks
                try:
                    latest_metrics = output_dir / "metrics.json"
                    shutil.copy2(metrics_path, latest_metrics)
                    # Also copy images to root for legacy endpoint if needed, 
                    # but better to rely on new logic. 
                    # For now, let's keep get_results working by copying metrics.json to root
                except Exception as e:
                    logger.warning(f"Failed to update latest metrics link: {e}")

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

# ============================================================================
# DATA CENTER CALCULATOR ENDPOINTS
# ============================================================================

class DataCenterParams(BaseModel):
    """Parameters for datacenter analysis"""
    num_servers: int
    topology: str = "spine_leaf"
    annual_power_kwh: float = 1000000
    baseline_pue: float = 1.67
    optimized_pue: float = 1.1
    region: str = "EU"

    @validator('num_servers')
    def validate_servers(cls, v):
        if v < 1 or v > 100000:
            raise ValueError("num_servers must be between 1 and 100,000")
        return v

    @validator('topology')
    def validate_topology(cls, v):
        valid_topologies = ["fat_tree", "clos", "spine_leaf", "three_tier"]
        if v not in valid_topologies:
            raise ValueError(f"topology must be one of {valid_topologies}")
        return v

    @validator('region')
    def validate_region(cls, v):
        valid_regions = ["EU", "ES", "DE", "US", "ASIA"]
        if v not in valid_regions:
            raise ValueError(f"region must be one of {valid_regions}")
        return v

class ROIParams(BaseModel):
    """Parameters for ROI analysis"""
    num_servers: int
    investment_eur: float
    annual_savings_eur: float

    @validator('investment_eur', 'annual_savings_eur')
    def validate_positive(cls, v):
        if v < 0:
            raise ValueError("Values must be non-negative")
        return v

@app.post("/calculator/embodied-carbon")
async def calculate_embodied_carbon(params: DataCenterParams):
    """
    Calculate embodied carbon emissions from datacenter hardware.
    Includes servers, switches, cooling systems, and infrastructure.
    """
    try:
        result = greendc.calculate_embodied_carbon(
            num_servers=params.num_servers,
            topology=params.topology
        )
        
        logger.info(f"Calculated embodied carbon for {params.num_servers} servers")
        return {
            "status": "success",
            "data": result
        }
    except Exception as e:
        logger.error(f"Embodied carbon calculation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/calculator/network-topology")
async def analyze_network_topology(params: DataCenterParams):
    """
    Analyze network topology requirements and carbon footprint.
    Supports Fat-Tree, Clos, Spine-Leaf, and 3-Tier architectures.
    """
    try:
        result = greendc.calculate_network_topology(
            num_servers=params.num_servers,
            topology=params.topology
        )
        
        logger.info(f"Analyzed {params.topology} topology for {params.num_servers} servers")
        return {
            "status": "success",
            "data": result
        }
    except Exception as e:
        logger.error(f"Network topology analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/calculator/scenario-comparison")
async def compare_scenarios(params: DataCenterParams):
    """
    Compare operational carbon across baseline vs. optimized scenarios.
    Uses region-specific pricing and carbon intensity.
    """
    try:
        calc = GreenDCCalculator(region=params.region)
        result = calc.compare_scenarios(
            num_servers=params.num_servers,
            baseline_pue=params.baseline_pue,
            optimized_pue=params.optimized_pue,
            annual_power_kwh=params.annual_power_kwh
        )
        logger.info(f"Compared scenarios for {params.num_servers} servers [{params.region}]")
        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"Scenario comparison error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/calculator/roi-analysis")
async def analyze_roi(params: ROIParams):
    """
    Financial return on investment analysis.
    Calculates payback period, ROI percentage, and net benefit over 10 years.
    """
    try:
        result = greendc.roi_analysis(
            num_servers=params.num_servers,
            investment_eur=params.investment_eur,
            annual_savings_eur=params.annual_savings_eur
        )
        
        logger.info(f"ROI analysis for {params.num_servers} servers")
        return {
            "status": "success",
            "data": result
        }
    except Exception as e:
        logger.error(f"ROI analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/calculator/comprehensive")
async def comprehensive_analysis(params: DataCenterParams):
    """
    Comprehensive datacenter sustainability analysis.
    Combines operational, embodied, and network topology analysis.
    Uses region-specific energy pricing and carbon intensity.
    """
    try:
        # Region-aware calculator instance for this request
        calc = GreenDCCalculator(region=params.region)

        operational = calc.compare_scenarios(
            num_servers=params.num_servers,
            baseline_pue=params.baseline_pue,
            optimized_pue=params.optimized_pue,
            annual_power_kwh=params.annual_power_kwh
        )

        embodied = calc.calculate_embodied_carbon(
            num_servers=params.num_servers,
            topology=params.topology
        )

        network = calc.calculate_network_topology(
            num_servers=params.num_servers,
            topology=params.topology
        )

        total_carbon = (
            embodied["annual_amortized_co2_kg"] +
            operational["scenario_comparison"]["optimized"]["annual_co2_kg"]
        )

        logger.info(f"Comprehensive analysis: {params.num_servers} servers, {params.topology}, region={params.region}")
        return {
            "status": "success",
            "data": {
                "operational": operational,
                "embodied": embodied,
                "network": network,
                "summary": {
                    "total_annual_carbon_kg": round(total_carbon, 2),
                    "datacenter_size": embodied["datacenter_size"],
                    "network_topology": params.topology,
                    "total_switches": network["total_switches"],
                    "breakeven_years": operational["improvements"].get("breakeven_years"),
                    "region": params.region,
                }
            }
        }
    except Exception as e:
        logger.error(f"Comprehensive analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/calculator/info")
async def calculator_info():
    """
    Get information about available calculators and their capabilities.
    """
    return {
        "version": "2.0.0",
        "calculators": [
            {
                "name": "Embodied Carbon",
                "endpoint": "/calculator/embodied-carbon",
                "description": "Calculate CO2 emissions from hardware manufacturing"
            },
            {
                "name": "Network Topology",
                "endpoint": "/calculator/network-topology",
                "description": "Analyze network architecture and its carbon impact"
            },
            {
                "name": "Scenario Comparison",
                "endpoint": "/calculator/scenario-comparison",
                "description": "Compare baseline vs. optimized operational efficiency"
            },
            {
                "name": "ROI Analysis",
                "endpoint": "/calculator/roi-analysis",
                "description": "Financial return on investment calculations"
            },
            {
                "name": "Comprehensive Analysis",
                "endpoint": "/calculator/comprehensive",
                "description": "Complete datacenter sustainability analysis"
            }
        ],
        "supported_topologies": ["fat_tree", "clos", "spine_leaf", "three_tier"],
        "default_parameters": {
            "electricity_price_eur_kwh": greendc.price,
            "carbon_intensity_kg_kwh": greendc.intensity,
            "region": greendc.region
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
