"""Integration tests for the full Financial Dynamics Pipeline."""

import numpy as np
import pandas as pd
import pytest

from financial_dynamics.pipeline import FinancialDynamicsPipeline
from financial_dynamics.types import Regime


class TestPipelineIntegration:
    def test_run_produces_dataframe(self, synthetic_ohlcv):
        df, _ = synthetic_ohlcv
        pipeline = FinancialDynamicsPipeline()
        results = pipeline.run(df)
        assert isinstance(results, pd.DataFrame)
        assert len(results) == len(df)

    def test_output_columns_present(self, synthetic_ohlcv):
        df, _ = synthetic_ohlcv
        pipeline = FinancialDynamicsPipeline()
        results = pipeline.run(df)
        assert "stabilized_regime" in results.columns
        assert "risk_adjusted_regime" in results.columns

    def test_warmup_produces_nones(self, synthetic_ohlcv):
        df, _ = synthetic_ohlcv
        pipeline = FinancialDynamicsPipeline()
        results = pipeline.run(df)
        warmup = pipeline.warmup_bars
        # First warmup-1 rows should have no regime (last warmup row may produce)
        assert results["risk_adjusted_regime"].iloc[:warmup - 1].isna().all()

    def test_post_warmup_has_regimes(self, synthetic_ohlcv):
        df, _ = synthetic_ohlcv
        pipeline = FinancialDynamicsPipeline()
        results = pipeline.run(df)
        valid = results.dropna(subset=["risk_adjusted_regime"])
        assert len(valid) > 0
        for regime_name in valid["risk_adjusted_regime"]:
            assert regime_name in [r.name for r in Regime]

    def test_probabilities_sum_to_one(self, synthetic_ohlcv):
        df, _ = synthetic_ohlcv
        pipeline = FinancialDynamicsPipeline()
        results = pipeline.run(df)
        prob_cols = [f"post_prob_{r.name}" for r in Regime]
        valid = results.dropna(subset=prob_cols)
        for _, row in valid.iterrows():
            total = sum(row[col] for col in prob_cols)
            assert total == pytest.approx(1.0, abs=1e-6)

    def test_transition_matrix_valid(self, synthetic_ohlcv):
        df, _ = synthetic_ohlcv
        pipeline = FinancialDynamicsPipeline()
        pipeline.run(df)
        report = pipeline.get_state_report()
        tm = report["transition_matrix"]
        assert tm.shape == (4, 4)
        for row in tm:
            assert row.sum() == pytest.approx(1.0)
            assert (row >= 0).all()

    def test_streaming_matches_batch(self, synthetic_ohlcv):
        df, _ = synthetic_ohlcv

        # Batch mode
        pipeline_batch = FinancialDynamicsPipeline()
        results_batch = pipeline_batch.run(df)

        # Streaming mode
        pipeline_stream = FinancialDynamicsPipeline()
        stream_regimes = []
        for _, row in df.iterrows():
            state = pipeline_stream.step(row.to_dict())
            regime = state.risk_adjusted_regime
            stream_regimes.append(regime.name if regime is not None else None)

        batch_regimes = results_batch["risk_adjusted_regime"].tolist()
        # Compare: batch uses NaN for missing, streaming uses None
        for s, b in zip(stream_regimes, batch_regimes, strict=True):
            if s is None:
                assert b is None or (isinstance(b, float) and np.isnan(b))
            else:
                assert s == b

    def test_reset_allows_rerun(self, synthetic_ohlcv):
        df, _ = synthetic_ohlcv
        pipeline = FinancialDynamicsPipeline()
        results1 = pipeline.run(df)
        results2 = pipeline.run(df)
        # Results should be identical after reset
        valid1 = results1.dropna(subset=["risk_adjusted_regime"])
        valid2 = results2.dropna(subset=["risk_adjusted_regime"])
        assert list(valid1["risk_adjusted_regime"]) == list(valid2["risk_adjusted_regime"])

    def test_state_report(self, synthetic_ohlcv):
        df, _ = synthetic_ohlcv
        pipeline = FinancialDynamicsPipeline()
        pipeline.run(df)
        report = pipeline.get_state_report()
        assert report["bar_count"] == len(df)
        assert report["is_warmed_up"] is True
        assert "transition_matrix" in report

    def test_short_data_doesnt_crash(self):
        df = pd.DataFrame({
            "open": [100, 101],
            "high": [102, 103],
            "low": [99, 100],
            "close": [101, 102],
            "volume": [1000, 1100],
        })
        pipeline = FinancialDynamicsPipeline()
        results = pipeline.run(df)
        assert len(results) == 2
        assert results["risk_adjusted_regime"].isna().all()
