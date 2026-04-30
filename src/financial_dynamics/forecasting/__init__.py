"""Regime forecasting using the learned transition matrix."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from financial_dynamics.types import Regime, RegimeProbabilities, NUM_REGIMES

__all__ = [
    "RegimeForecast",
    "forecast_regimes",
    "compute_expected_duration",
    "compute_stationary_distribution",
]


@dataclass
class RegimeForecast:
    """K-step-ahead regime probability forecast."""
    current_regime: Regime
    current_probabilities: RegimeProbabilities
    horizon_probabilities: list[RegimeProbabilities]
    expected_duration: float
    most_likely_path: list[Regime]


def forecast_regimes(
    transition_matrix: np.ndarray,
    current_regime: Regime,
    current_probs: RegimeProbabilities,
    horizon: int = 10,
) -> RegimeForecast:
    """Forecast regime probabilities k steps ahead.

    Uses matrix exponentiation: P(k) = P(0) @ T^k

    Args:
        transition_matrix: Learned 4x4 row-stochastic matrix.
        current_regime: Current regime assignment.
        current_probs: Current posterior probabilities.
        horizon: Number of steps to forecast.

    Returns:
        RegimeForecast with per-step probability distributions.
    """
    T = transition_matrix.copy()
    probs = current_probs.probs.copy()

    horizon_probs = []
    most_likely_path = []

    T_power = np.eye(NUM_REGIMES)
    for _ in range(horizon):
        T_power = T_power @ T
        step_probs = probs @ T_power
        step_probs = step_probs / step_probs.sum()
        horizon_probs.append(RegimeProbabilities(probs=step_probs))
        most_likely_path.append(Regime(int(np.argmax(step_probs))))

    duration = compute_expected_duration(transition_matrix, current_regime)

    return RegimeForecast(
        current_regime=current_regime,
        current_probabilities=current_probs,
        horizon_probabilities=horizon_probs,
        expected_duration=duration,
        most_likely_path=most_likely_path,
    )


def compute_expected_duration(
    transition_matrix: np.ndarray,
    regime: Regime,
) -> float:
    """Expected number of bars before leaving the current regime.

    For a Markov chain, E[duration] = 1 / (1 - T[i, i]).
    """
    self_transition = transition_matrix[int(regime), int(regime)]
    if self_transition >= 1.0:
        return float("inf")
    return 1.0 / (1.0 - self_transition)


def compute_stationary_distribution(
    transition_matrix: np.ndarray,
) -> RegimeProbabilities:
    """Compute the stationary (long-run) distribution of the Markov chain.

    Solves pi @ T = pi subject to sum(pi) = 1 via eigendecomposition.
    """
    eigenvalues, eigenvectors = np.linalg.eig(transition_matrix.T)
    idx = np.argmin(np.abs(eigenvalues - 1.0))
    stationary = np.real(eigenvectors[:, idx])
    stationary = np.abs(stationary)
    stationary = stationary / stationary.sum()
    return RegimeProbabilities(probs=stationary)
