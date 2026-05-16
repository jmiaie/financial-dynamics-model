"""Top-level pipeline orchestrator composing all phase engines."""

from __future__ import annotations

from typing import TypedDict, cast

import numpy as np
import pandas as pd

from financial_dynamics.config import PipelineConfig
from financial_dynamics.types import BarState, Regime, RegimeProbabilities
from financial_dynamics.phase0_features.feature_engine import FeatureEngine
from financial_dynamics.phase1_regimes.centroid_engine import CentroidEngine
from financial_dynamics.phase2_transitions.transition_engine import MarkovTransitionEngine
from financial_dynamics.phase3_stabilization.stabilizer import StabilizationEngine
from financial_dynamics.phase4_risk.risk_overlay import RiskConditioningEngine
from financial_dynamics.forecasting import (
    RegimeForecast,
    forecast_regimes,
)


class StateReport(TypedDict):
    """System state summary returned by get_state_report()."""
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


class FinancialDynamicsPipeline:
    """Orchestrates the full 5-phase Financial Dynamics Model.

    Processes OHLCV data through feature engineering, centroid-based regime
    classification, Markov transition learning, temporal stabilization,
    and risk conditioning.
    """

    def __init__(self, config: PipelineConfig | None = None):
        self.config = config or PipelineConfig()
        self._feature_engine = FeatureEngine(self.config.features)
        self._centroid_engine = CentroidEngine(self.config.regimes)
        self._transition_engine = MarkovTransitionEngine(self.config.transitions)
        self._stabilization_engine = StabilizationEngine(self.config.stabilization)
        self._risk_engine = RiskConditioningEngine(self.config.risk)
        self._bar_count = 0

    @property
    def warmup_bars(self) -> int:
        return self._feature_engine.warmup_bars

    def step(self, bar: dict[str, float], timestamp: int | float | str | None = None) -> BarState:
        """Process a single OHLCV bar through the full pipeline.

        Args:
            bar: dict with keys 'open', 'high', 'low', 'close', 'volume'.
            timestamp: Optional timestamp for the bar.

        Returns:
            Fully populated BarState.
        """
        state = BarState(timestamp=timestamp, ohlcv=bar)

        self._feature_engine.update(state)
        if state.features is None:
            self._bar_count += 1
            return state

        self._centroid_engine.update(state)
        self._transition_engine.update(state)
        self._stabilization_engine.update(state)
        self._risk_engine.update(state)

        self._bar_count += 1
        return state

    def run(self, df: pd.DataFrame) -> pd.DataFrame:
        """Batch mode: process an entire DataFrame.

        Args:
            df: DataFrame with columns ['open', 'high', 'low', 'close', 'volume'].

        Returns:
            DataFrame with all intermediate and final results.
        """
        required = {"open", "high", "low", "close", "volume"}
        missing = required - set(df.columns)
        if missing:
            raise ValueError(
                f"DataFrame missing required OHLCV columns: {sorted(missing)}"
            )

        self.reset()

        results = []
        for idx, row in df.iterrows():
            bar = row.to_dict()
            state = self.step(bar, timestamp=idx)
            results.append(self._state_to_record(state))

        return pd.DataFrame(results, index=df.index)

    def get_state_report(self) -> StateReport:
        """Return current system state summary."""
        return {
            "bar_count": self._bar_count,
            "warmup_bars": self.warmup_bars,
            "is_warmed_up": self._bar_count >= self.warmup_bars,
            "transition_matrix": self._transition_engine.get_transition_matrix(),
        }

    def forecast(self, horizon: int = 10) -> RegimeForecast | None:
        """Forecast regime probabilities k steps ahead from current state.

        Returns None if the pipeline hasn't processed enough data yet.
        """
        prev = self._transition_engine._prev_regime
        if prev is None:
            return None

        tm = self._transition_engine.get_transition_matrix()
        current_probs = RegimeProbabilities(probs=tm[int(prev)])
        return forecast_regimes(tm, prev, current_probs, horizon=horizon)

    def reset(self) -> None:
        self._feature_engine.reset()
        self._transition_engine.reset()
        self._stabilization_engine.reset()
        self._risk_engine.reset()
        self._bar_count = 0

    @staticmethod
    def _state_to_record(state: BarState) -> BarRecord:
        """Convert a BarState to a flat dict for DataFrame construction."""
        # Build into a plain dict first; dynamic f-string keys cannot be
        # statically verified against TypedDict, so we cast at the end.
        record: dict[str, object] = {}

        if state.features is not None:
            f = state.features
            record["feat_volatility"] = f.volatility
            record["feat_trend"] = f.trend_strength
            record["feat_drawdown"] = f.drawdown_pressure
            record["feat_corr_stress"] = f.correlation_stress
            record["feat_shock"] = f.shock_intensity

        if state.raw_probabilities is not None:
            for regime in Regime:
                record[f"raw_prob_{regime.name}"] = state.raw_probabilities[regime]

        if state.posterior_probabilities is not None:
            for regime in Regime:
                record[f"post_prob_{regime.name}"] = state.posterior_probabilities[regime]

        record["stabilized_regime"] = (
            state.stabilized_regime.name if state.stabilized_regime is not None else None
        )
        record["risk_adjusted_regime"] = (
            state.risk_adjusted_regime.name if state.risk_adjusted_regime is not None else None
        )
        record["risk_overlays"] = state.risk_overlays if state.risk_overlays else None

        return cast(BarRecord, record)
