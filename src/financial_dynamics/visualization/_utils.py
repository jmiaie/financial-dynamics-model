"""Shared visualization utilities to reduce duplication."""

from __future__ import annotations

import warnings

import numpy as np
from sklearn.decomposition import PCA

from financial_dynamics.types import Regime


def safe_regime_lookup(regime_label: str, index_value: object) -> Regime | None:
    """Look up a regime by its serialized label, warning on unknown labels.

    Returns None (with a UserWarning) instead of raising, so callers can
    skip rendering a single bad point rather than aborting the whole plot.
    """
    try:
        return Regime[regime_label]
    except KeyError:
        warnings.warn(
            f"Unknown regime '{regime_label}' at index {index_value}",
            stacklevel=2,
        )
        return None


def fit_pca_projection(
    feature_history: np.ndarray,
    centroids: np.ndarray,
    n_components: int = 2,
) -> tuple[np.ndarray, np.ndarray, PCA]:
    """Fit PCA on combined features+centroids and return projections.

    Args:
        feature_history: shape (N, 5) feature vectors.
        centroids: shape (4, 5) centroid matrix.
        n_components: number of PCA components (2 or 3).

    Returns:
        Tuple of (projected_features, projected_centroids, fitted_pca).
    """
    combined = np.vstack([feature_history, centroids])
    pca = PCA(n_components=n_components)
    pca.fit(combined)
    return pca.transform(feature_history), pca.transform(centroids), pca
