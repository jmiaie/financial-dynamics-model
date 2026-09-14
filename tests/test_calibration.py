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
from financial_dynamics.calibration.temporal import (
    SensitivityAnalyzer,
    TemporalCalibrationResult,
    TemporalCalibrator,
    TemporalSplit,
    TemporalValidator,
    WalkForwardResult,
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

    def test_supports_history_only_tuning(self, synthetic_ohlcv):
        df, labels = synthetic_ohlcv
        tuner = HyperparameterTuner()
        result = tuner.tune(
            df.iloc[120:180],
            labels.iloc[120:180],
            search_space={"regimes.temperature": [0.5, 1.0]},
            history_df=df.iloc[:120],
        )
        assert isinstance(result, TuningResult)
        assert len(result.all_trials) == 2

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


class TestTemporalSplit:
    def test_non_overlap_and_boundaries(self, synthetic_ohlcv):
        df, _ = synthetic_ohlcv
        split = TemporalSplit.from_frame(df)
        assert split.formation.end == split.validation.start
        assert split.validation.end == split.test.start
        assert split.formation.end_boundary < split.validation.start_boundary
        assert split.validation.end_boundary < split.test.start_boundary

    def test_rejects_duplicate_or_unsorted_index(self, synthetic_ohlcv):
        df, _ = synthetic_ohlcv
        bad = df.copy()
        bad.index = list(df.index[:-1]) + [df.index[-2]]
        with pytest.raises(ValueError, match="unique chronological index"):
            TemporalSplit.from_frame(bad)


class TestTemporalCalibrator:
    def test_calibrate_separates_validation_and_test(self, synthetic_ohlcv):
        df, labels = synthetic_ohlcv
        split = TemporalSplit.from_frame(
            df, formation_ratio=0.5, validation_ratio=0.25, test_ratio=0.25
        )
        calibrator = TemporalCalibrator()
        result = calibrator.calibrate(
            df,
            labels,
            split=split,
            search_space={"regimes.temperature": [0.5, 1.0]},
        )
        assert isinstance(result, TemporalCalibrationResult)
        assert result.final_test_result.history_bars == split.formation.size + split.validation.size
        assert "persistence" in set(result.test_benchmarks.summary["model"])

    def test_test_window_does_not_change_tuned_config(self, synthetic_ohlcv):
        df, labels = synthetic_ohlcv
        split = TemporalSplit.from_frame(
            df, formation_ratio=0.5, validation_ratio=0.25, test_ratio=0.25
        )
        calibrator = TemporalCalibrator()
        baseline = calibrator.calibrate(
            df,
            labels,
            split=split,
            search_space={"regimes.temperature": [0.5, 1.0]},
        )

        mutated_df = df.copy()
        mutated_df.iloc[split.test.start :, mutated_df.columns.get_loc("close")] *= 5
        mutated_labels = labels.copy()
        mutated_labels.iloc[split.test.start :] = "RISK_OFF"
        mutated = calibrator.calibrate(
            mutated_df,
            mutated_labels,
            split=split,
            search_space={"regimes.temperature": [0.5, 1.0]},
        )

        assert (
            baseline.calibrated_config.regimes.temperature
            == mutated.calibrated_config.regimes.temperature
        )
        assert baseline.fitted_centroids == mutated.fitted_centroids
        assert baseline.tuned_validation_result.accuracy == pytest.approx(
            mutated.tuned_validation_result.accuracy
        )


class TestTemporalValidator:
    def test_walk_forward_returns_steps(self, synthetic_ohlcv):
        df, labels = synthetic_ohlcv
        result = TemporalValidator().walk_forward(
            df,
            labels,
            initial_train_size=120,
            step_size=40,
            eval_size=40,
        )
        assert isinstance(result, WalkForwardResult)
        assert len(result.steps) > 0
        assert "balanced_accuracy" in result.summary.columns

    def test_walk_forward_is_future_safe(self, synthetic_ohlcv):
        df, labels = synthetic_ohlcv
        validator = TemporalValidator()
        baseline = validator.walk_forward(
            df, labels, initial_train_size=120, step_size=40, eval_size=40
        )

        mutated_df = df.copy()
        first_eval_end = baseline.steps[0].eval_window.end
        mutated_df.iloc[first_eval_end:, mutated_df.columns.get_loc("close")] *= 3
        mutated = validator.walk_forward(
            mutated_df,
            labels,
            initial_train_size=120,
            step_size=40,
            eval_size=40,
        )

        assert (
            baseline.steps[0].calibrated_config.regimes.centroids
            == mutated.steps[0].calibrated_config.regimes.centroids
        )
        assert baseline.steps[0].result.accuracy == pytest.approx(mutated.steps[0].result.accuracy)


class TestSensitivityAnalyzer:
    def test_returns_stability_summary(self, synthetic_ohlcv):
        df, labels = synthetic_ohlcv
        split = TemporalSplit.from_frame(
            df, formation_ratio=0.5, validation_ratio=0.25, test_ratio=0.25
        )
        result = SensitivityAnalyzer().analyze(
            df,
            labels,
            split=split,
            parameter_grid={
                "regimes.temperature": [1.0],
                "transitions.learning_rate": [0.05],
                "centroid_perturbation_scale": [0.0, 0.02],
            },
        )
        assert "median_accuracy" in result.summary.columns
        assert "accuracy_dispersion" in result.summary.columns
        assert set(result.summary["status"]) == {"ok"}
