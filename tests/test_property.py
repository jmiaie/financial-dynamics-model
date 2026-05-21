"""Property-based tests using Hypothesis for numerical invariants.

These tests verify that the pipeline maintains mathematical guarantees
(probability sums, stochastic matrix properties, regime validity)
across random inputs, catching edge cases that fixed test data cannot.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from hypothesis.extra.numpy import arrays

from financial_dynamics._utils import safe_renormalize
from financial_dynamics.phase1_regimes.centroid_engine import CentroidEngine
from financial_dynamics.phase2_transitions.transition_engine import MarkovTransitionEngine
from financial_dynamics.pipeline import FinancialDynamicsPipeline
from financial_dynamics.types import (
    NUM_REGIMES,
    BarState,
    FeatureVector,
    Regime,
    RegimeProbabilities,
)

# ---------------------------------------------------------------------------
# Strategy helpers
# ---------------------------------------------------------------------------

finite_floats = st.floats(min_value=-1e6, max_value=1e6, allow_nan=False, allow_infinity=False)
small_floats = st.floats(min_value=-10.0, max_value=10.0, allow_nan=False, allow_infinity=False)

feature_arrays = arrays(
    dtype=np.float64,
    shape=(5,),
    elements=st.floats(min_value=-5.0, max_value=5.0, allow_nan=False, allow_infinity=False),
)

prob_arrays = arrays(
    dtype=np.float64,
    shape=(NUM_REGIMES,),
    elements=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
).filter(lambda a: a.sum() > 1e-12)


def ohlcv_bar(close: float, rng: np.random.Generator) -> dict[str, float]:
    spread = abs(close) * 0.01 + 0.01
    high = close + abs(rng.normal(0, spread))
    low = close - abs(rng.normal(0, spread))
    return {
        "open": close + rng.normal(0, spread * 0.5),
        "high": max(high, close),
        "low": min(low, close),
        "close": close,
        "volume": float(abs(rng.normal(1e6, 1e5))),
    }


@st.composite
def ohlcv_dataframes(draw, min_rows=60, max_rows=200):
    n = draw(st.integers(min_value=min_rows, max_value=max_rows))
    seed = draw(st.integers(min_value=0, max_value=2**32 - 1))
    rng = np.random.default_rng(seed)
    start_price = draw(st.floats(min_value=10.0, max_value=1000.0))
    prices = [start_price]
    for _ in range(n - 1):
        ret = rng.normal(0, 0.02)
        prices.append(max(prices[-1] * (1 + ret), 0.01))
    bars = [ohlcv_bar(p, rng) for p in prices]
    return pd.DataFrame(bars, index=pd.date_range("2024-01-01", periods=n, freq="D"))


# ---------------------------------------------------------------------------
# Centroid engine: softmax always produces valid probabilities
# ---------------------------------------------------------------------------


class TestCentroidProperties:
    @given(fv=feature_arrays)
    @settings(max_examples=200, deadline=None)
    def test_probabilities_sum_to_one(self, fv: np.ndarray):
        engine = CentroidEngine()
        probs = engine.compute_probabilities(fv)
        assert abs(probs.probs.sum() - 1.0) < 1e-9

    @given(fv=feature_arrays)
    @settings(max_examples=200, deadline=None)
    def test_probabilities_all_nonnegative(self, fv: np.ndarray):
        engine = CentroidEngine()
        probs = engine.compute_probabilities(fv)
        assert (probs.probs >= 0).all()

    @given(fv=feature_arrays)
    @settings(max_examples=200, deadline=None)
    def test_dominant_regime_is_valid(self, fv: np.ndarray):
        engine = CentroidEngine()
        probs = engine.compute_probabilities(fv)
        assert 0 <= int(probs.dominant) < NUM_REGIMES


# ---------------------------------------------------------------------------
# safe_renormalize: always returns valid probability vector
# ---------------------------------------------------------------------------


class TestRenormalizeProperties:
    @given(arr=prob_arrays)
    @settings(max_examples=200, deadline=None)
    def test_output_sums_to_one(self, arr: np.ndarray):
        result = safe_renormalize(arr)
        assert abs(result.sum() - 1.0) < 1e-9

    @given(arr=prob_arrays)
    @settings(max_examples=200, deadline=None)
    def test_output_nonnegative(self, arr: np.ndarray):
        result = safe_renormalize(arr)
        assert (result >= 0).all()

    def test_zero_vector_returns_uniform(self):
        result = safe_renormalize(np.zeros(NUM_REGIMES))
        expected = np.full(NUM_REGIMES, 1.0 / NUM_REGIMES)
        np.testing.assert_array_almost_equal(result, expected)


# ---------------------------------------------------------------------------
# Transition matrix: always row-stochastic
# ---------------------------------------------------------------------------


class TestTransitionMatrixProperties:
    @given(
        regimes=st.lists(
            st.sampled_from(list(Regime)),
            min_size=10,
            max_size=50,
        )
    )
    @settings(max_examples=100, deadline=None)
    def test_matrix_is_row_stochastic(self, regimes: list[Regime]):
        engine = MarkovTransitionEngine()
        for regime in regimes:
            probs = np.full(NUM_REGIMES, 0.1)
            probs[int(regime)] = 0.7
            probs = probs / probs.sum()
            state = BarState()
            state.raw_probabilities = RegimeProbabilities(probs=probs)
            engine.update(state)

        tm = engine.get_transition_matrix()
        assert tm.shape == (NUM_REGIMES, NUM_REGIMES)
        for row in tm:
            assert abs(row.sum() - 1.0) < 1e-9
            assert (row >= 0).all()


# ---------------------------------------------------------------------------
# FeatureVector round-trip
# ---------------------------------------------------------------------------


class TestFeatureVectorProperties:
    @given(vals=st.tuples(small_floats, small_floats, small_floats, small_floats, small_floats))
    @settings(max_examples=200, deadline=None)
    def test_roundtrip_to_array_from_array(self, vals):
        fv = FeatureVector(*vals)
        arr = fv.to_array()
        reconstructed = FeatureVector.from_array(arr)
        assert abs(reconstructed.volatility - fv.volatility) < 1e-12
        assert abs(reconstructed.trend_strength - fv.trend_strength) < 1e-12
        assert abs(reconstructed.drawdown_pressure - fv.drawdown_pressure) < 1e-12
        assert abs(reconstructed.correlation_stress - fv.correlation_stress) < 1e-12
        assert abs(reconstructed.shock_intensity - fv.shock_intensity) < 1e-12


# ---------------------------------------------------------------------------
# RegimeProbabilities invariants
# ---------------------------------------------------------------------------


class TestRegimeProbabilitiesProperties:
    @given(arr=prob_arrays)
    @settings(max_examples=200, deadline=None)
    def test_dominant_is_argmax(self, arr: np.ndarray):
        normed = arr / arr.sum()
        rp = RegimeProbabilities(probs=normed)
        assert int(rp.dominant) == int(np.argmax(normed))

    @given(arr=prob_arrays)
    @settings(max_examples=200, deadline=None)
    def test_confidence_is_max(self, arr: np.ndarray):
        normed = arr / arr.sum()
        rp = RegimeProbabilities(probs=normed)
        assert abs(rp.confidence - float(np.max(normed))) < 1e-12


# ---------------------------------------------------------------------------
# Full pipeline: output invariants hold for random OHLCV data
# ---------------------------------------------------------------------------


class TestPipelineProperties:
    @given(df=ohlcv_dataframes(min_rows=80, max_rows=150))
    @settings(
        max_examples=15,
        deadline=None,
        suppress_health_check=[HealthCheck.too_slow],
    )
    def test_output_length_matches_input(self, df: pd.DataFrame):
        pipeline = FinancialDynamicsPipeline()
        result = pipeline.run(df)
        assert len(result) == len(df)

    @given(df=ohlcv_dataframes(min_rows=80, max_rows=150))
    @settings(
        max_examples=15,
        deadline=None,
        suppress_health_check=[HealthCheck.too_slow],
    )
    def test_post_warmup_rows_have_regimes(self, df: pd.DataFrame):
        pipeline = FinancialDynamicsPipeline()
        result = pipeline.run(df)
        warmup = pipeline.warmup_bars
        post_warmup = result.iloc[warmup:]
        non_null = post_warmup["risk_adjusted_regime"].dropna()
        assert len(non_null) > 0

    @given(df=ohlcv_dataframes(min_rows=80, max_rows=150))
    @settings(
        max_examples=15,
        deadline=None,
        suppress_health_check=[HealthCheck.too_slow],
    )
    def test_regime_names_are_valid(self, df: pd.DataFrame):
        pipeline = FinancialDynamicsPipeline()
        result = pipeline.run(df)
        valid_names = {r.name for r in Regime} | {None}
        for val in result["risk_adjusted_regime"]:
            if pd.isna(val):
                continue
            assert val in valid_names

    @given(df=ohlcv_dataframes(min_rows=80, max_rows=150))
    @settings(
        max_examples=15,
        deadline=None,
        suppress_health_check=[HealthCheck.too_slow],
    )
    def test_probability_columns_sum_to_one(self, df: pd.DataFrame):
        pipeline = FinancialDynamicsPipeline()
        result = pipeline.run(df)
        prob_cols = [c for c in result.columns if c.startswith("raw_prob_")]
        if prob_cols:
            prob_rows = result[prob_cols].dropna()
            if len(prob_rows) > 0:
                row_sums = prob_rows.sum(axis=1)
                np.testing.assert_allclose(row_sums, 1.0, atol=1e-6)
