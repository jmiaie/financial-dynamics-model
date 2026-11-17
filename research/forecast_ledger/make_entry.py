#!/usr/bin/env python3
"""Write one entry of the prospective forecast ledger (research/forecast_ledger/PROTOCOL.md).

Reads a raw-data directory of daily prices (not in this repository), computes the regime label,
the trailing-volatility quartile and the variance forecasts on the latest close, and writes
entries/<as_of_date>.json plus one line in ledger.jsonl. It never overwrites an entry.

    python research/forecast_ledger/make_entry.py --raw-dir /path/to/raw --trigger schedule
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
import sys
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "research" / "vol_benchmark"))

import vol_benchmark as vb  # noqa: E402

from financial_dynamics import FinancialDynamicsPipeline  # noqa: E402
from financial_dynamics.research.historical_study import (  # noqa: E402
    build_multi_asset_frame,
    pipeline_config_from_experiment_yaml,
)

SERIES_ID = "fdm-vol-v1"
SYMBOLS = ["SPY", "QQQ", "IWM", "TLT", "GLD"]
HORIZONS = [1, 5]
MIN_COUNT = 20
CONFIG = ROOT / "configs/experiments/fdm_historical_regime_study_v1.yaml"
ENTRIES = HERE / "entries"
LEDGER = HERE / "ledger.jsonl"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def clean(value: Any) -> Any:
    """JSON-safe values; a non-finite number is an error, never a silent null."""
    if isinstance(value, dict):
        return {str(k): clean(v) for k, v in value.items()}
    if isinstance(value, list):
        return [clean(v) for v in value]
    if isinstance(value, (float, np.floating)):
        if not math.isfinite(float(value)):
            raise ValueError("non-finite value in ledger entry")
        return float(f"{float(value):.10g}")
    if isinstance(value, np.integer):
        return int(value)
    return value


def regime_labels(panel: pd.DataFrame, config: Any) -> pd.Series:
    results = FinancialDynamicsPipeline(deepcopy(config)).run(panel)
    labels: pd.Series = results["risk_adjusted_regime"]
    out = labels.astype(object)
    return out.where(out.notna(), None).map(lambda v: None if v is None else str(v))


def symbol_forecasts(panel: pd.DataFrame, labels: pd.Series) -> dict[str, Any]:
    """Label, volatility quartile and variance forecasts on the last row of ``panel``."""
    returns = panel["close"].pct_change()
    buckets = vb.causal_volatility_bucket(returns)
    label, bucket = labels.iloc[-1], buckets.iloc[-1]
    if label is None or bucket is None or (isinstance(bucket, float) and math.isnan(bucket)):
        raise ValueError("missing label or volatility quartile on the as-of date")
    out: dict[str, Any] = {"regime_label": str(label), "vol_bucket": str(bucket), "forecasts": {}}
    for horizon in HORIZONS:
        target = vb.forward_sum_squared_returns(returns, horizon)
        out["forecasts"][str(horizon)] = {
            "fdm": vb.expanding_label_forecast(labels, target, horizon, MIN_COUNT).iloc[-1],
            "vol_bucket": vb.expanding_label_forecast(buckets, target, horizon, MIN_COUNT).iloc[-1],
            "unconditional": vb.expanding_unconditional_forecast(target, horizon).iloc[-1],
            "ewma": vb.ewma_forecast(returns, horizon).iloc[-1],
        }
    return out


def code_commit() -> str:
    try:
        done = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True
        )
        return done.stdout.strip()
    except (subprocess.CalledProcessError, OSError):
        return "unknown"


def previous_entry(ledger: Path) -> dict[str, str] | None:
    if not ledger.exists():
        return None
    lines = [ln for ln in ledger.read_text(encoding="utf-8").splitlines() if ln.strip()]
    if not lines:
        return None
    last: dict[str, str] = json.loads(lines[-1])
    return last


def build_entry(raw_dir: Path, trigger: str, created_utc: str) -> dict[str, Any]:
    _, config = pipeline_config_from_experiment_yaml(CONFIG)
    per_symbol: dict[str, Any] = {}
    as_of: set[str] = set()
    for symbol in SYMBOLS:
        references = [s for s in SYMBOLS if s != symbol]
        panel = build_multi_asset_frame(raw_dir, primary=symbol, references=references)
        as_of.add(str(panel.index[-1].date()))
        per_symbol[symbol] = symbol_forecasts(panel, regime_labels(panel, config))
    if len(as_of) != 1:
        raise ValueError(f"assets disagree on the latest close: {sorted(as_of)}")
    return {
        "schema": 1,
        "series_id": SERIES_ID,
        "protocol": "research/forecast_ledger/PROTOCOL.md",
        "as_of_date": as_of.pop(),
        "created_utc": created_utc,
        "trigger": trigger,
        "code_commit": code_commit(),
        "config_sha256": sha256_bytes(CONFIG.read_bytes()),
        "input_sha256": {
            f"{s}.csv": sha256_bytes((raw_dir / f"{s}.csv").read_bytes()) for s in SYMBOLS
        },
        "min_count": MIN_COUNT,
        "assets": per_symbol,
    }


def write_entry(entry: dict[str, Any], entries: Path, ledger: Path) -> Path:
    """Write the entry and append the ledger line. Refuses to overwrite or go back in time."""
    path = entries / f"{entry['as_of_date']}.json"
    if path.exists():
        raise FileExistsError(f"entry {path.name} already exists; entries are never overwritten")
    prev = previous_entry(ledger)
    if prev is not None and entry["as_of_date"] <= prev["as_of_date"]:
        raise ValueError(
            f"as_of_date {entry['as_of_date']} is not after the last entry {prev['as_of_date']}"
        )
    entry = {**entry, "previous_entry_sha256": prev["sha256"] if prev else None}
    body = (json.dumps(clean(entry), indent=2, sort_keys=True) + "\n").encode("utf-8")
    entries.mkdir(parents=True, exist_ok=True)
    path.write_bytes(body)
    line = {"as_of_date": entry["as_of_date"], "file": path.name, "sha256": sha256_bytes(body)}
    with ledger.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(line, sort_keys=True) + "\n")
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, required=True)
    parser.add_argument("--trigger", choices=["schedule", "manual", "dry-run"], required=True)
    parser.add_argument("--entries", type=Path, default=ENTRIES)
    parser.add_argument("--ledger", type=Path, default=LEDGER)
    args = parser.parse_args(argv)

    created = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    entry = build_entry(args.raw_dir, args.trigger, created)
    path = write_entry(entry, args.entries, args.ledger)
    print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
