"""Phase 3: Stabilization Engine -- composes hysteresis, persistence, and majority vote."""

from __future__ import annotations

from financial_dynamics.config import StabilizationConfig
from financial_dynamics.types import BarState, Regime
from financial_dynamics.phase3_stabilization.hysteresis import HysteresisFilter
from financial_dynamics.phase3_stabilization.persistence import PersistenceFilter
from financial_dynamics.phase3_stabilization.majority_vote import MajorityVoteFilter


class StabilizationEngine:
    """Phase 3: Applies temporal stabilization filters in sequence.

    Pipeline: posterior_probabilities -> hysteresis -> persistence -> majority_vote
    """

    def __init__(self, config: StabilizationConfig | None = None) -> None:
        self.config = config or StabilizationConfig()
        self._hysteresis = HysteresisFilter(self.config.hysteresis_threshold)
        self._persistence = PersistenceFilter(self.config.min_persistence_bars)
        self._majority = MajorityVoteFilter(self.config.majority_vote_window)
        self._current_regime: Regime = Regime.CALM_TREND

    def update(self, bar_state: BarState) -> BarState:
        """Apply stabilization filters to posterior probabilities.

        Reads bar_state.posterior_probabilities (or raw_probabilities as fallback).
        Writes bar_state.stabilized_regime.
        """
        probs = bar_state.posterior_probabilities or bar_state.raw_probabilities
        if probs is None:
            return bar_state

        after_hysteresis = self._hysteresis.apply(self._current_regime, probs)
        after_persistence = self._persistence.apply(after_hysteresis)
        after_majority = self._majority.apply(after_persistence)

        self._current_regime = after_majority
        bar_state.stabilized_regime = after_majority
        return bar_state

    def reset(self) -> None:
        self._persistence.reset()
        self._majority.reset()
        self._current_regime = Regime.CALM_TREND
