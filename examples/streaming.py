"""Streaming mode: process bars one at a time.

Demonstrates the pipeline's streaming API for real-time or event-driven use.
Each call to pipeline.step() processes one bar and returns the full state.

Usage:
    python examples/streaming.py
"""

from __future__ import annotations

from financial_dynamics import REGIME_NAMES, FinancialDynamicsPipeline
from financial_dynamics.data_loader import fetch_ohlcv


def main() -> None:
    print("Fetching SPY data...")
    df = fetch_ohlcv("SPY", period="6mo", interval="1d")
    print(f"  {len(df)} bars\n")

    pipeline = FinancialDynamicsPipeline()

    print(f"{'Bar':>4s}  {'Date':>12s}  {'Close':>8s}  {'Regime':>20s}  {'Confidence':>10s}")
    print("-" * 65)

    for idx, (timestamp, row) in enumerate(df.iterrows()):
        bar = {
            "open": row["open"],
            "high": row["high"],
            "low": row["low"],
            "close": row["close"],
            "volume": row["volume"],
        }
        state = pipeline.step(bar)

        if state.risk_adjusted_regime is not None:
            regime_name = REGIME_NAMES[state.risk_adjusted_regime]
            conf = max(state.posterior_probabilities) if state.posterior_probabilities else 0.0
            date_str = str(timestamp)[:10]
            print(
                f"{idx:4d}  {date_str:>12s}  {row['close']:8.2f}  {regime_name:>20s}  {conf:10.1%}"
            )

    report = pipeline.get_state_report()
    print("\nFinal state:")
    print(f"  Regime:     {REGIME_NAMES[report['current_regime']]}")
    print(f"  Bars seen:  {report['bars_processed']}")


if __name__ == "__main__":
    main()
