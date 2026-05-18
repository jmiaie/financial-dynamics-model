"""Tests for Phase 3: Stabilization."""

import numpy as np

from financial_dynamics.phase3_stabilization.hysteresis import HysteresisFilter
from financial_dynamics.phase3_stabilization.majority_vote import MajorityVoteFilter
from financial_dynamics.phase3_stabilization.persistence import PersistenceFilter
from financial_dynamics.phase3_stabilization.stabilizer import StabilizationEngine
from financial_dynamics.types import BarState, Regime, RegimeProbabilities


class TestHysteresis:
    def test_no_flip_below_threshold(self):
        hyst = HysteresisFilter(threshold=0.15)
        probs = RegimeProbabilities(probs=np.array([0.35, 0.30, 0.20, 0.15]))
        result = hyst.apply(Regime.VOLATILE_TREND, probs)
        # Gap between CALM(0.35) and VOL(0.30) is only 0.05 < 0.15
        assert result == Regime.VOLATILE_TREND

    def test_flip_above_threshold(self):
        hyst = HysteresisFilter(threshold=0.15)
        probs = RegimeProbabilities(probs=np.array([0.6, 0.1, 0.2, 0.1]))
        result = hyst.apply(Regime.VOLATILE_TREND, probs)
        # Gap between CALM(0.6) and VOL(0.1) is 0.5 > 0.15
        assert result == Regime.CALM_TREND

    def test_same_regime_stays(self):
        hyst = HysteresisFilter(threshold=0.15)
        probs = RegimeProbabilities(probs=np.array([0.1, 0.6, 0.2, 0.1]))
        result = hyst.apply(Regime.VOLATILE_TREND, probs)
        assert result == Regime.VOLATILE_TREND


class TestPersistence:
    def test_immediate_first_assignment(self):
        pf = PersistenceFilter(min_bars=3)
        result = pf.apply(Regime.CALM_TREND)
        assert result == Regime.CALM_TREND

    def test_no_flip_before_min_bars(self):
        pf = PersistenceFilter(min_bars=3)
        pf.apply(Regime.CALM_TREND)
        assert pf.apply(Regime.CHOP) == Regime.CALM_TREND
        assert pf.apply(Regime.CHOP) == Regime.CALM_TREND

    def test_flip_after_min_bars(self):
        pf = PersistenceFilter(min_bars=3)
        pf.apply(Regime.CALM_TREND)
        pf.apply(Regime.CHOP)
        pf.apply(Regime.CHOP)
        result = pf.apply(Regime.CHOP)
        assert result == Regime.CHOP

    def test_reset_clears_count(self):
        pf = PersistenceFilter(min_bars=3)
        pf.apply(Regime.CALM_TREND)
        pf.apply(Regime.CHOP)
        pf.apply(Regime.CHOP)
        pf.reset()
        result = pf.apply(Regime.RISK_OFF)
        assert result == Regime.RISK_OFF  # first assignment after reset

    def test_interrupted_candidate_resets(self):
        pf = PersistenceFilter(min_bars=3)
        pf.apply(Regime.CALM_TREND)
        pf.apply(Regime.CHOP)
        pf.apply(Regime.CHOP)
        pf.apply(Regime.VOLATILE_TREND)  # interrupt
        pf.apply(Regime.CHOP)
        assert pf.apply(Regime.CHOP) == Regime.CALM_TREND  # still need 3 consecutive


class TestMajorityVote:
    def test_unanimous_window(self):
        mv = MajorityVoteFilter(window=5)
        for _ in range(5):
            result = mv.apply(Regime.CALM_TREND)
        assert result == Regime.CALM_TREND

    def test_majority_wins(self):
        mv = MajorityVoteFilter(window=5)
        mv.apply(Regime.CALM_TREND)
        mv.apply(Regime.CALM_TREND)
        mv.apply(Regime.CALM_TREND)
        mv.apply(Regime.CHOP)
        result = mv.apply(Regime.CHOP)
        assert result == Regime.CALM_TREND

    def test_tie_breaks_to_most_recent(self):
        mv = MajorityVoteFilter(window=4)
        mv.apply(Regime.CALM_TREND)
        mv.apply(Regime.CALM_TREND)
        mv.apply(Regime.CHOP)
        result = mv.apply(Regime.CHOP)
        # Tie: 2 CALM, 2 CHOP. Most recent is CHOP
        assert result == Regime.CHOP

    def test_reset(self):
        mv = MajorityVoteFilter(window=5)
        for _ in range(5):
            mv.apply(Regime.CALM_TREND)
        mv.reset()
        assert len(mv._buffer) == 0


class TestStabilizationEngine:
    def test_produces_stabilized_regime(self):
        engine = StabilizationEngine()
        state = BarState()
        state.posterior_probabilities = RegimeProbabilities(
            probs=np.array([0.7, 0.1, 0.1, 0.1])
        )
        engine.update(state)
        assert state.stabilized_regime is not None
        assert isinstance(state.stabilized_regime, Regime)

    def test_skips_if_no_probs(self):
        engine = StabilizationEngine()
        state = BarState()
        engine.update(state)
        assert state.stabilized_regime is None

    def test_stable_input_stable_output(self):
        engine = StabilizationEngine()
        regimes = []
        for _ in range(20):
            state = BarState()
            state.posterior_probabilities = RegimeProbabilities(
                probs=np.array([0.7, 0.1, 0.1, 0.1])
            )
            engine.update(state)
            regimes.append(state.stabilized_regime)

        # After warmup, should consistently be CALM_TREND
        assert all(r == Regime.CALM_TREND for r in regimes[-10:])
