"""High-level calibrator combining centroid fitting and hyperparameter tuning."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass

import pandas as pd

from financial_dynamics.backtesting.evaluator import BacktestEvaluator, BacktestResult
from financial_dynamics.calibration.centroid_fitter import fit_centroids_from_pipeline
from financial_dynamics.calibration.hyperparameter_tuner import (
    HyperparameterTuner,
    SearchSpace,
)
from financial_dynamics.config import PipelineConfig


@dataclass
class CalibrationResult:
    """Outcome of a full calibration run."""
    calibrated_config: PipelineConfig
    baseline_accuracy: float
    centroid_only_accuracy: float
    tuned_accuracy: float
    baseline_result: BacktestResult
    centroid_only_result: BacktestResult
    tuned_result: BacktestResult


class Calibrator:
    """End-to-end calibration: fit centroids, then tune hyperparameters."""

    def __init__(self, base_config: PipelineConfig | None = None):
        self.base_config = base_config or PipelineConfig()

    def calibrate(
        self,
        df: pd.DataFrame,
        labels: pd.Series,
        search_space: SearchSpace | None = None,
    ) -> CalibrationResult:
        """Run the full calibration pipeline.

        Steps:
          1. Score baseline (default config) on the training data.
          2. Fit centroids from the data, score with new centroids.
          3. Grid-search hyperparameters on top of fitted centroids.

        Returns a CalibrationResult comparing all three stages.
        """
        baseline_eval = BacktestEvaluator(self.base_config)
        baseline_result = baseline_eval.evaluate(df, labels)

        new_centroids = fit_centroids_from_pipeline(df, labels, self.base_config)
        centroid_config = deepcopy(self.base_config)
        centroid_config.regimes.centroids = new_centroids

        centroid_eval = BacktestEvaluator(centroid_config)
        centroid_result = centroid_eval.evaluate(df, labels)

        tuner = HyperparameterTuner(centroid_config)
        tuning = tuner.tune(df, labels, search_space=search_space)

        tuned_eval = BacktestEvaluator(tuning.best_config)
        tuned_result = tuned_eval.evaluate(df, labels)

        return CalibrationResult(
            calibrated_config=tuning.best_config,
            baseline_accuracy=baseline_result.accuracy,
            centroid_only_accuracy=centroid_result.accuracy,
            tuned_accuracy=tuned_result.accuracy,
            baseline_result=baseline_result,
            centroid_only_result=centroid_result,
            tuned_result=tuned_result,
        )
