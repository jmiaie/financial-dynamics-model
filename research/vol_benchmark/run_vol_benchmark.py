#!/usr/bin/env python3
"""Run the regime-labels versus volatility-bucket study (research/vol_benchmark/PROTOCOL.md).

Reads a frozen raw-data directory (not in this repository) and its manifest, and writes
results/vol_benchmark/vol_benchmark.json. It changes no existing artifact.

    python research/vol_benchmark/run_vol_benchmark.py \\
        --raw-dir /path/to/yf_fd_etfs_daily_2015_2025_v3 \\
        --manifest /path/to/yf_fd_etfs_daily_2015_2025_v3.json
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

import vol_benchmark as vb

from financial_dynamics import FinancialDynamicsPipeline
from financial_dynamics.research.historical_study import (
    build_multi_asset_frame,
    pipeline_config_from_experiment_yaml,
)

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "configs/experiments/fdm_historical_regime_study_v1.yaml"
OUT = ROOT / "results/vol_benchmark/vol_benchmark.json"

SYMBOLS = ["SPY", "QQQ", "IWM", "TLT", "GLD"]
HORIZONS = [1, 5, 20]
PRIMARY_HORIZON = 1
BURN_IN = 504
MIN_COUNT = 20
MIN_COUNT_SENSITIVITY = 60
PREFIX_ROWS = 1500
MODELS = ["fdm", "vol_bucket", "unconditional", "ewma"]


def fdm_labels(panel: pd.DataFrame, config: Any) -> pd.Series:
    results = FinancialDynamicsPipeline(deepcopy(config)).run(panel)
    labels: pd.Series = results["risk_adjusted_regime"]
    return labels


def prefix_invariant(panel: pd.DataFrame, config: Any, full: pd.Series) -> dict[str, Any]:
    """Precondition P1: labels on a truncated panel equal the full run's labels."""
    short = fdm_labels(panel.iloc[:PREFIX_ROWS], config)
    a = short.astype(object).where(short.notna(), None).tolist()
    b = full.iloc[:PREFIX_ROWS].astype(object).where(full.iloc[:PREFIX_ROWS].notna(), None).tolist()
    mismatches = sum(1 for x, y in zip(a, b, strict=True) if str(x) != str(y))
    return {"rows_checked": len(a), "mismatches": mismatches, "passed": mismatches == 0}


def dm_dict(result: vb.DMResult) -> dict[str, Any]:
    return {
        "n": result.n,
        "mean_diff": result.mean_diff,
        "se": result.se,
        "stat": result.stat,
        "p_value": result.p_value,
        "lag": result.lag,
    }


def prepare_symbol(symbol: str, raw_dir: Path, config: Any) -> dict[str, Any]:
    """Compute the labels once per asset; both the primary and sensitivity runs reuse them."""
    references = [s for s in SYMBOLS if s != symbol]
    panel = build_multi_asset_frame(raw_dir, primary=symbol, references=references)
    returns = panel["close"].pct_change()
    raw_labels = fdm_labels(panel, config)
    check = prefix_invariant(panel, config, raw_labels)
    labels = raw_labels.astype(object)
    labels = labels.where(labels.notna(), None).map(lambda v: None if v is None else str(v))
    return {
        "symbol": symbol,
        "panel": panel,
        "returns": returns,
        "labels": labels,
        "buckets": vb.causal_volatility_bucket(returns),
        "prefix_invariance": check,
    }


def evaluate_symbol(
    prepared: dict[str, Any], min_count: int
) -> tuple[dict[str, Any], dict[int, pd.DataFrame]]:
    panel, returns = prepared["panel"], prepared["returns"]
    labels, buckets = prepared["labels"], prepared["buckets"]

    out: dict[str, Any] = {
        "rows": len(panel),
        "first_date": str(panel.index[0].date()),
        "last_date": str(panel.index[-1].date()),
        "prefix_invariance": prepared["prefix_invariance"],
        "fdm_label_counts": {str(k): int(v) for k, v in labels.value_counts().items()},
        "vol_bucket_counts": {str(k): int(v) for k, v in buckets.value_counts().items()},
        "horizons": {},
    }
    losses: dict[int, pd.DataFrame] = {}
    for horizon in HORIZONS:
        target = vb.forward_sum_squared_returns(returns, horizon)
        forecasts = pd.DataFrame(
            {
                "fdm": vb.expanding_label_forecast(labels, target, horizon, min_count),
                "vol_bucket": vb.expanding_label_forecast(buckets, target, horizon, min_count),
                "unconditional": vb.expanding_unconditional_forecast(target, horizon),
                "ewma": vb.ewma_forecast(returns, horizon),
            }
        )
        frame = forecasts.iloc[BURN_IN:].copy()
        frame["target"] = target.iloc[BURN_IN:]
        frame = frame.dropna()
        loss = pd.DataFrame({m: vb.qlike(frame[m], frame["target"]) for m in MODELS})
        losses[horizon] = loss
        out["horizons"][str(horizon)] = {
            "n": len(loss),
            "mean_qlike": {m: float(loss[m].mean()) for m in MODELS},
            "fdm_minus_vol_bucket": dm_dict(
                vb.diebold_mariano(loss["fdm"] - loss["vol_bucket"], horizon)
            ),
            "fdm_minus_unconditional": dm_dict(
                vb.diebold_mariano(loss["fdm"] - loss["unconditional"], horizon)
            ),
            "vol_bucket_minus_unconditional": dm_dict(
                vb.diebold_mariano(loss["vol_bucket"] - loss["unconditional"], horizon)
            ),
            "fdm_minus_ewma": dm_dict(vb.diebold_mariano(loss["fdm"] - loss["ewma"], horizon)),
            "vol_bucket_minus_ewma": dm_dict(
                vb.diebold_mariano(loss["vol_bucket"] - loss["ewma"], horizon)
            ),
        }
    return out, losses


def pooled(losses: dict[str, dict[int, pd.DataFrame]]) -> dict[str, Any]:
    """Average each day's losses across the five assets, then test the pooled series."""
    out: dict[str, Any] = {}
    for horizon in HORIZONS:
        frames = [losses[s][horizon] for s in SYMBOLS]
        common = frames[0].index
        for frame in frames[1:]:
            common = common.intersection(frame.index)
        mean = sum(frame.loc[common] for frame in frames) / len(frames)
        diff = mean["fdm"] - mean["vol_bucket"]
        result = vb.diebold_mariano(diff, horizon)
        gap = float(mean["unconditional"].mean() - mean["vol_bucket"].mean())
        mde = 2.8 * result.se if not math.isnan(result.se) else float("nan")
        out[str(horizon)] = {
            "n_dates": len(common),
            "mean_qlike": {m: float(mean[m].mean()) for m in MODELS},
            "fdm_minus_vol_bucket": dm_dict(result),
            "fdm_minus_unconditional": dm_dict(
                vb.diebold_mariano(mean["fdm"] - mean["unconditional"], horizon)
            ),
            "vol_bucket_minus_unconditional": dm_dict(
                vb.diebold_mariano(mean["vol_bucket"] - mean["unconditional"], horizon)
            ),
            "fdm_minus_ewma": dm_dict(vb.diebold_mariano(mean["fdm"] - mean["ewma"], horizon)),
            "vol_bucket_minus_ewma": dm_dict(
                vb.diebold_mariano(mean["vol_bucket"] - mean["ewma"], horizon)
            ),
            "mde80_qlike": mde,
            "vol_bucket_gain_over_unconditional": gap,
            "mde80_as_share_of_vol_bucket_gain": (mde / gap) if gap > 0 else float("nan"),
        }
    return out


def run(prepared: dict[str, dict[str, Any]], min_count: int) -> dict[str, Any]:
    per_symbol: dict[str, Any] = {}
    losses: dict[str, dict[int, pd.DataFrame]] = {}
    for symbol in SYMBOLS:
        per_symbol[symbol], losses[symbol] = evaluate_symbol(prepared[symbol], min_count)
    secondary = [
        per_symbol[s]["horizons"][str(PRIMARY_HORIZON)]["fdm_minus_vol_bucket"]["p_value"]
        for s in SYMBOLS
    ]
    for symbol, adjusted in zip(SYMBOLS, vb.holm_adjust(secondary), strict=True):
        per_symbol[symbol]["horizons"][str(PRIMARY_HORIZON)]["fdm_minus_vol_bucket"][
            "p_value_holm"
        ] = adjusted
    return {
        "min_count": min_count,
        "preconditions_passed": all(per_symbol[s]["prefix_invariance"]["passed"] for s in SYMBOLS),
        "pooled": pooled(losses),
        "per_symbol": per_symbol,
    }


def clean(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: clean(v) for k, v in value.items()}
    if isinstance(value, list):
        return [clean(v) for v in value]
    if isinstance(value, (float, np.floating)):
        return None if math.isnan(float(value)) else float(f"{float(value):.10g}")
    if isinstance(value, np.integer):
        return int(value)
    return value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args(argv)

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    _, config = pipeline_config_from_experiment_yaml(CONFIG)
    prepared = {symbol: prepare_symbol(symbol, args.raw_dir, config) for symbol in SYMBOLS}
    primary = run(prepared, MIN_COUNT)
    sensitivity = run(prepared, MIN_COUNT_SENSITIVITY)
    payload = {
        "study": "regime labels versus trailing-volatility bucket (forward variance, QLIKE)",
        "protocol": "research/vol_benchmark/PROTOCOL.md",
        "classification": "PREVIOUSLY INSPECTED / HISTORICAL EVALUATION",
        "dataset": {
            "dataset_id": manifest["dataset_id"],
            "dataset_canonical_sha256": manifest["sha256"]["dataset_canonical"],
            "source": manifest["source"],
            "source_version": manifest["source_version"],
            "retrieval_timestamp_utc": manifest["retrieval_timestamp_utc"],
        },
        "design": {
            "symbols": SYMBOLS,
            "horizons": HORIZONS,
            "primary_horizon": PRIMARY_HORIZON,
            "burn_in_rows": BURN_IN,
            "min_count": MIN_COUNT,
            "min_count_sensitivity": MIN_COUNT_SENSITIVITY,
            "prefix_rows": PREFIX_ROWS,
            "config": str(CONFIG.relative_to(ROOT)),
        },
        "primary": primary,
        "sensitivity_min_count_60": sensitivity,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(clean(payload), indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    pooled_primary = primary["pooled"][str(PRIMARY_HORIZON)]["fdm_minus_vol_bucket"]
    print(f"wrote {args.out}")
    print(f"preconditions passed: {primary['preconditions_passed']}")
    print(f"pooled 1-day FDM minus vol-bucket QLIKE: {pooled_primary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
