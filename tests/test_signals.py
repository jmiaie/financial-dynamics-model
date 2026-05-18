"""Tests for the signal/alert layer."""

import numpy as np

from financial_dynamics.pipeline import FinancialDynamicsPipeline
from financial_dynamics.signals import Signal, SignalDetector, SignalType
from financial_dynamics.types import BarState, Regime, RegimeProbabilities


def _make_bar_state(
    regime: Regime,
    probs: list[float] | None = None,
) -> BarState:
    """Helper to create a BarState with a given regime and probabilities."""
    state = BarState()
    state.risk_adjusted_regime = regime
    if probs is not None:
        state.posterior_probabilities = RegimeProbabilities(probs=np.array(probs))
    else:
        p = [0.1, 0.1, 0.1, 0.1]
        p[int(regime)] = 0.7
        state.posterior_probabilities = RegimeProbabilities(probs=np.array(p))
    return state


class TestSignalDetector:
    def test_no_signals_on_first_bar(self):
        detector = SignalDetector()
        state = _make_bar_state(Regime.CALM_TREND)
        signals = detector.check(state)
        assert all(s.signal_type != SignalType.REGIME_CHANGE for s in signals)

    def test_regime_change_detected(self):
        detector = SignalDetector()
        detector.check(_make_bar_state(Regime.CALM_TREND))
        signals = detector.check(_make_bar_state(Regime.VOLATILE_TREND))
        changes = [s for s in signals if s.signal_type == SignalType.REGIME_CHANGE]
        assert len(changes) == 1
        assert changes[0].regime == Regime.VOLATILE_TREND
        assert changes[0].previous_regime == Regime.CALM_TREND

    def test_no_regime_change_when_same(self):
        detector = SignalDetector()
        detector.check(_make_bar_state(Regime.CALM_TREND))
        signals = detector.check(_make_bar_state(Regime.CALM_TREND))
        changes = [s for s in signals if s.signal_type == SignalType.REGIME_CHANGE]
        assert len(changes) == 0

    def test_riskoff_warning(self):
        detector = SignalDetector(riskoff_probability_warning=0.25)
        state = _make_bar_state(Regime.VOLATILE_TREND, [0.1, 0.5, 0.1, 0.3])
        signals = detector.check(state)
        warnings = [s for s in signals if s.signal_type == SignalType.RISKOFF_WARNING]
        assert len(warnings) == 1

    def test_no_riskoff_warning_when_already_riskoff(self):
        detector = SignalDetector(riskoff_probability_warning=0.25)
        state = _make_bar_state(Regime.RISK_OFF, [0.1, 0.1, 0.1, 0.7])
        signals = detector.check(state)
        warnings = [s for s in signals if s.signal_type == SignalType.RISKOFF_WARNING]
        assert len(warnings) == 0

    def test_no_riskoff_warning_when_prob_low(self):
        detector = SignalDetector(riskoff_probability_warning=0.5)
        state = _make_bar_state(Regime.VOLATILE_TREND, [0.1, 0.5, 0.2, 0.2])
        signals = detector.check(state)
        warnings = [s for s in signals if s.signal_type == SignalType.RISKOFF_WARNING]
        assert len(warnings) == 0

    def test_confidence_drop_detected(self):
        detector = SignalDetector(confidence_threshold=0.4)
        detector.check(_make_bar_state(Regime.CALM_TREND, [0.6, 0.2, 0.1, 0.1]))
        signals = detector.check(_make_bar_state(Regime.CALM_TREND, [0.3, 0.25, 0.25, 0.2]))
        drops = [s for s in signals if s.signal_type == SignalType.CONFIDENCE_DROP]
        assert len(drops) == 1

    def test_regime_stabilized_after_consecutive(self):
        detector = SignalDetector()
        detector.check(_make_bar_state(Regime.CALM_TREND))
        detector.check(_make_bar_state(Regime.VOLATILE_TREND))
        detector.check(_make_bar_state(Regime.VOLATILE_TREND))
        signals = detector.check(_make_bar_state(Regime.VOLATILE_TREND))
        stabilized = [s for s in signals if s.signal_type == SignalType.REGIME_STABILIZED]
        assert len(stabilized) == 1
        assert stabilized[0].regime == Regime.VOLATILE_TREND

    def test_skips_none_regime_bars(self):
        detector = SignalDetector()
        state = BarState()
        signals = detector.check(state)
        assert signals == []

    def test_reset(self):
        detector = SignalDetector()
        detector.check(_make_bar_state(Regime.CALM_TREND))
        detector.reset()
        assert detector._prev_regime is None
        assert detector._bar_index == 0


class TestSignalIntegration:
    def test_signals_from_pipeline(self, synthetic_ohlcv):
        df, _ = synthetic_ohlcv
        pipeline = FinancialDynamicsPipeline()
        detector = SignalDetector()

        all_signals: list[Signal] = []
        for _, row in df.iterrows():
            state = pipeline.step(row.to_dict())
            signals = detector.check(state)
            all_signals.extend(signals)

        regime_changes = [s for s in all_signals if s.signal_type == SignalType.REGIME_CHANGE]
        assert len(regime_changes) > 0

    def test_signal_bar_indices_are_sequential(self, synthetic_ohlcv):
        df, _ = synthetic_ohlcv
        pipeline = FinancialDynamicsPipeline()
        detector = SignalDetector()

        all_signals: list[Signal] = []
        for _, row in df.iterrows():
            state = pipeline.step(row.to_dict())
            all_signals.extend(detector.check(state))

        indices = [s.bar_index for s in all_signals]
        assert indices == sorted(indices)
