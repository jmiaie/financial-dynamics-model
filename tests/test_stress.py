"""Pressure, shock, and stress tests -- extreme inputs, edge cases, numerical stability."""

import numpy as np
import pandas as pd
import pytest

from financial_dynamics.config import FeatureConfig, PipelineConfig, RegimeConfig
from financial_dynamics.phase0_features.normalizer import FeatureNormalizer
from financial_dynamics.phase1_regimes.centroid_engine import CentroidEngine
from financial_dynamics.phase2_transitions.bayesian_update import (
    compute_posterior,
)
from financial_dynamics.phase3_stabilization.hysteresis import HysteresisFilter
from financial_dynamics.phase3_stabilization.majority_vote import MajorityVoteFilter
from financial_dynamics.phase3_stabilization.persistence import PersistenceFilter
from financial_dynamics.phase4_risk._utils import safe_renormalize
from financial_dynamics.phase4_risk.chop_suppression import ChopDominanceSuppressor
from financial_dynamics.phase4_risk.overextension import OverextensionRebalancer
from financial_dynamics.pipeline import FinancialDynamicsPipeline
from financial_dynamics.types import BarState, Regime, RegimeProbabilities


class TestNumericalStability:
    def test_softmax_with_very_large_distances(self):
        """Centroid engine should not overflow with extreme feature vectors."""
        engine = CentroidEngine()
        x = np.array([1e6, 1e6, 1e6, 1e6, 1e6])
        probs = engine.compute_probabilities(x)
        assert np.isfinite(probs.probs).all()
        assert probs.probs.sum() == pytest.approx(1.0, abs=1e-6)

    def test_softmax_with_very_small_distances(self):
        """All centroids equidistant should produce near-uniform distribution."""
        engine = CentroidEngine()
        x = np.array([0.5, 0.5, 0.5, 0.5, 0.5])
        probs = engine.compute_probabilities(x)
        assert np.isfinite(probs.probs).all()
        assert probs.probs.sum() == pytest.approx(1.0, abs=1e-6)

    def test_softmax_with_negative_features(self):
        """Negative feature values should not crash the engine."""
        engine = CentroidEngine()
        x = np.array([-0.5, -1.0, -0.3, -2.0, -0.1])
        probs = engine.compute_probabilities(x)
        assert np.isfinite(probs.probs).all()
        assert (probs.probs >= 0).all()
        assert probs.probs.sum() == pytest.approx(1.0, abs=1e-6)

    def test_softmax_with_zero_temperature_like(self):
        """Very low temperature should produce a near-deterministic distribution."""
        config = RegimeConfig(temperature=0.01)
        engine = CentroidEngine(config)
        x = engine.centroids[0].copy()
        probs = engine.compute_probabilities(x)
        assert np.isfinite(probs.probs).all()
        assert probs.confidence > 0.99

    def test_softmax_with_very_high_temperature(self):
        """Very high temperature should produce near-uniform distribution."""
        config = RegimeConfig(temperature=100.0)
        engine = CentroidEngine(config)
        x = engine.centroids[0].copy()
        probs = engine.compute_probabilities(x)
        assert np.isfinite(probs.probs).all()
        for p in probs.probs:
            assert 0.1 < p < 0.5

    def test_posterior_with_all_zeros(self):
        """Posterior computation with zero inputs should not crash."""
        raw = np.array([0.0, 0.0, 0.0, 0.0])
        transition = np.array([0.0, 0.0, 0.0, 0.0])
        posterior = compute_posterior(raw, transition)
        assert np.isfinite(posterior).all()
        assert posterior.sum() == pytest.approx(1.0, abs=1e-6)

    def test_posterior_with_tiny_values(self):
        """Posterior computation with very small values should be stable."""
        raw = np.array([1e-30, 1e-30, 1e-30, 1e-30])
        transition = np.array([1e-30, 1e-30, 1e-30, 1e-30])
        posterior = compute_posterior(raw, transition)
        assert np.isfinite(posterior).all()
        assert posterior.sum() == pytest.approx(1.0, abs=1e-6)

    def test_safe_renormalize_zero_vector(self):
        """Renormalizing a zero vector should return uniform distribution."""
        result = safe_renormalize(np.array([0.0, 0.0, 0.0, 0.0]))
        assert result.sum() == pytest.approx(1.0)
        np.testing.assert_array_almost_equal(result, [0.25, 0.25, 0.25, 0.25])

    def test_safe_renormalize_near_zero(self):
        """Renormalizing near-zero values should be stable."""
        result = safe_renormalize(np.array([1e-15, 1e-15, 1e-15, 1e-15]))
        assert np.isfinite(result).all()
        assert result.sum() == pytest.approx(1.0, abs=1e-6)

    def test_normalizer_constant_input(self):
        """Normalizer should handle constant (zero-variance) input gracefully."""
        config = FeatureConfig()
        norm = FeatureNormalizer(config)
        constant = np.array([0.5, 0.5, 0.5, 0.5, 0.5])
        for _ in range(50):
            result = norm.update(constant)
        assert np.isfinite(result).all()

    def test_normalizer_extreme_outlier(self):
        """Normalizer should handle extreme outliers without crashing."""
        config = FeatureConfig()
        norm = FeatureNormalizer(config)
        for _ in range(30):
            norm.update(np.random.rand(5) * 0.01)
        result = norm.update(np.array([100.0, 100.0, 100.0, 100.0, 100.0]))
        assert np.isfinite(result).all()


class TestPressure:
    def test_rapid_regime_alternation(self):
        """Pipeline should handle rapid alternation between regimes without crashing."""
        pipeline = FinancialDynamicsPipeline()
        rng = np.random.default_rng(99)

        for i in range(300):
            if i % 2 == 0:
                close = 100 + rng.normal(0, 0.1)
            else:
                close = 50 + rng.normal(0, 5.0)
            bar = {
                "open": close - 0.1,
                "high": close + 1,
                "low": close - 1,
                "close": close,
                "volume": 5000,
            }
            state = pipeline.step(bar)
            if state.raw_probabilities is not None:
                assert np.isfinite(state.raw_probabilities.probs).all()

    def test_hysteresis_flood(self):
        """Hysteresis should remain stable under rapid near-threshold inputs."""
        hyst = HysteresisFilter(threshold=0.15)
        for _ in range(1000):
            # Probabilities that constantly hover near the flip threshold
            probs = RegimeProbabilities(probs=np.array([0.35, 0.30, 0.20, 0.15]))
            result = hyst.apply(Regime.VOLATILE_TREND, probs)
            assert isinstance(result, Regime)

    def test_persistence_rapid_candidate_changes(self):
        """Persistence filter should handle rapidly changing candidates."""
        pf = PersistenceFilter(min_bars=5)
        pf.apply(Regime.CALM_TREND)
        for i in range(200):
            regime = Regime(i % 4)
            result = pf.apply(regime)
            assert isinstance(result, Regime)

    def test_majority_vote_all_different(self):
        """Majority vote with constantly changing input should still return a valid Regime."""
        mv = MajorityVoteFilter(window=10)
        for i in range(100):
            result = mv.apply(Regime(i % 4))
            assert isinstance(result, Regime)

    def test_transition_matrix_stays_valid_under_pressure(self):
        """After many rapid updates, transition matrix should still be row-stochastic."""
        from financial_dynamics.config import TransitionConfig
        from financial_dynamics.phase2_transitions.transition_engine import MarkovTransitionEngine

        engine = MarkovTransitionEngine(TransitionConfig(learning_rate=1.0))
        for _i in range(10000):
            state = BarState()
            probs = np.random.dirichlet([0.1, 0.1, 0.1, 0.1])
            state.raw_probabilities = RegimeProbabilities(probs=probs)
            engine.update(state)

        tm = engine.get_transition_matrix()
        for row in tm:
            assert row.sum() == pytest.approx(1.0, abs=1e-10)
            assert (row >= 0).all()
            assert np.isfinite(row).all()


class TestShock:
    def test_flash_crash(self):
        """Pipeline should handle a sudden 50% price drop gracefully."""
        pipeline = FinancialDynamicsPipeline()

        # 80 bars of calm uptrend
        price = 100.0
        for _ in range(80):
            price *= 1.001
            bar = {
                "open": price - 0.05,
                "high": price + 0.1,
                "low": price - 0.1,
                "close": price,
                "volume": 2000,
            }
            pipeline.step(bar)

        # Flash crash: 50% drop in one bar
        crash_price = price * 0.5
        bar = {
            "open": price,
            "high": price,
            "low": crash_price * 0.95,
            "close": crash_price,
            "volume": 100000,
        }
        state = pipeline.step(bar)

        if state.features is not None:
            assert np.isfinite(state.features.to_array()).all()
            assert state.features.shock_intensity > 0

    def test_price_goes_to_near_zero(self):
        """Pipeline should handle price approaching zero."""
        pipeline = FinancialDynamicsPipeline()

        price = 100.0
        for _i in range(200):
            price = max(price * 0.97, 0.001)
            bar = {
                "open": price * 1.01,
                "high": price * 1.02,
                "low": price * 0.98,
                "close": price,
                "volume": 5000,
            }
            state = pipeline.step(bar)
            if state.raw_probabilities is not None:
                assert np.isfinite(state.raw_probabilities.probs).all()

    def test_price_spike_up(self):
        """Pipeline should handle a sudden 10x price spike."""
        pipeline = FinancialDynamicsPipeline()

        price = 100.0
        for _ in range(80):
            price *= 1.001
            bar = {
                "open": price - 0.05,
                "high": price + 0.1,
                "low": price - 0.1,
                "close": price,
                "volume": 2000,
            }
            pipeline.step(bar)

        # 10x spike
        spike_price = price * 10
        bar = {
            "open": price,
            "high": spike_price * 1.1,
            "low": price * 0.9,
            "close": spike_price,
            "volume": 200000,
        }
        state = pipeline.step(bar)

        if state.features is not None:
            assert np.isfinite(state.features.to_array()).all()

    def test_constant_price_no_movement(self):
        """Pipeline should handle flat price (zero returns) without division errors."""
        pipeline = FinancialDynamicsPipeline()

        for _ in range(150):
            bar = {"open": 100, "high": 100, "low": 100, "close": 100, "volume": 1000}
            state = pipeline.step(bar)
            if state.raw_probabilities is not None:
                assert np.isfinite(state.raw_probabilities.probs).all()
                assert state.raw_probabilities.probs.sum() == pytest.approx(1.0, abs=1e-6)

    def test_alternating_extreme_returns(self):
        """Pipeline should handle alternating +50%/-50% returns."""
        pipeline = FinancialDynamicsPipeline()

        price = 100.0
        for i in range(200):
            if i % 2 == 0:
                price *= 1.5
            else:
                price *= 0.5
            bar = {
                "open": price * 0.9,
                "high": price * 1.1,
                "low": price * 0.85,
                "close": price,
                "volume": 10000,
            }
            state = pipeline.step(bar)
            if state.raw_probabilities is not None:
                assert np.isfinite(state.raw_probabilities.probs).all()


class TestStress:
    def test_extremely_long_calm_period(self):
        """Pipeline should handle 1000 bars of identical calm market."""
        pipeline = FinancialDynamicsPipeline()
        rng = np.random.default_rng(55)

        for _ in range(1000):
            price = 100 + rng.normal(0, 0.01)
            bar = {
                "open": price,
                "high": price + 0.01,
                "low": price - 0.01,
                "close": price,
                "volume": 1000,
            }
            state = pipeline.step(bar)

        # Should have converged on a regime
        assert state.risk_adjusted_regime is not None
        report = pipeline.get_state_report()
        tm = report["transition_matrix"]
        for row in tm:
            assert row.sum() == pytest.approx(1.0, abs=1e-10)

    def test_overextension_extreme_dominance(self):
        """Overextension rebalancer with 100% single-regime history."""
        rebal = OverextensionRebalancer(window=50, decay=0.05)
        for _ in range(200):
            rebal.record(Regime.CALM_TREND)

        probs = np.array([0.9, 0.03, 0.04, 0.03])
        result = rebal.compute_suppression(probs)
        assert np.isfinite(result).all()
        assert result.sum() == pytest.approx(1.0)
        # CALM_TREND should be significantly suppressed
        assert result[0] < probs[0]

    def test_chop_suppression_100_percent_loop(self):
        """Chop suppressor with 100% Calm-Chop alternation."""
        cs = ChopDominanceSuppressor(window=30, penalty=0.1)
        for i in range(100):
            cs.record(Regime.CALM_TREND if i % 2 == 0 else Regime.CHOP)

        probs = np.array([0.4, 0.05, 0.5, 0.05])
        result = cs.compute_penalty(probs)
        assert np.isfinite(result).all()
        assert result.sum() == pytest.approx(1.0)
        assert result[int(Regime.CHOP)] < probs[int(Regime.CHOP)]

    def test_all_extreme_config_values(self):
        """Pipeline should handle extreme (but valid) configuration values."""
        config = PipelineConfig()
        config.regimes.temperature = 0.001
        config.transitions.learning_rate = 10.0
        config.stabilization.hysteresis_threshold = 0.99
        config.stabilization.min_persistence_bars = 1
        config.stabilization.majority_vote_window = 2

        pipeline = FinancialDynamicsPipeline(config)
        rng = np.random.default_rng(77)

        for _ in range(200):
            price = 100 + rng.normal(0, 2)
            bar = {
                "open": price - 0.5,
                "high": price + 1,
                "low": price - 1,
                "close": price,
                "volume": 5000,
            }
            state = pipeline.step(bar)
            if state.raw_probabilities is not None:
                assert np.isfinite(state.raw_probabilities.probs).all()
                assert state.raw_probabilities.probs.sum() == pytest.approx(1.0, abs=1e-6)

    def test_single_bar_input(self):
        """Pipeline should handle a single bar without crashing."""
        pipeline = FinancialDynamicsPipeline()
        bar = {"open": 100, "high": 101, "low": 99, "close": 100.5, "volume": 1000}
        state = pipeline.step(bar)
        assert state.features is None  # Not enough warmup
        assert state.risk_adjusted_regime is None

    def test_full_pipeline_invariants_on_large_run(self):
        """Verify all invariants hold across a large pipeline run."""
        rng = np.random.default_rng(123)
        n = 2000
        prices = 100 + np.cumsum(rng.normal(0, 0.5, n))
        prices = np.maximum(prices, 1.0)

        df = pd.DataFrame(
            {
                "open": prices - 0.1,
                "high": prices + abs(rng.normal(0, 0.3, n)),
                "low": prices - abs(rng.normal(0, 0.3, n)),
                "close": prices,
                "volume": rng.integers(1000, 10000, n),
            }
        )

        pipeline = FinancialDynamicsPipeline()
        results = pipeline.run(df)

        # Check all probability invariants
        raw_cols = [f"raw_prob_{r.name}" for r in Regime]
        post_cols = [f"post_prob_{r.name}" for r in Regime]

        for cols in [raw_cols, post_cols]:
            valid = results.dropna(subset=cols)
            for _, row in valid.iterrows():
                probs = np.array([row[c] for c in cols])
                assert (probs >= 0).all(), f"Negative probability: {probs}"
                assert np.isfinite(probs).all(), f"Non-finite probability: {probs}"
                assert probs.sum() == pytest.approx(1.0, abs=1e-5), (
                    f"Probs don't sum to 1: {probs.sum()}"
                )

        # Check transition matrix
        tm = pipeline.get_state_report()["transition_matrix"]
        assert tm.shape == (4, 4)
        for row in tm:
            assert (row >= 0).all()
            assert np.isfinite(row).all()
            assert row.sum() == pytest.approx(1.0, abs=1e-10)

        # Check all regimes are valid
        valid_regimes = results.dropna(subset=["risk_adjusted_regime"])
        for regime_name in valid_regimes["risk_adjusted_regime"]:
            assert regime_name in [r.name for r in Regime]
