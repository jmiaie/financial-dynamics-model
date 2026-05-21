"""Backtest and evaluate regime classification accuracy.

Compares pipeline predictions against labeled regime data to compute
accuracy, confusion matrix, and per-regime precision/recall/F1.

This example generates synthetic data with known regime segments,
then measures how well the pipeline recovers them.

Usage:
    python examples/backtesting.py
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from financial_dynamics import FinancialDynamicsPipeline, Regime
from financial_dynamics.backtesting.evaluator import BacktestEvaluator
from financial_dynamics.backtesting.metrics import (
    regime_accuracy,
    regime_classification_report,
    regime_confusion_matrix,
)


def generate_labeled_data() -> tuple[pd.DataFrame, pd.Series]:
    """Create synthetic OHLCV with known regime labels."""
    rng = np.random.default_rng(42)
    segments = [
        (Regime.CALM_TREND, 80, 0.0015, 0.007),
        (Regime.VOLATILE_TREND, 60, 0.003, 0.020),
        (Regime.CHOP, 60, 0.0, 0.008),
        (Regime.RISK_OFF, 40, -0.004, 0.018),
    ]

    price = 100.0
    rows = []
    labels = []

    for regime, n_bars, drift, vol in segments:
        for _ in range(n_bars):
            ret = drift + rng.normal(0, vol)
            close = price * (1 + ret)
            high = max(price, close) * (1 + abs(rng.normal(0, 0.002)))
            low = min(price, close) * (1 - abs(rng.normal(0, 0.002)))
            rows.append([price, high, low, close, int(rng.integers(2000, 20000))])
            labels.append(regime.name)
            price = close

    df = pd.DataFrame(rows, columns=["open", "high", "low", "close", "volume"])
    df.index = pd.date_range("2024-01-01", periods=len(df), freq="B")
    label_series = pd.Series(labels, index=df.index, name="regime")

    return df, label_series


def main() -> None:
    print("Generating synthetic data with 4 regime segments...\n")
    df, labels = generate_labeled_data()

    pipeline = FinancialDynamicsPipeline()
    results = pipeline.run(df)

    predicted = results["risk_adjusted_regime"]
    valid_mask = predicted.notna() & labels.notna()
    true = labels[valid_mask]
    pred = predicted[valid_mask]

    accuracy = regime_accuracy(true, pred)
    print(f"Overall accuracy: {accuracy:.1%}\n")

    print("Confusion matrix:")
    cm = regime_confusion_matrix(true, pred)
    print(cm.to_string())

    print("\nClassification report:")
    report = regime_classification_report(true, pred)
    print(report.to_string(float_format="{:.3f}".format))

    print("\n--- Evaluator API ---")
    evaluator = BacktestEvaluator()
    result = evaluator.evaluate(df, labels)
    print(f"Evaluator accuracy: {result.accuracy:.1%}")
    print(f"Evaluator bars:     {result.total_bars}")


if __name__ == "__main__":
    main()
