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
    results = pipeline.run(df)

    detector = SignalDetector()
    signals = detector.detect_all(results)

    print(f"\n{len(signals)} signals detected:\n")

    type_names = {
        SignalType.REGIME_CHANGE: "REGIME CHANGE",
        SignalType.RISKOFF_WARNING: "RISK-OFF WARN",
        SignalType.CONFIDENCE_DROP: "CONF DROP",
        SignalType.REGIME_STABILIZED: "STABILIZED",
    }

    for signal in signals:
        label = type_names.get(signal.signal_type, str(signal.signal_type))
        date = str(results.index[signal.bar_index])[:10] if signal.bar_index < len(results) else "?"
        print(f"  [{date}] {label:>15s}  {signal.message}")

    print("\nSignal summary:")
    for stype in SignalType:
        count = sum(1 for s in signals if s.signal_type == stype)
        if count > 0:
            label = type_names.get(stype, str(stype))
            print(f"  {label:>15s}: {count}")


if __name__ == "__main__":
    main()
