"""Shared visualization utilities to reduce duplication."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure, SubFigure


def resolve_ax(ax: "Axes | None", figsize: tuple[int, int] = (8, 6)) -> "tuple[Figure | SubFigure, Axes]":
    """Return (fig, ax), creating a new figure if ax is None.

    Consolidates the standard matplotlib optional-axes boilerplate used
    across all visualization plotters.
    """
    fig: "Figure | SubFigure"
    if ax is None:
        fig, ax = plt.subplots(1, 1, figsize=figsize)
    else:
        fig = ax.figure
    return fig, ax


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
