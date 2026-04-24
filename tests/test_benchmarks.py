"""Tests for baseline classifiers and the benchmark runner."""

import numpy as np
import pandas as pd
import pytest

from financial_dynamics.benchmarks.baselines import (
    GaussianMixtureClassifier,
    TrendVolGridClassifier,
    VolatilityBucketClassifier,
)
from financial_dynamics.benchmarks.runner import BenchmarkRunner, BenchmarkSummary
from financial_dynamics.types import Regime


VALID_REGIME_NAMES = {r.name for r in Regime}


class TestVolatilityBucketClassifier:
    def test_returns_series_aligned_with_input(self, synthetic_ohlcv):
        df, _ = synthetic_ohlcv
        clf = VolatilityBucketClassifier()
        preds = clf.classify(df)
        assert len(preds) == len(df)
        valid = preds.dropna()
        assert all(p in VALID_REGIME_NAMES for p in valid)

    def test_uses_all_four_regimes_on_diverse_data(self, synthetic_ohlcv):
        df, _ = synthetic_ohlcv
        clf = VolatilityBucketClassifier()
        preds = clf.classify(df).dropna()
        assert preds.nunique() == 4


class TestTrendVolGridClassifier:
    def test_returns_series(self, synthetic_ohlcv):
        df, _ = synthetic_ohlcv
        clf = TrendVolGridClassifier()
        preds = clf.classify(df)
        assert len(preds) == len(df)
        valid = preds.dropna()
        assert all(p in VALID_REGIME_NAMES for p in valid)


class TestGaussianMixtureClassifier:
    def test_returns_series(self, synthetic_ohlcv):
        df, _ = synthetic_ohlcv
        clf = GaussianMixtureClassifier()
        preds = clf.classify(df)
        assert len(preds) == len(df)
        valid = preds.dropna()
        assert all(p in VALID_REGIME_NAMES for p in valid)

    def test_uses_all_four_regimes(self, synthetic_ohlcv):
        df, _ = synthetic_ohlcv
        clf = GaussianMixtureClassifier()
        preds = clf.classify(df).dropna()
        assert preds.nunique() == 4

    def test_deterministic_with_seed(self, synthetic_ohlcv):
        df, _ = synthetic_ohlcv
        clf1 = GaussianMixtureClassifier(random_state=42)
        clf2 = GaussianMixtureClassifier(random_state=42)
        preds1 = clf1.classify(df).dropna()
        preds2 = clf2.classify(df).dropna()
        assert (preds1 == preds2).all()


class TestBenchmarkRunner:
    def test_returns_benchmark_summary(self, synthetic_ohlcv):
        df, labels = synthetic_ohlcv
        runner = BenchmarkRunner()
        result = runner.run(df, labels)
        assert isinstance(result, BenchmarkSummary)
        assert "model" in result.summary.columns
        assert "accuracy" in result.summary.columns

    def test_includes_pipeline_and_all_baselines(self, synthetic_ohlcv):
        df, labels = synthetic_ohlcv
        runner = BenchmarkRunner()
        result = runner.run(df, labels)
        models = set(result.summary["model"])
        assert "financial_dynamics_pipeline" in models
        assert "volatility_bucket" in models
        assert "trend_vol_grid" in models
        assert "gaussian_mixture" in models

    def test_summary_sorted_by_accuracy_desc(self, synthetic_ohlcv):
        df, labels = synthetic_ohlcv
        runner = BenchmarkRunner()
        result = runner.run(df, labels)
        accuracies = result.summary["accuracy"].tolist()
        assert accuracies == sorted(accuracies, reverse=True)

    def test_per_model_reports_present(self, synthetic_ohlcv):
        df, labels = synthetic_ohlcv
        runner = BenchmarkRunner()
        result = runner.run(df, labels)
        for model_name in result.summary["model"]:
            assert model_name in result.per_model_reports
            assert "precision" in result.per_model_reports[model_name].columns

    def test_custom_baseline_list(self, synthetic_ohlcv):
        df, labels = synthetic_ohlcv
        runner = BenchmarkRunner(baselines=[VolatilityBucketClassifier()])
        result = runner.run(df, labels)
        assert len(result.summary) == 2  # pipeline + 1 baseline
