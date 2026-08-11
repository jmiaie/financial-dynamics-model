"""CLI entry point for benchmarking the pipeline against simple baselines."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent))

from financial_dynamics.benchmarks import BenchmarkRunner
from scripts._cli_common import load_config, print_banner


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Benchmark the Financial Dynamics pipeline against simple baselines."
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to YAML config (default: config/default.yaml).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    print_banner("Financial Dynamics Model -- Benchmark vs. Baselines")

    config = load_config(args.config)

    from scripts.generate_synthetic_data import generate_synthetic_ohlcv

    print("\nGenerating synthetic data with known regime segments...")
    df, labels = generate_synthetic_ohlcv()
    print(f"  {len(df)} bars")

    print("\nRunning benchmark...")
    runner = BenchmarkRunner(config)
    result = runner.run(df, labels)

    print("\n  Results (sorted by accuracy):")
    print(f"  {result.summary.to_string(index=False)}")

    print("\n  Per-model classification reports:")
    for model_name, report in result.per_model_reports.items():
        print(f"\n  --- {model_name} ---")
        print(f"  {report.to_string()}")

    print("\nDone.")


if __name__ == "__main__":
    main()
