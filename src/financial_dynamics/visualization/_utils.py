"""Shared visualization utilities to reduce duplication."""

from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from sklearn.decomposition import PCA

from financial_dynamics.types import Regime, REGIME_NAMES


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


def ensure_ax(ax: Axes | None, figsize: tuple[float, float] = (8, 6)) -> tuple[Figure, Axes]:
    """Return ``(fig, ax)``, creating a new figure when *ax* is None.

    Args:
        ax: Existing axes to draw on, or None to create a new figure.
        figsize: Figure size passed to :func:`matplotlib.pyplot.subplots`
                 when a new figure is created.

    Returns:
        Tuple of (figure, axes).
    """
    if ax is None:
        fig, ax = plt.subplots(1, 1, figsize=figsize)
    else:
        fig = ax.figure
    return fig, ax


def plot_regime_centroids(
    centroid_proj: np.ndarray,
    ax: Axes,
    *,
    marker_size: int = 300,
    show_labels: bool = False,
    show_legend_labels: bool = False,
) -> None:
    """Scatter centroid star markers onto *ax*.

    Args:
        centroid_proj: shape (4, 2) centroid positions in the projected space.
        ax: Axes to draw on.
        marker_size: Size of the star markers.
        show_labels: If True, annotate each centroid with its regime name.
        show_legend_labels: If True, include regime names as legend labels.
    """
    # Import here to avoid a circular dependency (phase_space imports REGIME_COLORS
    # and _utils, so the import order would be fine, but keeping it local to this
    # function keeps the module lean).
    from financial_dynamics.visualization.phase_space import REGIME_COLORS

    for i, regime in enumerate(Regime):
        label = REGIME_NAMES[regime] if show_legend_labels else None
        ax.scatter(
            centroid_proj[i, 0], centroid_proj[i, 1],
            c=REGIME_COLORS[regime],
            marker="*", s=marker_size, edgecolors="black", linewidths=1.0,
            zorder=10, label=label,
        )
        if show_labels:
            ax.annotate(
                REGIME_NAMES[regime],
                (centroid_proj[i, 0], centroid_proj[i, 1]),
                textcoords="offset points", xytext=(8, 8),
                fontsize=7, alpha=0.8,
            )
