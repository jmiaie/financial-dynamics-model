"""Tests for the regime-labels versus volatility-bucket study (research/vol_benchmark)."""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research" / "vol_benchmark"))

import vol_benchmark as vb


def _returns(n: int = 900, seed: int = 0) -> pd.Series:
    rng = np.random.default_rng(seed)
    index = pd.bdate_range("2015-01-01", periods=n)
    return pd.Series(rng.normal(0.0, 0.01, n), index=index)


def test_forward_target_is_sum_of_next_h_squared_returns() -> None:
    returns = pd.Series([0.1, 0.2, -0.3, 0.4, 0.5])
    target = vb.forward_sum_squared_returns(returns, 2)
    assert target.iloc[0] == pytest.approx(0.2**2 + 0.3**2)
    assert target.iloc[2] == pytest.approx(0.4**2 + 0.5**2)
    assert math.isnan(target.iloc[3]) and math.isnan(target.iloc[4])


def test_label_forecast_matches_hand_computation() -> None:
    labels = pd.Series(["a", "b", "a", "a", "b", "a"])
    target = pd.Series([1.0, 10.0, 3.0, 5.0, 20.0, 7.0])
    forecast = vb.expanding_label_forecast(labels, target, horizon=1, min_count=2)
    # t=3 (label a): past targets with s <= 2 and label a are y0=1, y2=3 -> mean 2.
    assert forecast.iloc[3] == pytest.approx(2.0)
    # t=2 (label a): only y0 is available for label a (count 1 < 2) -> unconditional mean of y0, y1.
    assert forecast.iloc[2] == pytest.approx(5.5)
    # t=5 (label a): y0, y2, y3 -> mean 3.
    assert forecast.iloc[5] == pytest.approx(3.0)
    assert math.isnan(forecast.iloc[0])


@pytest.mark.parametrize("horizon", [1, 5])
def test_forecasts_do_not_use_the_future(horizon: int) -> None:
    """Changing returns after day t must not change any forecast made at or before t."""
    returns = _returns()
    cut = 600
    altered = returns.copy()
    altered.iloc[cut + 1 :] = altered.iloc[cut + 1 :] * 5.0 + 0.02

    def forecasts(r: pd.Series) -> pd.DataFrame:
        target = vb.forward_sum_squared_returns(r, horizon)
        bucket = vb.causal_volatility_bucket(r)
        return pd.DataFrame(
            {
                "bucket_forecast": vb.expanding_label_forecast(bucket, target, horizon, 20),
                "unconditional": vb.expanding_unconditional_forecast(target, horizon),
                "ewma": vb.ewma_forecast(r, horizon),
            }
        )

    a, b = forecasts(returns), forecasts(altered)
    pd.testing.assert_frame_equal(a.iloc[: cut + 1], b.iloc[: cut + 1])
    labels_a = vb.causal_volatility_bucket(returns).iloc[: cut + 1]
    labels_b = vb.causal_volatility_bucket(altered).iloc[: cut + 1]
    assert labels_a.equals(labels_b)


def test_volatility_bucket_has_four_roughly_equal_groups() -> None:
    bucket = vb.causal_volatility_bucket(_returns(3000, seed=1)).dropna()
    shares = bucket.value_counts(normalize=True)
    assert set(shares.index) == {"VOL_Q1", "VOL_Q2", "VOL_Q3", "VOL_Q4"}
    assert shares.min() > 0.10


def test_informative_labels_beat_unconditional_under_qlike() -> None:
    """With two known variance states, labelled forecasts must score better than no labels."""
    rng = np.random.default_rng(3)
    n = 4000
    state = np.repeat(rng.integers(0, 2, n // 50), 50)
    sigma = np.where(state == 1, 0.03, 0.005)
    index = pd.bdate_range("2010-01-01", periods=n)
    returns = pd.Series(rng.normal(0.0, 1.0, n) * sigma, index=index)
    # The label at t describes the state of day t+1, so it is informative about the target.
    labels = pd.Series(np.roll(state, -1), index=index).map({0: "LOW", 1: "HIGH"})
    target = vb.forward_sum_squared_returns(returns, 1)
    labelled = vb.qlike(vb.expanding_label_forecast(labels, target, 1, 20), target)
    plain = vb.qlike(vb.expanding_unconditional_forecast(target, 1), target)
    diff = (labelled - plain).iloc[504:]
    result = vb.diebold_mariano(diff, 1)
    assert result.mean_diff < 0
    assert result.p_value < 0.001


def test_diebold_mariano_on_white_noise_matches_t_statistic() -> None:
    rng = np.random.default_rng(7)
    d = pd.Series(rng.normal(0.2, 1.0, 2000))
    result = vb.diebold_mariano(d, 1)
    assert result.n == 2000
    assert result.lag == vb.newey_west_lag(2000, 1) == 7
    naive = d.mean() / (d.std(ddof=0) / math.sqrt(len(d)))
    assert result.stat == pytest.approx(naive, rel=0.15)
    assert 0.0 < result.p_value < 0.001


def test_diebold_mariano_rejects_at_nominal_rate_under_the_null() -> None:
    rng = np.random.default_rng(11)
    rejections = sum(
        vb.diebold_mariano(pd.Series(rng.normal(0.0, 1.0, 500)), 1).p_value < 0.05
        for _ in range(400)
    )
    assert 0.02 < rejections / 400 < 0.10


def test_diebold_mariano_needs_enough_observations() -> None:
    result = vb.diebold_mariano(pd.Series([0.1] * 10), 1)
    assert math.isnan(result.p_value)


def test_holm_adjustment() -> None:
    adjusted = vb.holm_adjust([0.01, 0.04, 0.03, float("nan")])
    assert adjusted[0] == pytest.approx(0.03)
    assert adjusted[2] == pytest.approx(0.06)
    assert adjusted[1] == pytest.approx(0.06)
    assert math.isnan(adjusted[3])


def test_qlike_is_minimised_at_the_true_variance() -> None:
    rng = np.random.default_rng(5)
    true_variance = 4e-4
    target = pd.Series(rng.normal(0.0, math.sqrt(true_variance), 20000) ** 2)
    scores = {
        f: float(vb.qlike(pd.Series(f, index=target.index), target).mean())
        for f in (true_variance / 2, true_variance, true_variance * 2)
    }
    assert scores[true_variance] == min(scores.values())
