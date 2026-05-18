"""Tests for visualization components."""

import matplotlib
import numpy as np
import pytest

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from financial_dynamics.phase1_regimes.regime_definitions import get_default_centroids
from financial_dynamics.pipeline import FinancialDynamicsPipeline
from financial_dynamics.types import Regime
from financial_dynamics.visualization.dashboard import SystemDashboard
from financial_dynamics.visualization.phase_space import PhaseSpacePlotter
from financial_dynamics.visualization.phase_space_3d import build_phase_space_3d
from financial_dynamics.visualization.trajectory import TrajectoryPlotter
from financial_dynamics.visualization.vector_field import VectorFieldPlotter


@pytest.fixture
def sample_features() -> np.ndarray:
    rng = np.random.default_rng(42)
    return rng.random((50, 5))


@pytest.fixture
def sample_regimes() -> list[Regime]:
    return [Regime(i % 4) for i in range(50)]


@pytest.fixture
def sample_centroids() -> np.ndarray:
    return get_default_centroids()


class TestPhaseSpacePlotter:
    def test_plot_generates_figure(self, sample_features, sample_regimes, sample_centroids):
        plotter = PhaseSpacePlotter(sample_centroids)
        fig = plotter.plot(sample_features, sample_regimes)
        assert fig is not None
        plt.close(fig)

    def test_plot_with_provided_axes(self, sample_features, sample_regimes, sample_centroids):
        fig, ax = plt.subplots()
        plotter = PhaseSpacePlotter(sample_centroids)
        result_fig = plotter.plot(sample_features, sample_regimes, ax=ax)
        assert result_fig is fig
        plt.close(fig)


class TestPhaseSpace3D:
    def test_builds_figure(self, sample_features, sample_regimes, sample_centroids):
        fig = build_phase_space_3d(sample_features, sample_regimes, sample_centroids)
        assert fig is not None
        assert len(fig.data) >= 5
        allowed_types = {"scatter3d", "mesh3d", "cone", "isosurface"}
        for trace in fig.data:
            assert trace.type in allowed_types

    def test_animation_frames(self, sample_features, sample_regimes, sample_centroids):
        fig = build_phase_space_3d(
            sample_features, sample_regimes, sample_centroids, animate=True
        )
        assert len(fig.frames) > 0

    def test_with_basins_and_arrows(
        self, sample_features, sample_regimes, sample_centroids
    ):
        confidences = np.linspace(0.4, 0.95, len(sample_features))
        T = np.array([
            [0.85, 0.10, 0.04, 0.01],
            [0.15, 0.70, 0.10, 0.05],
            [0.20, 0.10, 0.65, 0.05],
            [0.05, 0.15, 0.10, 0.70],
        ])
        fig = build_phase_space_3d(
            sample_features, sample_regimes, sample_centroids,
            confidences=confidences, transition_matrix=T,
            show_basins=True, show_transition_arrows=True,
        )
        types = [t.type for t in fig.data]
        assert "mesh3d" in types  # regime basins
        assert "cone" in types  # transition arrowheads

    def test_disable_basins_and_arrows(
        self, sample_features, sample_regimes, sample_centroids
    ):
        T = np.eye(4)
        fig = build_phase_space_3d(
            sample_features, sample_regimes, sample_centroids,
            transition_matrix=T,
            show_basins=False, show_transition_arrows=False,
            show_stationary_halos=False, show_loadings=False,
            show_ellipsoids=False,
        )
        types = {t.type for t in fig.data}
        assert "mesh3d" not in types
        assert "cone" not in types

    def test_vol_surface(self, sample_features, sample_regimes, sample_centroids):
        fig = build_phase_space_3d(
            sample_features, sample_regimes, sample_centroids,
            show_vol_surface=True, show_basins=False,
            show_stationary_halos=False,
        )
        types = [t.type for t in fig.data]
        assert "isosurface" in types

    def test_stationary_halos(self, sample_features, sample_regimes, sample_centroids):
        T = np.array([
            [0.85, 0.10, 0.04, 0.01],
            [0.15, 0.70, 0.10, 0.05],
            [0.20, 0.10, 0.65, 0.05],
            [0.05, 0.15, 0.10, 0.70],
        ])
        fig = build_phase_space_3d(
            sample_features, sample_regimes, sample_centroids,
            transition_matrix=T, show_basins=False,
            show_stationary_halos=True,
        )
        types = [t.type for t in fig.data]
        assert "mesh3d" in types

    def test_pca_loadings(self, sample_features, sample_regimes, sample_centroids):
        fig = build_phase_space_3d(
            sample_features, sample_regimes, sample_centroids,
            show_loadings=True, show_basins=False,
            show_stationary_halos=False,
        )
        loading_names = [t.name for t in fig.data if t.name and "Loading" in t.name]
        assert len(loading_names) == 5

    def test_regime_transition_markers(self, sample_centroids):
        rng = np.random.default_rng(99)
        features = rng.random((60, 5))
        regimes = ([Regime.CALM_TREND] * 20
                   + [Regime.RISK_OFF] * 20
                   + [Regime.CHOP] * 20)
        fig = build_phase_space_3d(
            features, regimes, sample_centroids,
            show_transitions_markers=True, show_basins=False,
            show_stationary_halos=False, show_loadings=False,
        )
        shift_traces = [t for t in fig.data if t.name and "Regime shifts" in t.name]
        assert len(shift_traces) == 1
        assert len(shift_traces[0].x) == 2  # two transitions

    def test_covariance_ellipsoids(self, sample_features, sample_regimes, sample_centroids):
        fig = build_phase_space_3d(
            sample_features, sample_regimes, sample_centroids,
            show_ellipsoids=True, show_basins=False,
            show_stationary_halos=False, show_loadings=False,
        )
        ellipsoid_traces = [t for t in fig.data if t.name and "1σ" in t.name]
        assert len(ellipsoid_traces) >= 1

    def test_velocity_trajectory(self, sample_features, sample_regimes, sample_centroids):
        fig = build_phase_space_3d(
            sample_features, sample_regimes, sample_centroids,
            show_trajectory=True, show_basins=False,
            show_stationary_halos=False, show_loadings=False,
        )
        vel_traces = [t for t in fig.data if t.name and "velocity" in t.name]
        assert len(vel_traces) == 1
        assert vel_traces[0].line.showscale is True  # has colorbar


class TestTrajectoryPlotter:
    def test_plot_generates_figure(self, sample_features, sample_regimes, sample_centroids):
        plotter = TrajectoryPlotter()
        fig = plotter.plot(sample_features, sample_regimes, sample_centroids)
        assert fig is not None
        plt.close(fig)


class TestVectorFieldPlotter:
    def test_plot_generates_figure(self, sample_centroids):
        plotter = VectorFieldPlotter()
        tm = np.array([
            [0.7, 0.1, 0.1, 0.1],
            [0.1, 0.6, 0.2, 0.1],
            [0.2, 0.1, 0.5, 0.2],
            [0.1, 0.2, 0.1, 0.6],
        ])
        fig = plotter.plot(sample_centroids, tm)
        assert fig is not None
        plt.close(fig)


class TestSystemDashboard:
    def test_full_dashboard(self, synthetic_ohlcv):
        df, _ = synthetic_ohlcv
        pipeline = FinancialDynamicsPipeline()
        results = pipeline.run(df)
        dashboard = SystemDashboard(pipeline)
        fig = dashboard.plot(df, results)
        assert fig is not None
        plt.close(fig)

    def test_save(self, synthetic_ohlcv, tmp_path):
        df, _ = synthetic_ohlcv
        pipeline = FinancialDynamicsPipeline()
        results = pipeline.run(df)
        dashboard = SystemDashboard(pipeline)
        dashboard.plot(df, results)
        output = tmp_path / "test_dashboard.png"
        dashboard.save(str(output))
        assert output.exists()
        plt.close("all")
