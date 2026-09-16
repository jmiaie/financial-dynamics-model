"""Offline tests for Directive #9 historical study helpers."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from financial_dynamics.config import PipelineConfig
from financial_dynamics.research.historical_study import (
    PeriodSpec,
    build_multi_asset_frame,
    load_frozen_symbol_csv,
    run_historical_period,
    slice_period,
    write_artifacts,
)


def _write_symbol_csv(path: Path, start: str, n: int, seed: int) -> None:
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range(start, periods=n)
    prices = 100 + np.cumsum(rng.normal(0, 1, n))
    df = pd.DataFrame(
        {
            "Capital Gains": 0.0,
            "Close": prices,
            "Dividends": 0.0,
            "High": prices + 0.5,
            "Low": prices - 0.5,
            "Open": prices,
            "Stock Splits": 0.0,
            "Volume": rng.integers(1_000_000, 2_000_000, n),
        },
        index=dates,
    )
    df.index.name = "Date"
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, date_format="%Y-%m-%d")


@pytest.fixture
def frozen_raw_dir(tmp_path: Path) -> Path:
    raw = tmp_path / "raw"
    for i, symbol in enumerate(["SPY", "QQQ", "IWM", "TLT", "GLD"]):
        _write_symbol_csv(raw / f"{symbol}.csv", "2015-01-02", n=400, seed=10 + i)
    return raw


def test_load_and_build_panel(frozen_raw_dir: Path):
    panel = build_multi_asset_frame(frozen_raw_dir, primary="SPY", references=["QQQ", "TLT"])
    assert list(panel.columns)[:5] == ["open", "high", "low", "close", "volume"]
    assert "ref_QQQ_close" in panel.columns
    assert "ref_TLT_close" in panel.columns
    assert panel["close"].isna().sum() == 0


def test_slice_period_inclusive_end(frozen_raw_dir: Path):
    panel = build_multi_asset_frame(frozen_raw_dir)
    period = PeriodSpec("demo", "2015-01-02", "2015-01-15")
    sliced = slice_period(panel, period)
    assert sliced.index.min() >= pd.Timestamp("2015-01-02")
    assert sliced.index.max() <= pd.Timestamp("2015-01-15")


def test_run_historical_period_writes_artifact(frozen_raw_dir: Path, tmp_path: Path):
    panel = build_multi_asset_frame(frozen_raw_dir)
    # Use enough bars for warmup (~60+)
    formation = PeriodSpec("formation_dev", "2015-01-02", "2015-12-31")
    validation = PeriodSpec("validation", "2016-01-01", "2016-06-30")
    artifacts = run_historical_period(
        experiment_id="unit_hist_val",
        dataset_id="unit_dataset",
        config_path="configs/experiments/fdm_historical_regime_study_v1.yaml",
        panel=panel,
        eval_period=validation,
        history_period=formation,
        pipeline_config=PipelineConfig(),
        horizons=(1, 5),
        seed=0,
        include_benchmarks=True,
        notes="unit test",
    )
    assert artifacts.models
    fdm = artifacts.models[0]
    assert fdm.model == "financial_dynamics_pipeline"
    assert fdm.evaluated_bars > 0
    assert "n_regimes_observed" in fdm.key_metrics
    path, digest = write_artifacts(artifacts, tmp_path / "out")
    assert path.exists()
    assert len(digest) == 64
    names = {m.model for m in artifacts.models}
    assert "volatility_bucket" in names
    assert "gaussian_mixture" in names


def test_load_frozen_symbol_rejects_missing_ohlcv(tmp_path: Path):
    bad = tmp_path / "BAD.csv"
    bad.write_text("Date,Close\n2015-01-02,1.0\n", encoding="utf-8")
    with pytest.raises(ValueError, match="missing OHLCV"):
        load_frozen_symbol_csv(bad)
