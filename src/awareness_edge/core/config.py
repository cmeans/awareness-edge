"""Pydantic configuration models with YAML + env var support."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_PATH = Path("~/.config/awareness-edge/config.yaml").expanduser()

ENV_PREFIX = "AWARENESS_EDGE_"


class AwarenessConfig(BaseModel):
    """Connection settings for the mcp-awareness server."""

    url: str = "http://localhost:8420"
    source: str = "awareness-edge"


class ProviderEntry(BaseModel):
    """A single provider definition in the config file."""

    name: str
    type: str
    enabled: bool = True
    config: dict[str, Any] = {}


class SinkEntry(BaseModel):
    """A single sink (outbound provider) definition in the config file."""

    name: str
    type: str
    enabled: bool = True
    config: dict[str, Any] = {}


class EvaluatorConfig(BaseModel):
    """Evaluator selection and settings."""

    type: Literal["threshold"] = "threshold"


class EdgeConfig(BaseModel):
    """Top-level configuration for awareness-edge."""

    awareness: AwarenessConfig = AwarenessConfig()
    evaluator: EvaluatorConfig = EvaluatorConfig()
    providers: list[ProviderEntry] = []
    sinks: list[SinkEntry] = []
    poll_interval_sec: int = 60
    logging_level: str = "INFO"


def _apply_env_overrides(config: EdgeConfig) -> None:
    """Apply AWARENESS_EDGE_* environment variable overrides in place."""
    env_map: dict[str, tuple[str, str]] = {
        "URL": ("awareness", "url"),
        "SOURCE": ("awareness", "source"),
        "POLL_INTERVAL": ("", "poll_interval_sec"),
        "LOG_LEVEL": ("", "logging_level"),
    }

    for suffix, (obj_path, field) in env_map.items():
        value = os.environ.get(f"{ENV_PREFIX}{suffix}")
        if value is None:
            continue

        target: Any = config
        if obj_path:
            for part in obj_path.split("."):
                target = getattr(target, part)

        current = getattr(target, field)
        if isinstance(current, bool):
            coerced: Any = value.lower() in ("true", "1", "yes")
        elif isinstance(current, int):
            coerced = int(value)
        else:
            coerced = value

        setattr(target, field, coerced)
        logger.debug(
            "Env override: %s%s -> %s.%s = %r",
            ENV_PREFIX,
            suffix,
            obj_path,
            field,
            coerced,
        )


def load_config(path: str | None = None) -> EdgeConfig:
    """Load config from YAML file with env var overrides.

    Args:
        path: Explicit path to config YAML. If None, uses default location.
              If the file doesn't exist, returns defaults.
    """
    config_path = Path(path) if path else DEFAULT_CONFIG_PATH

    if config_path.exists():
        logger.info("Loading config from %s", config_path)
        raw = yaml.safe_load(config_path.read_text()) or {}
        config = EdgeConfig.model_validate(raw)
    else:
        if path:
            msg = f"Config file not found: {config_path}"
            raise FileNotFoundError(msg)
        logger.info("No config file found, using defaults")
        config = EdgeConfig()

    _apply_env_overrides(config)
    return config
