"""Tests for Phase 2: Transition Matrix."""

import numpy as np
import pytest

from financial_dynamics.config import TransitionConfig
from financial_dynamics.phase2_transitions.bayesian_update import (
    bayesian_update,
    compute_posterior,
    counts_to_transition_matrix,
    initialize_count_matrix,
)
from financial_dynamics.phase2_transitions.transition_engine import MarkovTransitionEngine
from financial_dynamics.types import BarState, Regime, RegimeProbabilities


class TestBayesianUpdate:
    def test_initial_counts_uniform(self):
        counts = initialize_count_matrix(prior_strength=10.0)
        assert counts.shape == (4, 4)
        np.testing.assert_array_almost_equal(counts, 2.5)

    def test_transition_matrix_rows_sum_to_one(self):
        counts = initialize_count_matrix(10.0)
        tm = counts_to_transition_matrix(counts)
        for row in tm:
            assert row.sum() == pytest.approx(1.0)

    def test_bayesian_update_increments(self):
        counts = initialize_count_matrix(10.0)
        updated = bayesian_update(counts, prev_state=0, next_state=1, learning_rate=0.05)
        assert updated[0, 1] > counts[0, 1]
        assert updated[0, 1] == pytest.approx(counts[0, 1] + 0.05)

    def test_bayesian_update_does_not_mutate(self):
        counts = initialize_count_matrix(10.0)
        original = counts.copy()
        bayesian_update(counts, 0, 1, 0.05)
        np.testing.assert_array_equal(counts, original)

    def test_posterior_sums_to_one(self):
        raw = np.array([0.5, 0.2, 0.2, 0.1])
        transition = np.array([0.3, 0.4, 0.2, 0.1])
        posterior = compute_posterior(raw, transition)
        assert posterior.sum() == pytest.approx(1.0)

    def test_posterior_nonnegative(self):
        raw = np.array([0.5, 0.2, 0.2, 0.1])
        transition = np.array([0.3, 0.4, 0.2, 0.1])
        posterior = compute_posterior(raw, transition)
        assert (posterior >= 0).all()

    def test_posterior_handles_zero_transition(self):
        raw = np.array([0.5, 0.2, 0.2, 0.1])
        transition = np.array([0.0, 0.0, 0.0, 0.0])
        posterior = compute_posterior(raw, transition)
        assert posterior.sum() == pytest.approx(1.0)


class TestMarkovTransitionEngine:
    def test_update_produces_posterior(self):
        engine = MarkovTransitionEngine()
        state = BarState()
        state.raw_probabilities = RegimeProbabilities(probs=np.array([0.6, 0.2, 0.1, 0.1]))

        engine.update(state)
        assert state.posterior_probabilities is not None
        np.testing.assert_array_almost_equal(
            state.posterior_probabilities.probs,
            state.raw_probabilities.probs,
        )

    def test_transition_matrix_always_valid(self):
        engine = MarkovTransitionEngine()
        for _ in range(50):
            probs = np.random.dirichlet([1, 1, 1, 1])
            state = BarState()
            state.raw_probabilities = RegimeProbabilities(probs=probs)
            engine.update(state)

        tm = engine.get_transition_matrix()
        assert tm.shape == (4, 4)
        for row in tm:
            assert row.sum() == pytest.approx(1.0)
            assert (row >= 0).all()

    def test_learning_converges(self):
        engine = MarkovTransitionEngine(TransitionConfig(learning_rate=0.1))
        # Repeatedly observe 0 -> 1 transition
        for _ in range(100):
            state = BarState()
            state.raw_probabilities = RegimeProbabilities(
                probs=np.array([0.1, 0.7, 0.1, 0.1])
            )
            engine.update(state)

        tm = engine.get_transition_matrix()
        assert tm[0].sum() == pytest.approx(1.0)

    def test_predict_next(self):
        engine = MarkovTransitionEngine()
        pred = engine.predict_next(Regime.CALM_TREND)
        assert pred.probs.sum() == pytest.approx(1.0)

    def test_reset(self):
        engine = MarkovTransitionEngine()
        state = BarState()
        state.raw_probabilities = RegimeProbabilities(probs=np.array([0.6, 0.2, 0.1, 0.1]))
        engine.update(state)
        engine.reset()
        assert engine._prev_regime is None
        tm = engine.get_transition_matrix()
        assert tm[0, 0] == pytest.approx(0.25)
