"""Signal detection: monitor regime changes and risk warnings.

Demonstrates the signal detection API that fires events when
regimes change, Risk-Off warnings appear, confidence drops,
or regimes stabilize after turbulence.

Usage:
    python examples/signals.py
    python examples/signals.py --symbol AAPL
"""

from __future__ import annotations

import argparse

from financial_dynamics import FinancialDynamicsPipeline, SignalDetector, SignalType
from financial_dynamics.data_loader import fetch_ohlcv


def main() -> None:
    parser = argparse.ArgumentParser(description="Signal detection")
    parser.add_argument("--symbol", default="SPY")
    parser.add_argument("--period", default="1y")
    args = parser.parse_args()

    print(f"Loading {args.symbol}...")
    df = fetch_ohlcv(args.symbol, period=args.period)

    pipeline = FinancialDynamicsPipeline()
    detector = SignalDetector()
    all_signals = []

    for timestamp, row in df.iterrows():
        bar = {
            "open": row["open"],
            "high": row["high"],
            "low": row["low"],
            "close": row["close"],
            "volume": row["volume"],
        }
        state = pipeline.step(bar, timestamp=str(timestamp))
        signals = detector.check(state)
        all_signals.extend(signals)

    print(f"\n{len(all_signals)} signals detected:\n")

    type_names = {
        SignalType.REGIME_CHANGE: "REGIME CHANGE",
        SignalType.RISKOFF_WARNING: "RISK-OFF WARN",
        SignalType.CONFIDENCE_DROP: "CONF DROP",
        SignalType.REGIME_STABILIZED: "STABILIZED",
    }

    for signal in all_signals:
        label = type_names.get(signal.signal_type, str(signal.signal_type))
        print(f"  [bar {signal.bar_index:4d}] {label:>15s}  {signal.message}")

    print("\nSignal summary:")
    for stype in SignalType:
        count = sum(1 for s in all_signals if s.signal_type == stype)
        if count > 0:
            label = type_names.get(stype, str(stype))
            print(f"  {label:>15s}: {count}")


if __name__ == "__main__":
    main()
