"""Backtesting framework for evaluating regime classification quality."""

from financial_dynamics.backtesting.evaluator import BacktestEvaluator
from financial_dynamics.backtesting.metrics import (
    regime_accuracy,
    regime_confusion_matrix,
    regime_classification_report,
)

__all__ = [
    "BacktestEvaluator",
    "regime_accuracy",
    "regime_confusion_matrix",
    "regime_classification_report",
]
