"""Signal detection from pipeline state changes."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto

from financial_dynamics.types import BarState, Regime, RegimeProbabilities


class SignalType(Enum):
    REGIME_CHANGE = auto()
    RISKOFF_WARNING = auto()
    CONFIDENCE_DROP = auto()
    REGIME_STABILIZED = auto()


@dataclass
class Signal:
    signal_type: SignalType
    regime: Regime
    previous_regime: Regime | None
    confidence: float
    message: str
    bar_index: int


class SignalDetector:
    """Detects actionable signals from pipeline state transitions.

    Tracks regime changes, risk-off warnings, and confidence degradation.
    """

    def __init__(
        self,
        confidence_threshold: float = 0.4,
        riskoff_probability_warning: float = 0.3,
    ):
        self.confidence_threshold = confidence_threshold
        self.riskoff_probability_warning = riskoff_probability_warning
        self._prev_regime: Regime | None = None
        self._prev_confidence: float = 0.0
        self._bar_index: int = 0
        self._pending_regime: Regime | None = None
        self._pending_count: int = 0
        self._confirmed_regime: Regime | None = None

    def check(self, bar_state: BarState) -> list[Signal]:
        """Check a pipeline output for actionable signals.

        Returns a (possibly empty) list of signals detected on this bar.
        """
        signals: list[Signal] = []
        self._bar_index += 1

        regime = bar_state.risk_adjusted_regime
        if regime is None:
            return signals

        probs = bar_state.posterior_probabilities or bar_state.raw_probabilities
        confidence = probs.confidence if probs else 0.0

        if self._prev_regime is not None and regime != self._prev_regime:
            signals.append(Signal(
                signal_type=SignalType.REGIME_CHANGE,
                regime=regime,
                previous_regime=self._prev_regime,
                confidence=confidence,
                message=f"Regime changed: {self._prev_regime.name} -> {regime.name}",
                bar_index=self._bar_index,
            ))

        if probs is not None:
            riskoff_prob = probs[Regime.RISK_OFF]
            if (regime != Regime.RISK_OFF
                    and riskoff_prob > self.riskoff_probability_warning):
                signals.append(Signal(
                    signal_type=SignalType.RISKOFF_WARNING,
                    regime=regime,
                    previous_regime=self._prev_regime,
                    confidence=riskoff_prob,
                    message=(
                        f"Risk-Off probability elevated: "
                        f"{riskoff_prob:.1%} (threshold {self.riskoff_probability_warning:.1%})"
                    ),
                    bar_index=self._bar_index,
                ))

        if (self._prev_confidence > self.confidence_threshold
                and confidence < self.confidence_threshold):
            signals.append(Signal(
                signal_type=SignalType.CONFIDENCE_DROP,
                regime=regime,
                previous_regime=self._prev_regime,
                confidence=confidence,
                message=(
                    f"Confidence dropped below threshold: "
                    f"{self._prev_confidence:.1%} -> {confidence:.1%}"
                ),
                bar_index=self._bar_index,
            ))

        if self._pending_regime != regime:
            self._pending_regime = regime
            self._pending_count = 1
        else:
            self._pending_count += 1
            if self._pending_count == 3 and regime != self._confirmed_regime:
                signals.append(Signal(
                    signal_type=SignalType.REGIME_STABILIZED,
                    regime=regime,
                    previous_regime=self._confirmed_regime,
                    confidence=confidence,
                    message=f"Regime {regime.name} stabilized (3 consecutive bars)",
                    bar_index=self._bar_index,
                ))
                self._confirmed_regime = regime

        self._prev_regime = regime
        self._prev_confidence = confidence
        return signals

    def reset(self) -> None:
        self._prev_regime = None
        self._prev_confidence = 0.0
        self._bar_index = 0
        self._pending_regime = None
        self._pending_count = 0
        self._confirmed_regime = None
