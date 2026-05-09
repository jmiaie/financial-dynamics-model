"""Shared type definitions used across all pipeline phases."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
from typing import TypedDict

import numpy as np


class Regime(IntEnum):
    """The four market regimes identified by the model."""
    CALM_TREND = 0
    VOLATILE_TREND = 1
    CHOP = 2
    RISK_OFF = 3


REGIME_NAMES = {
    Regime.CALM_TREND: "Calm Trend",
    Regime.VOLATILE_TREND: "Volatile Trend",
    Regime.CHOP: "Chop",
    Regime.RISK_OFF: "Risk-Off",
}

NUM_REGIMES = len(Regime)


@dataclass
class FeatureVector:
    """The 5-dimensional feature vector X_t produced by Phase 0."""
    volatility: float
    trend_strength: float
    drawdown_pressure: float
    correlation_stress: float
    shock_intensity: float

    def to_array(self) -> np.ndarray:
        return np.array([
            self.volatility,
            self.trend_strength,
            self.drawdown_pressure,
            self.correlation_stress,
            self.shock_intensity,
        ])

    @classmethod
    def from_array(cls, arr: np.ndarray) -> FeatureVector:
        return cls(
            volatility=float(arr[0]),
            trend_strength=float(arr[1]),
            drawdown_pressure=float(arr[2]),
            correlation_stress=float(arr[3]),
            shock_intensity=float(arr[4]),
        )


@dataclass
class RegimeProbabilities:
    """Probability distribution over the 4 regimes."""
    probs: np.ndarray  # shape (4,), sums to 1.0

    @property
    def dominant(self) -> Regime:
        return Regime(int(np.argmax(self.probs)))

    @property
    def confidence(self) -> float:
        return float(np.max(self.probs))

    def __getitem__(self, regime: Regime) -> float:
        return float(self.probs[int(regime)])


@dataclass
class BarState:
    """Accumulated state for a single bar flowing through the pipeline.
    Each phase populates its corresponding field."""
    timestamp: int | float | str | None = None
    ohlcv: dict[str, float] = field(default_factory=dict)

    features: FeatureVector | None = None

    raw_probabilities: RegimeProbabilities | None = None

    transition_matrix: np.ndarray | None = None  # shape (4, 4), row-stochastic
    posterior_probabilities: RegimeProbabilities | None = None

    stabilized_regime: Regime | None = None

    risk_adjusted_regime: Regime | None = None
    risk_overlays: dict[str, bool] = field(default_factory=dict)


class StateReport(TypedDict):
    """System state summary returned by FinancialDynamicsPipeline.get_state_report()."""
    bar_count: int
    warmup_bars: int
    is_warmed_up: bool
    transition_matrix: np.ndarray


class BarRecord(TypedDict, total=False):
    """Flat record for DataFrame construction from BarState."""
    feat_volatility: float
    feat_trend: float
    feat_drawdown: float
    feat_corr_stress: float
    feat_shock: float
    raw_prob_CALM_TREND: float
    raw_prob_VOLATILE_TREND: float
    raw_prob_CHOP: float
    raw_prob_RISK_OFF: float
    post_prob_CALM_TREND: float
    post_prob_VOLATILE_TREND: float
    post_prob_CHOP: float
    post_prob_RISK_OFF: float
    stabilized_regime: str | None
    risk_adjusted_regime: str | None
    risk_overlays: dict[str, bool] | None


# Column names for the 5 normalized feature outputs in a BarRecord / pipeline DataFrame.
# Defined here as the canonical source of truth alongside BarRecord so that any consumer
# (centroid fitting, visualization, tests) can import rather than repeat the literal strings.
FEATURE_COLUMNS: list[str] = [
    "feat_volatility",
    "feat_trend",
    "feat_drawdown",
    "feat_corr_stress",
    "feat_shock",
]
