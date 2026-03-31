import json
import logging
import os
import re
import secrets
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import Header, HTTPException, Request

from src.utils.greendc import GreenDCCalculator
from src.utils.model_registry import (
    choose_evaluation_config_path,
    infer_model_mode as infer_model_mode_from_registry,
)


BASE_DIR = Path(__file__).resolve().parent.parent.parent
CONFIGS_DIR = (BASE_DIR / "configs").resolve()

LOCAL_CLIENT_HOSTS = {"127.0.0.1", "::1", "localhost", "testclient"}
MODEL_NAME_PATTERN = re.compile(r"[^A-Za-z0-9._ -]+")

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


def infer_model_mode(model_name: str) -> Optional[str]:
    return infer_model_mode_from_registry(model_name)


def choose_evaluation_config(requested_config: str, model_names: List[str]) -> str:
    resolved_requested = resolve_config_path(requested_config)
    inferred_config = choose_evaluation_config_path(resolved_requested, model_names)
    if inferred_config != resolved_requested:
        logging.getLogger("SCARI_API").info(
            "Auto-selected evaluation config %s for model(s): %s",
            inferred_config.name,
            ", ".join(model_names),
        )
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


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "time": self.formatTime(record),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
        }
        return json.dumps(log_obj)


def create_api_logger() -> logging.Logger:
    logger = logging.getLogger("SCARI_API")
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    return logger
