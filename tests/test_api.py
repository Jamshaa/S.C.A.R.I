import asyncio
import json
import shutil
import uuid
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

import src.api.app as api_app
from src.utils.greendc import GreenDCCalculator


client = TestClient(api_app.app)


def make_request(host: str):
    return SimpleNamespace(client=SimpleNamespace(host=host))


def make_workspace_tmp(prefix: str) -> Path:
    tmp_dir = Path("tmp") / f"{prefix}_{uuid.uuid4().hex}"
    tmp_dir.mkdir(parents=True, exist_ok=False)
    return tmp_dir


def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "online"


def test_get_models():
    response = client.get("/models")
    assert response.status_code == 200
    assert "models" in response.json()


def test_normalize_output_name_blocks_path_traversal():
    assert api_app.normalize_output_name("../evil model") == "evil_model"


def test_normalize_model_filename_appends_zip():
    assert api_app.normalize_model_filename("../unsafe model") == "unsafe_model.zip"


def test_resolve_config_path_rejects_files_outside_configs():
    with pytest.raises(ValueError, match="inside configs"):
        api_app.resolve_config_path("README.md")


def test_build_history_summary_supports_current_metrics_shape():
    metrics = {
        "baseline": {"total_power_consumption": 1000.0},
        "models": {
            "scari_safe": {
                "total_power_consumption": 800.0,
                "average_pue": 1.18,
                "total_steps": 1500,
            }
        },
    }
    summary = api_app.build_history_summary("eval_001", metrics)
    assert summary == {
        "id": "eval_001",
        "timestamp": "eval_001",
        "pue": 1.18,
        "savings": 20.0,
        "total_power_savings_percent": 20.0,
        "overhead_savings_percent": 20.0,
        "cooling_savings_percent": 20.0,
        "savings_basis": "total_power",
        "safety_override_rate_percent": 0.0,
        "safety_override_avg_fraction_active": 0.0,
        "steps": 1500,
        "model": "scari_safe",
    }


def test_evaluation_request_defaults_to_default_config():
    params = api_app.EvaluationRequest(model="example.zip")
    assert params.config.endswith("default.yaml")


def test_choose_evaluation_config_infers_liquid_profile_from_model_name():
    selected = api_app.choose_evaluation_config("configs/default.yaml", ["scari_water_model.zip"])
    assert selected.endswith("liquid.yaml")


def test_choose_evaluation_config_infers_hybrid_profile_from_model_name():
    selected = api_app.choose_evaluation_config("configs/default.yaml", ["scari_hybrid_model.zip"])
    assert selected.endswith("hybrid.yaml")


def test_choose_evaluation_config_preserves_explicit_config_choice():
    selected = api_app.choose_evaluation_config("configs/liquid.yaml", ["scari_air_model.zip"])
    assert selected.endswith("liquid.yaml")


def test_choose_evaluation_config_keeps_default_for_mixed_mode_comparison():
    selected = api_app.choose_evaluation_config(
        "configs/default.yaml",
        ["scari_air_model.zip", "scari_water_model.zip"],
    )
    assert selected.endswith("default.yaml")


def test_calculator_info_exposes_region_catalog():
    response = client.get("/calculator/info")
    assert response.status_code == 200
    payload = response.json()
    assert "regions" in payload
    assert any(region["code"] == "ES" for region in payload["regions"])
    assert any(region["currency_symbol"] == "€" for region in payload["regions"])


def test_roi_analysis_uses_requested_region():
    response = client.post(
        "/calculator/roi-analysis",
        json={
            "num_servers": 100,
            "investment_eur": 1000,
            "annual_savings_eur": 120,
            "region": "UK",
        },
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["annual_carbon_avoided_kg"] == 80.0
    assert data["payback_period_years"] == pytest.approx(8.3)


def test_build_sustainability_supports_current_metrics_shape():
    metrics = {
        "baseline": {"total_power_consumption": 3_600_000.0},
        "models": {
            "scari_safe": {
                "total_power_consumption": 2_880_000.0,
                "average_pue": 1.18,
                "total_steps": 3600,
            }
        },
    }
    sustainability = api_app.build_sustainability(metrics, GreenDCCalculator(region="ES"))
    assert sustainability["energy_savings_percent"] == 20.0
    assert sustainability["optimization_savings_percent"] == 20.0
    assert sustainability["energy_saved_kwh_sim"] == pytest.approx(0.2)
    assert sustainability["projected_yearly_savings_eur"] == pytest.approx(245.45)
    assert sustainability["projected_yearly_co2_kg"] == pytest.approx(322.59)
    assert sustainability["market_data"]["region"] == "ES"


def test_build_history_summary_prefers_non_it_overhead_when_available():
    metrics = {
        "baseline": {
            "total_power_consumption": 1000.0,
            "total_it_power_consumption": 800.0,
            "total_cooling_power_consumption": 200.0,
            "average_pue": 1.25,
        },
        "models": {
            "scari_safe": {
                "total_power_consumption": 900.0,
                "total_it_power_consumption": 820.0,
                "total_cooling_power_consumption": 80.0,
                "average_pue": 1.10,
                "safety_override_rate_percent": 4.5,
                "safety_override_avg_fraction_active": 0.08,
                "total_steps": 1500,
            }
        },
    }

    summary = api_app.build_history_summary("eval_002", metrics)
    assert summary["savings"] == 60.0
    assert summary["total_power_savings_percent"] == 10.0
    assert summary["overhead_savings_percent"] == 60.0
    assert summary["cooling_savings_percent"] == 60.0
    assert summary["savings_basis"] == "non_it_overhead"
    assert summary["safety_override_rate_percent"] == 4.5
    assert summary["safety_override_avg_fraction_active"] == 0.08


def test_build_sustainability_uses_measured_pue_and_overhead_metrics():
    metrics = {
        "baseline": {
            "total_power_consumption": 3_600_000.0,
            "total_it_power_consumption": 2_880_000.0,
            "total_cooling_power_consumption": 720_000.0,
            "average_pue": 1.25,
        },
        "models": {
            "scari_safe": {
                "total_power_consumption": 3_240_000.0,
                "total_it_power_consumption": 2_952_000.0,
                "total_cooling_power_consumption": 288_000.0,
                "average_pue": 1.10,
                "total_steps": 3600,
            }
        },
    }

    sustainability = api_app.build_sustainability(metrics, GreenDCCalculator(region="ES"))
    assert sustainability["energy_savings_percent"] == 10.0
    assert sustainability["optimization_savings_percent"] == 60.0
    assert sustainability["non_it_overhead_savings_percent"] == 60.0
    assert sustainability["cooling_savings_percent"] == 60.0
    assert sustainability["pue_baseline"] == 1.25
    assert sustainability["pue_optimized"] == 1.1
    assert sustainability["pue_improvement_percent"] == 12.0
    assert sustainability["pue_overhead_reduction_percent"] == 60.0
    assert sustainability["projected_yearly_savings_eur"] == pytest.approx(122.72)
    assert sustainability["projected_yearly_co2_kg"] == pytest.approx(161.29)


def test_build_evaluation_context_exposes_model_config_mode_baseline_seed_and_steps():
    metrics = {
        "metadata": {
            "config": "configs/liquid.yaml",
            "seed": 42,
            "baseline_controller": "TRADITIONAL_ENTERPRISE",
        },
        "baseline": {"average_pue": 1.5},
        "models": {
            "THERMAL_SAFE": {
                "average_pue": 1.2,
                "total_steps": 5000,
                "total_power_consumption": 800.0,
            }
        },
    }

    context = api_app.build_evaluation_context(metrics)

    assert context == {
        "model": "THERMAL_SAFE",
        "config": "configs/liquid.yaml",
        "cooling_mode": "LIQUID",
        "baseline": "TRADITIONAL_ENTERPRISE",
        "seed": 42,
        "steps": 5000,
    }


def test_require_admin_access_allows_local_without_api_key(monkeypatch):
    monkeypatch.delenv("SCARI_API_KEY", raising=False)
    asyncio.run(api_app.require_admin_access(make_request("127.0.0.1"), None))


def test_require_admin_access_rejects_remote_without_api_key(monkeypatch):
    monkeypatch.delenv("SCARI_API_KEY", raising=False)
    with pytest.raises(HTTPException) as exc:
        asyncio.run(api_app.require_admin_access(make_request("203.0.113.10"), None))
    assert exc.value.status_code == 403
    assert "local-only" in exc.value.detail


def test_require_admin_access_accepts_matching_api_key(monkeypatch):
    monkeypatch.setenv("SCARI_API_KEY", "topsecret")
    asyncio.run(api_app.require_admin_access(make_request("203.0.113.10"), "topsecret"))


def test_require_admin_access_rejects_wrong_api_key(monkeypatch):
    monkeypatch.setenv("SCARI_API_KEY", "topsecret")
    with pytest.raises(HTTPException) as exc:
        asyncio.run(api_app.require_admin_access(make_request("203.0.113.10"), "wrong"))
    assert exc.value.status_code == 401
    assert exc.value.detail == "Invalid or missing X-API-Key"


def test_choose_evaluation_config_prefers_model_metadata():
    tmp_path = make_workspace_tmp("metadata_eval")
    try:
        model_path = tmp_path / "renamed_model.zip"
        model_path.write_text("zip", encoding="utf-8")
        (tmp_path / "renamed_model.metadata.json").write_text(
            json.dumps({"cooling_mode": "LIQUID"}),
            encoding="utf-8",
        )

        selected = api_app.choose_evaluation_config("configs/default.yaml", [str(model_path)])

        assert selected.endswith("liquid.yaml")
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_rename_model_moves_metadata_and_vecnormalize(monkeypatch):
    tmp_path = make_workspace_tmp("rename_model")
    monkeypatch.setattr(api_app, "MODELS_DIR", tmp_path)
    try:
        (tmp_path / "old_model.zip").write_text("zip", encoding="utf-8")
        (tmp_path / "old_model.metadata.json").write_text("{}", encoding="utf-8")
        (tmp_path / "old_model_vec_normalize.pkl").write_text("stats", encoding="utf-8")

        response = client.post("/models/rename", json={"old_name": "old_model.zip", "new_name": "new_model"})

        assert response.status_code == 200
        assert (tmp_path / "new_model.zip").exists()
        assert (tmp_path / "new_model.metadata.json").exists()
        assert (tmp_path / "new_model_vec_normalize.pkl").exists()
        assert not (tmp_path / "old_model.metadata.json").exists()
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_delete_model_removes_metadata_and_vecnormalize(monkeypatch):
    tmp_path = make_workspace_tmp("delete_model")
    monkeypatch.setattr(api_app, "MODELS_DIR", tmp_path)
    try:
        (tmp_path / "sample_model.zip").write_text("zip", encoding="utf-8")
        (tmp_path / "sample_model.metadata.json").write_text("{}", encoding="utf-8")
        (tmp_path / "sample_model_vec_normalize.pkl").write_text("stats", encoding="utf-8")

        response = client.delete("/models/sample_model.zip")

        assert response.status_code == 200
        assert not (tmp_path / "sample_model.zip").exists()
        assert not (tmp_path / "sample_model.metadata.json").exists()
        assert not (tmp_path / "sample_model_vec_normalize.pkl").exists()
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)


def test_delete_all_models_removes_registry_sidecars(monkeypatch):
    tmp_path = make_workspace_tmp("delete_all_models")
    monkeypatch.setattr(api_app, "MODELS_DIR", tmp_path)
    try:
        (tmp_path / "air_model.zip").write_text("zip", encoding="utf-8")
        (tmp_path / "air_model.metadata.json").write_text("{}", encoding="utf-8")
        (tmp_path / "air_model_vec_normalize.pkl").write_text("stats", encoding="utf-8")
        (tmp_path / "vec_normalize.pkl").write_text("shared", encoding="utf-8")
        (tmp_path / "config.json").write_text("{}", encoding="utf-8")

        response = client.delete("/models")

        assert response.status_code == 200
        assert list(tmp_path.glob("*")) == []
    finally:
        shutil.rmtree(tmp_path, ignore_errors=True)
