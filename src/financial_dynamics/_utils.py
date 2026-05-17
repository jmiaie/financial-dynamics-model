"""Shared utilities used across multiple pipeline phases."""

import numpy as np

from financial_dynamics.types import NUM_REGIMES


def safe_renormalize(probs: np.ndarray) -> np.ndarray:
    """Safely renormalize a probability vector to sum to 1.0.

    If the sum is near zero, returns a uniform distribution.
    """
    total = probs.sum()
    if total > 1e-10:
        return probs / total
    return np.full(NUM_REGIMES, 1.0 / NUM_REGIMES)
