"""Tests for the backtesting framework."""

import numpy as np
import pandas as pd
import pytest

from financial_dynamics.backtesting.metrics import (
    regime_accuracy,
    regime_confusion_matrix,
    regime_classification_report,
)
from financial_dynamics.backtesting.evaluator import BacktestEvaluator, BacktestResult
from financial_dynamics.types import Regime


class TestRegimeAccuracy:
    def test_perfect_accuracy(self):
        labels = pd.Series(["CALM_TREND", "VOLATILE_TREND", "CHOP", "RISK_OFF"])
        preds = pd.Series(["CALM_TREND", "VOLATILE_TREND", "CHOP", "RISK_OFF"])
        assert regime_accuracy(labels, preds) == 1.0

    def test_zero_accuracy(self):
        labels = pd.Series(["CALM_TREND", "CALM_TREND", "CALM_TREND"])
        preds = pd.Series(["RISK_OFF", "RISK_OFF", "RISK_OFF"])
        assert regime_accuracy(labels, preds) == 0.0

    def test_partial_accuracy(self):
        labels = pd.Series(["CALM_TREND", "VOLATILE_TREND", "CHOP", "RISK_OFF"])
        preds = pd.Series(["CALM_TREND", "CALM_TREND", "CHOP", "RISK_OFF"])
        assert regime_accuracy(labels, preds) == 0.75

    def test_nan_predictions_excluded(self):
        labels = pd.Series(["CALM_TREND", "VOLATILE_TREND", "CHOP"])
        preds = pd.Series([None, "VOLATILE_TREND", "CHOP"])
        assert regime_accuracy(labels, preds) == 1.0

    def test_all_nan_returns_zero(self):
        labels = pd.Series(["CALM_TREND", "VOLATILE_TREND"])
        preds = pd.Series([None, None])
        assert regime_accuracy(labels, preds) == 0.0


class TestConfusionMatrix:
    def test_perfect_predictions(self):
        labels = pd.Series(["CALM_TREND"] * 5 + ["RISK_OFF"] * 3)
        preds = pd.Series(["CALM_TREND"] * 5 + ["RISK_OFF"] * 3)
        cm = regime_confusion_matrix(labels, preds)
        assert cm.shape == (4, 4)
        assert cm.loc["CALM_TREND", "CALM_TREND"] == 5
        assert cm.loc["RISK_OFF", "RISK_OFF"] == 3
        assert cm.values.sum() == 8

    def test_all_misclassified(self):
        labels = pd.Series(["CALM_TREND", "CALM_TREND"])
        preds = pd.Series(["RISK_OFF", "RISK_OFF"])
        cm = regime_confusion_matrix(labels, preds)
        assert cm.loc["CALM_TREND", "RISK_OFF"] == 2
        assert cm.loc["CALM_TREND", "CALM_TREND"] == 0

    def test_excludes_nan_predictions(self):
        labels = pd.Series(["CALM_TREND", "VOLATILE_TREND", "CHOP"])
        preds = pd.Series([None, "VOLATILE_TREND", "CHOP"])
        cm = regime_confusion_matrix(labels, preds)
        assert cm.values.sum() == 2


class TestClassificationReport:
    def test_perfect_predictions(self):
        labels = pd.Series(["CALM_TREND"] * 10 + ["RISK_OFF"] * 10)
        preds = pd.Series(["CALM_TREND"] * 10 + ["RISK_OFF"] * 10)
        report = regime_classification_report(labels, preds)
        assert report.loc["CALM_TREND", "precision"] == 1.0
        assert report.loc["CALM_TREND", "recall"] == 1.0
        assert report.loc["CALM_TREND", "f1"] == 1.0
        assert report.loc["weighted_avg", "f1"] == 1.0

    def test_zero_support_regime(self):
        labels = pd.Series(["CALM_TREND"] * 5)
        preds = pd.Series(["CALM_TREND"] * 5)
        report = regime_classification_report(labels, preds)
        assert report.loc["CHOP", "precision"] == 0.0
        assert report.loc["CHOP", "recall"] == 0.0
        assert report.loc["CHOP", "support"] == 0

    def test_report_has_all_regimes(self):
        labels = pd.Series(["CALM_TREND"])
        preds = pd.Series(["CALM_TREND"])
        report = regime_classification_report(labels, preds)
        expected = [r.name for r in Regime] + ["weighted_avg"]
        assert list(report.index) == expected


class TestBacktestEvaluator:
    def test_evaluate_returns_backtest_result(self, synthetic_ohlcv):
        df, labels = synthetic_ohlcv
        evaluator = BacktestEvaluator()
        result = evaluator.evaluate(df, labels)
        assert isinstance(result, BacktestResult)
        assert 0.0 <= result.accuracy <= 1.0
        assert result.total_bars == len(df)
        assert result.evaluated_bars > 0
        assert result.warmup_bars > 0

    def test_confusion_matrix_shape(self, synthetic_ohlcv):
        df, labels = synthetic_ohlcv
        evaluator = BacktestEvaluator()
        result = evaluator.evaluate(df, labels)
        assert result.confusion_matrix.shape == (4, 4)
        assert result.confusion_matrix.values.sum() == result.evaluated_bars

    def test_classification_report_shape(self, synthetic_ohlcv):
        df, labels = synthetic_ohlcv
        evaluator = BacktestEvaluator()
        result = evaluator.evaluate(df, labels)
        assert len(result.classification_report) == 5  # 4 regimes + weighted_avg
        assert "precision" in result.classification_report.columns

    def test_evaluate_stabilized_regime(self, synthetic_ohlcv):
        df, labels = synthetic_ohlcv
        evaluator = BacktestEvaluator()
        result = evaluator.evaluate(df, labels, regime_column="stabilized_regime")
        assert isinstance(result, BacktestResult)
        assert result.evaluated_bars > 0

    def test_rolling_evaluation(self, synthetic_ohlcv):
        df, labels = synthetic_ohlcv
        evaluator = BacktestEvaluator()
        rolling = evaluator.evaluate_rolling(
            df, labels, window_size=120, step_size=60
        )
        assert isinstance(rolling, pd.DataFrame)
        assert len(rolling) > 0
        assert "accuracy" in rolling.columns
        assert "evaluated_bars" in rolling.columns
        assert all(0.0 <= a <= 1.0 for a in rolling["accuracy"])
