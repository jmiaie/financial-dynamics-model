"""Transition probability vector field overlay."""

from __future__ import annotations

import numpy as np
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from sklearn.decomposition import PCA

from financial_dynamics.types import NUM_REGIMES, REGIME_NAMES, Regime
from financial_dynamics.visualization._utils import (
    get_or_create_axes,
    style_phase_space_axes,
)
from financial_dynamics.visualization.phase_space import REGIME_COLORS


class VectorFieldPlotter:
    """Overlays transition probability vectors on the phase-space plot.

    Arrows from each centroid show the expected direction and strength
    of regime transitions based on the learned transition matrix.
    """

    def plot(
        self,
        centroids: np.ndarray,
        transition_matrix: np.ndarray,
        ax: Axes | None = None,
    ) -> Figure:
        """Draw transition vectors between centroids.

        Args:
            centroids: shape (4, 5) centroid matrix.
            transition_matrix: shape (4, 4) row-stochastic matrix.
            ax: optional axes.
        """
        fig, ax = get_or_create_axes(ax)

        pca = PCA(n_components=2)
        centroid_proj = pca.fit_transform(centroids)

        for i, regime in enumerate(Regime):
            ax.scatter(
                centroid_proj[i, 0], centroid_proj[i, 1],
                c=REGIME_COLORS[regime],
                marker="*", s=400, edgecolors="black", linewidths=1.0,
                zorder=10, label=REGIME_NAMES[regime],
            )

        for i in range(NUM_REGIMES):
            for j in range(NUM_REGIMES):
                if i == j:
                    continue
                prob = transition_matrix[i, j]
                if prob < 0.05:
                    continue

                ax.annotate(
                    "",
                    xy=(centroid_proj[j, 0], centroid_proj[j, 1]),
                    xytext=(centroid_proj[i, 0], centroid_proj[i, 1]),
                    arrowprops=dict(
                        arrowstyle="->",
                        color=REGIME_COLORS[Regime(i)],
                        alpha=min(prob * 2, 0.9),
                        lw=max(prob * 5, 0.5),
                        connectionstyle="arc3,rad=0.15",
                    ),
                )
                mid_x = (centroid_proj[i, 0] + centroid_proj[j, 0]) / 2
                mid_y = (centroid_proj[i, 1] + centroid_proj[j, 1]) / 2
                if prob > 0.15:
                    ax.text(
                        mid_x, mid_y, f"{prob:.0%}",
                        fontsize=6, alpha=0.7,
                        ha="center", va="center",
                    )

        style_phase_space_axes(ax, "Transition Vector Field")

        return fig
