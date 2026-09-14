"""Backtesting framework for evaluating regime classification quality."""

from financial_dynamics.backtesting.evaluator import BacktestEvaluator
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
    validate_probability_frame,
)

__all__ = [
    "BacktestEvaluator",
    "HistoricalRegimeStatistics",
    "historical_regime_statistics",
    "regime_accuracy",
    "regime_balanced_accuracy",
    "regime_calibration_table",
    "regime_classification_report",
    "regime_confusion_matrix",
    "regime_log_loss",
    "regime_macro_f1",
    "regime_multiclass_brier_score",
    "validate_probability_frame",
]
