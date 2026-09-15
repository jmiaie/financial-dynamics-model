"""Chronology-safe calibration, evaluation, and sensitivity analysis."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from itertools import product

import numpy as np
import pandas as pd

from financial_dynamics.backtesting.evaluator import BacktestEvaluator, BacktestResult
from financial_dynamics.benchmarks.runner import BenchmarkRunner, BenchmarkSummary
from financial_dynamics.calibration.centroid_fitter import fit_centroids_from_pipeline
from financial_dynamics.calibration.hyperparameter_tuner import HyperparameterTuner, SearchSpace
from financial_dynamics.config import PipelineConfig


@dataclass(frozen=True)
class TemporalWindow:
    """Half-open positional window with boundary labels."""

    name: str
    start: int
    end: int
    start_boundary: object
    end_boundary: object

    @property
    def size(self) -> int:
        return self.end - self.start


@dataclass(frozen=True)
class TemporalSplit:
    """Chronological formation/validation/test split."""

    formation: TemporalWindow
    validation: TemporalWindow
    test: TemporalWindow

    @classmethod
    def from_frame(
        cls,
        df: pd.DataFrame | pd.Series,
        *,
        formation_ratio: float = 0.6,
        validation_ratio: float = 0.2,
        test_ratio: float = 0.2,
    ) -> TemporalSplit:
        """Build a chronological split with monotonic non-overlapping windows."""
        if formation_ratio <= 0 or validation_ratio <= 0 or test_ratio <= 0:
            raise ValueError("All split ratios must be positive")

        total_ratio = formation_ratio + validation_ratio + test_ratio
        if not np.isclose(total_ratio, 1.0):
            raise ValueError("Split ratios must sum to 1.0")

        index = df.index
        if not index.is_monotonic_increasing:
            raise ValueError("Temporal splits require a monotonic increasing index")
        if index.has_duplicates:
            raise ValueError("Temporal splits require a unique chronological index")
        if len(index) < 6:
            raise ValueError("Temporal splits require at least 6 rows")

        n = len(index)
        formation_end = max(1, int(n * formation_ratio))
        validation_end = formation_end + max(1, int(n * validation_ratio))
        validation_end = min(validation_end, n - 1)
        test_end = n

        if formation_end >= validation_end or validation_end >= test_end:
            raise ValueError("Temporal split ratios leave an empty window")

        formation = TemporalWindow(
            name="formation",
            start=0,
            end=formation_end,
            start_boundary=index[0],
            end_boundary=index[formation_end - 1],
        )
        validation = TemporalWindow(
            name="validation",
            start=formation_end,
            end=validation_end,
            start_boundary=index[formation_end],
            end_boundary=index[validation_end - 1],
        )
        test = TemporalWindow(
            name="test",
            start=validation_end,
            end=test_end,
            start_boundary=index[validation_end],
            end_boundary=index[test_end - 1],
        )
        return cls(formation=formation, validation=validation, test=test)

    def slice_frame(self, df: pd.DataFrame, window: str) -> pd.DataFrame:
        part = getattr(self, window)
        return df.iloc[part.start : part.end]

    def slice_series(self, values: pd.Series, window: str) -> pd.Series:
        part = getattr(self, window)
        return values.iloc[part.start : part.end]

    def history_before(self, df: pd.DataFrame, window: str) -> pd.DataFrame:
        if window == "validation":
            return self.slice_frame(df, "formation")
        if window == "test":
            return pd.concat(
                [self.slice_frame(df, "formation"), self.slice_frame(df, "validation")],
                axis=0,
            )
        if window == "formation":
            return df.iloc[0:0]
        raise ValueError(f"Unknown window '{window}'")


@dataclass
class TemporalCalibrationResult:
    """Chronology-safe calibration summary."""

    split: TemporalSplit
    calibrated_config: PipelineConfig
    fitted_centroids: dict[str, list[float]]
    baseline_validation_result: BacktestResult
    centroid_validation_result: BacktestResult
    tuned_validation_result: BacktestResult
    final_test_result: BacktestResult
    validation_benchmarks: BenchmarkSummary
    test_benchmarks: BenchmarkSummary


@dataclass
class WalkForwardStepResult:
    """One strict prior-only walk-forward evaluation step."""

    step_index: int
    train_window: TemporalWindow
    eval_window: TemporalWindow
    calibrated_config: PipelineConfig
    result: BacktestResult


@dataclass
class WalkForwardResult:
    """Collection of walk-forward steps and their summary table."""

    steps: list[WalkForwardStepResult]
    summary: pd.DataFrame


@dataclass
class SensitivityAnalysisResult:
    """Sensitivity-analysis outputs emphasizing stability over best-case outcomes."""

    summary: pd.DataFrame


class TemporalCalibrator:
    """Fit on formation, tune on validation, and evaluate once on final test."""

    def __init__(self, base_config: PipelineConfig | None = None):
        self.base_config = base_config or PipelineConfig()

    def calibrate(
        self,
        df: pd.DataFrame,
        labels: pd.Series,
        *,
        split: TemporalSplit | None = None,
        search_space: SearchSpace | None = None,
    ) -> TemporalCalibrationResult:
        split = split or TemporalSplit.from_frame(df)
        formation_df = split.slice_frame(df, "formation")
        validation_df = split.slice_frame(df, "validation")
        test_df = split.slice_frame(df, "test")

        formation_labels = split.slice_series(labels, "formation")
        validation_labels = split.slice_series(labels, "validation")
        test_labels = split.slice_series(labels, "test")

        base_evaluator = BacktestEvaluator(self.base_config)
        baseline_validation = base_evaluator.evaluate_with_history(
            formation_df,
            validation_df,
            validation_labels,
        )

        fitted_centroids = fit_centroids_from_pipeline(
            formation_df, formation_labels, self.base_config
        )
        centroid_config = deepcopy(self.base_config)
        centroid_config.regimes.centroids = fitted_centroids

        centroid_validation = BacktestEvaluator(centroid_config).evaluate_with_history(
            formation_df,
            validation_df,
            validation_labels,
        )

        tuning = HyperparameterTuner(centroid_config).tune(
            validation_df,
            validation_labels,
            search_space=search_space,
            history_df=formation_df,
        )
        tuned_validation = BacktestEvaluator(tuning.best_config).evaluate_with_history(
            formation_df,
            validation_df,
            validation_labels,
        )

        test_history = split.history_before(df, "test")
        test_benchmark_labels = pd.concat([formation_labels, validation_labels], axis=0)
        final_test = BacktestEvaluator(tuning.best_config).evaluate_with_history(
            test_history,
            test_df,
            test_labels,
        )

        validation_benchmarks = BenchmarkRunner(tuning.best_config).run_temporal(
            formation_df,
            validation_df,
            formation_labels,
            validation_labels,
        )
        test_benchmarks = BenchmarkRunner(tuning.best_config).run_temporal(
            test_history,
            test_df,
            test_benchmark_labels,
            test_labels,
        )

        return TemporalCalibrationResult(
            split=split,
            calibrated_config=tuning.best_config,
            fitted_centroids=fitted_centroids,
            baseline_validation_result=baseline_validation,
            centroid_validation_result=centroid_validation,
            tuned_validation_result=tuned_validation,
            final_test_result=final_test,
            validation_benchmarks=validation_benchmarks,
            test_benchmarks=test_benchmarks,
        )


class TemporalValidator:
    """Reusable genuine walk-forward evaluator."""

    def __init__(self, base_config: PipelineConfig | None = None):
        self.base_config = base_config or PipelineConfig()

    def walk_forward(
        self,
        df: pd.DataFrame,
        labels: pd.Series,
        *,
        initial_train_size: int,
        step_size: int,
        eval_size: int | None = None,
        expanding: bool = True,
        rolling_train_size: int | None = None,
    ) -> WalkForwardResult:
        if initial_train_size <= 0 or step_size <= 0:
            raise ValueError("initial_train_size and step_size must be positive")

        if not df.index.is_monotonic_increasing or df.index.has_duplicates:
            raise ValueError("Walk-forward validation requires a unique monotonic index")

        eval_size = eval_size or step_size
        if not expanding and rolling_train_size is None:
            rolling_train_size = initial_train_size

        steps: list[WalkForwardStepResult] = []
        rows: list[dict[str, int | float | str]] = []
        train_ends = range(initial_train_size, len(df) - eval_size + 1, step_size)
        for step_index, train_end in enumerate(train_ends):
            train_window_size = (
                rolling_train_size if rolling_train_size is not None else initial_train_size
            )
            train_start = 0 if expanding else max(0, train_end - train_window_size)
            eval_end = train_end + eval_size

            train_df = df.iloc[train_start:train_end]
            eval_df = df.iloc[train_end:eval_end]
            train_labels = labels.iloc[train_start:train_end]
            eval_labels = labels.iloc[train_end:eval_end]

            centroids = fit_centroids_from_pipeline(train_df, train_labels, self.base_config)
            calibrated_config = deepcopy(self.base_config)
            calibrated_config.regimes.centroids = centroids
            result = BacktestEvaluator(calibrated_config).evaluate_with_history(
                train_df,
                eval_df,
                eval_labels,
            )

            train_window = TemporalWindow(
                name="train",
                start=train_start,
                end=train_end,
                start_boundary=df.index[train_start],
                end_boundary=df.index[train_end - 1],
            )
            eval_window = TemporalWindow(
                name="eval",
                start=train_end,
                end=eval_end,
                start_boundary=df.index[train_end],
                end_boundary=df.index[eval_end - 1],
            )
            steps.append(
                WalkForwardStepResult(
                    step_index=step_index,
                    train_window=train_window,
                    eval_window=eval_window,
                    calibrated_config=calibrated_config,
                    result=result,
                )
            )
            rows.append(
                {
                    "step": step_index,
                    "mode": "expanding" if expanding else "rolling",
                    "train_start": train_start,
                    "train_end": train_end,
                    "eval_start": train_end,
                    "eval_end": eval_end,
                    "accuracy": result.accuracy,
                    "balanced_accuracy": result.balanced_accuracy,
                    "macro_f1": result.macro_f1,
                    "evaluated_bars": result.evaluated_bars,
                }
            )

        return WalkForwardResult(steps=steps, summary=pd.DataFrame(rows))


class SensitivityAnalyzer:
    """Controlled temporal sensitivity analysis for key model parameters."""

    def __init__(self, base_config: PipelineConfig | None = None):
        self.base_config = base_config or PipelineConfig()

    def analyze(
        self,
        df: pd.DataFrame,
        labels: pd.Series,
        *,
        split: TemporalSplit | None = None,
        parameter_grid: dict[str, list[float | int]] | None = None,
        random_state: int = 0,
    ) -> SensitivityAnalysisResult:
        split = split or TemporalSplit.from_frame(df)
        formation_df = split.slice_frame(df, "formation")
        validation_df = split.slice_frame(df, "validation")
        test_df = split.slice_frame(df, "test")
        formation_labels = split.slice_series(labels, "formation")
        validation_labels = split.slice_series(labels, "validation")
        test_labels = split.slice_series(labels, "test")
        test_history = split.history_before(df, "test")

        centroids = fit_centroids_from_pipeline(formation_df, formation_labels, self.base_config)
        centroid_config = deepcopy(self.base_config)
        centroid_config.regimes.centroids = centroids

        space = parameter_grid or {
            "regimes.temperature": [0.75, 1.0, 1.25],
            "transitions.learning_rate": [0.02, 0.05, 0.1],
            "stabilization.hysteresis_threshold": [0.1, 0.15, 0.25],
            "stabilization.min_persistence_bars": [3, 5, 8],
            "features.volatility_span": [10, 20, 30],
            "centroid_perturbation_scale": [0.0, 0.02],
        }
        param_names = list(space.keys())
        value_grid = [space[name] for name in param_names]
        rng = np.random.default_rng(random_state)

        rows: list[dict[str, str | float | int]] = []
        for values in product(*value_grid):
            params = dict(zip(param_names, values, strict=True))
            try:
                trial_config = self._apply_params(centroid_config, params, rng)
                validation_result = BacktestEvaluator(trial_config).evaluate_with_history(
                    formation_df,
                    validation_df,
                    validation_labels,
                )
                test_result = BacktestEvaluator(trial_config).evaluate_with_history(
                    test_history,
                    test_df,
                    test_labels,
                )
                accuracies = [validation_result.accuracy, test_result.accuracy]
                rows.append(
                    {
                        **params,
                        "validation_accuracy": validation_result.accuracy,
                        "test_accuracy": test_result.accuracy,
                        "median_accuracy": float(np.median(accuracies)),
                        "accuracy_dispersion": float(np.std(accuracies)),
                        "status": "ok",
                    }
                )
            except (ValueError, TypeError) as exc:
                rows.append(
                    {
                        **params,
                        "validation_accuracy": np.nan,
                        "test_accuracy": np.nan,
                        "median_accuracy": np.nan,
                        "accuracy_dispersion": np.nan,
                        "status": f"failure: {exc}",
                    }
                )

        return SensitivityAnalysisResult(summary=pd.DataFrame(rows))

    @staticmethod
    def _apply_params(
        base_config: PipelineConfig,
        params: dict[str, float | int],
        rng: np.random.Generator,
    ) -> PipelineConfig:
        noise_scale = float(params.get("centroid_perturbation_scale", 0.0))
        ordinary_params = {
            key: value for key, value in params.items() if key != "centroid_perturbation_scale"
        }
        trial_config = HyperparameterTuner._apply_params(base_config, ordinary_params)
        if noise_scale > 0.0:
            for regime_name, centroid in trial_config.regimes.centroids.items():
                perturbed = np.asarray(centroid, dtype=float) + rng.normal(
                    0.0, noise_scale, len(centroid)
                )
                trial_config.regimes.centroids[regime_name] = np.clip(perturbed, 0.0, 1.0).tolist()
        return trial_config
