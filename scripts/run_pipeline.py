"""CLI entry point for running the Financial Dynamics Pipeline."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import numpy as np

from financial_dynamics.pipeline import FinancialDynamicsPipeline
from financial_dynamics.config import PipelineConfig
from financial_dynamics.types import REGIME_NAMES, Regime


def main():
    # Generate synthetic data
    from scripts.generate_synthetic_data import generate_synthetic_ohlcv

    print("=" * 70)
    print("  Financial Dynamics Model -- System Dynamics Pipeline")
    print("=" * 70)

    # Load config
    config_path = Path(__file__).parent.parent / "config" / "default.yaml"
    if config_path.exists():
        config = PipelineConfig.from_yaml(config_path)
        print(f"\nLoaded config from {config_path}")
    else:
        config = PipelineConfig()
        print("\nUsing default config")

    # Generate data
    print("\nGenerating synthetic OHLCV data...")
    df, true_labels = generate_synthetic_ohlcv()
    print(f"  {len(df)} bars generated")
    print(f"  Price range: {df['close'].min():.2f} - {df['close'].max():.2f}")
    print(f"  True regime distribution:\n{true_labels.value_counts().to_string()}")

    # Run pipeline
    print("\nRunning pipeline...")
    pipeline = FinancialDynamicsPipeline(config)
    results = pipeline.run(df)

    # Report
    report = pipeline.get_state_report()
    valid = results.dropna(subset=["risk_adjusted_regime"])
    print(f"\n  Warmup bars: {report['warmup_bars']}")
    print(f"  Valid predictions: {len(valid)} / {len(results)}")

    if len(valid) > 0:
        print(f"\n  Predicted regime distribution:")
        print(f"  {valid['risk_adjusted_regime'].value_counts().to_string()}")

        print(f"\n  Transition Matrix (learned):")
        tm = report["transition_matrix"]
        header = "  " + " ".join(f"{REGIME_NAMES[r]:>14}" for r in Regime)
        print(header)
        for i, regime in enumerate(Regime):
            row = " ".join(f"{tm[i, j]:14.3f}" for j in range(4))
            print(f"  {REGIME_NAMES[regime]:<14} {row}")

    # Generate visualization
    print("\nGenerating dashboard...")
    try:
        from financial_dynamics.visualization.dashboard import SystemDashboard
        dashboard = SystemDashboard(pipeline)
        fig = dashboard.plot(df, results)
        output_path = Path("financial_dynamics_dashboard.png")
        dashboard.save(str(output_path))
        print(f"  Dashboard saved to {output_path}")
    except Exception as e:
        print(f"  Visualization skipped: {e}")

    print("\nDone.")


if __name__ == "__main__":
    main()
