"""Plotly chart builders and color theme for the Streamlit dashboard (app.py)."""

from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from financial_dynamics.types import Regime, REGIME_NAMES

# Color scheme: slate and teal
COLOR_SCHEME = {
    "primary": "#1e3a5f",      # Dark slate blue
    "secondary": "#0d7377",     # Teal
    "accent": "#14919b",        # Light teal
    "calm": "#10b981",          # Green (Calm Trend)
    "volatile": "#f59e0b",      # Amber (Volatile Trend)
    "chop": "#8b5cf6",          # Purple (Chop)
    "riskoff": "#ef4444",       # Red (Risk-Off)
    "background": "#0f172a",    # Very dark slate
    "surface": "#1e293b",       # Dark slate
    "text": "#f1f5f9",          # Light slate
}

REGIME_COLORS_PLOTLY = {
    Regime.CALM_TREND: COLOR_SCHEME["calm"],
    Regime.VOLATILE_TREND: COLOR_SCHEME["volatile"],
    Regime.CHOP: COLOR_SCHEME["chop"],
    Regime.RISK_OFF: COLOR_SCHEME["riskoff"],
}


def plot_price_with_regimes(df: pd.DataFrame, results: pd.DataFrame) -> go.Figure:
    """Interactive price chart with regime background bands."""
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df.index,
        y=df["close"],
        mode="lines",
        name="Close Price",
        line=dict(color=COLOR_SCHEME["text"], width=2),
        hovertemplate="<b>%{x|%Y-%m-%d}</b><br>Price: $%{y:.2f}<extra></extra>",
    ))

    # Add regime background bands
    regime_col = results["risk_adjusted_regime"]
    valid = regime_col.dropna()

    if len(valid) > 0:
        for i in range(len(valid) - 1):
            try:
                regime = Regime[valid.iloc[i]]
                color = REGIME_COLORS_PLOTLY[regime]
                fig.add_vrect(
                    x0=valid.index[i],
                    x1=valid.index[i + 1],
                    fillcolor=color,
                    opacity=0.15,
                    layer="below",
                    line_width=0,
                )
            except KeyError:
                warnings.warn(
                    f"Unknown regime '{valid.iloc[i]}' at index {valid.index[i]}",
                    stacklevel=2,
                )

    fig.update_layout(
        title="Market Price with Regime Classification",
        xaxis_title="Date",
        yaxis_title="Price (USD)",
        template="plotly_dark",
        hovermode="x unified",
        plot_bgcolor=COLOR_SCHEME["background"],
        paper_bgcolor=COLOR_SCHEME["surface"],
        font=dict(color=COLOR_SCHEME["text"]),
        height=400,
    )

    return fig


def plot_regime_probabilities(results: pd.DataFrame) -> go.Figure | None:
    """Stacked area chart of regime probabilities."""
    prob_cols = [f"post_prob_{r.name}" for r in Regime]
    valid = results.dropna(subset=prob_cols)

    if len(valid) < 2:
        return None

    fig = go.Figure()
    for regime in Regime:
        col = f"post_prob_{regime.name}"
        fig.add_trace(go.Scatter(
            x=valid.index,
            y=valid[col],
            mode="lines",
            name=REGIME_NAMES[regime],
            stackgroup="one",
            fillcolor=REGIME_COLORS_PLOTLY[regime],
            line=dict(width=0.5, color=REGIME_COLORS_PLOTLY[regime]),
            hovertemplate=f"{REGIME_NAMES[regime]}: %{{y:.1%}}<extra></extra>",
        ))

    fig.update_layout(
        title="Regime Probability Distribution (Posterior)",
        xaxis_title="Date",
        yaxis_title="Probability",
        template="plotly_dark",
        hovermode="x unified",
        plot_bgcolor=COLOR_SCHEME["background"],
        paper_bgcolor=COLOR_SCHEME["surface"],
        font=dict(color=COLOR_SCHEME["text"]),
        height=350,
        yaxis=dict(range=[0, 1]),
    )

    return fig


def plot_transition_matrix(tm: np.ndarray) -> go.Figure:
    """Heatmap of transition probabilities."""
    labels = [REGIME_NAMES[r] for r in Regime]

    fig = go.Figure(data=go.Heatmap(
        z=tm,
        x=labels,
        y=labels,
        colorscale="Greys",
        zmin=0,
        zmax=1,
        text=np.round(tm, 2),
        texttemplate="%{text:.2f}",
        textfont={"size": 12},
        colorbar=dict(title="Probability"),
        hovertemplate="From %{y} → To %{x}: %{z:.2%}<extra></extra>",
    ))

    fig.update_layout(
        title="Transition Probability Matrix",
        xaxis_title="To State",
        yaxis_title="From State",
        template="plotly_dark",
        plot_bgcolor=COLOR_SCHEME["background"],
        paper_bgcolor=COLOR_SCHEME["surface"],
        font=dict(color=COLOR_SCHEME["text"]),
        height=350,
    )

    return fig


def plot_features(results: pd.DataFrame) -> go.Figure | None:
    """Time series of the 5 engineered features."""
    feat_cols = [
        "feat_volatility",
        "feat_trend",
        "feat_drawdown",
        "feat_corr_stress",
        "feat_shock",
    ]
    feat_names = [
        "Volatility",
        "Trend Strength",
        "Drawdown Pressure",
        "Correlation Stress",
        "Shock Intensity",
    ]

    valid = results.dropna(subset=feat_cols)
    if len(valid) < 2:
        return None

    fig = go.Figure()
    colors = [COLOR_SCHEME["calm"], COLOR_SCHEME["volatile"], COLOR_SCHEME["chop"],
              COLOR_SCHEME["riskoff"], COLOR_SCHEME["accent"]]

    for col, name, color in zip(feat_cols, feat_names, colors):
        fig.add_trace(go.Scatter(
            x=valid.index,
            y=valid[col],
            mode="lines",
            name=name,
            line=dict(color=color, width=2),
            hovertemplate=f"{name}: %{{y:.3f}}<extra></extra>",
        ))

    fig.update_layout(
        title="Engineered Features Over Time",
        xaxis_title="Date",
        yaxis_title="Normalized Value",
        template="plotly_dark",
        hovermode="x unified",
        plot_bgcolor=COLOR_SCHEME["background"],
        paper_bgcolor=COLOR_SCHEME["surface"],
        font=dict(color=COLOR_SCHEME["text"]),
        height=350,
    )

    return fig
