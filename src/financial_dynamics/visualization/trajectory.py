"""Trajectory plotting through 2D phase space."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from financial_dynamics.types import REGIME_NAMES, Regime
from financial_dynamics.visualization._utils import fit_pca_projection
from financial_dynamics.visualization.phase_space import REGIME_COLORS


class TrajectoryPlotter:
    """Plots the system's drift path through 2D phase space with
    regime-colored segments."""

    def plot(
        self,
        feature_history: np.ndarray,
        regimes: list[Regime],
        centroids: np.ndarray,
        ax: Axes | None = None,
    ) -> Figure:
        """Plot trajectory path.

        Args:
            feature_history: shape (N, 5) feature vectors.
            regimes: list of N regime assignments.
            centroids: shape (4, 5) centroid matrix.
            ax: optional axes.
        """
        if ax is None:
            fig, ax = plt.subplots(1, 1, figsize=(8, 6))
        else:
            fig = ax.figure

        projected, centroid_proj, _ = fit_pca_projection(feature_history, centroids)

        for i in range(len(projected) - 1):
            color = REGIME_COLORS[regimes[i]]
            ax.plot(
                projected[i:i+2, 0], projected[i:i+2, 1],
                color=color, alpha=0.5, linewidth=0.8,
            )

        ax.scatter(projected[0, 0], projected[0, 1],
                   marker="o", s=100, c="green", zorder=10, label="Start")
        ax.scatter(projected[-1, 0], projected[-1, 1],
                   marker="s", s=100, c="red", zorder=10, label="End")

        for i, regime in enumerate(Regime):
            ax.scatter(
                centroid_proj[i, 0], centroid_proj[i, 1],
                c=REGIME_COLORS[regime],
                marker="*", s=300, edgecolors="black", linewidths=1.0,
                zorder=10,
            )
            ax.annotate(
                REGIME_NAMES[regime],
                (centroid_proj[i, 0], centroid_proj[i, 1]),
                textcoords="offset points", xytext=(8, 8),
                fontsize=7, alpha=0.8,
            )

        ax.set_xlabel("PC1")
        ax.set_ylabel("PC2")
        ax.set_title("System Trajectory")
        ax.legend(loc="best", fontsize=8)
        ax.grid(True, alpha=0.3)

        return fig
