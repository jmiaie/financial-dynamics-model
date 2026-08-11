"""Shared helpers for the scripts/ CLI entry points."""

from __future__ import annotations

from pathlib import Path


def print_banner(title: str) -> None:
    print("=" * 70)
    print(f"  {title}")
    print("=" * 70)


def load_config(config_arg: str | None):
    """Load a PipelineConfig from --config, falling back to config/default.yaml,
    then to built-in defaults."""
    from financial_dynamics.config import PipelineConfig

    if config_arg:
        config = PipelineConfig.from_yaml(config_arg)
        print(f"\nLoaded config from {config_arg}")
        return config

    default_path = Path(__file__).parent.parent / "config" / "default.yaml"
    if default_path.exists():
        config = PipelineConfig.from_yaml(default_path)
        print(f"\nLoaded config from {default_path}")
        return config

    print("\nUsing default config")
    return PipelineConfig()
