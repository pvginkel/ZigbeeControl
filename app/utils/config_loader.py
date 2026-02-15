"""Configuration loader that reads YAML and validates via Pydantic."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from app.exceptions import ConfigLoadFailed
from app.schemas.config import TabsConfig


def load_tabs_config(path: str) -> TabsConfig:
    """Read and validate the YAML configuration file."""
    candidate = Path(path)
    if not candidate.exists():
        raise ConfigLoadFailed("configuration file not found", path=path)
    if not candidate.is_file():
        raise ConfigLoadFailed("configuration path is not a file", path=path)

    try:
        raw = candidate.read_text(encoding="utf-8")
    except OSError as exc:
        raise ConfigLoadFailed(f"failed to read configuration: {exc.strerror}", path=path) from exc

    try:
        payload = yaml.safe_load(raw) or {}
    except yaml.YAMLError as exc:
        message = getattr(exc, "problem_mark", None)
        detail = f"malformed YAML: {exc}"
        if message:
            detail = f"malformed YAML at {message}"
        raise ConfigLoadFailed(detail, path=path) from exc

    parsed_payload: dict[str, Any]
    if isinstance(payload, list):
        parsed_payload = {"tabs": payload}
    elif isinstance(payload, dict):
        parsed_payload = payload
    else:
        raise ConfigLoadFailed("YAML root must be a mapping or list of tabs", path=path)

    try:
        return TabsConfig.model_validate(parsed_payload)
    except ValidationError as exc:
        raise ConfigLoadFailed(f"configuration validation failed: {exc}", path=path) from exc
