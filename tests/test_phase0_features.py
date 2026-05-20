"""Tests for Phase 0: Feature Engineering."""

import numpy as np
import pandas as pd
import pytest

from financial_dynamics.config import FeatureConfig
from financial_dynamics.phase0_features.feature_engine import FeatureEngine
from financial_dynamics.phase0_features.indicators import (
    compute_correlation_stress,
    compute_drawdown_pressure,
    compute_ewma_volatility,
    compute_shock_intensity,
    compute_trend_strength,
)
from financial_dynamics.phase0_features.normalizer import FeatureNormalizer
from financial_dynamics.types import BarState


class TestIndicators:
    def test_ewma_volatility_shape(self, calm_trend_data):
        returns = calm_trend_data["close"].pct_change()
        vol = compute_ewma_volatility(returns, span=20)
        assert len(vol) == len(returns)
        assert vol.iloc[25:].notna().all()

    def test_ewma_volatility_positive(self, calm_trend_data):
        returns = calm_trend_data["close"].pct_change()
        vol = compute_ewma_volatility(returns, span=20).dropna()
        assert (vol >= 0).all()

    def test_calm_volatility_lower_than_volatile(self, calm_trend_data, volatile_trend_data):
        calm_ret = calm_trend_data["close"].pct_change()
        vol_ret = volatile_trend_data["close"].pct_change()
        calm_vol = compute_ewma_volatility(calm_ret, 20).dropna().mean()
        vol_vol = compute_ewma_volatility(vol_ret, 20).dropna().mean()
        assert calm_vol < vol_vol

    def test_trend_strength_shape(self, calm_trend_data):
        ts = compute_trend_strength(calm_trend_data["close"], window=14)
        assert len(ts) == len(calm_trend_data)

    def test_trend_strength_nonnegative(self, calm_trend_data):
        ts = compute_trend_strength(calm_trend_data["close"], window=14).dropna()
        assert (ts >= 0).all()

    def test_chop_has_low_trend(self, chop_data, volatile_trend_data):
        chop_trend = compute_trend_strength(chop_data["close"], 14).dropna().mean()
        vol_trend = compute_trend_strength(volatile_trend_data["close"], 14).dropna().mean()
        assert chop_trend < vol_trend

    def test_drawdown_pressure_range(self, calm_trend_data):
        dd = compute_drawdown_pressure(calm_trend_data["close"], window=60)
        valid = dd.dropna()
        assert (valid >= 0).all()
        assert (valid <= 1).all()

    def test_drawdown_zero_at_peak(self):
        prices = pd.Series([100, 101, 102, 103, 104])
        dd = compute_drawdown_pressure(prices, window=5)
        assert dd.iloc[-1] == pytest.approx(0.0)

    def test_correlation_stress_nonneg(self, volatile_trend_data):
        returns = volatile_trend_data["close"].pct_change()
        cs = compute_correlation_stress(returns, window=20).dropna()
        assert (cs >= 0).all()

    def test_shock_intensity_shape(self, calm_trend_data):
        returns = calm_trend_data["close"].pct_change()
        shock = compute_shock_intensity(returns, window=20)
        assert len(shock) == len(returns)

    def test_shock_intensity_nonneg(self, calm_trend_data):
        returns = calm_trend_data["close"].pct_change()
        shock = compute_shock_intensity(returns, window=20).dropna()
        assert (shock >= 0).all()


class TestNormalizer:
    def test_output_shape(self):
        config = FeatureConfig()
        norm = FeatureNormalizer(config)
        for _ in range(30):
            result = norm.update(np.random.rand(5))
        assert result.shape == (5,)

    def test_zscore_output_bounded(self):
        config = FeatureConfig(normalization_method="zscore")
        norm = FeatureNormalizer(config)
        for _ in range(50):
            result = norm.update(np.random.rand(5))
        # Sigmoid-squashed output should be in [0, 1] * weights
        assert (result >= 0).all()
        assert (result <= 1.0 * max(config.feature_weights) + 0.01).all()

    def test_minmax_output_bounded(self):
        config = FeatureConfig(normalization_method="minmax")
        norm = FeatureNormalizer(config)
        for _ in range(50):
            result = norm.update(np.random.rand(5))
        assert (result >= 0).all()
        assert (result <= 1.01).all()

    def test_reset_clears_state(self):
        config = FeatureConfig()
        norm = FeatureNormalizer(config)
        for _ in range(10):
            norm.update(np.random.rand(5))
        norm.reset()
        assert len(norm._history) == 0


class TestFeatureEngine:
    def test_batch_output_columns(self, calm_trend_data):
        engine = FeatureEngine()
        result = engine.compute_batch(calm_trend_data)
        expected_cols = [
            "volatility",
            "trend_strength",
            "drawdown_pressure",
            "correlation_stress",
            "shock_intensity",
            "norm_volatility",
            "norm_trend_strength",
            "norm_drawdown_pressure",
            "norm_correlation_stress",
            "norm_shock_intensity",
        ]
        for col in expected_cols:
            assert col in result.columns

    def test_batch_output_length(self, calm_trend_data):
        engine = FeatureEngine()
        result = engine.compute_batch(calm_trend_data)
        assert len(result) == len(calm_trend_data)

    def test_streaming_warmup(self):
        engine = FeatureEngine()
        state = BarState(ohlcv={"close": 100.0})
        engine.update(state)
        assert state.features is None

    def test_streaming_produces_features(self, calm_trend_data):
        engine = FeatureEngine()
        last_state = None
        for _, row in calm_trend_data.iterrows():
            state = BarState(ohlcv=row.to_dict())
            engine.update(state)
            last_state = state
        assert last_state.features is not None
        arr = last_state.features.to_array()
        assert arr.shape == (5,)
        assert not np.isnan(arr).any()

    def test_warmup_bars_property(self):
        config = FeatureConfig(
            volatility_span=20, trend_window=14, drawdown_window=60, correlation_window=20
        )
        engine = FeatureEngine(config)
        assert engine.warmup_bars == 61
