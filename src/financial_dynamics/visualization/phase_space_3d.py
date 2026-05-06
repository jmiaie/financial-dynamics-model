"""Institutional-grade 3D phase-space visualization.

Renders the 5D feature space as an interactive 3D dynamical-systems chart with:
- Regime basins of attraction (convex-hull mesh surfaces)
- Markov transition flow arrows between centroids
- Confidence-weighted marker sizing and opacity
- Time-decay trail for the current trajectory
"""

from __future__ import annotations

import numpy as np
import plotly.graph_objects as go
from scipy.spatial import ConvexHull, QhullError

from financial_dynamics.types import Regime, REGIME_NAMES
from financial_dynamics.visualization._utils import fit_pca_projection

REGIME_COLORS_3D = {
    Regime.CALM_TREND: "#10b981",
    Regime.VOLATILE_TREND: "#f59e0b",
    Regime.CHOP: "#8b5cf6",
    Regime.RISK_OFF: "#ef4444",
}

REGIME_COLORS_RGB = {
    Regime.CALM_TREND: (16, 185, 129),
    Regime.VOLATILE_TREND: (245, 158, 11),
    Regime.CHOP: (139, 92, 246),
    Regime.RISK_OFF: (239, 68, 68),
}


def build_phase_space_3d(
    feature_history: np.ndarray,
    regimes: list[Regime],
    centroids: np.ndarray,
    confidences: np.ndarray | None = None,
    transition_matrix: np.ndarray | None = None,
    show_trajectory: bool = True,
    show_basins: bool = True,
    show_transition_arrows: bool = True,
    animate: bool = False,
) -> go.Figure:
    """Build an institutional-grade 3D phase-space plot.

    Args:
        feature_history: shape (N, 5) feature vectors.
        regimes: list of N regime assignments.
        centroids: shape (4, 5) centroid matrix.
        confidences: optional shape (N,) array of posterior probabilities
            in [0, 1]. Drives marker size and opacity.
        transition_matrix: optional shape (4, 4) Markov transition matrix.
            Renders flow arrows between regime attractors.
        show_trajectory: draw the time-ordered path through state space.
        show_basins: render translucent convex-hull basins for each regime.
        show_transition_arrows: render flow arrows from the transition matrix.
        animate: emit time-slider animation frames.
    """
    projected, centroid_proj, pca = fit_pca_projection(
        feature_history, centroids, n_components=3
    )

    if confidences is None:
        confidences = np.full(len(feature_history), 0.6)

    fig = go.Figure()

    if show_basins:
        for trace in _build_basins(projected, regimes):
            fig.add_trace(trace)

    for trace in _build_points(projected, regimes, confidences):
        fig.add_trace(trace)

    if show_trajectory and len(projected) > 1:
        fig.add_trace(_build_trajectory(projected))

    if show_transition_arrows and transition_matrix is not None:
        for trace in _build_transition_arrows(centroid_proj, transition_matrix):
            fig.add_trace(trace)

    for trace in _build_centroid_markers(centroid_proj):
        fig.add_trace(trace)

    fig.add_trace(_build_current_position(projected))

    if animate and len(projected) > 1:
        fig.frames = _build_animation_frames(projected, regimes, confidences)
        fig.update_layout(updatemenus=[_play_pause_buttons()])

    var_explained = pca.explained_variance_ratio_
    fig.update_layout(
        title=dict(
            text=(
                "<b>Phase-Space Attractor Field</b><br>"
                f"<sub style='color:#94a3b8'>"
                f"5D → 3D PCA projection · explained variance: "
                f"PC1 {var_explained[0]:.0%} · "
                f"PC2 {var_explained[1]:.0%} · "
                f"PC3 {var_explained[2]:.0%}"
                f"</sub>"
            ),
            x=0.5, xanchor="center",
            font=dict(size=16, color="#f1f5f9"),
        ),
        scene=_scene_layout(var_explained),
        paper_bgcolor="rgb(15, 23, 42)",
        font=dict(color="#cbd5e1", family="Inter, system-ui, sans-serif"),
        height=720,
        legend=dict(
            bgcolor="rgba(15, 23, 42, 0.85)",
            bordercolor="rgb(51, 65, 85)",
            borderwidth=1,
            x=0.02, y=0.98,
            font=dict(size=11),
        ),
        margin=dict(l=0, r=0, t=80, b=0),
    )
    return fig


def _scene_layout(var_explained: np.ndarray) -> dict:
    """Institutional dark-theme 3D scene styling."""
    def axis(label: str) -> dict:
        return dict(
            title=dict(text=label, font=dict(size=11, color="#94a3b8")),
            backgroundcolor="rgb(15, 23, 42)",
            gridcolor="rgba(71, 85, 105, 0.35)",
            gridwidth=1,
            showbackground=True,
            zerolinecolor="rgba(100, 116, 139, 0.5)",
            zerolinewidth=1,
            showspikes=False,
            tickfont=dict(size=9, color="#64748b"),
        )
    return dict(
        xaxis=axis(f"PC1 ({var_explained[0]:.0%})"),
        yaxis=axis(f"PC2 ({var_explained[1]:.0%})"),
        zaxis=axis(f"PC3 ({var_explained[2]:.0%})"),
        bgcolor="rgb(15, 23, 42)",
        camera=dict(eye=dict(x=1.7, y=1.7, z=1.1), up=dict(x=0, y=0, z=1)),
        aspectmode="cube",
    )


def _build_basins(
    projected: np.ndarray,
    regimes: list[Regime],
) -> list[go.Mesh3d]:
    """Convex-hull mesh for each regime — its basin of attraction."""
    traces = []
    for regime in Regime:
        mask = np.array([r == regime for r in regimes])
        pts = projected[mask]
        if len(pts) < 4:
            continue
        try:
            hull = ConvexHull(pts)
        except (QhullError, ValueError):
            continue
        i_idx, j_idx, k_idx = hull.simplices.T
        traces.append(go.Mesh3d(
            x=pts[:, 0], y=pts[:, 1], z=pts[:, 2],
            i=i_idx, j=j_idx, k=k_idx,
            color=REGIME_COLORS_3D[regime],
            opacity=0.10,
            flatshading=True,
            name=f"{REGIME_NAMES[regime]} basin",
            showlegend=False,
            hoverinfo="skip",
            lighting=dict(
                ambient=0.65, diffuse=0.5, specular=0.15,
                roughness=0.9, fresnel=0.05,
            ),
            lightposition=dict(x=100, y=100, z=200),
        ))
    return traces


def _build_points(
    projected: np.ndarray,
    regimes: list[Regime],
    confidences: np.ndarray,
) -> list[go.Scatter3d]:
    """Regime-colored points with size & opacity driven by posterior confidence."""
    traces = []
    for regime in Regime:
        mask = np.array([r == regime for r in regimes])
        if not mask.any():
            continue
        pts = projected[mask]
        conf = confidences[mask]
        sizes = 3.0 + 7.0 * np.clip(conf, 0.0, 1.0)
        opacities = 0.25 + 0.55 * np.clip(conf, 0.0, 1.0)
        rgb = REGIME_COLORS_RGB[regime]
        marker_colors = [
            f"rgba({rgb[0]}, {rgb[1]}, {rgb[2]}, {o:.2f})"
            for o in opacities
        ]
        traces.append(go.Scatter3d(
            x=pts[:, 0], y=pts[:, 1], z=pts[:, 2],
            mode="markers",
            name=REGIME_NAMES[regime],
            marker=dict(
                size=sizes,
                color=marker_colors,
                line=dict(width=0),
            ),
            customdata=np.column_stack([conf]),
            hovertemplate=(
                f"<b>{REGIME_NAMES[regime]}</b><br>"
                "Confidence: %{customdata[0]:.1%}<br>"
                "PC1: %{x:.2f} · PC2: %{y:.2f} · PC3: %{z:.2f}"
                "<extra></extra>"
            ),
        ))
    return traces


def _build_trajectory(projected: np.ndarray) -> go.Scatter3d:
    """Time-decayed trajectory line — recent points brightest."""
    n = len(projected)
    decay = np.linspace(0.15, 1.0, n)
    return go.Scatter3d(
        x=projected[:, 0], y=projected[:, 1], z=projected[:, 2],
        mode="lines",
        name="Trajectory (time)",
        line=dict(
            color=decay,
            colorscale=[[0, "rgba(100, 116, 139, 0.0)"],
                        [0.5, "rgba(13, 115, 119, 0.4)"],
                        [1.0, "rgba(20, 184, 166, 0.95)"]],
            width=4,
            showscale=False,
        ),
        hoverinfo="skip",
        showlegend=True,
    )


def _build_transition_arrows(
    centroid_proj: np.ndarray,
    transition_matrix: np.ndarray,
    threshold: float = 0.08,
) -> list:
    """3D flow arrows between centroids weighted by transition probability."""
    traces = []
    regimes_list = list(Regime)
    for i, src_regime in enumerate(regimes_list):
        for j, dst_regime in enumerate(regimes_list):
            if i == j:
                continue
            prob = float(transition_matrix[i, j])
            if prob < threshold:
                continue

            src = centroid_proj[i]
            dst = centroid_proj[j]
            direction = dst - src
            shaft_end = src + 0.78 * direction

            line_width = 2.0 + 8.0 * prob
            opacity = min(0.35 + 0.6 * prob, 0.95)
            rgb = REGIME_COLORS_RGB[src_regime]
            line_color = f"rgba({rgb[0]}, {rgb[1]}, {rgb[2]}, {opacity:.2f})"

            traces.append(go.Scatter3d(
                x=[src[0], shaft_end[0]],
                y=[src[1], shaft_end[1]],
                z=[src[2], shaft_end[2]],
                mode="lines",
                line=dict(color=line_color, width=line_width),
                showlegend=False,
                hovertemplate=(
                    f"<b>{REGIME_NAMES[src_regime]} → "
                    f"{REGIME_NAMES[dst_regime]}</b><br>"
                    f"P(transition) = {prob:.1%}"
                    "<extra></extra>"
                ),
                name=f"{REGIME_NAMES[src_regime]} → {REGIME_NAMES[dst_regime]}",
            ))

            traces.append(go.Cone(
                x=[shaft_end[0]], y=[shaft_end[1]], z=[shaft_end[2]],
                u=[direction[0] * 0.22],
                v=[direction[1] * 0.22],
                w=[direction[2] * 0.22],
                colorscale=[[0, line_color], [1, line_color]],
                showscale=False,
                sizemode="absolute",
                sizeref=0.4 + 1.2 * prob,
                anchor="tail",
                showlegend=False,
                hoverinfo="skip",
                lighting=dict(ambient=0.8, diffuse=0.3),
            ))
    return traces


def _build_centroid_markers(centroid_proj: np.ndarray) -> list[go.Scatter3d]:
    """Diamond attractor markers with text labels."""
    traces = []
    for i, regime in enumerate(Regime):
        traces.append(go.Scatter3d(
            x=[centroid_proj[i, 0]],
            y=[centroid_proj[i, 1]],
            z=[centroid_proj[i, 2]],
            mode="markers+text",
            name=f"{REGIME_NAMES[regime]} attractor",
            marker=dict(
                size=18,
                color=REGIME_COLORS_3D[regime],
                symbol="diamond",
                line=dict(color="rgba(241, 245, 249, 0.95)", width=2.5),
                opacity=1.0,
            ),
            text=[f"<b>{REGIME_NAMES[regime]}</b>"],
            textposition="top center",
            textfont=dict(color="#f1f5f9", size=12,
                          family="Inter, system-ui, sans-serif"),
            showlegend=False,
            hovertemplate=(
                f"<b>{REGIME_NAMES[regime]} ATTRACTOR</b><br>"
                "(centroid in feature space)"
                "<extra></extra>"
            ),
        ))
    return traces


def _build_current_position(projected: np.ndarray) -> go.Scatter3d:
    """Highlight the latest bar — 'you are here' marker."""
    if len(projected) == 0:
        return go.Scatter3d(x=[], y=[], z=[], mode="markers", showlegend=False)
    last = projected[-1]
    return go.Scatter3d(
        x=[last[0]], y=[last[1]], z=[last[2]],
        mode="markers",
        name="Current position",
        marker=dict(
            size=14,
            color="rgba(20, 184, 166, 0.0)",
            line=dict(color="rgba(20, 184, 166, 0.95)", width=3),
            symbol="circle",
        ),
        hovertemplate="<b>CURRENT POSITION</b><extra></extra>",
        showlegend=True,
    )


def _build_animation_frames(
    projected: np.ndarray,
    regimes: list[Regime],
    confidences: np.ndarray,
) -> list[go.Frame]:
    """Frame-by-frame reveal of the trajectory."""
    n = len(projected)
    step = max(1, n // 60)
    frames = []
    for k in range(step, n + 1, step):
        frame_data = []
        for regime in Regime:
            mask = np.array([r == regime for r in regimes[:k]])
            if mask.any():
                pts = projected[:k][mask]
                conf = confidences[:k][mask]
                sizes = 3.0 + 7.0 * np.clip(conf, 0.0, 1.0)
                rgb = REGIME_COLORS_RGB[regime]
                opacities = 0.25 + 0.55 * np.clip(conf, 0.0, 1.0)
                colors = [
                    f"rgba({rgb[0]}, {rgb[1]}, {rgb[2]}, {o:.2f})"
                    for o in opacities
                ]
                frame_data.append(go.Scatter3d(
                    x=pts[:, 0], y=pts[:, 1], z=pts[:, 2],
                    mode="markers",
                    marker=dict(size=sizes, color=colors),
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
                color=np.linspace(0.15, 1.0, k),
                colorscale=[[0, "rgba(100, 116, 139, 0.0)"],
                            [1.0, "rgba(20, 184, 166, 0.95)"]],
                width=4,
            ),
        ))
        frames.append(go.Frame(data=frame_data, name=str(k)))
    return frames


def _play_pause_buttons() -> dict:
    return dict(
        type="buttons",
        showactive=False,
        y=1.05, x=0.0,
        xanchor="left", yanchor="top",
        pad=dict(t=0, r=10),
        bgcolor="rgba(15, 23, 42, 0.8)",
        bordercolor="rgb(51, 65, 85)",
        font=dict(color="#f1f5f9"),
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
    )
