import asyncio
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

import src.api.app as api_app
from src.utils.greendc import GreenDCCalculator


client = TestClient(api_app.app)


def make_request(host: str):
    return SimpleNamespace(client=SimpleNamespace(host=host))


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
        "steps": 1500,
        "model": "scari_safe",
    }


def test_evaluation_request_defaults_to_default_config():
    params = api_app.EvaluationRequest(model="example.zip")
    assert params.config.endswith("default.yaml")


def test_build_sustainability_supports_current_metrics_shape():
    metrics = {
        "baseline": {"total_power_consumption": 1000.0},
        "models": {
            "scari_safe": {
                "total_power_consumption": 800.0,
                "average_pue": 1.18,
                "total_steps": 3600,
            }
        },
    }
    sustainability = api_app.build_sustainability(metrics, GreenDCCalculator(region="ES"))
    assert sustainability["energy_savings_percent"] == 20.0
    assert sustainability["optimization_savings_percent"] == 20.0
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


def test_build_sustainability_uses_measured_pue_and_overhead_metrics():
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
