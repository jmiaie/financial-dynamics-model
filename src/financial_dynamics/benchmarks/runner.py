"""Benchmark runner -- evaluate baselines and the full pipeline side-by-side."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from financial_dynamics.backtesting.evaluator import BacktestEvaluator
from financial_dynamics.backtesting.metrics import (
    regime_accuracy,
    regime_balanced_accuracy,
    regime_classification_report,
    regime_macro_f1,
)
from financial_dynamics.benchmarks.baselines import (
    BaselineClassifier,
    GaussianMixtureClassifier,
    PersistenceClassifier,
    TrendVolGridClassifier,
    VolatilityBucketClassifier,
)
from financial_dynamics.config import PipelineConfig


@dataclass
class BenchmarkSummary:
    """Side-by-side scores for the full pipeline and baseline classifiers."""

    summary: pd.DataFrame
    per_model_reports: dict[str, pd.DataFrame]


class BenchmarkRunner:
    """Score multiple regime classifiers against ground-truth labels."""

    def __init__(
        self,
        pipeline_config: PipelineConfig | None = None,
        baselines: list[BaselineClassifier] | None = None,
    ):
        self.pipeline_config = pipeline_config or PipelineConfig()
        self.baselines = baselines if baselines is not None else self._default_baselines()

    @staticmethod
    def _default_baselines() -> list[BaselineClassifier]:
        return [
            PersistenceClassifier(),
            VolatilityBucketClassifier(),
            TrendVolGridClassifier(),
            GaussianMixtureClassifier(),
        ]

    def run(
        self,
        df: pd.DataFrame,
        labels: pd.Series,
    ) -> BenchmarkSummary:
        """Run pipeline + baselines, return summary DataFrame and per-model reports."""
        rows: list[dict[str, str | float | int]] = []
        per_model_reports: dict[str, pd.DataFrame] = {}

        evaluator = BacktestEvaluator(self.pipeline_config)
        pipeline_result = evaluator.evaluate(df, labels)
        rows.append(
            {
                "model": "financial_dynamics_pipeline",
                "accuracy": pipeline_result.accuracy,
                "balanced_accuracy": pipeline_result.balanced_accuracy,
                "macro_f1": pipeline_result.macro_f1,
                "evaluated_bars": pipeline_result.evaluated_bars,
            }
        )
        per_model_reports["financial_dynamics_pipeline"] = pipeline_result.classification_report

        for baseline in self.baselines:
            fit_labels = labels if isinstance(baseline, PersistenceClassifier) else None
            preds = baseline.fit(df, fit_labels).predict(df)
            mask = preds.notna()
            aligned_labels = labels.loc[preds.index[mask]]
            aligned_preds = preds[mask]

            accuracy = regime_accuracy(aligned_labels, aligned_preds)
            balanced_accuracy = regime_balanced_accuracy(aligned_labels, aligned_preds)
            macro_f1 = regime_macro_f1(aligned_labels, aligned_preds)
            report = regime_classification_report(aligned_labels, aligned_preds)

            rows.append(
                {
                    "model": baseline.name,
                    "accuracy": accuracy,
                    "balanced_accuracy": balanced_accuracy,
                    "macro_f1": macro_f1,
                    "evaluated_bars": int(mask.sum()),
                }
            )
            per_model_reports[baseline.name] = report

        summary = pd.DataFrame(rows).sort_values("accuracy", ascending=False).reset_index(drop=True)
        return BenchmarkSummary(
            summary=summary,
            per_model_reports=per_model_reports,
        )

    def run_temporal(
        self,
        history_df: pd.DataFrame,
        eval_df: pd.DataFrame,
        history_labels: pd.Series,
        eval_labels: pd.Series,
    ) -> BenchmarkSummary:
        """Run chronology-safe OOS benchmark evaluation on a fixed period."""
        rows: list[dict[str, str | float | int]] = []
        per_model_reports: dict[str, pd.DataFrame] = {}

        evaluator = BacktestEvaluator(self.pipeline_config)
        pipeline_result = evaluator.evaluate_with_history(history_df, eval_df, eval_labels)
        rows.append(
            {
                "model": "financial_dynamics_pipeline",
                "accuracy": pipeline_result.accuracy,
                "balanced_accuracy": pipeline_result.balanced_accuracy,
                "macro_f1": pipeline_result.macro_f1,
                "evaluated_bars": pipeline_result.evaluated_bars,
                "history_bars": pipeline_result.history_bars,
            }
        )
        per_model_reports["financial_dynamics_pipeline"] = pipeline_result.classification_report

        for baseline in self.baselines:
            fit_labels = history_labels if isinstance(baseline, PersistenceClassifier) else None
            preds = baseline.fit(history_df, fit_labels).predict(eval_df, history_df=history_df)
            mask = preds.notna()
            aligned_labels = eval_labels.loc[preds.index[mask]]
            aligned_preds = preds[mask]

            rows.append(
                {
                    "model": baseline.name,
                    "accuracy": regime_accuracy(aligned_labels, aligned_preds),
                    "balanced_accuracy": regime_balanced_accuracy(aligned_labels, aligned_preds),
                    "macro_f1": regime_macro_f1(aligned_labels, aligned_preds),
                    "evaluated_bars": int(mask.sum()),
                    "history_bars": len(history_df),
                }
            )
            per_model_reports[baseline.name] = regime_classification_report(
                aligned_labels, aligned_preds
            )

        summary = pd.DataFrame(rows).sort_values("accuracy", ascending=False).reset_index(drop=True)
        return BenchmarkSummary(summary=summary, per_model_reports=per_model_reports)
