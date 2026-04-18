"""Performance simulations -- timing, scaling, and memory behavior."""

import time

import numpy as np
import pandas as pd
import pytest

from financial_dynamics.pipeline import FinancialDynamicsPipeline
from financial_dynamics.config import PipelineConfig


def _make_ohlcv(n: int, seed: int = 42) -> pd.DataFrame:
    """Generate n bars of synthetic OHLCV data."""
    rng = np.random.default_rng(seed)
    price = 100.0
    rows = []
    for _ in range(n):
        ret = rng.normal(0.0002, 0.015)
        close = price * (1 + ret)
        high = max(price, close) * (1 + abs(rng.normal(0, 0.005)))
        low = min(price, close) * (1 - abs(rng.normal(0, 0.005)))
        rows.append([price, high, low, close, rng.integers(1000, 10000)])
        price = close
    return pd.DataFrame(rows, columns=["open", "high", "low", "close", "volume"])


class TestPerformanceTiming:
    """Verify the pipeline runs within acceptable time bounds."""

    def test_240_bars_under_5_seconds(self):
        """240 bars (1 trading year of daily) should process in <5s."""
        df = _make_ohlcv(240)
        pipeline = FinancialDynamicsPipeline()
        start = time.perf_counter()
        pipeline.run(df)
        elapsed = time.perf_counter() - start
        assert elapsed < 5.0, f"240 bars took {elapsed:.2f}s (limit: 5s)"

    def test_1000_bars_under_15_seconds(self):
        """1000 bars should process in <15s."""
        df = _make_ohlcv(1000)
        pipeline = FinancialDynamicsPipeline()
        start = time.perf_counter()
        pipeline.run(df)
        elapsed = time.perf_counter() - start
        assert elapsed < 15.0, f"1000 bars took {elapsed:.2f}s (limit: 15s)"

    def test_5000_bars_under_60_seconds(self):
        """5000 bars (~20 years daily) should process in <60s."""
        df = _make_ohlcv(5000)
        pipeline = FinancialDynamicsPipeline()
        start = time.perf_counter()
        pipeline.run(df)
        elapsed = time.perf_counter() - start
        assert elapsed < 60.0, f"5000 bars took {elapsed:.2f}s (limit: 60s)"

    def test_streaming_vs_batch_comparable(self):
        """Streaming mode should not be drastically slower than batch."""
        df = _make_ohlcv(500)

        pipeline_batch = FinancialDynamicsPipeline()
        start = time.perf_counter()
        pipeline_batch.run(df)
        batch_time = time.perf_counter() - start

        pipeline_stream = FinancialDynamicsPipeline()
        start = time.perf_counter()
        for _, row in df.iterrows():
            pipeline_stream.step(row.to_dict())
        stream_time = time.perf_counter() - start

        # Streaming can be up to 3x slower due to per-row overhead
        assert stream_time < batch_time * 3.5, (
            f"Stream={stream_time:.2f}s vs Batch={batch_time:.2f}s "
            f"(ratio: {stream_time/batch_time:.1f}x)"
        )


class TestPerformanceScaling:
    """Verify roughly linear scaling behavior."""

    def test_linear_scaling_property(self):
        """Doubling input size should roughly double processing time (not quadratic)."""
        df_small = _make_ohlcv(300)
        df_large = _make_ohlcv(600)

        p1 = FinancialDynamicsPipeline()
        start = time.perf_counter()
        p1.run(df_small)
        t_small = time.perf_counter() - start

        p2 = FinancialDynamicsPipeline()
        start = time.perf_counter()
        p2.run(df_large)
        t_large = time.perf_counter() - start

        ratio = t_large / max(t_small, 0.001)
        # Allow up to 4x (generous for 2x input due to overhead)
        assert ratio < 4.0, (
            f"Scaling ratio: {ratio:.1f}x for 2x input "
            f"(small={t_small:.3f}s, large={t_large:.3f}s)"
        )


class TestPerformanceMemory:
    """Verify bounded memory behavior."""

    def test_pipeline_reset_clears_state(self):
        """After reset, internal buffers should be cleared."""
        df = _make_ohlcv(500)
        pipeline = FinancialDynamicsPipeline()
        pipeline.run(df)

        # Check that internal buffers exist
        assert pipeline._bar_count > 0

        pipeline.reset()
        assert pipeline._bar_count == 0

    def test_normalizer_history_bounded(self):
        """The normalizer's history should not grow beyond its window."""
        from financial_dynamics.phase0_features.normalizer import FeatureNormalizer
        from financial_dynamics.config import FeatureConfig

        config = FeatureConfig(normalization_window=100)
        norm = FeatureNormalizer(config)

        for _ in range(500):
            norm.update(np.random.rand(5))

        assert len(norm._history) <= config.normalization_window

    def test_overextension_history_bounded(self):
        """The overextension rebalancer's history should be bounded."""
        from financial_dynamics.phase4_risk.overextension import OverextensionRebalancer
        from financial_dynamics.types import Regime

        rebal = OverextensionRebalancer(window=50)
        for _ in range(500):
            rebal.record(Regime.CALM_TREND)

        assert len(rebal._history) <= 100  # window * 2

    def test_multiple_runs_no_leak(self):
        """Running the pipeline multiple times should not accumulate state."""
        df = _make_ohlcv(200)
        pipeline = FinancialDynamicsPipeline()

        for _ in range(10):
            results = pipeline.run(df)

        # Each run resets, so results should be consistent
        assert len(results) == len(df)
