import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Sequence, Union

from src.utils.config import Config, PROJECT_ROOT, resolve_config_file


MODE_TO_CONFIG = {
    "AIR": "configs/default.yaml",
    "LIQUID": "configs/liquid.yaml",
    "HYBRID": "configs/hybrid.yaml",
}

MODEL_METADATA_SUFFIX = ".metadata.json"
MODEL_VECNORMALIZE_SUFFIX = "_vec_normalize.pkl"


def _normalize_mode(value: str) -> str:
    normalized = (value or "").upper()
    if normalized not in MODE_TO_CONFIG:
        raise ValueError(f"Unsupported cooling mode: {value}")
    return normalized


def _project_label(path: Union[str, Path]) -> str:
    resolved = Path(path).resolve()
    try:
        return str(resolved.relative_to(PROJECT_ROOT)).replace("\\", "/")
    except ValueError:
        return str(resolved).replace("\\", "/")


def get_mode_config_path(mode: str) -> Path:
    return resolve_config_file(MODE_TO_CONFIG[_normalize_mode(mode)])


def get_config_cooling_mode(config_path: Union[str, Path]) -> str:
    return Config.from_yaml(resolve_config_file(config_path)).cooling.mode.upper()


def choose_training_config_path(
    requested_config: Optional[Union[str, Path]],
    cooling_mode: Optional[str],
) -> Path:
    normalized_mode = _normalize_mode(cooling_mode) if cooling_mode else None
    resolved_requested = resolve_config_file(requested_config) if requested_config else get_mode_config_path("AIR")
    if normalized_mode is None:
        return resolved_requested

    default_air_config = get_mode_config_path("AIR")
    if resolved_requested == default_air_config and normalized_mode != "AIR":
        return get_mode_config_path(normalized_mode)

    requested_mode = get_config_cooling_mode(resolved_requested)
    if requested_mode != normalized_mode:
        raise ValueError(
            f"config profile {resolved_requested.name} uses {requested_mode} cooling, "
            f"not {normalized_mode}"
        )
    return resolved_requested


def metadata_path_for_model(model_path: Union[str, Path]) -> Path:
    path = Path(model_path)
    return path.with_name(f"{path.stem}{MODEL_METADATA_SUFFIX}")


def vecnormalize_path_for_model(model_path: Union[str, Path]) -> Path:
    path = Path(model_path)
    return path.with_name(f"{path.stem}{MODEL_VECNORMALIZE_SUFFIX}")


def shared_vecnormalize_path(model_dir: Union[str, Path]) -> Path:
    return Path(model_dir) / "vec_normalize.pkl"


def build_model_metadata(
    *,
    config_path: Union[str, Path],
    cooling_mode: str,
    seed: int,
    timesteps: int,
) -> Dict[str, Any]:
    resolved_config = resolve_config_file(config_path)
    return {
        "config_path": _project_label(resolved_config),
        "resolved_config": str(resolved_config),
        "cooling_mode": _normalize_mode(cooling_mode),
        "seed": int(seed),
        "timesteps": int(timesteps),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


def save_model_metadata(model_path: Union[str, Path], metadata: Dict[str, Any]) -> Path:
    metadata_path = metadata_path_for_model(model_path)
    with metadata_path.open("w", encoding="utf-8") as handle:
        json.dump(metadata, handle, indent=2)
    return metadata_path


def load_model_metadata(model_reference: Union[str, Path]) -> Optional[Dict[str, Any]]:
    model_path = Path(model_reference)
    metadata_path = metadata_path_for_model(model_path)
    if not metadata_path.exists():
        return None
    try:
        with metadata_path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, json.JSONDecodeError):
        return None


def infer_model_mode(model_reference: Union[str, Path]) -> Optional[str]:
    metadata = load_model_metadata(model_reference)
    if isinstance(metadata, dict):
        raw_mode = metadata.get("cooling_mode")
        if raw_mode:
            try:
                return _normalize_mode(str(raw_mode))
            except ValueError:
                pass

    normalized = Path(model_reference).stem.lower()
    if any(token in normalized for token in ("liquid", "water", "hydro")):
        return "LIQUID"
    if "hybrid" in normalized:
        return "HYBRID"
    if "air" in normalized:
        return "AIR"
    return None


def choose_evaluation_config_path(
    requested_config: Optional[Union[str, Path]],
    model_references: Sequence[Union[str, Path]],
) -> Path:
    resolved_requested = resolve_config_file(requested_config) if requested_config else get_mode_config_path("AIR")
    default_air_config = get_mode_config_path("AIR")
    if resolved_requested != default_air_config:
        return resolved_requested

    inferred_modes = {
        mode
        for mode in (infer_model_mode(model_reference) for model_reference in model_references)
        if mode is not None
    }
    if len(inferred_modes) != 1:
        return resolved_requested

    return get_mode_config_path(inferred_modes.pop())


def rename_related_model_artifacts(old_model_path: Union[str, Path], new_model_path: Union[str, Path]) -> None:
    old_path = Path(old_model_path)
    new_path = Path(new_model_path)
    for source, destination in (
        (metadata_path_for_model(old_path), metadata_path_for_model(new_path)),
        (vecnormalize_path_for_model(old_path), vecnormalize_path_for_model(new_path)),
    ):
        if not source.exists():
            continue
        if destination.exists():
            raise FileExistsError(f"Destination already exists: {destination.name}")
        source.rename(destination)


def delete_related_model_artifacts(model_path: Union[str, Path]) -> None:
    for candidate in (
        metadata_path_for_model(model_path),
        vecnormalize_path_for_model(model_path),
    ):
        if candidate.exists():
            candidate.unlink()
