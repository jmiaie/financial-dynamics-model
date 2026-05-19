"""Interactive 3D phase-space visualization.

Renders the 5D feature space as an interactive 3D dynamical-systems chart with:
- Regime basins of attraction (convex-hull mesh surfaces)
- Covariance ellipsoids (1σ confidence regions)
- Markov transition flow arrows between centroids
- Confidence-weighted marker sizing and opacity
- PCA loading vectors (feature interpretability axes)
- Regime transition event markers
- Velocity-encoded trajectory (speed of movement through state space)
- Nearest-centroid distance colorbar
- Volatility isosurface underlay (high-vol danger zones)
- Exponential-decay comet trail (recent bars glow)
- Stationary-distribution halos around attractors
- Floor shadow projection for depth perception
"""

from __future__ import annotations

from typing import Any

import numpy as np
import plotly.graph_objects as go
from scipy.interpolate import griddata
from scipy.spatial import ConvexHull, QhullError
from sklearn.decomposition import PCA

from financial_dynamics.forecasting import compute_stationary_distribution
from financial_dynamics.types import NUM_REGIMES, REGIME_NAMES, Regime
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

FEATURE_NAMES = ["Volatility", "Trend", "Drawdown", "Stress", "Shock"]


def build_phase_space_3d(
    feature_history: np.ndarray,
    regimes: list[Regime],
    centroids: np.ndarray,
    confidences: np.ndarray | None = None,
    transition_matrix: np.ndarray | None = None,
    show_trajectory: bool = True,
    show_basins: bool = True,
    show_ellipsoids: bool = False,
    show_transition_arrows: bool = True,
    show_vol_surface: bool = False,
    show_stationary_halos: bool = True,
    show_loadings: bool = True,
    show_transitions_markers: bool = True,
    animate: bool = False,
) -> go.Figure:
    """Build the interactive 3D phase-space figure with all enabled layers."""
    projected, centroid_proj, pca = fit_pca_projection(
        feature_history, centroids, n_components=3
    )

    if confidences is None:
        confidences = np.full(len(feature_history), 0.6)

    # Nearest-centroid distance for each point
    centroid_dists = np.array([
        np.min(np.linalg.norm(centroid_proj - p, axis=1))
        for p in projected
    ])

    fig = go.Figure()

    # Layer 1: Floor shadow (depth cue)
    fig.add_trace(_build_floor_shadow(projected, regimes))

    # Layer 2: Volatility isosurface
    if show_vol_surface and len(projected) >= 30:
        vol_trace = _build_vol_isosurface(projected, feature_history[:, 0])
        if vol_trace is not None:
            fig.add_trace(vol_trace)

    # Layer 3: Regime basins (convex hull)
    if show_basins:
        for trace in _build_basins(projected, regimes):
            fig.add_trace(trace)

    # Layer 3b: Covariance ellipsoids (1σ confidence)
    if show_ellipsoids:
        for trace in _build_covariance_ellipsoids(projected, regimes):
            fig.add_trace(trace)

    # Layer 4: Stationary distribution halos
    if show_stationary_halos and transition_matrix is not None:
        for trace in _build_stationary_halos(centroid_proj, transition_matrix):
            fig.add_trace(trace)

    # Layer 5: Regime-colored points with confidence encoding
    for trace in _build_points(projected, regimes, confidences):
        fig.add_trace(trace)

    # Layer 6: Velocity-encoded trajectory
    if show_trajectory and len(projected) > 1:
        fig.add_trace(_build_velocity_trajectory(projected, centroid_dists))

    # Layer 7: Comet trail
    if len(projected) > 3:
        fig.add_trace(_build_comet_trail(projected, confidences))

    # Layer 8: Regime transition event markers
    if show_transitions_markers and len(regimes) > 1:
        tr_trace = _build_transition_markers(projected, regimes)
        if tr_trace is not None:
            fig.add_trace(tr_trace)

    # Layer 9: Transition flow arrows
    if show_transition_arrows and transition_matrix is not None:
        for trace in _build_transition_arrows(centroid_proj, transition_matrix):
            fig.add_trace(trace)

    # Layer 10: PCA loading vectors (feature interpretability)
    if show_loadings:
        for trace in _build_pca_loadings(pca, projected):
            fig.add_trace(trace)

    # Layer 11: Centroid attractor markers
    for trace in _build_centroid_markers(centroid_proj, transition_matrix):
        fig.add_trace(trace)

    # Layer 12: Current position highlight
    fig.add_trace(_build_current_position(projected, regimes, confidences))

    if animate and len(projected) > 1:
        fig.frames = _build_animation_frames(projected, regimes, confidences)
        fig.update_layout(updatemenus=[_play_pause_buttons()])

    var_explained = pca.explained_variance_ratio_
    fig.update_layout(
        title=dict(
            text=(
                "<b>Phase-Space Attractor Field</b><br>"
                f"<sub style='color:#94a3b8'>"
                f"5D → 3D PCA · "
                f"PC1 {var_explained[0]:.0%} · "
                f"PC2 {var_explained[1]:.0%} · "
                f"PC3 {var_explained[2]:.0%} · "
                f"Σ = {sum(var_explained[:3]):.0%}"
                f"</sub>"
            ),
            x=0.5, xanchor="center",
            font=dict(size=15, color="#f1f5f9"),
        ),
        scene=_scene_layout(var_explained),
        paper_bgcolor="rgb(15, 23, 42)",
        font=dict(color="#cbd5e1", family="Inter, system-ui, sans-serif"),
        height=750,
        legend=dict(
            bgcolor="rgba(15, 23, 42, 0.9)",
            bordercolor="rgb(51, 65, 85)",
            borderwidth=1,
            x=0.01, y=0.99,
            font=dict(size=10),
            itemsizing="constant",
            tracegroupgap=3,
        ),
        margin=dict(l=0, r=0, t=75, b=0),
    )
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# Scene layout
# ─────────────────────────────────────────────────────────────────────────────

def _scene_layout(var_explained: np.ndarray) -> dict[str, Any]:
    def axis(label: str) -> dict[str, Any]:
        return dict(
            title=dict(text=label, font=dict(size=10, color="#64748b")),
            backgroundcolor="rgb(15, 23, 42)",
            gridcolor="rgba(51, 65, 85, 0.3)",
            gridwidth=1,
            showbackground=True,
            zerolinecolor="rgba(71, 85, 105, 0.4)",
            zerolinewidth=1,
            showspikes=False,
            tickfont=dict(size=8, color="#475569"),
            nticks=6,
        )
    return dict(
        xaxis=axis(f"PC1 ({var_explained[0]:.0%})"),
        yaxis=axis(f"PC2 ({var_explained[1]:.0%})"),
        zaxis=axis(f"PC3 ({var_explained[2]:.0%})"),
        bgcolor="rgb(15, 23, 42)",
        camera=dict(eye=dict(x=1.6, y=1.6, z=1.05), up=dict(x=0, y=0, z=1)),
        aspectmode="cube",
    )


# ─────────────────────────────────────────────────────────────────────────────
# 1. PCA loading vectors (feature interpretability)
# ─────────────────────────────────────────────────────────────────────────────

LOADING_COLORS = ["#ef4444", "#f59e0b", "#8b5cf6", "#06b6d4", "#ec4899"]


def _build_pca_loadings(
    pca: PCA,
    projected: np.ndarray,
) -> list[go.Scatter3d | go.Cone]:
    """Arrows from the origin showing how each original feature maps into 3D PCA space."""
    traces: list[go.Scatter3d | go.Cone] = []
    components = pca.components_  # (3, 5)
    scale = np.std(projected, axis=0).mean() * 1.8

    for j, name in enumerate(FEATURE_NAMES):
        direction = components[:, j] * scale
        color = LOADING_COLORS[j]

        traces.append(go.Scatter3d(
            x=[0, direction[0]], y=[0, direction[1]], z=[0, direction[2]],
            mode="lines+text",
            line=dict(color=color, width=4),
            text=["", name],
            textposition="top center",
            textfont=dict(color=color, size=10,
                          family="Inter, system-ui, sans-serif"),
            showlegend=False,
            hovertemplate=(
                f"<b>{name} loading</b><br>"
                f"PC1: {components[0, j]:.2f} · "
                f"PC2: {components[1, j]:.2f} · "
                f"PC3: {components[2, j]:.2f}"
                "<extra></extra>"
            ),
            name=f"Loading: {name}",
        ))

        tip = direction * 0.85
        traces.append(go.Cone(
            x=[tip[0]], y=[tip[1]], z=[tip[2]],
            u=[direction[0] * 0.15],
            v=[direction[1] * 0.15],
            w=[direction[2] * 0.15],
            colorscale=[[0, color], [1, color]],
            showscale=False,
            sizemode="absolute",
            sizeref=0.3,
            anchor="tail",
            showlegend=False,
            hoverinfo="skip",
            lighting=dict(ambient=0.9, diffuse=0.2),
        ))
    return traces


# ─────────────────────────────────────────────────────────────────────────────
# 2. Regime transition event markers
# ─────────────────────────────────────────────────────────────────────────────

def _build_transition_markers(
    projected: np.ndarray,
    regimes: list[Regime],
) -> go.Scatter3d | None:
    """'X' markers at exact bars where a regime change occurred."""
    changes: list[int] = []
    for i in range(1, len(regimes)):
        if regimes[i] != regimes[i - 1]:
            changes.append(i)
    if not changes:
        return None
    pts = projected[changes]
    new_regimes = [regimes[i] for i in changes]
    colors = [REGIME_COLORS_3D[r] for r in new_regimes]
    labels = [
        f"{REGIME_NAMES[regimes[i-1]]} → {REGIME_NAMES[regimes[i]]}"
        for i in changes
    ]
    return go.Scatter3d(
        x=pts[:, 0], y=pts[:, 1], z=pts[:, 2],
        mode="markers",
        name="Regime shifts",
        marker=dict(
            size=7,
            color=colors,
            symbol="x",
            line=dict(color="rgba(241, 245, 249, 0.8)", width=1.5),
        ),
        customdata=labels,
        hovertemplate="<b>%{customdata}</b><extra></extra>",
        showlegend=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# 3. Covariance ellipsoids (1σ confidence regions)
# ─────────────────────────────────────────────────────────────────────────────

def _build_covariance_ellipsoids(
    projected: np.ndarray,
    regimes: list[Regime],
    n_std: float = 1.5,
    resolution: int = 16,
) -> list[go.Mesh3d]:
    """1σ ellipsoid for each regime fitted from the covariance of its points."""
    traces: list[go.Mesh3d] = []
    u = np.linspace(0, 2 * np.pi, resolution)
    v = np.linspace(0, np.pi, resolution)
    sphere_x = np.outer(np.cos(u), np.sin(v))
    sphere_y = np.outer(np.sin(u), np.sin(v))
    sphere_z = np.outer(np.ones_like(u), np.cos(v))
    sphere = np.column_stack([sphere_x.ravel(), sphere_y.ravel(), sphere_z.ravel()])

    for regime in Regime:
        mask = np.array([r == regime for r in regimes])
        pts = projected[mask]
        if len(pts) < 5:
            continue
        mean = pts.mean(axis=0)
        cov = np.cov(pts.T)
        try:
            eigenvalues, eigenvectors = np.linalg.eigh(cov)
        except np.linalg.LinAlgError:
            continue
        eigenvalues = np.maximum(eigenvalues, 1e-10)
        radii = n_std * np.sqrt(eigenvalues)
        ellipsoid = sphere * radii @ eigenvectors.T + mean
        rgb = REGIME_COLORS_RGB[regime]
        traces.append(go.Mesh3d(
            x=ellipsoid[:, 0], y=ellipsoid[:, 1], z=ellipsoid[:, 2],
            alphahull=0,
            color=f"rgba({rgb[0]}, {rgb[1]}, {rgb[2]}, 0.08)",
            opacity=0.08,
            flatshading=False,
            showlegend=False,
            hoverinfo="skip",
            name=f"{REGIME_NAMES[regime]} 1σ",
        ))
    return traces


# ─────────────────────────────────────────────────────────────────────────────
# 4. Velocity-encoded trajectory
# ─────────────────────────────────────────────────────────────────────────────

def _build_velocity_trajectory(
    projected: np.ndarray,
    centroid_dists: np.ndarray,
) -> go.Scatter3d:
    """Trajectory colored by speed (inter-bar distance) through state space.

    Also encodes nearest-centroid distance as line width so uncertain
    regions (far from any attractor) appear thicker.
    """
    n = len(projected)
    speeds = np.zeros(n)
    speeds[1:] = np.linalg.norm(np.diff(projected, axis=0), axis=1)
    speeds[0] = speeds[1]

    color_vals = speeds / (speeds.max() + 1e-10)

    return go.Scatter3d(
        x=projected[:, 0], y=projected[:, 1], z=projected[:, 2],
        mode="lines",
        name="Trajectory (velocity)",
        line=dict(
            color=color_vals,
            colorscale=[
                [0.0, "rgba(20, 184, 166, 0.6)"],   # slow: calm teal
                [0.3, "rgba(13, 115, 119, 0.75)"],
                [0.6, "rgba(245, 158, 11, 0.85)"],   # medium: amber
                [1.0, "rgba(239, 68, 68, 0.95)"],    # fast: red (transition)
            ],
            width=4,
            showscale=True,
            colorbar=dict(
                title=dict(text="Speed", font=dict(size=10, color="#94a3b8")),
                len=0.3, thickness=10,
                x=0.98, y=0.85,
                tickfont=dict(size=8, color="#64748b"),
                bgcolor="rgba(15, 23, 42, 0.8)",
                bordercolor="rgb(51, 65, 85)",
                borderwidth=1,
                tickvals=[],
                ticktext=[],
            ),
        ),
        customdata=np.column_stack([speeds, centroid_dists]),
        hovertemplate=(
            "Speed: %{customdata[0]:.3f}<br>"
            "Dist to attractor: %{customdata[1]:.2f}"
            "<extra></extra>"
        ),
        showlegend=True,
        legendgroup="trail",
    )


# ─────────────────────────────────────────────────────────────────────────────
# 4b. Volatility isosurface
# ─────────────────────────────────────────────────────────────────────────────

def _build_vol_isosurface(
    projected: np.ndarray,
    volatility: np.ndarray,
) -> go.Isosurface | None:
    """Render a translucent isosurface at the 75th percentile volatility level."""
    n_grid = 12
    mins = projected.min(axis=0)
    maxs = projected.max(axis=0)
    pad = (maxs - mins) * 0.05
    x_lin = np.linspace(mins[0] - pad[0], maxs[0] + pad[0], n_grid)
    y_lin = np.linspace(mins[1] - pad[1], maxs[1] + pad[1], n_grid)
    z_lin = np.linspace(mins[2] - pad[2], maxs[2] + pad[2], n_grid)
    xg, yg, zg = np.meshgrid(x_lin, y_lin, z_lin, indexing="ij")
    grid_pts = np.column_stack([xg.ravel(), yg.ravel(), zg.ravel()])

    try:
        vol_grid = griddata(projected, volatility, grid_pts, method="linear")
    except (ValueError, QhullError):
        return None

    vol_grid = np.where(np.isnan(vol_grid), 0.0, vol_grid)
    p75 = float(np.percentile(volatility, 75))

    return go.Isosurface(
        x=grid_pts[:, 0], y=grid_pts[:, 1], z=grid_pts[:, 2],
        value=vol_grid,
        isomin=p75,
        isomax=float(volatility.max()),
        surface_count=2,
        opacity=0.08,
        colorscale=[[0, "rgba(239, 68, 68, 0.0)"],
                    [0.5, "rgba(239, 68, 68, 0.3)"],
                    [1.0, "rgba(239, 68, 68, 0.6)"]],
        showscale=False,
        caps=dict(x_show=False, y_show=False, z_show=False),
        name="High-vol zone",
        showlegend=True,
        hoverinfo="skip",
    )


# ─────────────────────────────────────────────────────────────────────────────
# 5. Comet trail (exponential decay on recent bars)
# ─────────────────────────────────────────────────────────────────────────────

def _build_comet_trail(
    projected: np.ndarray,
    confidences: np.ndarray,
    tail_length: int = 20,
) -> go.Scatter3d:
    """Last N bars as individually-sized markers with exponential brightness decay."""
    n = len(projected)
    tail = min(tail_length, n)
    pts = projected[-tail:]
    conf = confidences[-tail:]

    decay = np.exp(np.linspace(-2.5, 0.0, tail))
    sizes = (4.0 + 10.0 * conf * decay)
    opacities = 0.15 + 0.75 * decay

    colors = [
        f"rgba(20, 184, 166, {o:.3f})" for o in opacities
    ]

    return go.Scatter3d(
        x=pts[:, 0], y=pts[:, 1], z=pts[:, 2],
        mode="markers",
        name="Recent trail",
        marker=dict(
            size=sizes,
            color=colors,
            symbol="circle",
            line=dict(width=0),
        ),
        hoverinfo="skip",
        showlegend=True,
        legendgroup="trail",
    )


# ─────────────────────────────────────────────────────────────────────────────
# 6. Stationary distribution halos
# ─────────────────────────────────────────────────────────────────────────────

def _build_stationary_halos(
    centroid_proj: np.ndarray,
    transition_matrix: np.ndarray,
) -> list[go.Mesh3d]:
    """Translucent sphere around each centroid sized by stationary distribution."""
    pi = _compute_stationary(transition_matrix)
    traces: list[go.Mesh3d] = []
    for i, regime in enumerate(Regime):
        weight = float(pi[i])
        if weight < 0.01:
            continue
        radius = 0.3 + 1.5 * weight
        sphere = _sphere_mesh(centroid_proj[i], radius, resolution=14)
        rgb = REGIME_COLORS_RGB[regime]
        traces.append(go.Mesh3d(
            x=sphere[:, 0], y=sphere[:, 1], z=sphere[:, 2],
            alphahull=0,
            color=f"rgba({rgb[0]}, {rgb[1]}, {rgb[2]}, 0.06)",
            opacity=0.06,
            flatshading=False,
            showlegend=False,
            hovertemplate=(
                f"<b>{REGIME_NAMES[regime]}</b><br>"
                f"Stationary weight: π = {weight:.1%}"
                "<extra></extra>"
            ),
            name=f"{REGIME_NAMES[regime]} halo",
        ))
    return traces


def _compute_stationary(T: np.ndarray) -> np.ndarray:
    """Stationary distribution from the transition matrix.

    Delegates to the canonical implementation in forecasting module.
    """
    return compute_stationary_distribution(T).probs


def _sphere_mesh(center: np.ndarray, radius: float, resolution: int = 14) -> np.ndarray:
    """Generate sphere surface points for Mesh3d alphahull."""
    u = np.linspace(0, 2 * np.pi, resolution)
    v = np.linspace(0, np.pi, resolution)
    uu, vv = np.meshgrid(u, v)
    x = center[0] + radius * np.cos(uu) * np.sin(vv)
    y = center[1] + radius * np.sin(uu) * np.sin(vv)
    z = center[2] + radius * np.cos(vv)
    return np.column_stack([x.ravel(), y.ravel(), z.ravel()])


# ─────────────────────────────────────────────────────────────────────────────
# 7. Floor shadow (depth perception)
# ─────────────────────────────────────────────────────────────────────────────

def _build_floor_shadow(
    projected: np.ndarray,
    regimes: list[Regime],
) -> go.Scatter3d:
    """Project points to the z-floor as a subtle shadow for depth cue."""
    z_floor = float(projected[:, 2].min()) - 0.3
    colors = [
        f"rgba({REGIME_COLORS_RGB[r][0]}, {REGIME_COLORS_RGB[r][1]}, "
        f"{REGIME_COLORS_RGB[r][2]}, 0.07)"
        for r in regimes
    ]
    return go.Scatter3d(
        x=projected[:, 0],
        y=projected[:, 1],
        z=np.full(len(projected), z_floor),
        mode="markers",
        marker=dict(size=2.5, color=colors, symbol="circle", line=dict(width=0)),
        showlegend=False,
        hoverinfo="skip",
        name="shadow",
    )


# ─────────────────────────────────────────────────────────────────────────────
# Regime basins (convex hulls)
# ─────────────────────────────────────────────────────────────────────────────

def _build_basins(
    projected: np.ndarray,
    regimes: list[Regime],
) -> list[go.Mesh3d]:
    """Convex-hull mesh for each regime — its basin of attraction."""
    traces: list[go.Mesh3d] = []
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
            opacity=0.09,
            flatshading=True,
            name=f"{REGIME_NAMES[regime]} basin",
            showlegend=False,
            hoverinfo="skip",
            lighting=dict(
                ambient=0.7, diffuse=0.45, specular=0.1,
                roughness=0.95, fresnel=0.02,
            ),
            lightposition=dict(x=100, y=100, z=200),
        ))
    return traces


# ─────────────────────────────────────────────────────────────────────────────
# Confidence-encoded scatter
# ─────────────────────────────────────────────────────────────────────────────

def _build_points(
    projected: np.ndarray,
    regimes: list[Regime],
    confidences: np.ndarray,
) -> list[go.Scatter3d]:
    """Regime-colored points with size & opacity driven by posterior confidence."""
    traces: list[go.Scatter3d] = []
    for regime in Regime:
        mask = np.array([r == regime for r in regimes])
        if not mask.any():
            continue
        pts = projected[mask]
        conf = confidences[mask]
        sizes = 2.5 + 6.5 * np.clip(conf, 0.0, 1.0)
        opacities = 0.2 + 0.55 * np.clip(conf, 0.0, 1.0)
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
            legendgroup=f"regime_{regime.name}",
        ))
    return traces


# ─────────────────────────────────────────────────────────────────────────────
# Transition flow arrows
# ─────────────────────────────────────────────────────────────────────────────

def _build_transition_arrows(
    centroid_proj: np.ndarray,
    transition_matrix: np.ndarray,
    threshold: float = 0.08,
) -> list[go.Scatter3d | go.Cone]:
    """3D flow arrows between centroids weighted by transition probability."""
    traces: list[go.Scatter3d | go.Cone] = []
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

            line_width = 2.0 + 7.0 * prob
            opacity = min(0.3 + 0.55 * prob, 0.9)
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
                    f"P = {prob:.1%}"
                    "<extra></extra>"
                ),
                name=f"{REGIME_NAMES[src_regime]}→{REGIME_NAMES[dst_regime]}",
            ))

            traces.append(go.Cone(
                x=[shaft_end[0]], y=[shaft_end[1]], z=[shaft_end[2]],
                u=[direction[0] * 0.22],
                v=[direction[1] * 0.22],
                w=[direction[2] * 0.22],
                colorscale=[[0, line_color], [1, line_color]],
                showscale=False,
                sizemode="absolute",
                sizeref=0.35 + 1.0 * prob,
                anchor="tail",
                showlegend=False,
                hoverinfo="skip",
                lighting=dict(ambient=0.8, diffuse=0.3),
            ))
    return traces


# ─────────────────────────────────────────────────────────────────────────────
# Centroid markers (enhanced with stationary weight labels)
# ─────────────────────────────────────────────────────────────────────────────

def _build_centroid_markers(
    centroid_proj: np.ndarray,
    transition_matrix: np.ndarray | None = None,
) -> list[go.Scatter3d]:
    """Diamond attractor markers with stationary weight annotation."""
    pi = (_compute_stationary(transition_matrix)
          if transition_matrix is not None
          else np.full(NUM_REGIMES, 0.25))
    traces: list[go.Scatter3d] = []
    for i, regime in enumerate(Regime):
        weight = float(pi[i])
        label = f"{REGIME_NAMES[regime]}\nπ={weight:.0%}"
        traces.append(go.Scatter3d(
            x=[centroid_proj[i, 0]],
            y=[centroid_proj[i, 1]],
            z=[centroid_proj[i, 2]],
            mode="markers+text",
            name=f"{REGIME_NAMES[regime]} attractor",
            marker=dict(
                size=16 + 8 * weight,
                color=REGIME_COLORS_3D[regime],
                symbol="diamond",
                line=dict(color="rgba(241, 245, 249, 0.9)", width=2),
                opacity=1.0,
            ),
            text=[label],
            textposition="top center",
            textfont=dict(
                color="#e2e8f0", size=11,
                family="Inter, system-ui, sans-serif",
            ),
            showlegend=False,
            hovertemplate=(
                f"<b>{REGIME_NAMES[regime]} ATTRACTOR</b><br>"
                f"Stationary weight π = {weight:.1%}<br>"
                "(centroid in 5D feature space)"
                "<extra></extra>"
            ),
        ))
    return traces


# ─────────────────────────────────────────────────────────────────────────────
# Current position marker
# ─────────────────────────────────────────────────────────────────────────────

def _build_current_position(
    projected: np.ndarray,
    regimes: list[Regime],
    confidences: np.ndarray | None = None,
) -> go.Scatter3d:
    """'You are here' pulse ring at the latest bar."""
    if len(projected) == 0:
        return go.Scatter3d(x=[], y=[], z=[], mode="markers", showlegend=False)
    last = projected[-1]
    current_regime = regimes[-1]
    conf = float(confidences[-1]) if confidences is not None else 0.0
    rgb = REGIME_COLORS_RGB[current_regime]
    return go.Scatter3d(
        x=[last[0]], y=[last[1]], z=[last[2]],
        mode="markers",
        name="NOW",
        marker=dict(
            size=16,
            color=f"rgba({rgb[0]}, {rgb[1]}, {rgb[2]}, 0.25)",
            line=dict(
                color=f"rgba({rgb[0]}, {rgb[1]}, {rgb[2]}, 0.95)",
                width=3.5,
            ),
            symbol="circle",
        ),
        hovertemplate=(
            f"<b>CURRENT: {REGIME_NAMES[current_regime]}</b><br>"
            f"Confidence: {conf:.1%}"
            "<extra></extra>"
        ),
        showlegend=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Animation
# ─────────────────────────────────────────────────────────────────────────────

def _build_animation_frames(
    projected: np.ndarray,
    regimes: list[Regime],
    confidences: np.ndarray,
) -> list[go.Frame]:
    """Frame-by-frame reveal of the trajectory."""
    n = len(projected)
    step = max(1, n // 60)
    frames: list[go.Frame] = []
    for k in range(step, n + 1, step):
        frame_data: list[go.Scatter3d] = []
        # floor shadow
        z_floor = float(projected[:k, 2].min()) - 0.3
        frame_data.append(go.Scatter3d(
            x=projected[:k, 0], y=projected[:k, 1],
            z=np.full(k, z_floor),
            mode="markers",
            marker=dict(size=2, color="rgba(100, 116, 139, 0.06)"),
        ))
        for regime in Regime:
            mask = np.array([r == regime for r in regimes[:k]])
            if mask.any():
                pts = projected[:k][mask]
                conf = confidences[:k][mask]
                sizes = 2.5 + 6.5 * np.clip(conf, 0.0, 1.0)
                rgb = REGIME_COLORS_RGB[regime]
                opacities = 0.2 + 0.55 * np.clip(conf, 0.0, 1.0)
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
        # trajectory
        decay = np.linspace(0.0, 1.0, k)
        frame_data.append(go.Scatter3d(
            x=projected[:k, 0], y=projected[:k, 1], z=projected[:k, 2],
            mode="lines",
            line=dict(
                color=decay,
                colorscale=[[0, "rgba(71, 85, 105, 0.0)"],
                            [1.0, "rgba(20, 184, 166, 0.9)"]],
                width=3.5,
            ),
        ))
        frames.append(go.Frame(data=frame_data, name=str(k)))
    return frames


def _play_pause_buttons() -> dict[str, Any]:
    return dict(
        type="buttons",
        showactive=False,
        y=1.05, x=0.0,
        xanchor="left", yanchor="top",
        pad=dict(t=0, r=10),
        bgcolor="rgba(15, 23, 42, 0.85)",
        bordercolor="rgb(51, 65, 85)",
        font=dict(color="#f1f5f9", size=11),
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
