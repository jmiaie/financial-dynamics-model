"""Phase 0: Feature Engine -- composes indicators and normalizer."""

from __future__ import annotations

from collections import deque

import numpy as np
import pandas as pd

from financial_dynamics.config import FeatureConfig
from financial_dynamics.types import BarState, FeatureVector
from financial_dynamics.phase0_features.indicators import (
    compute_drawdown_pressure,
    compute_correlation_stress,
    compute_ewma_volatility,
    compute_shock_intensity,
    compute_trend_strength,
)
from financial_dynamics.phase0_features.normalizer import FeatureNormalizer


class FeatureEngine:
    """Phase 0: Transforms raw OHLCV bars into normalized 5D feature vectors.

    Supports both batch and incremental (streaming) operation.
    """

    def __init__(self, config: FeatureConfig | None = None):
        self.config = config or FeatureConfig()
        self.normalizer = FeatureNormalizer(self.config)
        self._close_buffer: deque[float] = deque(
            maxlen=self._max_window + 10
        )

    @property
    def _max_window(self) -> int:
        return max(
            self.config.volatility_span,
            self.config.trend_window,
            self.config.drawdown_window,
            self.config.correlation_window,
        )

    @property
    def warmup_bars(self) -> int:
        return self._max_window + 1

    def compute_batch(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute all features for a historical DataFrame.

        Args:
            df: Must contain columns ['open', 'high', 'low', 'close', 'volume'].

        Returns:
            DataFrame with columns for each raw and normalized feature.
        """
        close = df["close"]
        returns = close.pct_change()

        raw = pd.DataFrame({
            "volatility": compute_ewma_volatility(returns, self.config.volatility_span),
            "trend_strength": compute_trend_strength(close, self.config.trend_window),
            "drawdown_pressure": compute_drawdown_pressure(close, self.config.drawdown_window),
            "correlation_stress": compute_correlation_stress(returns, self.config.correlation_window),
            "shock_intensity": compute_shock_intensity(returns, self.config.correlation_window),
        }, index=df.index)

        normalized_rows = []
        self.normalizer.reset()
        for _, row in raw.iterrows():
            vals = row.values
            if np.isnan(vals).any():
                normalized_rows.append(np.full(5, np.nan))
            else:
                normalized_rows.append(self.normalizer.update(vals))

        normalized = pd.DataFrame(
            normalized_rows,
            index=df.index,
            columns=[f"norm_{c}" for c in raw.columns],
        )

        return pd.concat([raw, normalized], axis=1)

    def update(self, bar_state: BarState) -> BarState:
        """Incremental update for a single bar.

        Reads bar_state.ohlcv, computes features, writes bar_state.features.
        Returns None for features if not enough warmup data.
        """
        if "close" not in bar_state.ohlcv:
            raise KeyError(
                f"Bar is missing required key 'close'. "
                f"Got keys: {sorted(bar_state.ohlcv.keys())}"
            )
        close = bar_state.ohlcv["close"]
        self._close_buffer.append(close)

        if len(self._close_buffer) < self.warmup_bars:
            bar_state.features = None
            return bar_state

        close_series = pd.Series(list(self._close_buffer))
        returns = close_series.pct_change().dropna()

        raw = np.array([
            float(compute_ewma_volatility(returns, self.config.volatility_span).iloc[-1]),
            float(compute_trend_strength(close_series, self.config.trend_window).iloc[-1]),
            float(compute_drawdown_pressure(close_series, self.config.drawdown_window).iloc[-1]),
            float(compute_correlation_stress(returns, self.config.correlation_window).iloc[-1]),
            float(compute_shock_intensity(returns, self.config.correlation_window).iloc[-1]),
        ])

        if np.isnan(raw).any():
            bar_state.features = None
            return bar_state

        normalized = self.normalizer.update(raw)
        bar_state.features = FeatureVector.from_array(normalized)
        return bar_state

    def reset(self) -> None:
        self._close_buffer.clear()
        self.normalizer.reset()
