"""Tests for the prospective forecast ledger (research/forecast_ledger)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

LEDGER_DIR = Path(__file__).resolve().parents[1] / "research" / "forecast_ledger"
sys.path.insert(0, str(LEDGER_DIR))

import make_entry as me  # noqa: E402
import verify_ledger as vl  # noqa: E402


def _entry(date: str) -> dict:
    return {"schema": 1, "series_id": me.SERIES_ID, "as_of_date": date, "assets": {"SPY": 1.5}}


def _panel(n: int = 700, seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    index = pd.bdate_range("2020-01-01", periods=n)
    vol = np.repeat(rng.choice([0.006, 0.012, 0.025], n // 40 + 1), 40)[:n]
    close = 100 * np.exp(np.cumsum(rng.normal(0, 1, n) * vol))
    return pd.DataFrame({"close": close}, index=index)


def test_entries_chain_and_verify(tmp_path: Path) -> None:
    entries, ledger = tmp_path / "entries", tmp_path / "ledger.jsonl"
    first = me.write_entry(_entry("2026-11-20"), entries, ledger)
    second = me.write_entry(_entry("2026-11-27"), entries, ledger)
    assert json.loads(first.read_text())["previous_entry_sha256"] is None
    first_sha = me.sha256_bytes(first.read_bytes())
    assert json.loads(second.read_text())["previous_entry_sha256"] == first_sha
    assert vl.verify(entries, ledger) == []


def test_never_overwrites_or_goes_back(tmp_path: Path) -> None:
    entries, ledger = tmp_path / "entries", tmp_path / "ledger.jsonl"
    me.write_entry(_entry("2026-11-27"), entries, ledger)
    with pytest.raises(FileExistsError):
        me.write_entry(_entry("2026-11-27"), entries, ledger)
    with pytest.raises(ValueError, match="not after"):
        me.write_entry(_entry("2026-11-20"), entries, ledger)
    assert len(ledger.read_text().splitlines()) == 1


def test_verify_detects_tampering(tmp_path: Path) -> None:
    entries, ledger = tmp_path / "entries", tmp_path / "ledger.jsonl"
    first = me.write_entry(_entry("2026-11-20"), entries, ledger)
    me.write_entry(_entry("2026-11-27"), entries, ledger)
    first.write_text(first.read_text().replace("1.5", "1.6"))
    problems = vl.verify(entries, ledger)
    assert any("does not match" in p for p in problems)


def test_verify_detects_missing_unlisted_and_broken_chain(tmp_path: Path) -> None:
    entries, ledger = tmp_path / "entries", tmp_path / "ledger.jsonl"
    first = me.write_entry(_entry("2026-11-20"), entries, ledger)
    second = me.write_entry(_entry("2026-11-27"), entries, ledger)
    (entries / "2026-12-04.json").write_text("{}")
    assert any("not listed" in p for p in vl.verify(entries, ledger))
    (entries / "2026-12-04.json").unlink()
    lines = ledger.read_text().splitlines()
    ledger.write_text(lines[1] + "\n")
    assert any("breaks the chain" in p for p in vl.verify(entries, ledger))
    ledger.write_text("\n".join(lines) + "\n")
    second.unlink()
    assert any("is missing" in p for p in vl.verify(entries, ledger))
    assert first.exists()


def test_non_finite_value_is_an_error(tmp_path: Path) -> None:
    bad = _entry("2026-11-20")
    bad["assets"] = {"SPY": float("nan")}
    with pytest.raises(ValueError, match="non-finite"):
        me.write_entry(bad, tmp_path / "entries", tmp_path / "ledger.jsonl")
    assert not (tmp_path / "ledger.jsonl").exists()


def test_forecasts_use_only_data_up_to_the_as_of_date() -> None:
    """The last-row forecasts are unchanged when later rows are appended."""
    panel = _panel()
    labels = pd.Series(
        np.where(panel["close"].pct_change().rolling(20).std() > 0.012, "HIGH", "LOW"),
        index=panel.index,
        dtype=object,
    )
    cut = 600
    short = me.symbol_forecasts(panel.iloc[:cut], labels.iloc[:cut])
    assert set(short["forecasts"]) == {"1", "5"}
    for horizon in ("1", "5"):
        assert all(v > 0 for v in short["forecasts"][horizon].values())
    # The same numbers must come out of the full series at that row: later rows change nothing.
    returns = panel["close"].pct_change()
    buckets = me.vb.causal_volatility_bucket(returns)
    for horizon in (1, 5):
        target = me.vb.forward_sum_squared_returns(returns, horizon)
        full = {
            "fdm": me.vb.expanding_label_forecast(labels, target, horizon, me.MIN_COUNT),
            "vol_bucket": me.vb.expanding_label_forecast(buckets, target, horizon, me.MIN_COUNT),
            "unconditional": me.vb.expanding_unconditional_forecast(target, horizon),
            "ewma": me.vb.ewma_forecast(returns, horizon),
        }
        for name, series in full.items():
            assert series.iloc[cut - 1] == pytest.approx(short["forecasts"][str(horizon)][name])
    assert short["vol_bucket"] == buckets.iloc[cut - 1]


def test_missing_label_on_as_of_date_raises() -> None:
    panel = _panel()
    labels = pd.Series(["LOW"] * (len(panel) - 1) + [None], index=panel.index, dtype=object)
    with pytest.raises(ValueError, match="missing label"):
        me.symbol_forecasts(panel, labels)


def _raw(tmp_path: Path, n: int = 6) -> Path:
    raw = tmp_path / "raw"
    raw.mkdir()
    index = pd.bdate_range("2026-01-05", periods=n, name="Date")
    for symbol in me.SYMBOLS:
        frame = pd.DataFrame(1.0, index=index, columns=["Open", "High", "Low", "Close", "Volume"])
        frame.to_csv(raw / f"{symbol}.csv")
    return raw


def _blank(raw: Path, symbol: str, row: int) -> None:
    frame = pd.read_csv(raw / f"{symbol}.csv", index_col=0)
    frame.iloc[row, :4] = np.nan
    frame.to_csv(raw / f"{symbol}.csv")


def test_incomplete_newest_bar_is_dropped_for_every_asset(tmp_path: Path) -> None:
    raw = _raw(tmp_path)
    _blank(raw, "SPY", -1)
    dropped = me.drop_incomplete_tail(raw, tmp_path / "out")
    assert dropped == {symbol: 1 for symbol in me.SYMBOLS}
    for symbol in me.SYMBOLS:
        kept = pd.read_csv(tmp_path / "out" / f"{symbol}.csv", index_col=0)
        assert len(kept) == 5 and kept.notna().all().all()


def test_complete_files_lose_nothing(tmp_path: Path) -> None:
    raw = _raw(tmp_path)
    assert me.drop_incomplete_tail(raw, tmp_path / "out") == {s: 0 for s in me.SYMBOLS}


def test_incomplete_row_before_the_as_of_date_is_an_error(tmp_path: Path) -> None:
    raw = _raw(tmp_path)
    _blank(raw, "TLT", 2)
    with pytest.raises(ValueError, match="TLT has incomplete rows"):
        me.drop_incomplete_tail(raw, tmp_path / "out")
