"""Tests for the backtesting framework."""

import numpy as np
import pandas as pd
import pytest

from financial_dynamics.backtesting.evaluator import BacktestEvaluator, BacktestResult
from financial_dynamics.backtesting.metrics import (
    block_bootstrap_mean_ci,
    historical_regime_statistics,
    regime_accuracy,
    regime_balanced_accuracy,
    regime_bootstrap_uncertainty,
    regime_calibration_table,
    regime_classification_report,
    regime_confusion_matrix,
    regime_log_loss,
    regime_macro_f1,
    regime_multiclass_brier_score,
    validate_probability_frame,
)
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


class TestProbabilityMetrics:
    def test_balanced_accuracy(self):
        labels = pd.Series(["CALM_TREND", "CALM_TREND", "RISK_OFF", "RISK_OFF"])
        preds = pd.Series(["CALM_TREND", "RISK_OFF", "RISK_OFF", "RISK_OFF"])
        assert regime_balanced_accuracy(labels, preds) == 0.75

    def test_probability_validation_rejects_bad_rows(self):
        probabilities = pd.DataFrame(
            {
                "post_prob_CALM_TREND": [0.6],
                "post_prob_VOLATILE_TREND": [0.3],
                "post_prob_CHOP": [0.2],
                "post_prob_RISK_OFF": [-0.1],
            }
        )
        with pytest.raises(ValueError, match="between 0 and 1"):
            validate_probability_frame(probabilities)

    def test_probability_metrics(self):
        labels = pd.Series(["CALM_TREND", "RISK_OFF"])
        probabilities = pd.DataFrame(
            {
                "post_prob_CALM_TREND": [0.7, 0.05],
                "post_prob_VOLATILE_TREND": [0.1, 0.1],
                "post_prob_CHOP": [0.1, 0.15],
                "post_prob_RISK_OFF": [0.1, 0.7],
            }
        )
        assert regime_log_loss(labels, probabilities) is not None
        assert regime_multiclass_brier_score(labels, probabilities) is not None
        calibration = regime_calibration_table(labels, probabilities, bins=2)
        assert not calibration.empty
        assert regime_macro_f1(labels, pd.Series(["CALM_TREND", "RISK_OFF"])) == 1.0


class TestHistoricalRegimeStatistics:
    def test_returns_summary_and_transitions(self):
        index = pd.date_range("2024-01-01", periods=8, freq="D")
        close = pd.Series([100, 101, 102, 101, 100, 99, 100, 101], index=index)
        inferred = pd.Series(
            [
                "CALM_TREND",
                "CALM_TREND",
                "CHOP",
                "CHOP",
                "RISK_OFF",
                "RISK_OFF",
                "CALM_TREND",
                "CALM_TREND",
            ],
            index=index,
        )
        stats = historical_regime_statistics(close, inferred, horizons=(1, 2))
        assert not stats.summary.empty
        assert "mean_duration" in stats.summary.columns
        assert stats.transitions.loc["CALM_TREND", "CHOP"] >= 0.0

    def test_transition_matrix_records_switches(self):
        """Identically named regime Series must still yield off-diagonal mass."""
        idx = pd.date_range("2020-01-01", periods=6, freq="D")
        close = pd.Series([100.0, 101.0, 102.0, 101.0, 100.0, 99.0], index=idx)
        inferred = pd.Series(
            ["CHOP", "CHOP", "VOLATILE_TREND", "VOLATILE_TREND", "RISK_OFF", "RISK_OFF"],
            index=idx,
            name="risk_adjusted_regime",
        )
        stats = historical_regime_statistics(close, inferred, horizons=(1,))
        assert stats.transitions.loc["CHOP", "VOLATILE_TREND"] > 0.0
        assert stats.transitions.loc["VOLATILE_TREND", "RISK_OFF"] > 0.0

    def test_adverse_drawdown_catches_an_intra_horizon_dip_a_flat_forward_return_would_miss(self):
        """A 3-day horizon that dips hard on day 1 then fully recovers by day
        3 has forward_return == 0.0 -- the adverse drawdown must still show
        the dip, since a trader holding through the horizon lived through it
        even though the endpoint-to-endpoint return looks benign."""
        index = pd.date_range("2024-01-01", periods=4, freq="D")
        close = pd.Series([100.0, 80.0, 90.0, 100.0], index=index)  # -20% then back to par
        inferred = pd.Series(["CALM_TREND"] * 4, index=index)

        stats = historical_regime_statistics(close, inferred, horizons=(3,))
        row = stats.summary.iloc[0]
        assert row["mean_return"] == pytest.approx(0.0)
        assert row["worst_adverse_drawdown"] == pytest.approx(-0.20)
        assert row["mean_adverse_drawdown"] == pytest.approx(-0.20)

    def test_forward_occurrences_is_populated_and_chronologically_ordered(self):
        index = pd.date_range("2024-01-01", periods=6, freq="D")
        close = pd.Series([100.0, 101.0, 102.0, 101.0, 100.0, 99.0], index=index)
        inferred = pd.Series(["CALM_TREND"] * 6, index=index)

        stats = historical_regime_statistics(close, inferred, horizons=(1,))
        assert not stats.forward_occurrences.empty
        assert list(stats.forward_occurrences.index) == sorted(stats.forward_occurrences.index)

    def test_positive_return_freq_is_horizon_level_not_daily_level(self):
        """Real defect (independent review, 2026-09-17): positive_return_freq
        must be the fraction of OCCURRENCES whose horizon-level compounded
        forward_return was positive -- not the fraction of individual days
        inside each window that were positive (a different statistic the
        code previously computed and reported instead).

        Construct a repeating +1%/-3% daily pattern: every 2-day window has
        exactly one up-day and one down-day (daily-positive-fraction ==
        0.5 for every window, so the old buggy definition would read 0.5),
        but the -3% day always dominates, so every window's COMPOUNDED
        2-day return is negative (the correct definition must read 0.0).
        """
        index = pd.date_range("2024-01-01", periods=6, freq="D")
        prices = [100.0]
        for i in range(5):
            prices.append(prices[-1] * (1.01 if i % 2 == 0 else 0.97))
        close = pd.Series(prices, index=index)
        inferred = pd.Series(["CALM_TREND"] * 6, index=index)

        stats = historical_regime_statistics(close, inferred, horizons=(2,))
        row = stats.summary.iloc[0]
        assert (stats.forward_occurrences["forward_return"] < 0).all()
        assert row["positive_return_freq"] == pytest.approx(0.0)


class TestBlockBootstrap:
    def test_recovers_the_sample_mean_and_brackets_it_with_a_ci(self):
        rng = np.random.default_rng(0)
        values = pd.Series(rng.normal(0.001, 0.01, size=200))
        result = block_bootstrap_mean_ci(
            values, method="moving_block", block_size=10, n_bootstrap=500, seed=1
        )
        assert result["insufficient_data"] is False
        assert result["mean"] == pytest.approx(float(values.mean()))
        assert result["ci_low"] < result["mean"] < result["ci_high"]

    def test_stationary_method_also_brackets_the_mean(self):
        rng = np.random.default_rng(0)
        values = pd.Series(rng.normal(0.001, 0.01, size=200))
        result = block_bootstrap_mean_ci(
            values, method="stationary", block_size=10, n_bootstrap=500, seed=1
        )
        assert result["insufficient_data"] is False
        assert result["ci_low"] < result["mean"] < result["ci_high"]

    def test_flags_insufficient_data_below_two_observations(self):
        assert block_bootstrap_mean_ci(pd.Series([0.01]))["insufficient_data"] is True
        assert block_bootstrap_mean_ci(pd.Series([], dtype=float))["insufficient_data"] is True

    def test_regime_bootstrap_uncertainty_covers_every_regime_horizon_and_method(self):
        index = pd.date_range("2024-01-01", periods=40, freq="D")
        rng = np.random.default_rng(2)
        close = pd.Series(100 + np.cumsum(rng.normal(0, 0.5, 40)), index=index)
        inferred = pd.Series(
            ["CALM_TREND" if i < 20 else "RISK_OFF" for i in range(40)], index=index
        )
        stats = historical_regime_statistics(close, inferred, horizons=(1, 5))

        table = regime_bootstrap_uncertainty(
            stats.forward_occurrences,
            methods=("moving_block", "stationary"),
            block_size=5,
            n_bootstrap=200,
            seed=0,
        )
        assert not table.empty
        seen = set(zip(table["regime"], table["horizon"], table["method"], strict=True))
        expected_groups = set(
            zip(
                stats.forward_occurrences["regime"],
                stats.forward_occurrences["horizon"],
                strict=False,
            )
        )
        for regime, horizon in expected_groups:
            assert (regime, horizon, "moving_block") in seen
            assert (regime, horizon, "stationary") in seen

    def test_regime_bootstrap_uncertainty_returns_empty_frame_for_empty_input(self):
        assert regime_bootstrap_uncertainty(pd.DataFrame()).empty


class TestBacktestEvaluator:
    def test_evaluate_returns_backtest_result(self, synthetic_ohlcv):
        df, labels = synthetic_ohlcv
        evaluator = BacktestEvaluator()
        result = evaluator.evaluate(df, labels)
        assert isinstance(result, BacktestResult)
        assert 0.0 <= result.accuracy <= 1.0
        assert 0.0 <= result.balanced_accuracy <= 1.0
        assert 0.0 <= result.macro_f1 <= 1.0
        assert result.total_bars == len(df)
        assert result.evaluated_bars > 0
        assert result.warmup_bars > 0
        assert result.log_loss is not None
        assert result.brier_score is not None
        assert not result.calibration_report.empty

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
        rolling = evaluator.evaluate_rolling(df, labels, window_size=120, step_size=60)
        assert isinstance(rolling, pd.DataFrame)
        assert len(rolling) > 0
        assert "accuracy" in rolling.columns
        assert "evaluated_bars" in rolling.columns
        assert all(0.0 <= a <= 1.0 for a in rolling["accuracy"])

    def test_evaluate_with_history_uses_prior_window(self, synthetic_ohlcv):
        df, labels = synthetic_ohlcv
        evaluator = BacktestEvaluator()
        history = df.iloc[:120]
        eval_df = df.iloc[120:180]
        eval_labels = labels.iloc[120:180]
        result = evaluator.evaluate_with_history(history, eval_df, eval_labels)
        assert result.total_bars == len(eval_df)
        assert result.history_bars == len(history)
        assert result.pipeline_results.index.equals(eval_df.index)
