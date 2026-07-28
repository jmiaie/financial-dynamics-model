"""High-level backtest evaluator that runs the pipeline and scores results."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from financial_dynamics.backtesting.metrics import (
    regime_accuracy,
    regime_classification_report,
    regime_confusion_matrix,
)
from financial_dynamics.config import PipelineConfig
from financial_dynamics.pipeline import FinancialDynamicsPipeline


@dataclass
class BacktestResult:
    """Container for backtest outputs."""
    pipeline_results: pd.DataFrame
    accuracy: float
    confusion_matrix: pd.DataFrame
    classification_report: pd.DataFrame
    warmup_bars: int
    total_bars: int
    evaluated_bars: int


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

        predicted = results[regime_column]
        mask = predicted.notna()
        aligned_true = true_labels.loc[mask.index[mask]]

        return BacktestResult(
            pipeline_results=results,
            accuracy=regime_accuracy(aligned_true, predicted[mask]),
            confusion_matrix=regime_confusion_matrix(aligned_true, predicted[mask]),
            classification_report=regime_classification_report(aligned_true, predicted[mask]),
            warmup_bars=pipeline.warmup_bars,
            total_bars=len(df),
            evaluated_bars=int(mask.sum()),
        )

    def evaluate_rolling(
        self,
        df: pd.DataFrame,
        true_labels: pd.Series,
        window_size: int = 60,
        step_size: int = 20,
    ) -> pd.DataFrame:
        """Evaluate accuracy over rolling windows.

        Returns a DataFrame with columns [window_start, window_end, accuracy,
        evaluated_bars] for each window position.
        """
        rows = []
        n = len(df)

        for start in range(0, n - window_size + 1, step_size):
            end = start + window_size
            window_df = df.iloc[start:end]
            window_labels = true_labels.iloc[start:end]

            result = self.evaluate(window_df, window_labels)
            rows.append({
                "window_start": start,
                "window_end": end,
                "accuracy": result.accuracy,
                "evaluated_bars": result.evaluated_bars,
            })

        return pd.DataFrame(rows)
