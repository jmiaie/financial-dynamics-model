"""Tests for cross-asset correlation stress and multi-asset pipeline integration."""

import numpy as np
import pandas as pd
import pytest

from financial_dynamics.phase0_features.feature_engine import FeatureEngine
from financial_dynamics.phase0_features.indicators import (
    compute_correlation_stress,
    compute_cross_asset_stress,
)
from financial_dynamics.pipeline import FinancialDynamicsPipeline


class TestCrossAssetStress:
    @pytest.fixture
    def returns_and_refs(self):
        rng = np.random.default_rng(42)
        n = 100
        primary = pd.Series(rng.normal(0, 0.01, n))
        ref_a = pd.Series(primary * 0.8 + rng.normal(0, 0.005, n))
        ref_b = pd.Series(-primary * 0.5 + rng.normal(0, 0.008, n))
        return primary, {"ref_a": ref_a, "ref_b": ref_b}

    def test_returns_series(self, returns_and_refs):
        primary, refs = returns_and_refs
        result = compute_cross_asset_stress(primary, refs, window=20)
        assert isinstance(result, pd.Series)
        assert len(result) == len(primary)

    def test_high_correlation_gives_high_stress(self):
        rng = np.random.default_rng(42)
        n = 100
        base = rng.normal(0, 0.01, n)
        primary = pd.Series(base)
        ref = pd.Series(base + rng.normal(0, 0.001, n))
        result = compute_cross_asset_stress(primary, {"ref": ref}, window=20)
        valid = result.dropna()
        assert valid.mean() > 0.5

    def test_uncorrelated_gives_low_stress(self):
        rng = np.random.default_rng(42)
        n = 200
        primary = pd.Series(rng.normal(0, 0.01, n))
        ref = pd.Series(rng.normal(0, 0.01, n))
        result = compute_cross_asset_stress(primary, {"ref": ref}, window=20)
        valid = result.dropna()
        assert valid.mean() < 0.5

    def test_no_references_falls_back_to_kurtosis(self):
        rng = np.random.default_rng(42)
        primary = pd.Series(rng.normal(0, 0.01, 100))
        result = compute_cross_asset_stress(primary, {}, window=20)
        expected = compute_correlation_stress(primary, window=20)
        pd.testing.assert_series_equal(result, expected)

    def test_values_non_negative(self, returns_and_refs):
        primary, refs = returns_and_refs
        result = compute_cross_asset_stress(primary, refs, window=20)
        valid = result.dropna()
        assert (valid >= 0).all()


class TestMultiAssetFeatureEngine:
    def test_ref_columns_used_in_batch(self):
        rng = np.random.default_rng(42)
        n = 120
        prices = 100 + np.cumsum(rng.normal(0, 0.5, n))
        df = pd.DataFrame(
            {
                "open": prices - 0.2,
                "high": prices + abs(rng.normal(0, 0.3, n)),
                "low": prices - abs(rng.normal(0, 0.3, n)),
                "close": prices,
                "volume": rng.integers(1000, 5000, n),
                "ref_VIX_close": 20 + rng.normal(0, 2, n),
            }
        )

        engine = FeatureEngine()
        features = engine.compute_batch(df)
        assert "correlation_stress" in features.columns
        valid = features["correlation_stress"].dropna()
        assert len(valid) > 0

    def test_ref_columns_used_in_streaming(self):
        rng = np.random.default_rng(42)
        n = 80

        from financial_dynamics.types import BarState

        engine = FeatureEngine()
        features_found = False
        for _i in range(n):
            bar = {
                "open": 100 + rng.normal(0, 0.5),
                "high": 102 + rng.normal(0, 0.5),
                "low": 98 + rng.normal(0, 0.5),
                "close": 100 + rng.normal(0, 0.5),
                "volume": 1000,
                "ref_VIX_close": 20 + rng.normal(0, 1),
            }
            state = BarState(ohlcv=bar)
            engine.update(state)
            if state.features is not None:
                features_found = True
        assert features_found

    def test_no_ref_columns_uses_kurtosis_fallback(self):
        rng = np.random.default_rng(42)
        n = 120
        prices = 100 + np.cumsum(rng.normal(0, 0.5, n))
        df = pd.DataFrame(
            {
                "open": prices - 0.2,
                "high": prices + abs(rng.normal(0, 0.3, n)),
                "low": prices - abs(rng.normal(0, 0.3, n)),
                "close": prices,
                "volume": rng.integers(1000, 5000, n),
            }
        )

        engine = FeatureEngine()
        features = engine.compute_batch(df)
        assert "correlation_stress" in features.columns


class TestMultiAssetPipeline:
    def test_pipeline_accepts_ref_columns(self):
        rng = np.random.default_rng(42)
        n = 120
        prices = 100 + np.cumsum(rng.normal(0, 0.5, n))
        df = pd.DataFrame(
            {
                "open": prices - 0.2,
                "high": prices + abs(rng.normal(0, 0.3, n)),
                "low": prices - abs(rng.normal(0, 0.3, n)),
                "close": prices,
                "volume": rng.integers(1000, 5000, n),
                "ref_VIX_close": 20 + rng.normal(0, 2, n),
                "ref_TLT_close": 90 + rng.normal(0, 1, n),
            }
        )

        pipeline = FinancialDynamicsPipeline()
        results = pipeline.run(df)
        assert len(results) == n
        valid = results.dropna(subset=["risk_adjusted_regime"])
        assert len(valid) > 0

    def test_pipeline_without_refs_still_works(self, synthetic_ohlcv):
        df, _ = synthetic_ohlcv
        pipeline = FinancialDynamicsPipeline()
        results = pipeline.run(df)
        valid = results.dropna(subset=["risk_adjusted_regime"])
        assert len(valid) > 0
