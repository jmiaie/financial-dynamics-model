"""CLI entry point for benchmarking the pipeline against simple baselines."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent))

from financial_dynamics.benchmarks import BenchmarkRunner
from financial_dynamics.config import PipelineConfig


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

    print("=" * 70)
    print("  Financial Dynamics Model -- Benchmark vs. Baselines")
    print("=" * 70)

    default_config_path = Path(__file__).parent.parent / "config" / "default.yaml"
    config, config_path = PipelineConfig.resolve(args.config, default_config_path)
    if config_path:
        print(f"\nLoaded config from {config_path}")
    else:
        print("\nUsing default config")

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
