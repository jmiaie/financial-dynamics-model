"""Tests for visualization components."""

import numpy as np
import pytest
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from financial_dynamics.types import Regime
from financial_dynamics.phase1_regimes.regime_definitions import get_default_centroids
from financial_dynamics.visualization.trajectory import TrajectoryPlotter
from financial_dynamics.visualization.vector_field import VectorFieldPlotter
from financial_dynamics.visualization.dashboard import SystemDashboard
from financial_dynamics.pipeline import FinancialDynamicsPipeline


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
