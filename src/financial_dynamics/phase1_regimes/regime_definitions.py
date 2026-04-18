"""Centroid definitions and regime metadata for Phase 1."""

from __future__ import annotations

import numpy as np

from financial_dynamics.types import Regime, NUM_REGIMES
from financial_dynamics.config import RegimeConfig


def get_centroids(config: RegimeConfig) -> np.ndarray:
    """Build the centroid matrix from configuration.

    Returns:
        np.ndarray of shape (4, 5) where each row is a regime centroid
        in the 5D feature space, ordered by Regime enum value.
    """
    centroids = np.zeros((NUM_REGIMES, 5))
    name_to_regime = {r.name: r for r in Regime}
    for name, vector in config.centroids.items():
        regime = name_to_regime[name]
        centroids[int(regime)] = vector
    return centroids


def get_default_centroids() -> np.ndarray:
    """Return the default centroid matrix using default config."""
    return get_centroids(RegimeConfig())
