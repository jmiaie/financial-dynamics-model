"""Shared visualization utilities to reduce duplication."""

from __future__ import annotations

import numpy as np
from matplotlib.axes import Axes
from sklearn.decomposition import PCA

from financial_dynamics.types import Regime

# Canonical regime colour palette shared across all visualization modules.
# Defined here (the neutral shared-utils layer) so that trajectory.py,
# vector_field.py, and dashboard.py do not need to import phase_space.py
# solely for this constant, which would create a needless coupling that
# could become a real cycle if phase_space.py ever imports from its siblings.
REGIME_COLORS: dict[Regime, str] = {
    Regime.CALM_TREND:     "#2ecc71",
    Regime.VOLATILE_TREND: "#f39c12",
    Regime.CHOP:           "#9b59b6",
    Regime.RISK_OFF:       "#e74c3c",
}


def finalize_phase_space_axes(ax: Axes, title: str) -> None:
    """Apply standard PCA phase-space axis labels, legend, grid, and title.

    All three phase-space plotters (PhaseSpacePlotter, TrajectoryPlotter,
    VectorFieldPlotter) share the same PC1/PC2 axis labels, legend style,
    and grid settings; only the title differs.
    """
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
