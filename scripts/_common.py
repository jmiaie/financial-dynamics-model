"""Shared utilities for CLI scripts."""

from __future__ import annotations

from pathlib import Path

from financial_dynamics.config import PipelineConfig

_DEFAULT_CONFIG_PATH = Path(__file__).parent.parent / "config" / "default.yaml"


def load_config(config_arg: str | None) -> PipelineConfig:
    """Load a PipelineConfig from an explicit path or the default location.

    If *config_arg* is provided it is used directly.  Otherwise the file
    ``config/default.yaml`` (relative to the repo root) is tried.  When
    neither file exists a default in-memory config is returned.

    Args:
        config_arg: Value of the ``--config`` CLI argument, or None.

    Returns:
        Fully initialised PipelineConfig and prints what was loaded.
    """
    if config_arg:
        config_path = Path(config_arg)
    else:
        config_path = _DEFAULT_CONFIG_PATH

    if config_path.exists():
        config = PipelineConfig.from_yaml(config_path)
        print(f"\nLoaded config from {config_path}")
    else:
        config = PipelineConfig()
        print("\nUsing default config")

    return config
