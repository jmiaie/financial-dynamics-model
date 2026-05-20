"""Phase 1: Centroid-based probabilistic regime classification.

Maps a 5D feature vector to a probability distribution over 4 regimes
using softmax of negative Euclidean distances to regime centroids.
"""

from __future__ import annotations

import numpy as np

from financial_dynamics.config import RegimeConfig
from financial_dynamics.phase1_regimes.regime_definitions import get_centroids
from financial_dynamics.types import NUM_REGIMES, BarState, RegimeProbabilities


class CentroidEngine:
    """Phase 1: Maps feature vectors to regime probabilities."""

    def __init__(self, config: RegimeConfig | None = None):
        self.config = config or RegimeConfig()
        self.centroids = get_centroids(self.config)
        self.temperature = self.config.temperature

    def compute_probabilities(self, feature_vector: np.ndarray) -> RegimeProbabilities:
        """Compute regime probabilities from a feature vector.

        Uses softmax of negative Euclidean distances:
            d_i = ||X_t - C_i||
            P(S_i) = exp(-d_i / tau) / sum_j exp(-d_j / tau)

        Numerically stable implementation (subtract max before exp).
        """
        distances = np.linalg.norm(self.centroids - feature_vector, axis=1)
        logits = -distances / self.temperature
        logits -= logits.max()
        exp_logits = np.exp(logits)
        probs = exp_logits / exp_logits.sum()

        return RegimeProbabilities(probs=probs)

    def update(self, bar_state: BarState) -> BarState:
        """Pipeline interface: reads features, writes raw_probabilities."""
        if bar_state.features is None:
            return bar_state

        feature_array = bar_state.features.to_array()
        bar_state.raw_probabilities = self.compute_probabilities(feature_array)
        return bar_state

    def set_centroids(self, centroids: np.ndarray) -> None:
        """Allow dynamic centroid updates for recalibration."""
        if centroids.shape != (NUM_REGIMES, 5):
            raise ValueError(f"Expected centroid shape ({NUM_REGIMES}, 5), got {centroids.shape}")
        self.centroids = centroids.copy()
