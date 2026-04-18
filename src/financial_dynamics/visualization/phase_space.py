"""2D phase-space projection of the 5D feature space."""

from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.axes import Axes
from sklearn.decomposition import PCA

from financial_dynamics.types import Regime, REGIME_NAMES, NUM_REGIMES

REGIME_COLORS = {
    Regime.CALM_TREND: "#2ecc71",
    Regime.VOLATILE_TREND: "#f39c12",
    Regime.CHOP: "#9b59b6",
    Regime.RISK_OFF: "#e74c3c",
}


class PhaseSpacePlotter:
    """2D PCA projection of feature history with centroid attractors."""

    def __init__(self, centroids: np.ndarray):
        """Args:
            centroids: shape (4, 5) centroid matrix.
        """
        self.centroids = centroids
        self._pca: PCA | None = None

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
        if ax is None:
            fig, ax = plt.subplots(1, 1, figsize=(8, 6))
        else:
            fig = ax.figure

        # Fit PCA on combined data (features + centroids)
        combined = np.vstack([feature_history, self.centroids])
        self._pca = PCA(n_components=2)
        self._pca.fit(combined)

        projected = self._pca.transform(feature_history)
        centroid_proj = self._pca.transform(self.centroids)

        # Plot feature points colored by regime
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

        # Plot centroids as large markers
        for i, regime in enumerate(Regime):
            ax.scatter(
                centroid_proj[i, 0], centroid_proj[i, 1],
                c=REGIME_COLORS[regime],
                marker="*", s=300, edgecolors="black", linewidths=1.0,
                zorder=10,
            )

        ax.set_xlabel("PC1")
        ax.set_ylabel("PC2")
        ax.set_title("Phase-Space Projection")
        ax.legend(loc="best", fontsize=8)
        ax.grid(True, alpha=0.3)

        return fig
