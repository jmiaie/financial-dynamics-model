"""Allow running the pipeline via `python -m financial_dynamics`."""

from __future__ import annotations

import argparse
import sys

from financial_dynamics import REGIME_NAMES, FinancialDynamicsPipeline, Regime
from financial_dynamics.config import PipelineConfig


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="python -m financial_dynamics",
        description="Financial Dynamics Model — Bayesian regime classification pipeline",
    )
    parser.add_argument("symbol", nargs="?", default="SPY", help="Ticker symbol (default: SPY)")
    parser.add_argument("--period", default="1y", help="Data period (default: 1y)")
    parser.add_argument("--interval", default="1d", help="Bar interval (default: 1d)")
    parser.add_argument("--config", default=None, help="Path to YAML config file")
    parser.add_argument("--forecast", type=int, default=10, help="Forecast horizon (default: 10)")
    parser.add_argument("--version", action="store_true", help="Show version and exit")
    args = parser.parse_args()

    if args.version:
        from financial_dynamics import __version__

        print(f"financial-dynamics {__version__}")
        sys.exit(0)

    try:
        from financial_dynamics.data_loader import fetch_ohlcv
    except ImportError:
        print("yfinance is required for live data: pip install financial-dynamics[data]")
        sys.exit(1)

    if args.config:
        config = PipelineConfig.from_yaml(args.config)
    else:
        config = PipelineConfig()

    print(f"Loading {args.symbol} ({args.period}, {args.interval})...")
    df = fetch_ohlcv(args.symbol, period=args.period, interval=args.interval)
    print(f"  {len(df)} bars\n")

    pipeline = FinancialDynamicsPipeline(config)
    results = pipeline.run(df)

    valid = results.dropna(subset=["risk_adjusted_regime"])
    current = valid["risk_adjusted_regime"].iloc[-1]
    prob_cols = [f"post_prob_{r.name}" for r in Regime]
    confidence = valid[prob_cols].iloc[-1].max()

    print(f"Current regime: {current} ({confidence:.1%} confidence)")
    print(f"Classified:     {len(valid)} / {len(results)} bars\n")

    print("Regime distribution:")
    counts = valid["risk_adjusted_regime"].value_counts()
    for regime_name, count in counts.items():
        pct = count / len(valid) * 100
        bar = "█" * int(pct / 2)
        print(f"  {regime_name:20s} {count:4d} ({pct:5.1f}%) {bar}")

    forecast = pipeline.forecast(horizon=args.forecast)
    if forecast:
        print(f"\nForecast (next {args.forecast} bars):")
        print(f"  Expected duration: {forecast.expected_duration:.1f} bars in current regime")
        path = " → ".join(REGIME_NAMES[r] for r in forecast.most_likely_path[:5])
        print(f"  Most likely path:  {path}")

    print("\nTransition matrix:")
    tm = pipeline._transition_engine.get_transition_matrix()
    header = "".join(f"{REGIME_NAMES[r]:>14s}" for r in Regime)
    print(f"  {'From / To':>14s}{header}")
    for i, r_from in enumerate(Regime):
        row = "".join(f"{tm[i, j]:14.3f}" for j in range(len(Regime)))
        print(f"  {REGIME_NAMES[r_from]:>14s}{row}")


if __name__ == "__main__":
    main()
