"""Tests for the calibration module."""

import numpy as np
import pandas as pd
import pytest

from financial_dynamics.calibration.calibrator import CalibrationResult, Calibrator
from financial_dynamics.calibration.centroid_fitter import (
    FEATURE_COLUMNS,
    fit_centroids,
    fit_centroids_from_pipeline,
)
from financial_dynamics.calibration.hyperparameter_tuner import (
    HyperparameterTuner,
    TuningResult,
)
from financial_dynamics.config import PipelineConfig
from financial_dynamics.types import Regime


class TestFitCentroids:
    def test_returns_one_centroid_per_regime(self):
        n = 80
        rng = np.random.default_rng(42)
        features = pd.DataFrame(
            rng.random((n, 5)),
            columns=FEATURE_COLUMNS,
        )
        labels = pd.Series([Regime(i % 4).name for i in range(n)])

        centroids = fit_centroids(features, labels)
        assert set(centroids.keys()) == {r.name for r in Regime}
        for vec in centroids.values():
            assert len(vec) == 5

    def test_centroid_is_mean_of_labeled_features(self):
        features = pd.DataFrame(
            [[0.1, 0.2, 0.3, 0.4, 0.5]] * 10 + [[0.9, 0.8, 0.7, 0.6, 0.5]] * 10,
            columns=FEATURE_COLUMNS,
        )
        labels = pd.Series(["CALM_TREND"] * 10 + ["RISK_OFF"] * 10)

        centroids = fit_centroids(features, labels)
        np.testing.assert_array_almost_equal(centroids["CALM_TREND"], [0.1, 0.2, 0.3, 0.4, 0.5])
        np.testing.assert_array_almost_equal(centroids["RISK_OFF"], [0.9, 0.8, 0.7, 0.6, 0.5])

    def test_missing_regime_falls_back_to_overall_mean(self):
        features = pd.DataFrame(
            [[0.5, 0.5, 0.5, 0.5, 0.5]] * 10,
            columns=FEATURE_COLUMNS,
        )
        labels = pd.Series(["CALM_TREND"] * 10)

        centroids = fit_centroids(features, labels)
        np.testing.assert_array_almost_equal(centroids["RISK_OFF"], [0.5, 0.5, 0.5, 0.5, 0.5])

    def test_skips_nan_features(self):
        features = pd.DataFrame(
            [[np.nan] * 5] * 5 + [[0.2, 0.2, 0.2, 0.2, 0.2]] * 10,
            columns=FEATURE_COLUMNS,
        )
        labels = pd.Series(["CALM_TREND"] * 15)

        centroids = fit_centroids(features, labels)
        np.testing.assert_array_almost_equal(centroids["CALM_TREND"], [0.2, 0.2, 0.2, 0.2, 0.2])

    def test_raises_on_missing_columns(self):
        features = pd.DataFrame({"feat_volatility": [0.1, 0.2]})
        labels = pd.Series(["CALM_TREND", "CHOP"])
        with pytest.raises(ValueError, match="missing required columns"):
            fit_centroids(features, labels)


class TestFitCentroidsFromPipeline:
    def test_produces_valid_centroids(self, synthetic_ohlcv):
        df, labels = synthetic_ohlcv
        centroids = fit_centroids_from_pipeline(df, labels)
        assert set(centroids.keys()) == {r.name for r in Regime}
        for vec in centroids.values():
            assert len(vec) == 5
            assert all(0.0 <= v <= 1.0 for v in vec)


class TestHyperparameterTuner:
    def test_returns_tuning_result(self, synthetic_ohlcv):
        df, labels = synthetic_ohlcv
        tuner = HyperparameterTuner()
        space = {
            "regimes.temperature": [0.5, 1.0],
            "transitions.learning_rate": [0.05],
        }
        result = tuner.tune(df, labels, search_space=space)
        assert isinstance(result, TuningResult)
        assert 0.0 <= result.best_accuracy <= 1.0
        assert isinstance(result.best_config, PipelineConfig)

    def test_explores_full_grid(self, synthetic_ohlcv):
        df, labels = synthetic_ohlcv
        tuner = HyperparameterTuner()
        space = {
            "regimes.temperature": [0.5, 1.0, 2.0],
            "stabilization.hysteresis_threshold": [0.1, 0.2],
        }
        result = tuner.tune(df, labels, search_space=space)
        assert len(result.all_trials) == 6

    def test_best_params_match_best_accuracy_row(self, synthetic_ohlcv):
        df, labels = synthetic_ohlcv
        tuner = HyperparameterTuner()
        space = {"regimes.temperature": [0.5, 1.0, 2.0]}
        result = tuner.tune(df, labels, search_space=space)

        best_row = result.all_trials.loc[result.all_trials["accuracy"].idxmax()]
        assert result.best_params["regimes.temperature"] == best_row["regimes.temperature"]
        assert result.best_accuracy == pytest.approx(best_row["accuracy"])

    def test_raises_on_unknown_path(self, synthetic_ohlcv):
        df, labels = synthetic_ohlcv
        tuner = HyperparameterTuner()
        with pytest.raises(ValueError, match="Unknown config path"):
            tuner.tune(df, labels, search_space={"bogus.param": [1.0]})

    def test_raises_on_empty_space(self, synthetic_ohlcv):
        df, labels = synthetic_ohlcv
        tuner = HyperparameterTuner()
        with pytest.raises(ValueError, match="at least one parameter"):
            tuner.tune(df, labels, search_space={})

    def test_uses_default_space_when_none(self, synthetic_ohlcv):
        """Cover line 63: search_space is None triggers _DEFAULT_SPACE."""
        df, labels = synthetic_ohlcv
        tuner = HyperparameterTuner()
        result = tuner.tune(df, labels, search_space=None)
        assert isinstance(result, TuningResult)
        # Default space has 4*3*3*3 = 108 combos
        assert len(result.all_trials) == 108

    def test_raises_on_unknown_key_in_valid_section(self, synthetic_ohlcv):
        """Cover line 112: valid section but unknown attribute key."""
        df, labels = synthetic_ohlcv
        tuner = HyperparameterTuner()
        with pytest.raises(ValueError, match="has no 'nonexistent_key'"):
            tuner.tune(df, labels, search_space={"regimes.nonexistent_key": [1.0]})


class TestCalibrator:
    def test_calibrate_returns_result(self, synthetic_ohlcv):
        df, labels = synthetic_ohlcv
        calibrator = Calibrator()
        space = {"regimes.temperature": [0.5, 1.0]}
        result = calibrator.calibrate(df, labels, search_space=space)
        assert isinstance(result, CalibrationResult)
        assert isinstance(result.calibrated_config, PipelineConfig)

    def test_calibration_does_not_decrease_accuracy(self, synthetic_ohlcv):
        df, labels = synthetic_ohlcv
        calibrator = Calibrator()
        space = {"regimes.temperature": [0.5, 1.0, 2.0]}
        result = calibrator.calibrate(df, labels, search_space=space)
        assert result.tuned_accuracy >= result.baseline_accuracy

    def test_centroids_change_after_calibration(self, synthetic_ohlcv):
        df, labels = synthetic_ohlcv
        calibrator = Calibrator()
        space = {"regimes.temperature": [1.0]}
        result = calibrator.calibrate(df, labels, search_space=space)

        baseline_centroids = PipelineConfig().regimes.centroids
        calibrated_centroids = result.calibrated_config.regimes.centroids

        for regime_name in baseline_centroids:
            assert calibrated_centroids[regime_name] != baseline_centroids[regime_name]
