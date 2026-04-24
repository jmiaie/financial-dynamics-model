"""Tests for the persistence layer -- save/load pipeline state."""

import json

import numpy as np
import pandas as pd
import pytest

from financial_dynamics.persistence import save_state, load_state
from financial_dynamics.persistence.state_io import _extract_state
from financial_dynamics.pipeline import FinancialDynamicsPipeline
from financial_dynamics.config import PipelineConfig
from financial_dynamics.types import Regime


class TestSaveLoad:
    def test_save_creates_file(self, synthetic_ohlcv, tmp_path):
        df, _ = synthetic_ohlcv
        pipeline = FinancialDynamicsPipeline()
        pipeline.run(df)

        path = tmp_path / "state.json"
        save_state(pipeline, path)
        assert path.exists()

    def test_save_is_valid_json(self, synthetic_ohlcv, tmp_path):
        df, _ = synthetic_ohlcv
        pipeline = FinancialDynamicsPipeline()
        pipeline.run(df)

        path = tmp_path / "state.json"
        save_state(pipeline, path)

        with open(path) as f:
            data = json.load(f)
        assert data["version"] == 1
        assert "config" in data
        assert "transition_engine" in data

    def test_save_creates_parent_dirs(self, synthetic_ohlcv, tmp_path):
        df, _ = synthetic_ohlcv
        pipeline = FinancialDynamicsPipeline()
        pipeline.run(df)

        path = tmp_path / "nested" / "dir" / "state.json"
        save_state(pipeline, path)
        assert path.exists()

    def test_load_restores_pipeline(self, synthetic_ohlcv, tmp_path):
        df, _ = synthetic_ohlcv
        pipeline = FinancialDynamicsPipeline()
        pipeline.run(df)

        path = tmp_path / "state.json"
        save_state(pipeline, path)
        restored = load_state(path)

        assert isinstance(restored, FinancialDynamicsPipeline)

    def test_roundtrip_preserves_bar_count(self, synthetic_ohlcv, tmp_path):
        df, _ = synthetic_ohlcv
        pipeline = FinancialDynamicsPipeline()
        pipeline.run(df)

        path = tmp_path / "state.json"
        save_state(pipeline, path)
        restored = load_state(path)

        assert restored._bar_count == pipeline._bar_count

    def test_roundtrip_preserves_transition_matrix(self, synthetic_ohlcv, tmp_path):
        df, _ = synthetic_ohlcv
        pipeline = FinancialDynamicsPipeline()
        pipeline.run(df)

        path = tmp_path / "state.json"
        save_state(pipeline, path)
        restored = load_state(path)

        original_tm = pipeline._transition_engine.get_transition_matrix()
        restored_tm = restored._transition_engine.get_transition_matrix()
        np.testing.assert_array_almost_equal(original_tm, restored_tm)

    def test_roundtrip_preserves_counts(self, synthetic_ohlcv, tmp_path):
        df, _ = synthetic_ohlcv
        pipeline = FinancialDynamicsPipeline()
        pipeline.run(df)

        path = tmp_path / "state.json"
        save_state(pipeline, path)
        restored = load_state(path)

        np.testing.assert_array_almost_equal(
            pipeline._transition_engine.counts,
            restored._transition_engine.counts,
        )

    def test_roundtrip_preserves_prev_regime(self, synthetic_ohlcv, tmp_path):
        df, _ = synthetic_ohlcv
        pipeline = FinancialDynamicsPipeline()
        pipeline.run(df)

        path = tmp_path / "state.json"
        save_state(pipeline, path)
        restored = load_state(path)

        assert pipeline._transition_engine._prev_regime == restored._transition_engine._prev_regime

    def test_roundtrip_preserves_stabilization_state(self, synthetic_ohlcv, tmp_path):
        df, _ = synthetic_ohlcv
        pipeline = FinancialDynamicsPipeline()
        pipeline.run(df)

        path = tmp_path / "state.json"
        save_state(pipeline, path)
        restored = load_state(path)

        assert (
            pipeline._stabilization_engine._current_regime
            == restored._stabilization_engine._current_regime
        )
        assert (
            pipeline._stabilization_engine._persistence._confirmed_regime
            == restored._stabilization_engine._persistence._confirmed_regime
        )

    def test_roundtrip_preserves_config(self, tmp_path):
        config = PipelineConfig()
        config.transitions.learning_rate = 0.1
        config.regimes.temperature = 2.5

        pipeline = FinancialDynamicsPipeline(config)
        df = pd.DataFrame({
            "open": [100] * 100,
            "high": [102] * 100,
            "low": [99] * 100,
            "close": [101] * 100,
            "volume": [1000] * 100,
        })
        pipeline.run(df)

        path = tmp_path / "state.json"
        save_state(pipeline, path)
        restored = load_state(path)

        assert restored.config.transitions.learning_rate == 0.1
        assert restored.config.regimes.temperature == 2.5


class TestResumption:
    def test_resumed_pipeline_produces_identical_output(self, synthetic_ohlcv, tmp_path):
        """Run pipeline on data, save state, then process more bars.
        Compare with a pipeline that runs on the full data without interruption."""
        df, _ = synthetic_ohlcv
        split = len(df) // 2
        first_half = df.iloc[:split]
        second_half = df.iloc[split:]

        # Pipeline 1: run full dataset in one shot
        full_pipeline = FinancialDynamicsPipeline()
        full_results = full_pipeline.run(df)

        # Pipeline 2: run first half, save, load, run second half
        partial_pipeline = FinancialDynamicsPipeline()
        partial_pipeline.run(first_half)

        path = tmp_path / "checkpoint.json"
        save_state(partial_pipeline, path)
        resumed = load_state(path)

        resumed_results = []
        for _, row in second_half.iterrows():
            state = resumed.step(row.to_dict())
            regime = state.risk_adjusted_regime
            resumed_results.append(regime.name if regime is not None else None)

        full_second_half = full_results.iloc[split:]
        full_regimes = full_second_half["risk_adjusted_regime"].tolist()

        for resumed_r, full_r in zip(resumed_results, full_regimes):
            if resumed_r is None:
                assert full_r is None or (isinstance(full_r, float) and np.isnan(full_r))
            else:
                assert resumed_r == full_r

    def test_save_fresh_pipeline(self, tmp_path):
        """Saving a pipeline with no data processed should work."""
        pipeline = FinancialDynamicsPipeline()
        path = tmp_path / "fresh.json"
        save_state(pipeline, path)

        restored = load_state(path)
        assert restored._bar_count == 0
        assert restored._transition_engine._prev_regime is None


class TestExtractState:
    def test_state_dict_structure(self, synthetic_ohlcv):
        df, _ = synthetic_ohlcv
        pipeline = FinancialDynamicsPipeline()
        pipeline.run(df)

        state = _extract_state(pipeline)
        assert "version" in state
        assert "bar_count" in state
        assert "config" in state
        assert "feature_engine" in state
        assert "transition_engine" in state
        assert "stabilization_engine" in state
        assert "risk_engine" in state

    def test_transition_matrix_is_serializable(self, synthetic_ohlcv):
        df, _ = synthetic_ohlcv
        pipeline = FinancialDynamicsPipeline()
        pipeline.run(df)

        state = _extract_state(pipeline)
        json_str = json.dumps(state)
        assert json_str  # no serialization error
