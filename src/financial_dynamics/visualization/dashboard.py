"""Combined multi-panel dashboard for the Financial Dynamics Model."""

from __future__ import annotations

from typing import TYPE_CHECKING

import warnings

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.patches import Patch
import matplotlib.gridspec as gridspec

from financial_dynamics.types import Regime, REGIME_NAMES, NUM_REGIMES
from financial_dynamics.visualization.phase_space import REGIME_COLORS
from financial_dynamics.visualization.trajectory import TrajectoryPlotter
from financial_dynamics.visualization.vector_field import VectorFieldPlotter

if TYPE_CHECKING:
    from financial_dynamics.pipeline import FinancialDynamicsPipeline


class SystemDashboard:
    """Combined 5-panel dashboard:
    1. Price chart with regime-colored background bands
    2. Phase-space projection with trajectory
    3. Regime probability time series (stacked area)
    4. Transition matrix heatmap
    5. Risk overlay indicators
    """

    def __init__(self, pipeline: FinancialDynamicsPipeline):
        self.pipeline = pipeline
        self._fig: Figure | None = None

    def plot(self, df: pd.DataFrame, results: pd.DataFrame) -> Figure:
        """Generate the full dashboard.

        Args:
            df: Original OHLCV DataFrame.
            results: Pipeline output DataFrame from pipeline.run().
        """
        fig = plt.figure(figsize=(20, 16))
        gs = gridspec.GridSpec(3, 2, figure=fig, hspace=0.35, wspace=0.3)

        ax1 = fig.add_subplot(gs[0, :])
        ax2 = fig.add_subplot(gs[1, 0])
        ax3 = fig.add_subplot(gs[1, 1])
        ax4 = fig.add_subplot(gs[2, 0])
        ax5 = fig.add_subplot(gs[2, 1])

        self._plot_price_chart(df, results, ax1)
        self._plot_phase_space(results, ax2)
        self._plot_vector_field(ax3)
        self._plot_probability_series(results, ax4)
        self._plot_transition_heatmap(ax5)

        fig.suptitle("Financial Dynamics Model -- System Dashboard", fontsize=16, y=0.98)
        self._fig = fig
        return fig

    def save(self, path: str, dpi: int = 150) -> None:
        if self._fig is None:
            raise RuntimeError("No figure to save. Call plot() before save().")
        self._fig.savefig(path, dpi=dpi, bbox_inches="tight")

    def _plot_price_chart(self, df: pd.DataFrame, results: pd.DataFrame, ax: Axes) -> None:
        """Panel 1: Price with regime-colored background bands."""
        ax.plot(df.index, df["close"], color="black", linewidth=0.8, alpha=0.9)

        regime_col = results["risk_adjusted_regime"]
        valid = regime_col.dropna()

        if len(valid) > 0:
            for i in range(len(valid) - 1):
                regime_str = valid.iloc[i]
                try:
                    regime = Regime[regime_str]
                except KeyError:
                    warnings.warn(
                        f"Unknown regime '{regime_str}' at index {valid.index[i]}",
                        stacklevel=2,
                    )
                    continue
                ax.axvspan(
                    valid.index[i], valid.index[i + 1],
                    alpha=0.15, color=REGIME_COLORS[regime],
                )

        legend_patches = [
            Patch(facecolor=REGIME_COLORS[r], alpha=0.3, label=REGIME_NAMES[r])
            for r in Regime
        ]
        ax.legend(handles=legend_patches, loc="upper left", fontsize=8)
        ax.set_title("Price with Regime Classification")
        ax.set_ylabel("Price")
        ax.grid(True, alpha=0.3)

    def _plot_phase_space(self, results: pd.DataFrame, ax: Axes) -> None:
        """Panel 2: Phase-space projection with trajectory."""
        feat_cols = ["feat_volatility", "feat_trend", "feat_drawdown",
                     "feat_corr_stress", "feat_shock"]
        valid = results.dropna(subset=feat_cols + ["risk_adjusted_regime"])

        if len(valid) < 5:
            ax.text(0.5, 0.5, "Insufficient data", ha="center", va="center",
                    transform=ax.transAxes)
            return

        features = valid[feat_cols].values
        regimes = [Regime[r] for r in valid["risk_adjusted_regime"]]

        centroids = self.pipeline._centroid_engine.centroids
        plotter = TrajectoryPlotter()
        plotter.plot(features, regimes, centroids, ax=ax)

    def _plot_vector_field(self, ax: Axes) -> None:
        """Panel 3: Transition probability vector field."""
        centroids = self.pipeline._centroid_engine.centroids
        tm = self.pipeline._transition_engine.get_transition_matrix()
        plotter = VectorFieldPlotter()
        plotter.plot(centroids, tm, ax=ax)

    def _plot_probability_series(self, results: pd.DataFrame, ax: Axes) -> None:
        """Panel 4: Regime probability time series (stacked area)."""
        prob_cols = [f"post_prob_{r.name}" for r in Regime]
        valid = results.dropna(subset=prob_cols)

        if len(valid) < 2:
            ax.text(0.5, 0.5, "Insufficient data", ha="center", va="center",
                    transform=ax.transAxes)
            return

        colors = [REGIME_COLORS[r] for r in Regime]
        labels = [REGIME_NAMES[r] for r in Regime]

        ax.stackplot(
            valid.index,
            *[valid[col].values for col in prob_cols],
            labels=labels,
            colors=colors,
            alpha=0.7,
        )
        ax.set_ylim(0, 1)
        ax.set_ylabel("Probability")
        ax.set_title("Regime Probabilities (Posterior)")
        ax.legend(loc="upper right", fontsize=7)
        ax.grid(True, alpha=0.3)

    def _plot_transition_heatmap(self, ax: Axes) -> None:
        """Panel 5: Transition matrix heatmap."""
        tm = self.pipeline._transition_engine.get_transition_matrix()
        labels = [REGIME_NAMES[r] for r in Regime]

        im = ax.imshow(tm, cmap="YlOrRd", vmin=0, vmax=1, aspect="auto")
        ax.set_xticks(range(NUM_REGIMES))
        ax.set_yticks(range(NUM_REGIMES))
        ax.set_xticklabels(labels, fontsize=8, rotation=30, ha="right")
        ax.set_yticklabels(labels, fontsize=8)
        ax.set_xlabel("To State")
        ax.set_ylabel("From State")
        ax.set_title("Transition Probability Matrix")

        for i in range(NUM_REGIMES):
            for j in range(NUM_REGIMES):
                ax.text(j, i, f"{tm[i, j]:.2f}",
                        ha="center", va="center", fontsize=9,
                        color="white" if tm[i, j] > 0.5 else "black")

        plt.colorbar(im, ax=ax, shrink=0.8)
