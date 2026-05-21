"""Tests verifying the package is correctly configured for distribution."""

from __future__ import annotations

import importlib
from pathlib import Path


class TestPackageMetadata:
    def test_version_is_string(self):
        from financial_dynamics import __version__

        assert isinstance(__version__, str)
        parts = __version__.split(".")
        assert len(parts) >= 2

    def test_all_public_exports(self):
        import financial_dynamics

        expected = {
            "FinancialDynamicsPipeline",
            "Regime",
            "BarState",
            "FeatureVector",
            "RegimeProbabilities",
            "RegimeForecast",
            "Signal",
            "SignalDetector",
            "SignalType",
            "NUM_REGIMES",
            "REGIME_NAMES",
        }
        assert expected.issubset(set(financial_dynamics.__all__))

    def test_py_typed_marker_exists(self):
        pkg_dir = Path(importlib.util.find_spec("financial_dynamics").origin).parent
        assert (pkg_dir / "py.typed").exists()

    def test_config_yaml_importable(self):
        from financial_dynamics.config import PipelineConfig

        config = PipelineConfig()
        assert config.features.volatility_span == 20

    def test_submodules_importable(self):
        modules = [
            "financial_dynamics.pipeline",
            "financial_dynamics.types",
            "financial_dynamics.config",
            "financial_dynamics.forecasting",
            "financial_dynamics.signals",
            "financial_dynamics.signals.detector",
            "financial_dynamics.persistence.state_io",
            "financial_dynamics.backtesting.evaluator",
            "financial_dynamics.calibration.calibrator",
            "financial_dynamics.phase0_features.feature_engine",
            "financial_dynamics.phase1_regimes.centroid_engine",
            "financial_dynamics.phase2_transitions.transition_engine",
            "financial_dynamics.phase3_stabilization.stabilizer",
            "financial_dynamics.phase4_risk.risk_overlay",
        ]
        for mod in modules:
            importlib.import_module(mod)
