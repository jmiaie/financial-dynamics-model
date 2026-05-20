"""Feature normalization and weighting for Phase 0."""

from __future__ import annotations

import numpy as np

from financial_dynamics.config import FeatureConfig


class FeatureNormalizer:
    """Normalizes raw indicator values and applies feature weights.

    Supports two normalization methods:
    - 'zscore': (x - mean) / std, then sigmoid-squashed to [0, 1]
    - 'minmax': (x - min) / (max - min) clipped to [0, 1]

    Maintains rolling statistics for online normalization.
    """

    _VALID_METHODS = {"zscore", "minmax"}

    def __init__(self, config: FeatureConfig):
        if config.normalization_method not in self._VALID_METHODS:
            raise ValueError(
                f"Unsupported normalization_method '{config.normalization_method}'. "
                f"Valid options: {sorted(self._VALID_METHODS)}"
            )
        self.method = config.normalization_method
        self.window = config.normalization_window
        self.weights = np.array(config.feature_weights, dtype=float)
        self._history: list[np.ndarray] = []

    def update(self, raw_features: np.ndarray) -> np.ndarray:
        """Add a new observation and return the normalized feature vector.

        Args:
            raw_features: shape (5,) raw indicator values.

        Returns:
            shape (5,) normalized and weighted feature vector in [0, 1].
        """
        self._history.append(raw_features.copy())
        if len(self._history) > self.window:
            self._history = self._history[-self.window :]

        if len(self._history) < 2:
            return np.clip(raw_features, 0.0, 1.0) * self.weights

        history = np.array(self._history)

        if self.method == "zscore":
            normalized = self._zscore_normalize(raw_features, history)
        else:
            normalized = self._minmax_normalize(raw_features, history)

        return normalized * self.weights

    def _zscore_normalize(self, x: np.ndarray, history: np.ndarray) -> np.ndarray:
        """Z-score normalize then squash through sigmoid to [0, 1]."""
        mean = history.mean(axis=0)
        std = history.std(axis=0)
        std = np.where(std < 1e-10, 1.0, std)
        z = (x - mean) / std
        return 1.0 / (1.0 + np.exp(-z))

    def _minmax_normalize(self, x: np.ndarray, history: np.ndarray) -> np.ndarray:
        """Min-Max normalize to [0, 1]."""
        mins = history.min(axis=0)
        maxs = history.max(axis=0)
        range_ = maxs - mins
        range_ = np.where(range_ < 1e-10, 1.0, range_)
        return np.clip((x - mins) / range_, 0.0, 1.0)

    def reset(self) -> None:
        self._history.clear()
