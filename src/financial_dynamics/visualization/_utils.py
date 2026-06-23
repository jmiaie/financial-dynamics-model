"""Shared visualization utilities to reduce duplication."""

from __future__ import annotations

import numpy as np
from matplotlib.axes import Axes
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


def setup_phase_space_axes(ax: Axes, title: str) -> None:
    """Apply standard phase-space axis labels, title, and grid.

    Used by PhaseSpacePlotter, TrajectoryPlotter, and VectorFieldPlotter
    to avoid repeating the same three-line setup.
    """
    ax.set_xlabel("PC1")
    ax.set_ylabel("PC2")
    ax.set_title(title)
    ax.grid(True, alpha=0.3)
