"""Offline tests for historical-data acquisition helpers (no network)."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "acquire_yf_fd_etfs_daily.py"


def _load_acquire_module():
    spec = importlib.util.spec_from_file_location("acquire_yf_fd_etfs_daily", SCRIPT)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def acq():
    return _load_acquire_module()


def _sample_frame(n: int = 10) -> pd.DataFrame:
    dates = pd.date_range("2015-01-02", periods=n, freq="B")
    rng = np.random.default_rng(0)
    prices = 100 + np.cumsum(rng.normal(0, 0.5, n))
    return pd.DataFrame(
        {
            "Open": prices - 0.1,
            "High": prices + 0.2,
            "Low": prices - 0.2,
            "Close": prices,
            "Volume": rng.integers(1_000_000, 2_000_000, n),
            "Dividends": 0.0,
            "Stock Splits": 0.0,
            "Capital Gains": 0.0,
        },
        index=dates,
    )


def test_validate_frame_counts(acq):
    df = _sample_frame()
    stats = acq.validate_frame("SPY", df)
    assert stats["row_count"] == 10
    assert stats["missing_ohlcv_cells"] == 0
    assert stats["actual_start"] == "2015-01-02"
    assert stats["actions"]["dividends"]["present"] is True


def test_validate_frame_rejects_duplicates(acq):
    df = _sample_frame()
    df.index = list(df.index[:-1]) + [df.index[-2]]
    with pytest.raises(ValueError, match="duplicate"):
        acq.validate_frame("SPY", df)


def test_canonical_hash_is_order_independent_on_dict_insertion(acq):
    a = {"QQQ.csv": "abc", "SPY.csv": "def"}
    b = {"SPY.csv": "def", "QQQ.csv": "abc"}
    assert acq.canonical_dataset_hash(a) == acq.canonical_dataset_hash(b)


def test_sha256_file(acq, tmp_path: Path):
    path = tmp_path / "x.csv"
    path.write_text("a,b\n1,2\n", encoding="utf-8")
    digest = acq.sha256_file(path)
    assert len(digest) == 64
    assert digest == acq.sha256_file(path)


def test_build_manifest_null_sha_before_freeze(acq):
    per = {
        "SPY": {
            "row_count": 1,
            "missing_ohlcv_cells": 0,
            "actual_start": "2015-01-02",
            "actual_end": "2015-01-02",
            "actions": {},
            "columns": ["Close"],
        }
    }
    manifest = acq.build_manifest(
        dataset_id="yf_fd_etfs_daily_2015_2025_v1",
        symbols=["SPY"],
        yf_version="1.7.0",
        retrieval_ts="2026-09-16T00:00:00Z",
        freeze_ts=None,
        status="VALIDATED",
        per_symbol=per,
        parameters={"interval": "1d", "start": "2015-01-01", "end": "2026-01-01"},
        sha256=None,
        notes="test",
    )
    assert manifest["sha256"] is None
    assert manifest["freeze_timestamp_utc"] is None
    assert manifest["status"] == "VALIDATED"


def test_flatten_multiindex_columns(acq):
    arrays = [
        ["Close", "Open", "High", "Low", "Volume", "Dividends", "Stock Splits", "Capital Gains"],
        ["SPY"] * 8,
    ]
    cols = pd.MultiIndex.from_arrays(arrays)
    idx = pd.date_range("2015-01-02", periods=3, freq="B")
    raw = pd.DataFrame(np.arange(24, dtype=float).reshape(3, 8), index=idx, columns=cols)
    flat = acq._flatten_columns(raw, "SPY")
    assert "Close" in flat.columns
    assert "Dividends" in flat.columns
