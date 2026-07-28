"""2D phase-space projection of the 5D feature space."""

from __future__ import annotations

import numpy as np
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from financial_dynamics.types import REGIME_NAMES, Regime
from financial_dynamics.visualization._utils import (
    fit_pca_projection,
    get_or_create_axes,
    style_phase_space_axes,
)

REGIME_COLORS = {
    Regime.CALM_TREND: "#2ecc71",
    Regime.VOLATILE_TREND: "#f39c12",
    Regime.CHOP: "#9b59b6",
    Regime.RISK_OFF: "#e74c3c",
}


class PhaseSpacePlotter:
    """2D PCA projection of feature history with centroid attractors."""

    def __init__(self, centroids: np.ndarray):
        self.centroids = centroids

    def plot(
        self,
        feature_history: np.ndarray,
        regimes: list[Regime],
        ax: Axes | None = None,
    ) -> Figure:
        """Plot the phase-space projection.

        Args:
            feature_history: shape (N, 5) array of feature vectors.
            regimes: list of N regime assignments for coloring.
            ax: optional axes to draw on.
        """
        fig, ax = get_or_create_axes(ax)

        projected, centroid_proj, _ = fit_pca_projection(
            feature_history, self.centroids
        )

        for regime in Regime:
            mask = [r == regime for r in regimes]
            if any(mask):
                pts = projected[mask]
                ax.scatter(
                    pts[:, 0], pts[:, 1],
                    c=REGIME_COLORS[regime],
                    alpha=0.4, s=15,
                    label=REGIME_NAMES[regime],
                )

        for i, regime in enumerate(Regime):
            ax.scatter(
                centroid_proj[i, 0], centroid_proj[i, 1],
                c=REGIME_COLORS[regime],
                marker="*", s=300, edgecolors="black", linewidths=1.0,
                zorder=10,
            )

        style_phase_space_axes(ax, "Phase-Space Projection")

        return fig
