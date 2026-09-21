"""CLI entry point for running the Financial Dynamics Pipeline."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent))


from financial_dynamics.config import PipelineConfig
from financial_dynamics.pipeline import FinancialDynamicsPipeline
from financial_dynamics.types import REGIME_NAMES, Regime


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Financial Dynamics Model pipeline.")
    parser.add_argument(
        "--symbol",
        type=str,
        default=None,
        help="Ticker symbol to fetch live data (e.g. SPY, AAPL). If omitted, uses synthetic data.",
    )
    parser.add_argument(
        "--period",
        type=str,
        default="1y",
        help="Lookback period for live data (default: 1y). Examples: 6mo, 1y, 2y, 5y.",
    )
    parser.add_argument(
        "--interval",
        type=str,
        default="1d",
        help="Bar interval for live data (default: 1d). Examples: 1d, 1h, 5m.",
    )
    parser.add_argument(
        "--reference-symbols",
        type=str,
        nargs="*",
        default=None,
        help="Reference symbols for cross-asset correlation stress "
        "(e.g. ^VIX TLT HYG). Requires --symbol.",
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to YAML config file. Defaults to config/default.yaml if it exists.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    print("=" * 70)
    print("  Financial Dynamics Model -- System Dynamics Pipeline")
    print("=" * 70)

    # Load config
    if args.config:
        config_path = Path(args.config)
    else:
        config_path = Path(__file__).parent.parent / "config" / "default.yaml"

    if config_path.exists():
        config = PipelineConfig.from_yaml(config_path)
        print(f"\nLoaded config from {config_path}")
    else:
        config = PipelineConfig()
        print("\nUsing default config")

    # Load data
    if args.symbol:
        ref_syms = args.reference_symbols or []
        if ref_syms:
            from financial_dynamics.data_loader import fetch_multi_asset

            print(
                f"\nFetching live data for {args.symbol} "
                f"+ references {ref_syms} "
                f"(period={args.period}, interval={args.interval})..."
            )
            df = fetch_multi_asset(
                args.symbol,
                ref_syms,
                period=args.period,
                interval=args.interval,
            )
            ref_cols = [c for c in df.columns if c.startswith("ref_")]
            print(f"  Reference columns loaded: {ref_cols}")
        else:
            from financial_dynamics.data_loader import fetch_ohlcv

            print(
                f"\nFetching live data for {args.symbol} "
                f"(period={args.period}, interval={args.interval})..."
            )
            df = fetch_ohlcv(args.symbol, period=args.period, interval=args.interval)
        print(f"  {len(df)} bars fetched")
        print(f"  Date range: {df.index[0]} - {df.index[-1]}")
        print(f"  Price range: {df['close'].min():.2f} - {df['close'].max():.2f}")
    else:
        from scripts.generate_synthetic_data import generate_synthetic_ohlcv

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
        print("\n  Predicted regime distribution:")
        print(f"  {valid['risk_adjusted_regime'].value_counts().to_string()}")

        print("\n  Transition Matrix (learned):")
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
    except ImportError as e:
        print(f"  Visualization skipped (missing dependency): {e}")
    else:
        dashboard = SystemDashboard(pipeline)
        dashboard.plot(df, results)
        output_path = Path("financial_dynamics_dashboard.png")
        try:
            dashboard.save(str(output_path))
            print(f"  Dashboard saved to {output_path}")
        except OSError as e:
            print(f"  Warning: could not save dashboard to {output_path}: {e}")

    print("\nDone.")


if __name__ == "__main__":
    main()
