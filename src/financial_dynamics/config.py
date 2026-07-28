"""Configuration dataclasses for all pipeline phases."""

from __future__ import annotations

import warnings
from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class FeatureConfig:
    volatility_span: int = 20
    trend_window: int = 14
    drawdown_window: int = 60
    correlation_window: int = 20
    shock_threshold: float = 2.0
    normalization_method: str = "zscore"  # "zscore" or "minmax"
    normalization_window: int = 252
    feature_weights: list[float] = field(
        default_factory=lambda: [1.0, 1.0, 1.0, 1.0, 1.0]
    )
    reference_symbols: list[str] = field(default_factory=list)


@dataclass
class RegimeConfig:
    temperature: float = 1.0
    centroids: dict[str, list[float]] = field(default_factory=lambda: {
        "CALM_TREND":     [0.1, 0.8, 0.05, 0.1, 0.1],
        "VOLATILE_TREND": [0.8, 0.7, 0.3,  0.5, 0.6],
        "CHOP":           [0.4, 0.2, 0.15, 0.3, 0.3],
        "RISK_OFF":       [0.9, 0.3, 0.8,  0.9, 0.9],
    })


@dataclass
class TransitionConfig:
    prior_strength: float = 10.0
    learning_rate: float = 0.05


@dataclass
class StabilizationConfig:
    hysteresis_threshold: float = 0.15
    min_persistence_bars: int = 5
    majority_vote_window: int = 10


@dataclass
class RiskConfig:
    drawdown_threshold: float = 0.5
    correlation_stress_threshold: float = 0.6
    shock_threshold: float = 0.7
    riskoff_confirmation_count: int = 3
    overextension_window: int = 50
    overextension_decay: float = 0.02
    chop_penalty_window: int = 30
    chop_penalty_factor: float = 0.1


@dataclass
class PipelineConfig:
    features: FeatureConfig = field(default_factory=FeatureConfig)
    regimes: RegimeConfig = field(default_factory=RegimeConfig)
    transitions: TransitionConfig = field(default_factory=TransitionConfig)
    stabilization: StabilizationConfig = field(default_factory=StabilizationConfig)
    risk: RiskConfig = field(default_factory=RiskConfig)

    @classmethod
    def from_yaml(cls, path: str | Path) -> PipelineConfig:
        """Load configuration from YAML, merging with defaults."""
        path = Path(path)
        try:
            with open(path) as f:
                raw = yaml.safe_load(f)
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Pipeline config not found: {path.resolve()}"
            ) from None
        except yaml.YAMLError as exc:
            raise ValueError(
                f"Invalid YAML in {path.resolve()}: {exc}"
            ) from exc

        if raw is not None and not isinstance(raw, dict):
            raise ValueError(
                f"Expected YAML mapping at top level of {path.resolve()}, "
                f"got {type(raw).__name__}"
            )
        data = raw or {}

        config = cls()
        section_map = {
            "features": (config.features, FeatureConfig),
            "regimes": (config.regimes, RegimeConfig),
            "transitions": (config.transitions, TransitionConfig),
            "stabilization": (config.stabilization, StabilizationConfig),
            "risk": (config.risk, RiskConfig),
        }
        for section_name, (section_obj, _) in section_map.items():
            if section_name in data:
                for key, value in data[section_name].items():
                    if hasattr(section_obj, key):
                        setattr(section_obj, key, value)
                    else:
                        warnings.warn(
                            f"Unknown config key '{key}' in section "
                            f"'{section_name}'; ignoring.",
                            stacklevel=2,
                        )
        return config

    @classmethod
    def resolve(
        cls,
        config_arg: str | Path | None,
        default_path: str | Path | None = None,
    ) -> tuple[PipelineConfig, Path | None]:
        """Resolve a config from an explicit path, else a default file, else built-in defaults.

        Returns (config, source_path); source_path is None when neither
        config_arg nor default_path pointed at an existing file.
        """
        if config_arg:
            return cls.from_yaml(config_arg), Path(config_arg)
        if default_path is not None:
            default_path = Path(default_path)
            if default_path.exists():
                return cls.from_yaml(default_path), default_path
        return cls(), None
