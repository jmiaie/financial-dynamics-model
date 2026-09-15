"""High-level backtest evaluator that runs the pipeline and scores results."""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from financial_dynamics.backtesting.metrics import (
    HistoricalRegimeStatistics,
    historical_regime_statistics,
    regime_accuracy,
    regime_balanced_accuracy,
    regime_calibration_table,
    regime_classification_report,
    regime_confusion_matrix,
    regime_log_loss,
    regime_macro_f1,
    regime_multiclass_brier_score,
)
from financial_dynamics.config import PipelineConfig
from financial_dynamics.pipeline import FinancialDynamicsPipeline
from financial_dynamics.types import Regime


@dataclass
class BacktestResult:
    """Container for backtest outputs."""

    pipeline_results: pd.DataFrame
    accuracy: float
    balanced_accuracy: float
    macro_f1: float
    log_loss: float | None
    brier_score: float | None
    confusion_matrix: pd.DataFrame
    classification_report: pd.DataFrame
    warmup_bars: int
    total_bars: int
    evaluated_bars: int
    calibration_report: pd.DataFrame = field(default_factory=pd.DataFrame)
    sample_counts: pd.Series = field(default_factory=pd.Series)
    history_bars: int = 0


class BacktestEvaluator:
    """Runs the pipeline on historical data and evaluates against ground truth."""

    def __init__(self, config: PipelineConfig | None = None):
        self.config = config or PipelineConfig()

    def evaluate(
        self,
        df: pd.DataFrame,
        true_labels: pd.Series,
        regime_column: str = "risk_adjusted_regime",
    ) -> BacktestResult:
        """Run pipeline on df and compare predictions to true_labels.

        Args:
            df: OHLCV DataFrame.
            true_labels: Series of regime name strings aligned with df's index.
            regime_column: Which output column to evaluate (default: final output).

        Returns:
            BacktestResult with accuracy, confusion matrix, and classification report.
        """
        pipeline = FinancialDynamicsPipeline(self.config)
        results = pipeline.run(df)
        return self._build_result(
            pipeline_results=results,
            true_labels=true_labels,
            regime_column=regime_column,
            warmup_bars=pipeline.warmup_bars,
            total_bars=len(df),
        )

    def evaluate_with_history(
        self,
        history_df: pd.DataFrame,
        eval_df: pd.DataFrame,
        true_labels: pd.Series,
        regime_column: str = "risk_adjusted_regime",
    ) -> BacktestResult:
        """Evaluate eval_df using only prior history_df to warm online state."""
        pipeline = FinancialDynamicsPipeline(self.config)
        combined = pd.concat([history_df, eval_df], axis=0)
        combined_results = pipeline.run(combined)
        eval_results = combined_results.iloc[len(history_df) :].copy()
        return self._build_result(
            pipeline_results=eval_results,
            true_labels=true_labels,
            regime_column=regime_column,
            warmup_bars=pipeline.warmup_bars,
            total_bars=len(eval_df),
            history_bars=len(history_df),
        )

    def evaluate_rolling(
        self,
        df: pd.DataFrame,
        true_labels: pd.Series,
        window_size: int = 60,
        step_size: int = 20,
    ) -> pd.DataFrame:
        """Evaluate in-sample accuracy over rolling windows.

        Returns a DataFrame with columns [window_start, window_end, accuracy,
        evaluated_bars] for each window position.
        """
        rows: list[dict[str, int | float]] = []
        n = len(df)

        for start in range(0, n - window_size + 1, step_size):
            end = start + window_size
            window_df = df.iloc[start:end]
            window_labels = true_labels.iloc[start:end]

            result = self.evaluate(window_df, window_labels)
            rows.append(
                {
                    "window_start": start,
                    "window_end": end,
                    "accuracy": result.accuracy,
                    "evaluated_bars": result.evaluated_bars,
                }
            )

        return pd.DataFrame(rows)

    @staticmethod
    def characterize_historical_regimes(
        df: pd.DataFrame,
        inferred_regimes: pd.Series,
        *,
        close_column: str = "close",
        horizons: tuple[int, ...] = (1, 5, 20),
    ) -> HistoricalRegimeStatistics:
        """Describe return/risk behavior by inferred regime."""
        return historical_regime_statistics(
            df[close_column],
            inferred_regimes,
            horizons=horizons,
        )

    def _build_result(
        self,
        *,
        pipeline_results: pd.DataFrame,
        true_labels: pd.Series,
        regime_column: str,
        warmup_bars: int,
        total_bars: int,
        history_bars: int = 0,
    ) -> BacktestResult:
        predicted = pipeline_results[regime_column]
        mask = predicted.notna()
        predicted_valid = predicted[mask]
        aligned_true = true_labels.loc[predicted_valid.index]
        probability_columns = [f"post_prob_{regime.name}" for regime in Regime]
        probability_frame = pipeline_results.loc[predicted_valid.index, probability_columns]

        return BacktestResult(
            pipeline_results=pipeline_results,
            accuracy=regime_accuracy(aligned_true, predicted_valid),
            balanced_accuracy=regime_balanced_accuracy(aligned_true, predicted_valid),
            macro_f1=regime_macro_f1(aligned_true, predicted_valid),
            log_loss=regime_log_loss(aligned_true, probability_frame),
            brier_score=regime_multiclass_brier_score(aligned_true, probability_frame),
            confusion_matrix=regime_confusion_matrix(aligned_true, predicted_valid),
            classification_report=regime_classification_report(aligned_true, predicted_valid),
            calibration_report=regime_calibration_table(aligned_true, probability_frame),
            sample_counts=aligned_true.value_counts().sort_index(),
            history_bars=history_bars,
            warmup_bars=warmup_bars,
            total_bars=total_bars,
            evaluated_bars=int(mask.sum()),
        )
