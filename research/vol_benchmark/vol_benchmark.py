"""Regime labels versus a trailing-volatility bucket as forward-variance forecasters.

Frozen design: research/vol_benchmark/PROTOCOL.md. This module holds the forecasting
and scoring functions; run_vol_benchmark.py applies them to the frozen dataset.

Everything here is causal: a forecast for the variance after day t uses only
information available at the close of day t.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import pandas as pd

VARIANCE_FLOOR = 1e-10


def forward_sum_squared_returns(returns: pd.Series, horizon: int) -> pd.Series:
    """Target y_t = sum of squared returns over days t+1 .. t+horizon (NaN near the end)."""
    squared = returns.to_numpy(dtype=float) ** 2
    n = len(squared)
    out = np.full(n, np.nan)
    cumulative = np.concatenate([[0.0], np.nancumsum(squared)])
    for t in range(n - horizon):
        window = squared[t + 1 : t + 1 + horizon]
        if np.isnan(window).any():
            continue
        out[t] = cumulative[t + 1 + horizon] - cumulative[t + 1]
    return pd.Series(out, index=returns.index)


def expanding_unconditional_forecast(target: pd.Series, horizon: int) -> pd.Series:
    """Mean of all targets already observable at t (those dated t - horizon or earlier)."""
    y = target.to_numpy(dtype=float)
    n = len(y)
    out = np.full(n, np.nan)
    total, count = 0.0, 0
    for t in range(n):
        s = t - horizon
        if s >= 0 and not np.isnan(y[s]):
            total += y[s]
            count += 1
        if count:
            out[t] = total / count
    return pd.Series(out, index=target.index)


def expanding_label_forecast(
    labels: pd.Series, target: pd.Series, horizon: int, min_count: int
) -> pd.Series:
    """Per-label expanding mean of the target, falling back to the unconditional mean.

    The forecast at t for label k is the mean of y_s over s <= t - horizon with
    label_s == k, provided at least ``min_count`` such days exist; otherwise the
    unconditional expanding mean. Days with a missing label get NaN.
    """
    y = target.to_numpy(dtype=float)
    lab = labels.to_numpy(dtype=object)
    n = len(y)
    out = np.full(n, np.nan)
    sums: dict[object, float] = {}
    counts: dict[object, int] = {}
    total, count = 0.0, 0
    for t in range(n):
        s = t - horizon
        if s >= 0 and not np.isnan(y[s]):
            total += y[s]
            count += 1
            key = lab[s]
            if not _is_missing(key):
                sums[key] = sums.get(key, 0.0) + y[s]
                counts[key] = counts.get(key, 0) + 1
        key_t = lab[t]
        if _is_missing(key_t) or not count:
            continue
        if counts.get(key_t, 0) >= min_count:
            out[t] = sums[key_t] / counts[key_t]
        else:
            out[t] = total / count
    return pd.Series(out, index=target.index)


def _is_missing(value: object) -> bool:
    return value is None or (isinstance(value, float) and math.isnan(value))


def causal_volatility_bucket(
    returns: pd.Series, window: int = 20, min_history: int = 252
) -> pd.Series:
    """Quartile bucket (0-3) of trailing realised volatility, with expanding thresholds.

    vol_t is the standard deviation of the last ``window`` returns up to t. The bucket
    at t compares vol_t with the quartiles of vol_s for s <= t - 1, so the thresholds
    never see the day being classified or anything after it.
    """
    vol = returns.rolling(window).std().to_numpy(dtype=float)
    n = len(vol)
    out = np.full(n, np.nan, dtype=object)
    history: list[float] = []
    for t in range(n):
        if not np.isnan(vol[t]) and len(history) >= min_history:
            q1, q2, q3 = np.quantile(np.asarray(history), [0.25, 0.5, 0.75])
            if vol[t] <= q1:
                out[t] = "VOL_Q1"
            elif vol[t] <= q2:
                out[t] = "VOL_Q2"
            elif vol[t] <= q3:
                out[t] = "VOL_Q3"
            else:
                out[t] = "VOL_Q4"
        if not np.isnan(vol[t]):
            history.append(float(vol[t]))
    return pd.Series(out, index=returns.index)


def ewma_forecast(
    returns: pd.Series, horizon: int, decay: float = 0.94, seed_window: int = 20
) -> pd.Series:
    """RiskMetrics EWMA variance at t, scaled to the horizon. Reference only."""
    r = returns.to_numpy(dtype=float)
    n = len(r)
    out = np.full(n, np.nan)
    valid = [i for i in range(n) if not np.isnan(r[i])]
    if len(valid) < seed_window:
        return pd.Series(out, index=returns.index)
    seed_idx = valid[:seed_window]
    variance = float(np.mean(r[seed_idx] ** 2))
    start = seed_idx[-1]
    out[start] = variance * horizon
    for t in range(start + 1, n):
        if not np.isnan(r[t]):
            variance = decay * variance + (1.0 - decay) * r[t] ** 2
        out[t] = variance * horizon
    return pd.Series(out, index=returns.index)


def qlike(forecast: pd.Series, target: pd.Series) -> pd.Series:
    """QLIKE loss y / f + ln f (Patton 2011); lower is better."""
    f = forecast.clip(lower=VARIANCE_FLOOR)
    return target / f + np.log(f)


@dataclass(frozen=True)
class DMResult:
    n: int
    mean_diff: float
    se: float
    stat: float
    p_value: float
    lag: int


def newey_west_lag(n: int, horizon: int) -> int:
    """Bartlett lag: the larger of horizon - 1 and floor(4 (n / 100)^(2/9))."""
    return max(horizon - 1, math.floor(4.0 * (n / 100.0) ** (2.0 / 9.0)))


def diebold_mariano(diff: pd.Series, horizon: int) -> DMResult:
    """Two-sided Diebold-Mariano test on a loss differential with a Newey-West variance."""
    d = diff.dropna().to_numpy(dtype=float)
    n = len(d)
    if n < 30:
        return DMResult(n, float("nan"), float("nan"), float("nan"), float("nan"), 0)
    lag = newey_west_lag(n, horizon)
    mean = float(d.mean())
    centred = d - mean
    variance = float(np.dot(centred, centred) / n)
    for k in range(1, lag + 1):
        gamma = float(np.dot(centred[k:], centred[:-k]) / n)
        variance += 2.0 * (1.0 - k / (lag + 1.0)) * gamma
    if variance <= 0:
        return DMResult(n, mean, float("nan"), float("nan"), float("nan"), lag)
    se = math.sqrt(variance / n)
    stat = mean / se
    p_value = math.erfc(abs(stat) / math.sqrt(2.0))
    return DMResult(n, mean, se, stat, p_value, lag)


def holm_adjust(p_values: list[float]) -> list[float]:
    """Holm step-down adjusted p-values, in the input order (NaN stays NaN)."""
    indexed = [(p, i) for i, p in enumerate(p_values) if not math.isnan(p)]
    indexed.sort()
    m = len(indexed)
    adjusted = [float("nan")] * len(p_values)
    running = 0.0
    for rank, (p, i) in enumerate(indexed):
        running = max(running, min(1.0, (m - rank) * p))
        adjusted[i] = running
    return adjusted
