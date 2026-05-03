"""3D phase-space projection using Plotly for interactive visualization."""

from __future__ import annotations

import numpy as np
import plotly.graph_objects as go

from financial_dynamics.types import Regime, REGIME_NAMES
from financial_dynamics.visualization._utils import fit_pca_projection

REGIME_COLORS_3D = {
    Regime.CALM_TREND: "#10b981",
    Regime.VOLATILE_TREND: "#f59e0b",
    Regime.CHOP: "#8b5cf6",
    Regime.RISK_OFF: "#ef4444",
}


def build_phase_space_3d(
    feature_history: np.ndarray,
    regimes: list[Regime],
    centroids: np.ndarray,
    show_trajectory: bool = True,
    animate: bool = False,
) -> go.Figure:
    """Build a 3D interactive phase-space plot.

    Projects 5D features → 3D via PCA, plots the trajectory through state
    space colored by regime, with centroids as glowing attractor markers.

    Args:
        feature_history: shape (N, 5) array of feature vectors.
        regimes: list of N regime assignments.
        centroids: shape (4, 5) centroid matrix.
        show_trajectory: draw connecting line through time.
        animate: include time-slider animation frames.

    Returns:
        Plotly Figure ready for Streamlit / HTML rendering.
    """
    projected, centroid_proj, pca = fit_pca_projection(
        feature_history, centroids, n_components=3
    )

    fig = go.Figure()

    for regime in Regime:
        mask = np.array([r == regime for r in regimes])
        if not mask.any():
            continue
        pts = projected[mask]
        fig.add_trace(go.Scatter3d(
            x=pts[:, 0], y=pts[:, 1], z=pts[:, 2],
            mode="markers",
            name=REGIME_NAMES[regime],
            marker=dict(
                size=4,
                color=REGIME_COLORS_3D[regime],
                opacity=0.55,
                line=dict(width=0),
            ),
            hovertemplate=(
                f"<b>{REGIME_NAMES[regime]}</b><br>"
                "PC1: %{x:.2f}<br>PC2: %{y:.2f}<br>PC3: %{z:.2f}"
                "<extra></extra>"
            ),
        ))

    if show_trajectory and len(projected) > 1:
        fig.add_trace(go.Scatter3d(
            x=projected[:, 0], y=projected[:, 1], z=projected[:, 2],
            mode="lines",
            name="Trajectory",
            line=dict(
                color=np.arange(len(projected)),
                colorscale="Viridis",
                width=3,
            ),
            opacity=0.6,
            showlegend=True,
            hoverinfo="skip",
        ))

    for i, regime in enumerate(Regime):
        fig.add_trace(go.Scatter3d(
            x=[centroid_proj[i, 0]],
            y=[centroid_proj[i, 1]],
            z=[centroid_proj[i, 2]],
            mode="markers+text",
            name=f"{REGIME_NAMES[regime]} (centroid)",
            marker=dict(
                size=14,
                color=REGIME_COLORS_3D[regime],
                symbol="diamond",
                line=dict(color="white", width=2),
                opacity=1.0,
            ),
            text=[REGIME_NAMES[regime]],
            textposition="top center",
            textfont=dict(color="white", size=11),
            showlegend=False,
            hovertemplate=(
                f"<b>{REGIME_NAMES[regime]} ATTRACTOR</b>"
                "<extra></extra>"
            ),
        ))

    if animate and len(projected) > 1:
        frames = _build_animation_frames(projected, regimes)
        fig.frames = frames
        fig.update_layout(
            updatemenus=[dict(
                type="buttons",
                showactive=False,
                y=1.05, x=0.0,
                xanchor="left", yanchor="top",
                pad=dict(t=0, r=10),
                buttons=[
                    dict(
                        label="▶ Play",
                        method="animate",
                        args=[None, dict(
                            frame=dict(duration=80, redraw=True),
                            fromcurrent=True,
                            transition=dict(duration=0),
                        )],
                    ),
                    dict(
                        label="⏸ Pause",
                        method="animate",
                        args=[[None], dict(
                            frame=dict(duration=0, redraw=False),
                            mode="immediate",
                            transition=dict(duration=0),
                        )],
                    ),
                ],
            )],
        )

    var_explained = pca.explained_variance_ratio_
    fig.update_layout(
        title=dict(
            text=(
                "Phase-Space Attractor Field (3D)<br>"
                f"<sub>PCA explained variance: "
                f"PC1={var_explained[0]:.0%}, "
                f"PC2={var_explained[1]:.0%}, "
                f"PC3={var_explained[2]:.0%}</sub>"
            ),
            x=0.5,
            xanchor="center",
        ),
        scene=dict(
            xaxis=dict(
                title=f"PC1 ({var_explained[0]:.0%})",
                backgroundcolor="rgb(15, 23, 42)",
                gridcolor="rgb(51, 65, 85)",
                showbackground=True,
                zerolinecolor="rgb(71, 85, 105)",
            ),
            yaxis=dict(
                title=f"PC2 ({var_explained[1]:.0%})",
                backgroundcolor="rgb(15, 23, 42)",
                gridcolor="rgb(51, 65, 85)",
                showbackground=True,
                zerolinecolor="rgb(71, 85, 105)",
            ),
            zaxis=dict(
                title=f"PC3 ({var_explained[2]:.0%})",
                backgroundcolor="rgb(15, 23, 42)",
                gridcolor="rgb(51, 65, 85)",
                showbackground=True,
                zerolinecolor="rgb(71, 85, 105)",
            ),
            bgcolor="rgb(15, 23, 42)",
            camera=dict(eye=dict(x=1.6, y=1.6, z=1.0)),
        ),
        paper_bgcolor="rgb(30, 41, 59)",
        font=dict(color="#f1f5f9"),
        height=650,
        legend=dict(
            bgcolor="rgba(15, 23, 42, 0.7)",
            bordercolor="rgb(71, 85, 105)",
            borderwidth=1,
        ),
        margin=dict(l=0, r=0, t=80, b=0),
    )

    return fig


def _build_animation_frames(
    projected: np.ndarray,
    regimes: list[Regime],
) -> list[go.Frame]:
    """Build animation frames revealing the trajectory bar-by-bar."""
    n = len(projected)
    step = max(1, n // 60)
    frames = []
    for k in range(step, n + 1, step):
        frame_data = []
        for regime in Regime:
            mask = np.array([r == regime for r in regimes[:k]])
            if mask.any():
                pts = projected[:k][mask]
                frame_data.append(go.Scatter3d(
                    x=pts[:, 0], y=pts[:, 1], z=pts[:, 2],
                    mode="markers",
                    marker=dict(
                        size=4,
                        color=REGIME_COLORS_3D[regime],
                        opacity=0.55,
                    ),
                ))
            else:
                frame_data.append(go.Scatter3d(
                    x=[], y=[], z=[], mode="markers",
                ))
        frame_data.append(go.Scatter3d(
            x=projected[:k, 0],
            y=projected[:k, 1],
            z=projected[:k, 2],
            mode="lines",
            line=dict(
                color=np.arange(k),
                colorscale="Viridis",
                width=3,
            ),
            opacity=0.6,
        ))
        frames.append(go.Frame(data=frame_data, name=str(k)))
    return frames
