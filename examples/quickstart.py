"""Quick start example: classify market regimes for any ticker.

Usage:
    python examples/quickstart.py
    python examples/quickstart.py --symbol AAPL --period 2y
"""

from __future__ import annotations

import argparse

from financial_dynamics import REGIME_NAMES, FinancialDynamicsPipeline, Regime
from financial_dynamics.data_loader import fetch_ohlcv


def main() -> None:
    parser = argparse.ArgumentParser(description="Classify market regimes")
    parser.add_argument("--symbol", default="SPY", help="Ticker symbol")
    parser.add_argument("--period", default="1y", help="Data period (1mo, 6mo, 1y, 2y)")
    parser.add_argument("--interval", default="1d", help="Bar interval (1h, 1d, 1wk)")
    args = parser.parse_args()

    print(f"Fetching {args.symbol} ({args.period}, {args.interval})...")
    df = fetch_ohlcv(args.symbol, period=args.period, interval=args.interval)
    print(f"  {len(df)} bars loaded\n")

    pipeline = FinancialDynamicsPipeline()
    results = pipeline.run(df)

    valid = results.dropna(subset=["risk_adjusted_regime"])
    current = valid["risk_adjusted_regime"].iloc[-1]

    prob_cols = [f"post_prob_{r.name}" for r in Regime]
    confidence = valid[prob_cols].iloc[-1].max()

    print(f"Current regime: {current} ({confidence:.1%} confidence)")
    print(f"Warmup bars:    {pipeline.warmup_bars}")
    print(f"Classified:     {len(valid)} / {len(results)} bars\n")

    print("Regime distribution:")
    counts = valid["risk_adjusted_regime"].value_counts()
    for regime_name, count in counts.items():
        pct = count / len(valid) * 100
        print(f"  {regime_name:20s} {count:4d} bars ({pct:5.1f}%)")

    forecast = pipeline.forecast(horizon=10)
    if forecast:
        print("\nForecast (next 10 bars):")
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
