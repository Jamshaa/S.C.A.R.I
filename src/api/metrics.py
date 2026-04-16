from typing import Any, Dict, Tuple

from src.api.common import BASE_DIR, infer_model_mode, resolve_config_path
from src.utils.config import Config
from src.utils.greendc import GreenDCCalculator


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
    baseline_avg_power = float(summary["baseline_power_w"]) / max(total_steps, 1)
    primary_avg_power = float(summary["primary_power_w"]) / max(total_steps, 1)
    sustainability = calculator.calculate_impact(
        baseline_power_w=baseline_avg_power,
        scari_power_w=primary_avg_power,
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
