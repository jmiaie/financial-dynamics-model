"""Tests for Phase 4: Risk Conditioning."""

import numpy as np
import pytest

from financial_dynamics.config import RiskConfig
from financial_dynamics.phase4_risk.chop_suppression import ChopDominanceSuppressor
from financial_dynamics.phase4_risk.overextension import OverextensionRebalancer
from financial_dynamics.phase4_risk.risk_overlay import RiskConditioningEngine
from financial_dynamics.types import BarState, FeatureVector, Regime, RegimeProbabilities


class TestOverextension:
    def test_no_suppression_short_history(self):
        rebal = OverextensionRebalancer(window=50, decay=0.02)
        probs = np.array([0.7, 0.1, 0.1, 0.1])
        result = rebal.compute_suppression(probs)
        np.testing.assert_array_equal(result, probs)

    def test_suppression_after_dominance(self):
        rebal = OverextensionRebalancer(window=50, decay=0.02)
        for _ in range(60):
            rebal.record(Regime.CALM_TREND)

        probs = np.array([0.7, 0.1, 0.1, 0.1])
        result = rebal.compute_suppression(probs)
        assert result.sum() == pytest.approx(1.0)
        # CALM_TREND probability should be reduced
        assert result[0] < probs[0]

    def test_output_sums_to_one(self):
        rebal = OverextensionRebalancer(window=20, decay=0.05)
        for _ in range(30):
            rebal.record(Regime.CHOP)
        probs = np.array([0.2, 0.2, 0.5, 0.1])
        result = rebal.compute_suppression(probs)
        assert result.sum() == pytest.approx(1.0)

    def test_reset(self):
        rebal = OverextensionRebalancer(window=20)
        for _ in range(25):
            rebal.record(Regime.CALM_TREND)
        rebal.reset()
        assert len(rebal._history) == 0


class TestChopSuppression:
    def test_no_penalty_short_history(self):
        cs = ChopDominanceSuppressor(window=30, penalty=0.1)
        probs = np.array([0.3, 0.1, 0.5, 0.1])
        result = cs.compute_penalty(probs)
        np.testing.assert_array_equal(result, probs)

    def test_penalty_on_calm_chop_loop(self):
        cs = ChopDominanceSuppressor(window=30, penalty=0.1)
        for i in range(35):
            cs.record(Regime.CALM_TREND if i % 2 == 0 else Regime.CHOP)

        probs = np.array([0.3, 0.1, 0.5, 0.1])
        result = cs.compute_penalty(probs)
        assert result.sum() == pytest.approx(1.0)
        # CHOP and CALM should be penalized
        assert result[int(Regime.CHOP)] < probs[int(Regime.CHOP)]

    def test_no_penalty_with_diverse_regimes(self):
        cs = ChopDominanceSuppressor(window=30, penalty=0.1)
        regimes = [Regime.CALM_TREND, Regime.VOLATILE_TREND, Regime.CHOP, Regime.RISK_OFF]
        for i in range(35):
            cs.record(regimes[i % 4])

        probs = np.array([0.25, 0.25, 0.25, 0.25])
        result = cs.compute_penalty(probs)
        np.testing.assert_array_almost_equal(result, probs)


class TestRiskConditioningEngine:
    def test_produces_final_regime(self):
        engine = RiskConditioningEngine()
        state = BarState()
        state.features = FeatureVector(0.1, 0.8, 0.05, 0.1, 0.1)
        state.stabilized_regime = Regime.CALM_TREND
        state.posterior_probabilities = RegimeProbabilities(probs=np.array([0.7, 0.1, 0.1, 0.1]))
        engine.update(state)
        assert state.risk_adjusted_regime is not None
        assert isinstance(state.risk_adjusted_regime, Regime)

    def test_skips_if_not_stabilized(self):
        engine = RiskConditioningEngine()
        state = BarState()
        engine.update(state)
        assert state.risk_adjusted_regime is None

    def test_riskoff_not_confirmed_without_stressors(self):
        engine = RiskConditioningEngine()
        state = BarState()
        state.features = FeatureVector(0.1, 0.2, 0.1, 0.1, 0.1)  # Low stress
        state.stabilized_regime = Regime.RISK_OFF
        state.posterior_probabilities = RegimeProbabilities(probs=np.array([0.1, 0.1, 0.1, 0.7]))
        engine.update(state)
        assert state.risk_overlays.get("riskoff_confirmed") is False

    def test_riskoff_confirmed_with_stressors(self):
        config = RiskConfig(riskoff_confirmation_count=3)
        engine = RiskConditioningEngine(config)
        state = BarState()
        state.features = FeatureVector(0.9, 0.1, 0.8, 0.9, 0.9)  # High stress everywhere
        state.stabilized_regime = Regime.RISK_OFF
        state.posterior_probabilities = RegimeProbabilities(
            probs=np.array([0.05, 0.05, 0.05, 0.85])
        )
        engine.update(state)
        assert state.risk_overlays.get("riskoff_confirmed") is True
        assert state.risk_adjusted_regime == Regime.RISK_OFF

    def test_reset(self):
        engine = RiskConditioningEngine()
        state = BarState()
        state.features = FeatureVector(0.5, 0.5, 0.5, 0.5, 0.5)
        state.stabilized_regime = Regime.CALM_TREND
        state.posterior_probabilities = RegimeProbabilities(probs=np.array([0.7, 0.1, 0.1, 0.1]))
        engine.update(state)
        engine.reset()
        assert len(engine._overextension._history) == 0
        assert len(engine._chop_suppressor._history) == 0
