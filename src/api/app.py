import json
import logging
import os
import re
import secrets
import shutil
import subprocess
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from fastapi import BackgroundTasks, Depends, FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, field_validator

from src.utils.config import Config
from src.utils.greendc import GreenDCCalculator


BASE_DIR = Path(__file__).resolve().parent.parent.parent
CONFIGS_DIR = (BASE_DIR / "configs").resolve()
MODELS_DIR = BASE_DIR / "data" / "models"
OUTPUTS_DIR = BASE_DIR / "outputs" / "eval"

LOCAL_CLIENT_HOSTS = {"127.0.0.1", "::1", "localhost", "testclient"}
MODEL_NAME_PATTERN = re.compile(r"[^A-Za-z0-9._ -]+")


def parse_bool(value: Optional[str], default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def load_cors_origins() -> List[str]:
    raw = os.getenv("CORS_ORIGINS", "").strip()
    if not raw:
        return [
            "http://localhost",
            "http://127.0.0.1",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:3000",
        ]
    try:
        if raw.startswith("["):
            origins = json.loads(raw)
        else:
            origins = [item.strip() for item in raw.split(",")]
    except json.JSONDecodeError:
        origins = [item.strip() for item in raw.split(",")]
    return [origin.rstrip("/") for origin in origins if origin]


def is_local_client(host: str) -> bool:
    return host in LOCAL_CLIENT_HOSTS or host.startswith("127.")


def normalize_output_name(value: str) -> str:
    cleaned = MODEL_NAME_PATTERN.sub("", (value or "").strip()).replace(" ", "_")
    cleaned = cleaned.strip("._-")
    if not cleaned:
        raise ValueError("name must contain letters or numbers")
    return cleaned[:80]


def normalize_model_filename(value: str) -> str:
    cleaned = MODEL_NAME_PATTERN.sub("", os.path.basename((value or "").strip())).replace(" ", "_")
    cleaned = cleaned.strip("._-")
    if not cleaned:
        raise ValueError("model name must contain letters or numbers")
    if not cleaned.endswith(".zip"):
        cleaned = f"{cleaned}.zip"
    return cleaned[:100]


def resolve_config_path(value: str) -> Path:
    candidate = Path(value)
    if not candidate.is_absolute():
        candidate = (BASE_DIR / candidate).resolve()
    else:
        candidate = candidate.resolve()
    if not candidate.is_relative_to(CONFIGS_DIR):
        raise ValueError("config must point to a file inside configs/")
    if candidate.suffix.lower() not in {".yaml", ".yml"}:
        raise ValueError("config must be a YAML file")
    if not candidate.exists():
        raise ValueError("config file not found")
    return candidate


MODE_TO_CONFIG = {
    "AIR": "configs/default.yaml",
    "LIQUID": "configs/liquid.yaml",
    "HYBRID": "configs/hybrid.yaml",
}

CURRENCY_SYMBOLS = {
    "EUR": "€",
    "GBP": "£",
    "USD": "$",
}

REGION_LABELS = {
    "EU": "Europe",
    "ES": "Spain",
    "DE": "Germany",
    "UK": "United Kingdom",
    "FR": "France",
    "NO": "Norway",
    "US": "United States",
    "BR": "Brazil",
    "CA": "Canada",
    "IN": "India",
    "ASIA": "Asia-Pacific",
}


def infer_model_mode(model_name: str) -> Optional[str]:
    normalized = Path(model_name).stem.lower()
    if any(token in normalized for token in ("liquid", "water", "hydro")):
        return "LIQUID"
    if "hybrid" in normalized:
        return "HYBRID"
    if "air" in normalized:
        return "AIR"
    return None


def choose_evaluation_config(requested_config: str, model_names: List[str]) -> str:
    resolved_requested = resolve_config_path(requested_config)
    default_config = resolve_config_path(MODE_TO_CONFIG["AIR"])
    if resolved_requested != default_config:
        return str(resolved_requested)

    inferred_modes = {
        infer_model_mode(model_name)
        for model_name in model_names
        if infer_model_mode(model_name) is not None
    }
    if len(inferred_modes) != 1:
        return str(resolved_requested)

    inferred_mode = inferred_modes.pop()
    inferred_config = resolve_config_path(MODE_TO_CONFIG[inferred_mode])
    logger.info("Auto-selected evaluation config %s for model(s): %s", inferred_config.name, ", ".join(model_names))
    return str(inferred_config)


def build_region_catalog() -> List[Dict[str, Any]]:
    regions: List[Dict[str, Any]] = []
    for code in sorted(GreenDCCalculator.REGION_DATA.keys()):
        region_data = GreenDCCalculator.REGION_DATA[code]
        currency_code = region_data["currency"]
        regions.append(
            {
                "code": code,
                "label": REGION_LABELS.get(code, code),
                "price_per_kwh": region_data["price"],
                "carbon_intensity_kg_kwh": region_data["intensity"],
                "currency_code": currency_code,
                "currency_symbol": {"EUR": "€", "GBP": "£", "USD": "$"}.get(
                    currency_code,
                    CURRENCY_SYMBOLS.get(currency_code, currency_code),
                ),
            }
        )
    return regions


def get_api_key() -> str:
    return os.getenv("SCARI_API_KEY", "").strip()


async def require_admin_access(
    request: Request,
    x_api_key: Optional[str] = Header(default=None, alias="X-API-Key"),
) -> None:
    configured_key = get_api_key()
    client_host = request.client.host if request.client else ""
    if configured_key:
        if not x_api_key or not secrets.compare_digest(x_api_key, configured_key):
            raise HTTPException(status_code=401, detail="Invalid or missing X-API-Key")
        return
    if not is_local_client(client_host):
        raise HTTPException(
            status_code=403,
            detail="Protected endpoints are local-only unless SCARI_API_KEY is configured",
        )


def extract_primary_model(metrics: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    models = metrics.get("models")
    if isinstance(models, dict) and models:
        name, data = min(
            models.items(),
            key=lambda item: item[1].get("total_power_consumption", float("inf")),
        )
        return name, data
    scari = metrics.get("scari")
    if isinstance(scari, dict):
        return "SCARI", scari
    return "baseline", metrics.get("baseline", {})


def calculate_efficiency_summary(baseline: Dict[str, Any], primary: Dict[str, Any]) -> Dict[str, float | str]:
    baseline_power = max(0.0, float(baseline.get("total_power_consumption", 0.0)))
    primary_power = max(0.0, float(primary.get("total_power_consumption", baseline_power)))

    has_it_data = (
        "total_it_power_consumption" in baseline
        or "total_it_power_consumption" in primary
    )
    baseline_it = max(0.0, float(baseline.get("total_it_power_consumption", 0.0)))
    primary_it = max(0.0, float(primary.get("total_it_power_consumption", 0.0)))
    baseline_overhead = max(0.0, baseline_power - baseline_it) if has_it_data else 0.0
    primary_overhead = max(0.0, primary_power - primary_it) if has_it_data else 0.0

    baseline_cooling = max(0.0, float(baseline.get("total_cooling_power_consumption", baseline_overhead)))
    primary_cooling = max(0.0, float(primary.get("total_cooling_power_consumption", primary_overhead)))

    total_power_savings = (
        (baseline_power - primary_power) / baseline_power * 100 if baseline_power > 0 else 0.0
    )
    non_it_overhead_savings = (
        (baseline_overhead - primary_overhead) / baseline_overhead * 100 if baseline_overhead > 0 else total_power_savings
    )
    cooling_savings = (
        (baseline_cooling - primary_cooling) / baseline_cooling * 100 if baseline_cooling > 0 else non_it_overhead_savings
    )

    baseline_pue = max(0.0, float(baseline.get("average_pue", 0.0)))
    optimized_pue = max(0.0, float(primary.get("average_pue", baseline_pue)))
    pue_improvement = (
        (baseline_pue - optimized_pue) / baseline_pue * 100 if baseline_pue > 0 else 0.0
    )
    baseline_pue_overhead = max(0.0, baseline_pue - 1.0)
    optimized_pue_overhead = max(0.0, optimized_pue - 1.0)
    pue_overhead_reduction = (
        (baseline_pue_overhead - optimized_pue_overhead) / baseline_pue_overhead * 100
        if baseline_pue_overhead > 1e-6
        else pue_improvement
    )

    return {
        "baseline_power_w": baseline_power,
        "primary_power_w": primary_power,
        "baseline_overhead_power_w": baseline_overhead,
        "primary_overhead_power_w": primary_overhead,
        "baseline_cooling_power_w": baseline_cooling,
        "primary_cooling_power_w": primary_cooling,
        "total_power_savings_percent": total_power_savings,
        "non_it_overhead_savings_percent": non_it_overhead_savings,
        "cooling_savings_percent": cooling_savings,
        "optimization_savings_percent": non_it_overhead_savings,
        "savings_basis": "non_it_overhead" if has_it_data and baseline_overhead > 0 else "total_power",
        "baseline_pue": baseline_pue,
        "optimized_pue": optimized_pue,
        "pue_improvement_percent": pue_improvement,
        "pue_overhead_reduction_percent": pue_overhead_reduction,
    }


def build_history_summary(entry_name: str, metrics: Dict[str, Any]) -> Dict[str, Any]:
    baseline = metrics.get("baseline", {})
    model_name, primary = extract_primary_model(metrics)
    summary = calculate_efficiency_summary(baseline, primary)
    return {
        "id": entry_name,
        "timestamp": entry_name,
        "pue": primary.get("average_pue"),
        "savings": round(float(summary["optimization_savings_percent"]), 2),
        "total_power_savings_percent": round(float(summary["total_power_savings_percent"]), 2),
        "overhead_savings_percent": round(float(summary["non_it_overhead_savings_percent"]), 2),
        "cooling_savings_percent": round(float(summary["cooling_savings_percent"]), 2),
        "savings_basis": summary["savings_basis"],
        "safety_override_rate_percent": round(float(primary.get("safety_override_rate_percent", 0.0)), 2),
        "safety_override_avg_fraction_active": round(float(primary.get("safety_override_avg_fraction_active", 0.0)), 4),
        "steps": int(primary.get("total_steps", 5000)),
        "model": model_name,
    }


def build_sustainability(metrics: Dict[str, Any], calculator: GreenDCCalculator) -> Dict[str, Any]:
    baseline = metrics.get("baseline", {})
    _, primary = extract_primary_model(metrics)
    summary = calculate_efficiency_summary(baseline, primary)
    total_steps = int(primary.get("total_steps", 5000))
    sustainability = calculator.calculate_impact(
        baseline_power_w=float(summary["baseline_power_w"]),
        scari_power_w=float(summary["primary_power_w"]),
        simulation_steps=total_steps,
    )
    if float(summary["baseline_pue"]) > 0:
        sustainability["pue_baseline"] = round(float(summary["baseline_pue"]), 3)
    if float(summary["optimized_pue"]) > 0:
        sustainability["pue_optimized"] = round(float(summary["optimized_pue"]), 3)
    sustainability.update(
        {
            "total_power_savings_percent": round(float(summary["total_power_savings_percent"]), 2),
            "non_it_overhead_savings_percent": round(float(summary["non_it_overhead_savings_percent"]), 2),
            "cooling_savings_percent": round(float(summary["cooling_savings_percent"]), 2),
            "optimization_savings_percent": round(float(summary["optimization_savings_percent"]), 2),
            "optimization_savings_basis": summary["savings_basis"],
            "pue_improvement_percent": round(float(summary["pue_improvement_percent"]), 2),
            "pue_overhead_reduction_percent": round(float(summary["pue_overhead_reduction_percent"]), 2),
        }
    )
    return sustainability


def build_evaluation_context(metrics: Dict[str, Any]) -> Dict[str, Any]:
    baseline = metrics.get("baseline", {})
    model_name, primary = extract_primary_model(metrics)
    metadata = metrics.get("metadata", {})
    raw_config = str(metadata.get("config", "configs/default.yaml"))
    config_label = raw_config
    cooling_mode = infer_model_mode(model_name) or "AIR"
    try:
        resolved_config = resolve_config_path(raw_config)
        config_label = str(resolved_config.relative_to(BASE_DIR)).replace("\\", "/")
        cooling_mode = Config.from_yaml(resolved_config).cooling.mode.upper()
    except Exception:
        pass

    return {
        "model": model_name,
        "config": config_label,
        "cooling_mode": cooling_mode,
        "baseline": str(metadata.get("baseline_controller", baseline.get("controller_name", "BASELINE"))),
        "seed": metadata.get("seed"),
        "steps": int(primary.get("total_steps", baseline.get("total_steps", 0) or 0)),
    }


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "time": self.formatTime(record),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
        }
        return json.dumps(log_obj)


logger = logging.getLogger("SCARI_API")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    logger.addHandler(handler)
logger.setLevel(logging.INFO)
logger.propagate = False

app = FastAPI(title="S.C.A.R.I API", version="2.1.0")

origin_regex = r"^https?://[a-z0-9-]+-\d+\.app\.github\.dev(:\d+)?$"
app.add_middleware(
    CORSMiddleware,
    allow_origins=load_cors_origins(),
    allow_origin_regex=origin_regex,
    allow_credentials=parse_bool(os.getenv("CORS_ALLOW_CREDENTIALS"), False),
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type", "X-API-Key"],
)

MODELS_DIR.mkdir(parents=True, exist_ok=True)
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/outputs/eval", StaticFiles(directory=str(OUTPUTS_DIR)), name="outputs-eval")


def get_python_executable() -> str:
    for candidate in [
        BASE_DIR / ".venv" / "Scripts" / "python.exe",
        BASE_DIR / "venv" / "Scripts" / "python.exe",
        BASE_DIR / ".venv" / "bin" / "python",
        BASE_DIR / "venv" / "bin" / "python",
    ]:
        if candidate.exists():
            return str(candidate)
    return "python"


class TrainingParams(BaseModel):
    timesteps: int = 10000
    config: str = "configs/default.yaml"
    name: str = "scari_model"
    cooling_mode: str = "AIR"

    @field_validator("timesteps")
    @classmethod
    def validate_timesteps(cls, value: int) -> int:
        if value < 1000 or value > 10000000:
            raise ValueError("timesteps must be between 1,000 and 10,000,000")
        return value

    @field_validator("config")
    @classmethod
    def validate_config(cls, value: str) -> str:
        return str(resolve_config_path(value))

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        return normalize_output_name(value)

    @field_validator("cooling_mode")
    @classmethod
    def validate_cooling_mode(cls, value: str) -> str:
        valid = {"AIR", "LIQUID", "HYBRID"}
        normalized = value.upper()
        if normalized not in valid:
            raise ValueError(f"cooling_mode must be one of {sorted(valid)}")
        return normalized


class RenameRequest(BaseModel):
    old_name: str
    new_name: str

    @field_validator("new_name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        return normalize_model_filename(value)


class EvaluationRequest(BaseModel):
    model: str = "default_model.zip"
    models: Optional[List[str]] = None
    steps: int = 5000
    name: Optional[str] = None
    config: str = "configs/default.yaml"

    @field_validator("steps")
    @classmethod
    def validate_steps(cls, value: int) -> int:
        if value < 100 or value > 100000:
            raise ValueError("steps must be between 100 and 100,000")
        return value

    @field_validator("config")
    @classmethod
    def validate_config(cls, value: str) -> str:
        return str(resolve_config_path(value))


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
greendc = GreenDCCalculator()
training_lock = threading.Lock()
evaluation_lock = threading.Lock()


@app.get("/")
async def root() -> Dict[str, Any]:
    return {
        "name": "S.C.A.R.I API",
        "version": "2.1.0",
        "status": "online",
        "endpoints": [
            "/models",
            "/status",
            "/evaluation-results",
            "/outputs/eval",
            "/health",
        ],
    }


@app.get("/health")
async def health_check() -> Dict[str, Any]:
    import torch

    evaluation_dirs = [d for d in OUTPUTS_DIR.iterdir() if d.is_dir() and (d / "metrics.json").exists()]
    return {
        "status": "operating",
        "compute": {
            "device": "cuda" if torch.cuda.is_available() else "cpu",
            "torch_version": torch.__version__,
        },
        "storage": {
            "models_count": len(list(MODELS_DIR.glob("*.zip"))),
            "evaluations_count": len(evaluation_dirs),
        },
    }


@app.get("/models")
async def get_models() -> Dict[str, List[str]]:
    models = [f.name for f in MODELS_DIR.glob("*.zip") if f.is_file() and not f.name.startswith(".")]
    return {"models": sorted(models)}


@app.post("/models/rename")
async def rename_model(
    request: RenameRequest,
    _: None = Depends(require_admin_access),
) -> Dict[str, str]:
    old_name = normalize_model_filename(request.old_name)
    new_name = normalize_model_filename(request.new_name)
    old_path = MODELS_DIR / old_name
    new_path = MODELS_DIR / new_name
    if not old_path.exists():
        raise HTTPException(status_code=404, detail="Model not found")
    if new_path.exists():
        raise HTTPException(status_code=400, detail="New name already exists")
    try:
        old_path.rename(new_path)
        logger.info("Renamed model %s to %s", old_name, new_name)
        return {"message": f"Renamed {old_name} to {new_name}", "new_name": new_name}
    except OSError as exc:
        logger.error("Rename error: %s", exc)
        raise HTTPException(status_code=500, detail=f"Failed to rename: {exc}") from exc


@app.delete("/models")
async def delete_all_models(_: None = Depends(require_admin_access)) -> Dict[str, Any]:
    deleted_files: List[str] = []
    try:
        for model_file in MODELS_DIR.glob("*.zip"):
            model_file.unlink()
            deleted_files.append(model_file.name)
        logger.info("Deleted all models (%s files)", len(deleted_files))
        return {"message": f"Deleted {len(deleted_files)} models", "deleted": deleted_files}
    except OSError as exc:
        logger.error("Delete all error: %s", exc)
        raise HTTPException(status_code=500, detail=f"Failed to delete all: {exc}") from exc


@app.delete("/models/{model_name}")
async def delete_model(
    model_name: str,
    _: None = Depends(require_admin_access),
) -> Dict[str, str]:
    safe_name = normalize_model_filename(model_name)
    model_path = MODELS_DIR / safe_name
    if not model_path.exists():
        raise HTTPException(status_code=404, detail="Model not found")
    try:
        model_path.unlink()
        logger.info("Deleted model: %s", safe_name)
        return {"message": f"Deleted {safe_name}"}
    except OSError as exc:
        logger.error("Delete error: %s", exc)
        raise HTTPException(status_code=500, detail=f"Failed to delete: {exc}") from exc


def run_train_task(params: TrainingParams) -> None:
    global status
    status.is_training = True
    status.progress = 0
    status.current_step = 0
    status.total_steps = params.timesteps
    logger.info("Starting training task: %s for %s steps", params.name, params.timesteps)
    try:
        cmd = [
            get_python_executable(),
            "-m",
            "src.train",
            "--timesteps",
            str(params.timesteps),
            "--config",
            params.config,
            "--output-name",
            params.name,
            "--cooling-mode",
            params.cooling_mode,
        ]
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONUNBUFFERED"] = "1"
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            cwd=str(BASE_DIR),
            env=env,
            bufsize=1,
        )

        import queue

        def reader(pipe: Any, output_queue: "queue.Queue[Optional[str]]") -> None:
            try:
                with pipe:
                    for line in iter(pipe.readline, ""):
                        output_queue.put(line)
            finally:
                output_queue.put(None)

        output_queue: "queue.Queue[Optional[str]]" = queue.Queue()
        thread = threading.Thread(target=reader, args=(process.stdout, output_queue), daemon=True)
        thread.start()

        while True:
            try:
                line = output_queue.get(timeout=1)
            except queue.Empty:
                if process.poll() is not None:
                    break
                continue
            if line is None:
                break
            status.last_log = line.strip()
            if "Training complete" in line:
                status.progress = 100
            if "total_timesteps" in line:
                try:
                    parts = [part.strip() for part in line.split("|") if part.strip()]
                    step_value = next((int(part) for part in parts if part.isdigit()), None)
                    if step_value is not None:
                        status.current_step = step_value
                        status.progress = min(99, int(step_value / params.timesteps * 100))
                except ValueError:
                    logger.debug("Could not parse training progress from log line: %s", line.strip())
        process.wait()
        if process.returncode == 0:
            status.progress = 100
            status.last_log = "Training completed successfully."
        else:
            status.last_log = f"Training failed with exit code {process.returncode}"
    except Exception as exc:
        status.last_log = f"Error: {exc}"
        logger.error("Training crashed: %s", exc)
    finally:
        status.is_training = False


@app.post("/train")
async def start_training(
    params: TrainingParams,
    background_tasks: BackgroundTasks,
    _: None = Depends(require_admin_access),
) -> Dict[str, str]:
    if not training_lock.acquire(blocking=False):
        raise HTTPException(status_code=429, detail="A training process is already running. Please wait.")

    def run_train_with_lock(training_params: TrainingParams) -> None:
        try:
            run_train_task(training_params)
        finally:
            training_lock.release()

    background_tasks.add_task(run_train_with_lock, params)
    return {"message": "Training started"}


@app.get("/status")
async def get_status() -> Dict[str, Any]:
    return {
        "is_training": status.is_training,
        "last_log": status.last_log,
        "progress": status.progress,
    }


@app.get("/history")
async def get_history() -> Dict[str, List[Dict[str, Any]]]:
    history: List[Dict[str, Any]] = []
    try:
        for entry in sorted(OUTPUTS_DIR.iterdir(), key=lambda path: path.stat().st_mtime, reverse=True):
            metrics_path = entry / "metrics.json"
            if not entry.is_dir() or not metrics_path.exists():
                continue
            try:
                with metrics_path.open("r", encoding="utf-8") as handle:
                    metrics = json.load(handle)
                history.append(build_history_summary(entry.name, metrics))
            except Exception as exc:
                logger.warning("Failed to parse history entry %s: %s", entry.name, exc)
        return {"history": history}
    except OSError as exc:
        logger.error("Error listing history: %s", exc)
        return {"history": []}


@app.get("/history/{eval_id}")
async def get_historical_result(eval_id: str) -> Dict[str, Any]:
    eval_dir = (OUTPUTS_DIR / eval_id).resolve()
    if not eval_dir.is_relative_to(OUTPUTS_DIR.resolve()):
        raise HTTPException(status_code=400, detail="Path traversal attempt detected")
    metrics_path = eval_dir / "metrics.json"
    if not eval_dir.exists() or not metrics_path.exists():
        raise HTTPException(status_code=404, detail="Evaluation not found")
    try:
        with metrics_path.open("r", encoding="utf-8") as handle:
            metrics = json.load(handle)
    except Exception as exc:
        logger.error("Error reading historical metrics: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to parse results") from exc

    images = [
        f"/outputs/eval/{eval_id}/{image.name}"
        for image in sorted(eval_dir.glob("*.png"))
        if image.stat().st_size > 0
    ]
    return {
        "id": eval_id,
        "metrics": metrics,
        "images": images,
        "context": build_evaluation_context(metrics),
        "downloads": {
            "metrics_json": f"/outputs/eval/{eval_id}/metrics.json",
            "charts": images,
        },
        "sustainability": build_sustainability(metrics, greendc),
    }


@app.delete("/history/{eval_id}")
async def delete_historical_result(
    eval_id: str,
    _: None = Depends(require_admin_access),
) -> Dict[str, str]:
    eval_dir = (OUTPUTS_DIR / eval_id).resolve()
    if not eval_dir.is_relative_to(OUTPUTS_DIR.resolve()):
        raise HTTPException(status_code=400, detail="Path traversal attempt detected")
    if not eval_dir.exists() or not eval_dir.is_dir():
        raise HTTPException(status_code=404, detail="Evaluation not found")
    try:
        shutil.rmtree(eval_dir)
        logger.info("Deleted historical evaluation: %s", eval_id)
        return {"message": f"Deleted evaluation {eval_id}"}
    except OSError as exc:
        logger.error("Failed to delete evaluation %s: %s", eval_id, exc)
        raise HTTPException(status_code=500, detail=f"Failed to delete: {exc}") from exc


def run_eval_task(models_arg: str, steps: int, output_dir: Path, config_path: str) -> None:
    global eval_status
    eval_status.is_evaluating = True
    eval_status.error = ""
    eval_status.result = None
    logger.info("Starting evaluation task in %s", output_dir)
    cmd = [
        get_python_executable(),
        "-m",
        "src.evaluate",
        "--config",
        config_path,
        "--models",
        models_arg,
        "--output",
        str(output_dir),
        "--steps",
        str(steps),
    ]
    try:
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            cwd=str(BASE_DIR),
            env=env,
        )
        if process.stdout is not None:
            for line in process.stdout:
                eval_status.last_log = line.strip()
        process.wait()
        if process.returncode == 0:
            metrics_path = output_dir / "metrics.json"
            if metrics_path.exists():
                with metrics_path.open("r", encoding="utf-8") as handle:
                    eval_status.result = json.load(handle)
        else:
            eval_status.error = f"Evaluation process exited with code {process.returncode}"
    except Exception as exc:
        eval_status.error = str(exc)
    finally:
        eval_status.is_evaluating = False


@app.post("/evaluate")
async def run_evaluation(
    params: EvaluationRequest,
    background_tasks: BackgroundTasks,
    _: None = Depends(require_admin_access),
) -> Dict[str, str]:
    models_to_test: List[str] = []
    if params.models:
        for model_name in params.models:
            model_path = MODELS_DIR / normalize_model_filename(model_name)
            if not model_path.exists():
                raise HTTPException(status_code=404, detail=f"Model not found: {model_name}")
            models_to_test.append(str(model_path))
    elif params.model.upper() == "MULTI":
        for mode in ["AIR", "LIQUID", "HYBRID"]:
            model_path = MODELS_DIR / f"{mode}_model.zip"
            if model_path.exists():
                models_to_test.append(str(model_path))
        if not models_to_test:
            models_to_test = [str(path) for path in MODELS_DIR.glob("*.zip") if path.is_file()][:3]
        if not models_to_test:
            raise HTTPException(status_code=404, detail="No trained models found for comparison")
    else:
        model_path = MODELS_DIR / normalize_model_filename(params.model)
        if not model_path.exists():
            raise HTTPException(status_code=404, detail="Model not found")
        models_to_test.append(str(model_path))

    if not evaluation_lock.acquire(blocking=False):
        raise HTTPException(status_code=429, detail="An evaluation process is already running. Please wait.")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    clean_name = normalize_output_name(params.name) if params.name else "eval"
    run_dir = OUTPUTS_DIR / f"{clean_name}_{timestamp}"
    run_dir.mkdir(parents=True, exist_ok=True)
    models_arg = ",".join(models_to_test)
    selected_config = choose_evaluation_config(params.config, [Path(model_path).name for model_path in models_to_test])

    def run_eval_with_lock(selected_models: str, selected_steps: int, destination: Path, config_path: str) -> None:
        try:
            run_eval_task(selected_models, selected_steps, destination, config_path)
        finally:
            evaluation_lock.release()

    background_tasks.add_task(run_eval_with_lock, models_arg, params.steps, run_dir, selected_config)
    return {"message": "Evaluation started", "run_name": run_dir.name}


@app.get("/evaluation-status")
async def get_evaluation_status() -> Dict[str, Any]:
    return {
        "is_evaluating": eval_status.is_evaluating,
        "last_log": eval_status.last_log,
        "error": eval_status.error,
        "has_result": eval_status.result is not None,
    }


@app.get("/evaluation-results")
async def get_results() -> Dict[str, Any]:
    run_dirs = [directory for directory in OUTPUTS_DIR.iterdir() if directory.is_dir() and (directory / "metrics.json").exists()]
    if not run_dirs:
        return {"error": "No results available. Please run an evaluation first."}
    latest_dir = max(run_dirs, key=lambda directory: directory.stat().st_mtime)
    metrics_path = latest_dir / "metrics.json"
    try:
        with metrics_path.open("r", encoding="utf-8") as handle:
            metrics = json.load(handle)
    except Exception as exc:
        logger.error("Error reading metrics.json: %s", exc)
        return {"error": "Failed to parse evaluation results."}
    images = [
        f"/outputs/eval/{latest_dir.name}/{image.name}"
        for image in sorted(latest_dir.glob("*.png"))
        if image.stat().st_size > 0
    ]
    return {
        "metrics": metrics,
        "images": images,
        "context": build_evaluation_context(metrics),
        "downloads": {
            "metrics_json": f"/outputs/eval/{latest_dir.name}/metrics.json",
            "charts": images,
        },
        "sustainability": build_sustainability(metrics, greendc),
    }


@app.get("/explain")
async def get_explanations() -> Dict[str, Any]:
    from src.api.sample_decisions import SAMPLE_DECISIONS

    return {"decisions": SAMPLE_DECISIONS}


class DataCenterParams(BaseModel):
    num_servers: int
    topology: str = "spine_leaf"
    annual_power_kwh: float = 1000000
    baseline_pue: float = 1.67
    optimized_pue: float = 1.1
    region: str = "EU"

    @field_validator("num_servers")
    @classmethod
    def validate_servers(cls, value: int) -> int:
        if value < 1 or value > 100000:
            raise ValueError("num_servers must be between 1 and 100,000")
        return value

    @field_validator("topology")
    @classmethod
    def validate_topology(cls, value: str) -> str:
        valid_topologies = {"fat_tree", "clos", "spine_leaf", "three_tier"}
        if value not in valid_topologies:
            raise ValueError(f"topology must be one of {sorted(valid_topologies)}")
        return value

    @field_validator("region")
    @classmethod
    def validate_region(cls, value: str) -> str:
        valid_regions = set(GreenDCCalculator.REGION_DATA.keys())
        if value not in valid_regions:
            raise ValueError(f"region must be one of {sorted(valid_regions)}")
        return value


class ROIParams(BaseModel):
    num_servers: int
    investment_eur: float
    annual_savings_eur: float
    region: str = "EU"

    @field_validator("investment_eur", "annual_savings_eur")
    @classmethod
    def validate_positive(cls, value: float) -> float:
        if value < 0:
            raise ValueError("Values must be non-negative")
        return value

    @field_validator("region")
    @classmethod
    def validate_region(cls, value: str) -> str:
        valid_regions = set(GreenDCCalculator.REGION_DATA.keys())
        if value not in valid_regions:
            raise ValueError(f"region must be one of {sorted(valid_regions)}")
        return value


@app.post("/calculator/embodied-carbon")
async def calculate_embodied_carbon(params: DataCenterParams) -> Dict[str, Any]:
    result = greendc.calculate_embodied_carbon(num_servers=params.num_servers, topology=params.topology)
    return {"status": "success", "data": result}


@app.post("/calculator/network-topology")
async def analyze_network_topology(params: DataCenterParams) -> Dict[str, Any]:
    result = greendc.calculate_network_topology(num_servers=params.num_servers, topology=params.topology)
    return {"status": "success", "data": result}


@app.post("/calculator/scenario-comparison")
async def compare_scenarios(params: DataCenterParams) -> Dict[str, Any]:
    calc = GreenDCCalculator(region=params.region)
    result = calc.compare_scenarios(
        num_servers=params.num_servers,
        baseline_pue=params.baseline_pue,
        optimized_pue=params.optimized_pue,
        annual_power_kwh=params.annual_power_kwh,
    )
    return {"status": "success", "data": result}


@app.post("/calculator/roi-analysis")
async def analyze_roi(params: ROIParams) -> Dict[str, Any]:
    calc = GreenDCCalculator(region=params.region)
    result = calc.roi_analysis(
        num_servers=params.num_servers,
        investment_eur=params.investment_eur,
        annual_savings_eur=params.annual_savings_eur,
    )
    return {"status": "success", "data": result}


@app.post("/calculator/comprehensive")
async def comprehensive_analysis(params: DataCenterParams) -> Dict[str, Any]:
    calc = GreenDCCalculator(region=params.region)
    operational = calc.compare_scenarios(
        num_servers=params.num_servers,
        baseline_pue=params.baseline_pue,
        optimized_pue=params.optimized_pue,
        annual_power_kwh=params.annual_power_kwh,
    )
    embodied = calc.calculate_embodied_carbon(num_servers=params.num_servers, topology=params.topology)
    network = calc.calculate_network_topology(num_servers=params.num_servers, topology=params.topology)
    total_carbon = embodied["annual_amortized_co2_kg"] + operational["scenario_comparison"]["optimized"]["annual_co2_kg"]
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
            },
        },
    }


@app.get("/calculator/info")
async def calculator_info() -> Dict[str, Any]:
    regions = build_region_catalog()
    return {
        "version": "2.1.0",
        "calculators": [
            {
                "name": "Embodied Carbon",
                "endpoint": "/calculator/embodied-carbon",
                "description": "Calculate CO2 emissions from hardware manufacturing",
            },
            {
                "name": "Network Topology",
                "endpoint": "/calculator/network-topology",
                "description": "Analyze network architecture and its carbon impact",
            },
            {
                "name": "Scenario Comparison",
                "endpoint": "/calculator/scenario-comparison",
                "description": "Compare baseline vs. optimized operational efficiency",
            },
            {
                "name": "ROI Analysis",
                "endpoint": "/calculator/roi-analysis",
                "description": "Financial return on investment calculations",
            },
            {
                "name": "Comprehensive Analysis",
                "endpoint": "/calculator/comprehensive",
                "description": "Complete datacenter sustainability analysis",
            },
        ],
        "supported_topologies": ["fat_tree", "clos", "spine_leaf", "three_tier"],
        "supported_regions": [region["code"] for region in regions],
        "regions": regions,
        "default_parameters": {
            "electricity_price_eur_kwh": greendc.price,
            "carbon_intensity_kg_kwh": greendc.intensity,
            "region": greendc.region,
        },
    }


@app.get("/cooling-modes")
async def get_cooling_modes() -> Dict[str, Any]:
    from src.utils.config import COOLING_COST_DB

    modes = []
    for mode_key, mode_data in COOLING_COST_DB.items():
        modes.append(
            {
                "id": mode_key,
                "label": mode_data["label"],
                "description": mode_data["description"],
                "capex_per_server_eur": mode_data["capex_per_server_eur"],
                "opex_per_server_year_eur": mode_data["opex_per_server_year_eur"],
                "typical_pue": mode_data["typical_pue"],
                "max_density_kw_per_rack": mode_data["max_density_kw_per_rack"],
            }
        )
    return {"modes": modes}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
