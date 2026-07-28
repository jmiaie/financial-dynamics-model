"""Shared visualization utilities to reduce duplication."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from sklearn.decomposition import PCA


def get_or_create_axes(
    ax: Axes | None,
    figsize: tuple[float, float] = (8, 6),
) -> tuple[Figure, Axes]:
    """Return (figure, axes), creating a new figure if ax is not provided.

    A caller-supplied Axes can live inside a SubFigure, so we assert the
    narrowing to Figure explicitly rather than declaring it away.
    """
    if ax is None:
        fig: Figure
        fig, ax = plt.subplots(1, 1, figsize=figsize)
        return fig, ax
    raw_fig = ax.figure
    assert isinstance(raw_fig, Figure)
    return raw_fig, ax


def style_phase_space_axes(ax: Axes, title: str) -> None:
    """Apply the shared axis labels, legend, and grid styling used by
    every phase-space-derived plot (phase space, trajectory, vector field)."""
    ax.set_xlabel("PC1")
    ax.set_ylabel("PC2")
    ax.set_title(title)
    ax.legend(loc="best", fontsize=8)
    ax.grid(True, alpha=0.3)


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
