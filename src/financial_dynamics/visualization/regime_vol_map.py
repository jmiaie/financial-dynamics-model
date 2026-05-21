"""Regime-Volatility mapping visualizations.

Provides visual tools that map the relationship between market regimes and
volatility, revealing how volatility distributes across regimes, where
regime boundaries lie in vol-space, and how regime transitions correlate
with volatility shifts.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.patches import Patch

from financial_dynamics.types import REGIME_NAMES, Regime
from financial_dynamics.visualization.phase_space import REGIME_COLORS

if TYPE_CHECKING:
    from financial_dynamics.pipeline import FinancialDynamicsPipeline


def build_regime_vol_map(
    results: pd.DataFrame,
    pipeline: FinancialDynamicsPipeline | None = None,
) -> Figure:
    """Build a 4-panel regime-volatility mapping dashboard.

    Panels:
        1. Volatility violin plots by regime (distribution shape)
        2. Regime-conditioned vol heatmap (2D density)
        3. Vol time series with regime-colored bands
        4. Regime transition vol-shift histogram

    Args:
        results: Pipeline output from pipeline.run().
        pipeline: Optional pipeline instance for transition matrix overlay.

    Returns:
        Matplotlib Figure with all 4 panels.
    """
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle("Regime–Volatility Map", fontsize=16, y=0.98)

    valid = results.dropna(subset=["risk_adjusted_regime", "feat_volatility"])
    if len(valid) < 10:
        for ax in axes.flat:
            ax.text(0.5, 0.5, "Insufficient data", ha="center", va="center", transform=ax.transAxes)
        return fig

    _plot_vol_violins(valid, axes[0, 0])
    _plot_vol_regime_heatmap(valid, axes[0, 1])
    _plot_vol_timeseries(valid, axes[1, 0])
    _plot_transition_vol_shifts(valid, axes[1, 1])

    fig.tight_layout(rect=(0, 0, 1, 0.95))
    return fig


def _plot_vol_violins(valid: pd.DataFrame, ax: Axes) -> None:
    """Panel 1: Volatility distribution per regime as violin plots."""
    regime_vols: dict[str, np.ndarray] = {}
    positions = []
    labels = []

    for i, regime in enumerate(Regime):
        mask = valid["risk_adjusted_regime"] == regime.name
        vol_data = np.asarray(valid.loc[mask, "feat_volatility"].values)
        if len(vol_data) >= 2:
            regime_vols[regime.name] = vol_data
            positions.append(i)
            labels.append(REGIME_NAMES[regime])

    if not regime_vols:
        ax.text(0.5, 0.5, "No data", ha="center", va="center", transform=ax.transAxes)
        return

    data = [regime_vols[Regime(p).name] for p in positions]
    parts = ax.violinplot(data, positions=positions, showmedians=True, showextrema=True)

    for idx, pc in enumerate(parts["bodies"]):  # type: ignore[arg-type, var-annotated]
        regime = Regime(positions[idx])
        pc.set_facecolor(REGIME_COLORS[regime])  # type: ignore[union-attr]
        pc.set_alpha(0.6)  # type: ignore[union-attr]

    for component in ["cbars", "cmins", "cmaxes", "cmedians"]:
        if component in parts:
            parts[component].set_color("black")
            parts[component].set_linewidth(0.8)

    for _i, pos in enumerate(positions):
        regime = Regime(pos)
        vals = regime_vols[regime.name]
        ax.scatter(
            np.full(len(vals), pos) + np.random.default_rng(42).normal(0, 0.04, len(vals)),
            vals,
            c=REGIME_COLORS[regime],
            alpha=0.15,
            s=5,
            zorder=0,
        )

    ax.set_xticks(positions)
    ax.set_xticklabels(labels, fontsize=9)
    ax.set_ylabel("Volatility")
    ax.set_title("Volatility Distribution by Regime")
    ax.grid(True, alpha=0.3, axis="y")


def _plot_vol_regime_heatmap(valid: pd.DataFrame, ax: Axes) -> None:
    """Panel 2: 2D density heatmap of (regime probability, volatility)."""
    prob_cols = [f"post_prob_{r.name}" for r in Regime]
    available_cols = [c for c in prob_cols if c in valid.columns]

    if not available_cols:
        ax.text(0.5, 0.5, "No probability data", ha="center", va="center", transform=ax.transAxes)
        return

    max_prob = valid[available_cols].max(axis=1)
    vol = valid["feat_volatility"]

    prob_bins = np.linspace(0.25, 1.0, 30)
    vol_bins = np.linspace(vol.min(), vol.max(), 30)

    hist, xedges, yedges = np.histogram2d(max_prob, vol, bins=[prob_bins, vol_bins])

    im = ax.pcolormesh(
        xedges,
        yedges,
        hist.T,
        cmap="inferno",
        shading="auto",
    )

    for regime in Regime:
        col = f"post_prob_{regime.name}"
        if col not in valid.columns:
            continue
        mask = valid["risk_adjusted_regime"] == regime.name
        regime_data = valid.loc[mask]
        if len(regime_data) >= 5:
            mean_prob = regime_data[col].mean()
            mean_vol = regime_data["feat_volatility"].mean()
            ax.plot(
                mean_prob,
                mean_vol,
                marker="*",
                markersize=14,
                color=REGIME_COLORS[regime],
                markeredgecolor="white",
                markeredgewidth=1.0,
                zorder=10,
            )
            ax.annotate(
                REGIME_NAMES[regime],
                (mean_prob, mean_vol),
                fontsize=7,
                color="white",
                fontweight="bold",
                xytext=(5, 5),
                textcoords="offset points",
            )

    plt.colorbar(im, ax=ax, label="Frequency", shrink=0.8)
    ax.set_xlabel("Max Regime Probability (Confidence)")
    ax.set_ylabel("Volatility")
    ax.set_title("Regime Confidence vs Volatility Density")


def _plot_vol_timeseries(valid: pd.DataFrame, ax: Axes) -> None:
    """Panel 3: Volatility time series with regime-colored background bands."""
    ax.plot(valid.index, valid["feat_volatility"], color="black", linewidth=0.6, alpha=0.8)

    regime_col = valid["risk_adjusted_regime"]
    for i in range(len(valid) - 1):
        try:
            regime = Regime[regime_col.iloc[i]]
        except (KeyError, ValueError):
            continue
        ax.axvspan(
            valid.index[i],
            valid.index[i + 1],
            alpha=0.2,
            color=REGIME_COLORS[regime],
        )

    vol_mean = valid["feat_volatility"].mean()
    vol_std = valid["feat_volatility"].std()
    ax.axhline(vol_mean, color="gray", linestyle="--", linewidth=0.8, alpha=0.7)
    ax.axhline(vol_mean + 2 * vol_std, color="red", linestyle=":", linewidth=0.7, alpha=0.6)
    ax.axhline(vol_mean - vol_std, color="green", linestyle=":", linewidth=0.7, alpha=0.6)

    legend_patches = [
        Patch(facecolor=REGIME_COLORS[r], alpha=0.3, label=REGIME_NAMES[r]) for r in Regime
    ]
    ax.legend(handles=legend_patches, loc="upper right", fontsize=7)
    ax.set_ylabel("Volatility")
    ax.set_title("Volatility with Regime Classification")
    ax.grid(True, alpha=0.3)


def _plot_transition_vol_shifts(valid: pd.DataFrame, ax: Axes) -> None:
    """Panel 4: Histogram of volatility changes at regime transitions."""
    regime_col = valid["risk_adjusted_regime"]
    vol_col = valid["feat_volatility"]

    transition_mask = regime_col != regime_col.shift(1)
    transition_mask.iloc[0] = False
    transitions = valid.loc[transition_mask]

    if len(transitions) < 3:
        ax.text(0.5, 0.5, "Too few transitions", ha="center", va="center", transform=ax.transAxes)
        return

    vol_changes = vol_col.diff().loc[transition_mask].dropna()

    ax.hist(vol_changes, bins=25, color="#3498db", alpha=0.7, edgecolor="black", linewidth=0.5)
    ax.axvline(0, color="black", linestyle="-", linewidth=0.8)
    ax.axvline(
        vol_changes.mean(),
        color="red",
        linestyle="--",
        linewidth=1.2,
        label=f"Mean: {vol_changes.mean():.4f}",
    )
    ax.axvline(
        vol_changes.median(),
        color="orange",
        linestyle="--",
        linewidth=1.2,
        label=f"Median: {vol_changes.median():.4f}",
    )

    ax.set_xlabel("Volatility Change at Transition")
    ax.set_ylabel("Count")
    ax.set_title(f"Vol Shifts at Regime Transitions (n={len(vol_changes)})")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)


def build_regime_vol_map_plotly(
    results: pd.DataFrame,
    pipeline: FinancialDynamicsPipeline | None = None,
) -> dict:
    """Build an interactive Plotly regime-volatility map for Streamlit.

    Returns a dict of Plotly figures keyed by panel name.
    """
    import plotly.graph_objects as go

    valid = results.dropna(subset=["risk_adjusted_regime", "feat_volatility"])
    figures: dict[str, go.Figure] = {}

    if len(valid) < 10:
        return figures

    figures["vol_violin"] = _plotly_vol_violin(valid)
    figures["vol_heatmap"] = _plotly_vol_heatmap(valid)
    figures["vol_timeseries"] = _plotly_vol_timeseries(valid)
    figures["vol_transitions"] = _plotly_transition_shifts(valid)

    return figures


def _plotly_vol_violin(valid: pd.DataFrame) -> object:
    """Interactive violin plot of volatility by regime."""
    import plotly.graph_objects as go

    fig = go.Figure()
    for regime in Regime:
        mask = valid["risk_adjusted_regime"] == regime.name
        vol_data = valid.loc[mask, "feat_volatility"]
        if len(vol_data) < 2:
            continue

        fig.add_trace(
            go.Violin(
                y=vol_data,
                name=REGIME_NAMES[regime],
                line_color=REGIME_COLORS[regime],
                fillcolor=REGIME_COLORS[regime],
                opacity=0.6,
                meanline_visible=True,
                box_visible=True,
                points="outliers",
            )
        )

    fig.update_layout(
        title="Volatility Distribution by Regime",
        yaxis_title="Volatility",
        showlegend=True,
        template="plotly_dark",
        height=450,
    )
    return fig


def _plotly_vol_heatmap(valid: pd.DataFrame) -> object:
    """Interactive 2D density of confidence vs volatility."""
    import plotly.graph_objects as go

    prob_cols = [f"post_prob_{r.name}" for r in Regime]
    available = [c for c in prob_cols if c in valid.columns]
    if not available:
        return go.Figure()

    max_prob = valid[available].max(axis=1)
    vol = valid["feat_volatility"]

    fig = go.Figure(
        go.Histogram2d(
            x=max_prob,
            y=vol,
            nbinsx=30,
            nbinsy=30,
            colorscale="Inferno",
            colorbar=dict(title="Frequency"),
        )
    )

    for regime in Regime:
        col = f"post_prob_{regime.name}"
        if col not in valid.columns:
            continue
        mask = valid["risk_adjusted_regime"] == regime.name
        regime_data = valid.loc[mask]
        if len(regime_data) >= 5:
            fig.add_trace(
                go.Scatter(
                    x=[regime_data[col].mean()],
                    y=[regime_data["feat_volatility"].mean()],
                    mode="markers+text",
                    marker=dict(
                        size=16,
                        symbol="star",
                        color=REGIME_COLORS[regime],
                        line=dict(width=1, color="white"),
                    ),
                    text=[REGIME_NAMES[regime]],
                    textposition="top center",
                    textfont=dict(size=10, color=REGIME_COLORS[regime]),
                    showlegend=False,
                )
            )

    fig.update_layout(
        title="Regime Confidence vs Volatility",
        xaxis_title="Max Regime Probability",
        yaxis_title="Volatility",
        template="plotly_dark",
        height=450,
    )
    return fig


def _plotly_vol_timeseries(valid: pd.DataFrame) -> object:
    """Interactive vol time series with regime coloring."""
    import plotly.graph_objects as go

    fig = go.Figure()

    for regime in Regime:
        mask = valid["risk_adjusted_regime"] == regime.name
        regime_data = valid.loc[mask]
        if len(regime_data) == 0:
            continue
        fig.add_trace(
            go.Scatter(
                x=regime_data.index,
                y=regime_data["feat_volatility"],
                mode="markers",
                marker=dict(size=4, color=REGIME_COLORS[regime], opacity=0.6),
                name=REGIME_NAMES[regime],
            )
        )

    fig.add_trace(
        go.Scatter(
            x=valid.index,
            y=valid["feat_volatility"],
            mode="lines",
            line=dict(color="white", width=0.8),
            opacity=0.4,
            showlegend=False,
        )
    )

    vol_mean = valid["feat_volatility"].mean()
    vol_std = valid["feat_volatility"].std()
    fig.add_hline(
        y=vol_mean, line_dash="dash", line_color="gray", opacity=0.5, annotation_text="Mean"
    )
    fig.add_hline(
        y=vol_mean + 2 * vol_std,
        line_dash="dot",
        line_color="red",
        opacity=0.4,
        annotation_text="+2σ",
    )

    fig.update_layout(
        title="Volatility Time Series by Regime",
        yaxis_title="Volatility",
        template="plotly_dark",
        height=400,
    )
    return fig


def _plotly_transition_shifts(valid: pd.DataFrame) -> object:
    """Interactive histogram of vol changes at transitions."""
    import plotly.graph_objects as go

    regime_col = valid["risk_adjusted_regime"]
    vol_col = valid["feat_volatility"]

    transition_mask = regime_col != regime_col.shift(1)
    transition_mask.iloc[0] = False
    vol_changes = vol_col.diff().loc[transition_mask].dropna()

    if len(vol_changes) < 3:
        return go.Figure()

    fig = go.Figure(
        go.Histogram(
            x=vol_changes,
            nbinsx=25,
            marker_color="#3498db",
            opacity=0.7,
        )
    )

    fig.add_vline(x=0, line_color="white", line_width=1)
    fig.add_vline(
        x=vol_changes.mean(),
        line_dash="dash",
        line_color="red",
        annotation_text=f"Mean: {vol_changes.mean():.4f}",
    )

    fig.update_layout(
        title=f"Volatility Shifts at Regime Transitions (n={len(vol_changes)})",
        xaxis_title="Δ Volatility",
        yaxis_title="Count",
        template="plotly_dark",
        height=400,
    )
    return fig
