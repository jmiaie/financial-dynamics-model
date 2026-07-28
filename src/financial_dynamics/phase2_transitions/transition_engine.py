"""Phase 2: Markov Transition Engine -- maintains and updates the transition matrix."""

from __future__ import annotations

import numpy as np

from financial_dynamics.config import TransitionConfig
from financial_dynamics.phase2_transitions.bayesian_update import (
    bayesian_update,
    compute_posterior,
    counts_to_transition_matrix,
    initialize_count_matrix,
)
from financial_dynamics.types import BarState, Regime, RegimeProbabilities


class MarkovTransitionEngine:
    """Phase 2: Maintains a Markov transition probability matrix.

    Combines centroid-based probabilities with learned transition structure
    to produce posterior regime probabilities.
    """

    def __init__(self, config: TransitionConfig | None = None):
        self.config = config or TransitionConfig()
        self.counts = initialize_count_matrix(self.config.prior_strength)
        self._transition_matrix = counts_to_transition_matrix(self.counts)
        self._prev_regime: Regime | None = None

    def update(self, bar_state: BarState) -> BarState:
        """Process a bar through the transition engine.

        Reads bar_state.raw_probabilities, updates the transition matrix,
        computes posterior probabilities.
        """
        if bar_state.raw_probabilities is None:
            return bar_state

        current_dominant = bar_state.raw_probabilities.dominant

        if self._prev_regime is not None:
            self.counts = bayesian_update(
                self.counts,
                int(self._prev_regime),
                int(current_dominant),
                self.config.learning_rate,
            )
            self._transition_matrix = counts_to_transition_matrix(self.counts)

        # Compute posterior probabilities
        if self._prev_regime is not None:
            transition_row = self._transition_matrix[int(self._prev_regime)]
            posterior = compute_posterior(
                bar_state.raw_probabilities.probs,
                transition_row,
            )
        else:
            posterior = bar_state.raw_probabilities.probs.copy()

        bar_state.transition_matrix = self._transition_matrix.copy()
        bar_state.posterior_probabilities = RegimeProbabilities(probs=posterior)

        self._prev_regime = current_dominant
        return bar_state

    def get_transition_matrix(self) -> np.ndarray:
        return self._transition_matrix.copy()

    def predict_next(self, current_regime: Regime) -> RegimeProbabilities:
        """One-step-ahead prediction from the transition matrix."""
        row = self._transition_matrix[int(current_regime)]
        return RegimeProbabilities(probs=row.copy())

    def reset(self) -> None:
        self.counts = initialize_count_matrix(self.config.prior_strength)
        self._transition_matrix = counts_to_transition_matrix(self.counts)
        self._prev_regime = None
