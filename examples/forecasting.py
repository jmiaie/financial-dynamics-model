"""Regime forecasting: predict where the market is heading.

Uses the learned Markov transition matrix to forecast regime probabilities
k steps ahead. Also computes expected duration in the current regime and
the stationary (long-run equilibrium) distribution.

Usage:
    python examples/forecasting.py
    python examples/forecasting.py --symbol QQQ --horizon 20
"""

from __future__ import annotations

import argparse

from financial_dynamics import REGIME_NAMES, FinancialDynamicsPipeline, Regime
from financial_dynamics.data_loader import fetch_ohlcv
from financial_dynamics.forecasting import compute_stationary_distribution


def main() -> None:
    parser = argparse.ArgumentParser(description="Regime forecasting")
    parser.add_argument("--symbol", default="SPY")
    parser.add_argument("--period", default="1y")
    parser.add_argument("--horizon", type=int, default=10, help="Forecast horizon (bars)")
    args = parser.parse_args()

    print(f"Loading {args.symbol}...")
    df = fetch_ohlcv(args.symbol, period=args.period)
    pipeline = FinancialDynamicsPipeline()
    results = pipeline.run(df)

    valid = results.dropna(subset=["risk_adjusted_regime"])
    current = valid["risk_adjusted_regime"].iloc[-1]
    print(f"Current regime: {current}\n")

    forecast = pipeline.forecast(horizon=args.horizon)
    if not forecast:
        print("Forecast unavailable (insufficient data)")
        return

    print(f"Expected duration in current regime: {forecast.expected_duration:.1f} bars")
    print(f"\nMost likely path (next {args.horizon} bars):")
    for step, regime in enumerate(forecast.most_likely_path, 1):
        probs = forecast.horizon_probs[step - 1]
        conf = max(probs)
        print(f"  t+{step:2d}: {REGIME_NAMES[regime]:20s} ({conf:.1%})")

    print("\nProbability evolution:")
    header = "".join(f"{REGIME_NAMES[r]:>14s}" for r in Regime)
    print(f"  {'Step':>6s}{header}")
    for step, probs in enumerate(forecast.horizon_probs, 1):
        row = "".join(f"{p:14.3f}" for p in probs)
        print(f"  t+{step:4d}{row}")

    tm = pipeline._transition_engine.get_transition_matrix()
    stationary = compute_stationary_distribution(tm)
    print("\nStationary (long-run) distribution:")
    for regime, prob in zip(Regime, stationary.probs, strict=True):
        bar = "█" * int(prob * 40)
        print(f"  {REGIME_NAMES[regime]:20s} {prob:6.1%} {bar}")


if __name__ == "__main__":
    main()
