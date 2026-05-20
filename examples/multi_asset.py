"""Multi-asset regime detection with cross-asset stress signals.

Loads a primary ticker plus reference assets, using cross-correlation
to detect systemic stress (contagion). The correlation_stress feature
spikes when assets become abnormally correlated.

Usage:
    python examples/multi_asset.py
    python examples/multi_asset.py --symbol QQQ --refs SPY,IWM,TLT,GLD
"""

from __future__ import annotations

import argparse

from financial_dynamics import FinancialDynamicsPipeline
from financial_dynamics.data_loader import fetch_multi_asset


def main() -> None:
    parser = argparse.ArgumentParser(description="Multi-asset regime detection")
    parser.add_argument("--symbol", default="SPY", help="Primary ticker")
    parser.add_argument(
        "--refs", default="QQQ,IWM,TLT,GLD,^VIX", help="Comma-separated reference tickers"
    )
    parser.add_argument("--period", default="1y")
    args = parser.parse_args()

    ref_symbols = [s.strip() for s in args.refs.split(",")]

    print(f"Loading {args.symbol} + {len(ref_symbols)} reference assets...")
    df = fetch_multi_asset(
        args.symbol,
        reference_symbols=ref_symbols,
        period=args.period,
    )

    ref_cols = [c for c in df.columns if c.startswith("ref_")]
    print(f"  {len(df)} bars, {len(ref_cols)} reference series loaded")
    for col in ref_cols:
        non_null = df[col].notna().sum()
        print(f"    {col}: {non_null} valid bars")

    print("\nRunning pipeline...")
    pipeline = FinancialDynamicsPipeline()
    results = pipeline.run(df)
    valid = results.dropna(subset=["risk_adjusted_regime"])

    print(f"\nRegime distribution ({len(valid)} classified bars):")
    counts = valid["risk_adjusted_regime"].value_counts()
    for regime_name, count in counts.items():
        pct = count / len(valid) * 100
        bar = "█" * int(pct / 2)
        print(f"  {regime_name:20s} {count:4d} ({pct:5.1f}%) {bar}")

    if "feat_corr_stress" in results.columns:
        stress = results["feat_corr_stress"].dropna()
        print("\nCorrelation stress stats:")
        print(f"  Mean:  {stress.mean():.3f}")
        print(f"  Max:   {stress.max():.3f}")
        print(f"  >0.6:  {(stress > 0.6).sum()} bars (high stress)")

    riskoff_bars = valid[valid["risk_adjusted_regime"] == "RISK_OFF"]
    if len(riskoff_bars) > 0:
        print(f"\nRisk-Off episodes: {len(riskoff_bars)} bars")
        print(f"  First: {riskoff_bars.index[0]}")
        print(f"  Last:  {riskoff_bars.index[-1]}")
    else:
        print("\nNo Risk-Off episodes detected in this period.")


if __name__ == "__main__":
    main()
