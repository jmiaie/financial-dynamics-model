"""CLI entry point for calibrating the Financial Dynamics Pipeline."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent))

import yaml

from financial_dynamics.calibration import Calibrator
from financial_dynamics.persistence.state_io import _extract_config
from scripts._common import load_config


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Calibrate the Financial Dynamics Model on labeled training data."
    )
    parser.add_argument(
        "--output",
        type=str,
        default="config/calibrated.yaml",
        help="Where to save the calibrated config (default: config/calibrated.yaml).",
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to base YAML config. Defaults to config/default.yaml if it exists.",
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Use a smaller hyperparameter search space for faster runs.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    print("=" * 70)
    print("  Financial Dynamics Model -- Calibration")
    print("=" * 70)

    base_config = load_config(args.config)

    from scripts.generate_synthetic_data import generate_synthetic_ohlcv

    print("\nGenerating synthetic training data...")
    df, labels = generate_synthetic_ohlcv()
    print(f"  {len(df)} bars, regime distribution:")
    print(f"  {labels.value_counts().to_string()}")

    if args.quick:
        search_space = {
            "regimes.temperature": [0.5, 1.0, 2.0],
            "stabilization.hysteresis_threshold": [0.1, 0.2],
        }
    else:
        search_space = None

    print("\nRunning calibration...")
    calibrator = Calibrator(base_config)
    result = calibrator.calibrate(df, labels, search_space=search_space)

    print(f"\n  Baseline accuracy:        {result.baseline_accuracy:.1%}")
    print(f"  + fitted centroids:       {result.centroid_only_accuracy:.1%}  "
          f"(delta {result.centroid_only_accuracy - result.baseline_accuracy:+.1%})")
    print(f"  + tuned hyperparameters:  {result.tuned_accuracy:.1%}  "
          f"(delta {result.tuned_accuracy - result.baseline_accuracy:+.1%})")

    print(f"\n  Confusion matrix (calibrated):")
    print(f"  {result.tuned_result.confusion_matrix.to_string()}")

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    config_dict = _extract_config(result.calibrated_config)

    with open(output_path, "w") as f:
        yaml.safe_dump(config_dict, f, sort_keys=False)
    print(f"\n  Calibrated config saved to {output_path}")

    print("\nDone.")


if __name__ == "__main__":
    main()
