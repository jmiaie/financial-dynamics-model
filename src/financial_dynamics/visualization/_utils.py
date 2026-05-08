"""Shared visualization utilities to reduce duplication."""

from __future__ import annotations

import numpy as np
from sklearn.decomposition import PCA


def fit_pca_projection(
    feature_history: np.ndarray,
    centroids: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, PCA]:
    """Fit PCA on combined features+centroids and return projections.

    Args:
        feature_history: shape (N, 5) feature vectors.
        centroids: shape (4, 5) centroid matrix.

    Returns:
        Tuple of (projected_features, projected_centroids, fitted_pca).
    """
    combined = np.vstack([feature_history, centroids])
    pca = PCA(n_components=2)
    pca.fit(combined)
    return pca.transform(feature_history), pca.transform(centroids), pca


def fit_pca_centroids_only(centroids: np.ndarray) -> np.ndarray:
    """Fit PCA on the centroid matrix alone and return the 2D projections.

    Used by plotters that display centroid positions without a feature
    history (e.g. the transition vector field).

    Args:
        centroids: shape (4, 5) centroid matrix.

    Returns:
        shape (4, 2) projected centroid positions.
    """
    pca = PCA(n_components=2)
    return pca.fit_transform(centroids)
