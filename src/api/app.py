import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from src.api.common import (
    BASE_DIR,
    CONFIGS_DIR,
    build_region_catalog,
    choose_evaluation_config,
    create_api_logger,
    get_api_key,
    infer_model_mode,
    is_local_client,
    load_cors_origins,
    normalize_model_filename,
    normalize_output_name,
    parse_bool,
    require_admin_access,
    resolve_config_path,
)
from src.api.metrics import (
    build_evaluation_context,
    build_history_summary,
    build_sustainability,
    calculate_efficiency_summary,
    extract_primary_model,
)
from src.api.schemas import DataCenterParams, EvaluationRequest, ROIParams, RenameRequest, TrainingParams
from src.api.state import eval_status, evaluation_lock, greendc, status, training_lock
from src.api.tasks import (
    get_python_executable as resolve_python_executable,
    run_eval_task as run_eval_subprocess,
    run_train_task as run_train_subprocess,
)
from src.utils.model_registry import (
    choose_training_config_path,
    delete_related_model_artifacts,
    get_config_cooling_mode,
    metadata_path_for_model,
    rename_related_model_artifacts,
    shared_vecnormalize_path,
    vecnormalize_path_for_model,
)


logger = create_api_logger()

MODELS_DIR = BASE_DIR / "data" / "models"
OUTPUTS_DIR = BASE_DIR / "outputs" / "eval"

app = FastAPI(title="S.C.A.R.I API", version="2.1.0")

origin_regex = r"^https?://[a-z0-9-]+-\d+\.app\.github\.dev(:\d+)?$"
app.add_middleware(
    CORSMiddleware,
    allow_origins=load_cors_origins(),
    allow_origin_regex=origin_regex,
    allow_credentials=parse_bool(__import__("os").getenv("CORS_ALLOW_CREDENTIALS"), False),
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type", "X-API-Key"],
)

MODELS_DIR.mkdir(parents=True, exist_ok=True)
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/outputs/eval", StaticFiles(directory=str(OUTPUTS_DIR)), name="outputs-eval")


def get_python_executable() -> str:
    return resolve_python_executable(BASE_DIR)


def run_train_task(params: TrainingParams) -> None:
    run_train_subprocess(params, base_dir=BASE_DIR, status=status, logger=logger)


def run_eval_task(models_arg: str, steps: int, output_dir: Path, config_path: str) -> None:
    logger.info("Starting evaluation task in %s", output_dir)
    run_eval_subprocess(
        models_arg,
        steps,
        output_dir,
        config_path,
        base_dir=BASE_DIR,
        eval_status=eval_status,
    )


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
    for destination in (
        metadata_path_for_model(new_path),
        vecnormalize_path_for_model(new_path),
    ):
        if destination.exists():
            raise HTTPException(status_code=400, detail=f"Destination already exists: {destination.name}")
    try:
        old_path.rename(new_path)
        rename_related_model_artifacts(old_path, new_path)
        logger.info("Renamed model %s to %s", old_name, new_name)
        return {"message": f"Renamed {old_name} to {new_name}", "new_name": new_name}
    except OSError as exc:
        logger.error("Rename error: %s", exc)
        raise HTTPException(status_code=500, detail=f"Failed to rename: {exc}") from exc
    except FileExistsError as exc:
        logger.error("Rename related artifacts error: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.delete("/models")
async def delete_all_models(_: None = Depends(require_admin_access)) -> Dict[str, Any]:
    deleted_files: List[str] = []
    try:
        for model_file in MODELS_DIR.glob("*.zip"):
            delete_related_model_artifacts(model_file)
            model_file.unlink()
            deleted_files.append(model_file.name)
        for pattern in ("*.metadata.json", "*_vec_normalize.pkl", "config.json"):
            for extra_file in MODELS_DIR.glob(pattern):
                if extra_file.is_file():
                    extra_file.unlink()
        shared_vec_path = shared_vecnormalize_path(MODELS_DIR)
        if shared_vec_path.exists():
            shared_vec_path.unlink()
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
        delete_related_model_artifacts(model_path)
        model_path.unlink()
        logger.info("Deleted model: %s", safe_name)
        return {"message": f"Deleted {safe_name}"}
    except OSError as exc:
        logger.error("Delete error: %s", exc)
        raise HTTPException(status_code=500, detail=f"Failed to delete: {exc}") from exc


@app.post("/train")
async def start_training(
    params: TrainingParams,
    background_tasks: BackgroundTasks,
    _: None = Depends(require_admin_access),
) -> Dict[str, str]:
    try:
        selected_config = choose_training_config_path(params.config, params.cooling_mode)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not training_lock.acquire(blocking=False):
        raise HTTPException(status_code=429, detail="A training process is already running. Please wait.")

    resolved_params = params.model_copy(
        update={
            "config": str(selected_config),
            "cooling_mode": get_config_cooling_mode(selected_config),
        }
    )

    def run_train_with_lock(training_params: TrainingParams) -> None:
        try:
            run_train_task(training_params)
        finally:
            training_lock.release()

    background_tasks.add_task(run_train_with_lock, resolved_params)
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
    selected_config = choose_evaluation_config(params.config, models_to_test)

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
    calc = greendc.__class__(region=params.region)
    result = calc.compare_scenarios(
        num_servers=params.num_servers,
        baseline_pue=params.baseline_pue,
        optimized_pue=params.optimized_pue,
        annual_power_kwh=params.annual_power_kwh,
    )
    return {"status": "success", "data": result}


@app.post("/calculator/roi-analysis")
async def analyze_roi(params: ROIParams) -> Dict[str, Any]:
    calc = greendc.__class__(region=params.region)
    result = calc.roi_analysis(
        num_servers=params.num_servers,
        investment_eur=params.investment_eur,
        annual_savings_eur=params.annual_savings_eur,
    )
    return {"status": "success", "data": result}


@app.post("/calculator/comprehensive")
async def comprehensive_analysis(params: DataCenterParams) -> Dict[str, Any]:
    calc = greendc.__class__(region=params.region)
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
