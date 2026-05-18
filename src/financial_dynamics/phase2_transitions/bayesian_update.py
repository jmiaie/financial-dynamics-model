"""Bayesian update logic for the Markov transition matrix."""

import numpy as np

from financial_dynamics._utils import safe_renormalize
from financial_dynamics.types import NUM_REGIMES


def initialize_count_matrix(prior_strength: float) -> np.ndarray:
    """Create a 4x4 Dirichlet-initialized count matrix.

    Each cell gets prior_strength / NUM_REGIMES pseudo-counts,
    encoding a uniform prior over transitions.
    """
    return np.full((NUM_REGIMES, NUM_REGIMES), prior_strength / NUM_REGIMES)


def counts_to_transition_matrix(counts: np.ndarray) -> np.ndarray:
    """Convert count matrix to row-stochastic transition matrix.

    Each row sums to 1.0.
    """
    row_sums = counts.sum(axis=1, keepdims=True)
    row_sums = np.where(row_sums < 1e-10, 1.0, row_sums)
    return counts / row_sums


def bayesian_update(
    counts: np.ndarray,
    prev_state: int,
    next_state: int,
    learning_rate: float,
) -> np.ndarray:
    """Update the count matrix given an observed state transition.

    Adds learning_rate pseudo-count to counts[prev_state, next_state].
    Returns the updated count matrix.
    """
    counts = counts.copy()
    counts[prev_state, next_state] += learning_rate
    return counts


def compute_posterior(
    raw_probs: np.ndarray,
    transition_row: np.ndarray,
) -> np.ndarray:
    """Combine centroid-based probabilities with transition structure.

    Uses multiplicative Bayesian fusion:
        P_post(S_t) = P_centroid(S_t|X_t) * T[S_{t-1}, S_t] / Z

    Args:
        raw_probs: shape (4,) from centroid engine.
        transition_row: shape (4,) row of transition matrix for previous state.

    Returns:
        shape (4,) posterior probabilities summing to 1.0.
    """
    posterior = raw_probs * transition_row
    return safe_renormalize(posterior)
