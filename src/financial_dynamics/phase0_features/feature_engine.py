"""Phase 0: Feature Engine -- composes indicators and normalizer."""

from __future__ import annotations

from collections import deque

import numpy as np
import pandas as pd

from financial_dynamics.config import FeatureConfig
from financial_dynamics.types import BarState, FeatureVector
from financial_dynamics.phase0_features.indicators import (
    compute_cross_asset_stress,
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
    When reference asset data is available (columns named ref_*_close),
    uses cross-asset correlation stress instead of single-asset kurtosis.
    """

    def __init__(self, config: FeatureConfig | None = None):
        self.config = config or FeatureConfig()
        self.normalizer = FeatureNormalizer(self.config)
        self._close_buffer: deque[float] = deque(
            maxlen=self._max_window + 10
        )
        self._ref_buffers: dict[str, deque[float]] = {}

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

    def _compute_corr_stress(
        self,
        returns: pd.Series,
        ref_returns: dict[str, pd.Series] | None = None,
    ) -> pd.Series:
        """Compute correlation stress using cross-asset or single-asset method.

        Args:
            returns: Primary asset returns.
            ref_returns: Optional dict of reference asset returns.

        Returns:
            Correlation stress Series (same length as returns).
        """
        if ref_returns:
            return compute_cross_asset_stress(
                returns, ref_returns, self.config.correlation_window
            )
        return compute_correlation_stress(returns, self.config.correlation_window)

    def compute_batch(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute all features for a historical DataFrame.

        Args:
            df: Must contain columns ['open', 'high', 'low', 'close', 'volume'].

        Returns:
            DataFrame with columns for each raw and normalized feature.
        """
        close = df["close"]
        returns = close.pct_change()

        ref_cols = [c for c in df.columns if c.startswith("ref_") and c.endswith("_close")]
        ref_returns = {col: df[col].pct_change() for col in ref_cols} if ref_cols else None
        corr_stress = self._compute_corr_stress(returns, ref_returns)

        raw = pd.DataFrame({
            "volatility": compute_ewma_volatility(returns, self.config.volatility_span),
            "trend_strength": compute_trend_strength(close, self.config.trend_window),
            "drawdown_pressure": compute_drawdown_pressure(close, self.config.drawdown_window),
            "correlation_stress": corr_stress,
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

    def _update_ref_buffers(self, ohlcv: dict) -> None:
        """Append reference-asset close prices from an OHLCV dict into their buffers."""
        for key, value in ohlcv.items():
            if key.startswith("ref_") and key.endswith("_close"):
                if key not in self._ref_buffers:
                    self._ref_buffers[key] = deque(maxlen=self._max_window + 10)
                self._ref_buffers[key].append(value)

    def _build_ref_returns(self) -> "dict[str, pd.Series] | None":
        """Convert reference-asset buffers to return Series; return None if none are ready."""
        if not self._ref_buffers:
            return None
        ref_returns = {
            ref_key: pd.Series(list(buf)).pct_change().dropna()
            for ref_key, buf in self._ref_buffers.items()
            if len(buf) >= self.warmup_bars
        }
        return ref_returns or None

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
        self._update_ref_buffers(bar_state.ohlcv)

        if len(self._close_buffer) < self.warmup_bars:
            bar_state.features = None
            return bar_state

        close_series = pd.Series(list(self._close_buffer))
        returns = close_series.pct_change().dropna()
        ref_returns = self._build_ref_returns()

        corr_stress_val = float(self._compute_corr_stress(returns, ref_returns).iloc[-1])

        raw = np.array([
            float(compute_ewma_volatility(returns, self.config.volatility_span).iloc[-1]),
            float(compute_trend_strength(close_series, self.config.trend_window).iloc[-1]),
            float(compute_drawdown_pressure(close_series, self.config.drawdown_window).iloc[-1]),
            corr_stress_val,
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
        self._ref_buffers.clear()
        self.normalizer.reset()
