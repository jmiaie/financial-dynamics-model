"""Tests for regime forecasting."""

import numpy as np
import pytest

from financial_dynamics.forecasting import (
    RegimeForecast,
    compute_expected_duration,
    compute_stationary_distribution,
    forecast_regimes,
)
from financial_dynamics.pipeline import FinancialDynamicsPipeline
from financial_dynamics.types import Regime, RegimeProbabilities


@pytest.fixture
def learned_tm() -> np.ndarray:
    return np.array([
        [0.7, 0.1, 0.1, 0.1],
        [0.1, 0.6, 0.2, 0.1],
        [0.2, 0.1, 0.5, 0.2],
        [0.1, 0.2, 0.1, 0.6],
    ])


class TestForecastRegimes:
    def test_returns_forecast(self, learned_tm):
        probs = RegimeProbabilities(probs=np.array([0.7, 0.1, 0.1, 0.1]))
        result = forecast_regimes(learned_tm, Regime.CALM_TREND, probs, horizon=5)
        assert isinstance(result, RegimeForecast)
        assert len(result.horizon_probabilities) == 5
        assert len(result.most_likely_path) == 5

    def test_probabilities_sum_to_one(self, learned_tm):
        probs = RegimeProbabilities(probs=np.array([0.7, 0.1, 0.1, 0.1]))
        result = forecast_regimes(learned_tm, Regime.CALM_TREND, probs, horizon=10)
        for step_probs in result.horizon_probabilities:
            assert step_probs.probs.sum() == pytest.approx(1.0, abs=1e-8)

    def test_probabilities_non_negative(self, learned_tm):
        probs = RegimeProbabilities(probs=np.array([0.7, 0.1, 0.1, 0.1]))
        result = forecast_regimes(learned_tm, Regime.CALM_TREND, probs, horizon=10)
        for step_probs in result.horizon_probabilities:
            assert (step_probs.probs >= 0).all()

    def test_converges_toward_stationary(self, learned_tm):
        probs = RegimeProbabilities(probs=np.array([1.0, 0.0, 0.0, 0.0]))
        result = forecast_regimes(learned_tm, Regime.CALM_TREND, probs, horizon=100)
        stationary = compute_stationary_distribution(learned_tm)
        np.testing.assert_array_almost_equal(
            result.horizon_probabilities[-1].probs,
            stationary.probs,
            decimal=2,
        )

    def test_most_likely_path_contains_valid_regimes(self, learned_tm):
        probs = RegimeProbabilities(probs=np.array([0.7, 0.1, 0.1, 0.1]))
        result = forecast_regimes(learned_tm, Regime.CALM_TREND, probs, horizon=5)
        for regime in result.most_likely_path:
            assert isinstance(regime, Regime)

    def test_expected_duration_positive(self, learned_tm):
        probs = RegimeProbabilities(probs=np.array([0.7, 0.1, 0.1, 0.1]))
        result = forecast_regimes(learned_tm, Regime.CALM_TREND, probs)
        assert result.expected_duration > 0


class TestExpectedDuration:
    def test_high_self_transition_gives_long_duration(self, learned_tm):
        duration = compute_expected_duration(learned_tm, Regime.CALM_TREND)
        assert duration == pytest.approx(1.0 / 0.3, rel=1e-6)

    def test_low_self_transition_gives_short_duration(self):
        tm = np.array([
            [0.1, 0.3, 0.3, 0.3],
            [0.3, 0.1, 0.3, 0.3],
            [0.3, 0.3, 0.1, 0.3],
            [0.3, 0.3, 0.3, 0.1],
        ])
        duration = compute_expected_duration(tm, Regime.CALM_TREND)
        assert duration == pytest.approx(1.0 / 0.9, rel=1e-6)

    def test_absorbing_state_gives_inf(self):
        tm = np.eye(4)
        duration = compute_expected_duration(tm, Regime.CALM_TREND)
        assert duration == float("inf")


class TestStationaryDistribution:
    def test_sums_to_one(self, learned_tm):
        stat = compute_stationary_distribution(learned_tm)
        assert stat.probs.sum() == pytest.approx(1.0, abs=1e-8)

    def test_non_negative(self, learned_tm):
        stat = compute_stationary_distribution(learned_tm)
        assert (stat.probs >= 0).all()

    def test_uniform_tm_gives_uniform_stationary(self):
        tm = np.full((4, 4), 0.25)
        stat = compute_stationary_distribution(tm)
        np.testing.assert_array_almost_equal(stat.probs, [0.25, 0.25, 0.25, 0.25])

    def test_is_eigenvector(self, learned_tm):
        stat = compute_stationary_distribution(learned_tm)
        result = stat.probs @ learned_tm
        np.testing.assert_array_almost_equal(result, stat.probs, decimal=6)


class TestPipelineForecast:
    def test_forecast_after_run(self, synthetic_ohlcv):
        df, _ = synthetic_ohlcv
        pipeline = FinancialDynamicsPipeline()
        pipeline.run(df)
        forecast = pipeline.forecast(horizon=5)
        assert forecast is not None
        assert len(forecast.horizon_probabilities) == 5

    def test_forecast_before_warmup_returns_none(self):
        pipeline = FinancialDynamicsPipeline()
        assert pipeline.forecast() is None
