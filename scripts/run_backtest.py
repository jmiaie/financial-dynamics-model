"""CLI entry point for running backtests on synthetic or loaded data."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd

from financial_dynamics.backtesting import BacktestEvaluator
from scripts._common import load_config


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Backtest the Financial Dynamics Model against labeled data."
    )
    parser.add_argument(
        "--data",
        type=str,
        default=None,
        help="Path to OHLCV CSV file. If omitted, uses synthetic data.",
    )
    parser.add_argument(
        "--labels",
        type=str,
        default=None,
        help="Path to labels CSV file (must align with --data).",
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to YAML config file.",
    )
    parser.add_argument(
        "--rolling",
        action="store_true",
        help="Run rolling-window evaluation.",
    )
    parser.add_argument(
        "--window-size",
        type=int,
        default=120,
        help="Rolling window size in bars (default: 120).",
    )
    parser.add_argument(
        "--step-size",
        type=int,
        default=30,
        help="Rolling window step size (default: 30).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    print("=" * 70)
    print("  Financial Dynamics Model -- Backtest Evaluation")
    print("=" * 70)

    config = load_config(args.config)

    if args.data and args.labels:
        print(f"\nLoading data from {args.data}")
        df = pd.read_csv(args.data, index_col=0, parse_dates=True)
        true_labels = pd.read_csv(args.labels, index_col=0, squeeze=False).iloc[:, 0]
        print(f"  {len(df)} bars loaded")
    else:
        from scripts.generate_synthetic_data import generate_synthetic_ohlcv

        print("\nUsing synthetic data with known regime segments...")
        df, true_labels = generate_synthetic_ohlcv()
        print(f"  {len(df)} bars generated")

    print(f"  True regime distribution:\n  {true_labels.value_counts().to_string()}")

    evaluator = BacktestEvaluator(config)

    print("\nRunning backtest...")
    result = evaluator.evaluate(df, true_labels)

    print(f"\n  Total bars:     {result.total_bars}")
    print(f"  Warmup bars:    {result.warmup_bars}")
    print(f"  Evaluated bars: {result.evaluated_bars}")
    print(f"  Overall accuracy: {result.accuracy:.1%}")

    print(f"\n  Confusion Matrix:")
    print(f"  {result.confusion_matrix.to_string()}")

    print(f"\n  Classification Report:")
    print(f"  {result.classification_report.to_string()}")

    if args.rolling:
        print(f"\n  Rolling evaluation (window={args.window_size}, step={args.step_size}):")
        rolling = evaluator.evaluate_rolling(
            df, true_labels,
            window_size=args.window_size,
            step_size=args.step_size,
        )
        for _, row in rolling.iterrows():
            print(
                f"    bars {int(row['window_start']):>4}-{int(row['window_end']):>4}: "
                f"accuracy={row['accuracy']:.1%} "
                f"(n={int(row['evaluated_bars'])})"
            )

    print("\nDone.")


if __name__ == "__main__":
    main()
