"""Regime classification and historical-characterization metrics."""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import pairwise
from typing import cast

import numpy as np
import pandas as pd

from financial_dynamics.types import NUM_REGIMES, Regime

PROBABILITY_COLUMNS = [f"post_prob_{regime.name}" for regime in Regime]


@dataclass
class HistoricalRegimeStatistics:
    """Historical characterization statistics for inferred regimes."""

    summary: pd.DataFrame
    transitions: pd.DataFrame
    # Raw per-occurrence rows (regime, horizon, forward_return, ...) behind
    # `summary`'s per-(regime, horizon) aggregates -- kept in chronological
    # order so callers can bootstrap the mean respecting the original time
    # ordering (see regime_bootstrap_uncertainty). Empty when summary is.
    forward_occurrences: pd.DataFrame = field(default_factory=pd.DataFrame)


def regime_accuracy(
    true_labels: pd.Series,
    predicted_labels: pd.Series,
) -> float:
    """Overall accuracy: fraction of bars where predicted == true.

    Both Series should contain Regime name strings (e.g. "CALM_TREND").
    NaN predictions (warmup) are excluded from the calculation.
    """
    mask = predicted_labels.notna()
    if mask.sum() == 0:
        return 0.0
    return float((true_labels[mask] == predicted_labels[mask]).mean())


def regime_confusion_matrix(
    true_labels: pd.Series,
    predicted_labels: pd.Series,
) -> pd.DataFrame:
    """Build a 4x4 confusion matrix as a labeled DataFrame.

    Rows = true regime, columns = predicted regime.
    NaN predictions are excluded.
    """
    regime_names = [r.name for r in Regime]
    mask = predicted_labels.notna()
    t = true_labels[mask]
    p = predicted_labels[mask]

    matrix = np.zeros((NUM_REGIMES, NUM_REGIMES), dtype=int)
    name_to_idx = {r.name: int(r) for r in Regime}

    for true_val, pred_val in zip(t, p, strict=False):
        ti = name_to_idx.get(true_val)
        pi = name_to_idx.get(pred_val)
        if ti is not None and pi is not None:
            matrix[ti, pi] += 1

    return pd.DataFrame(matrix, index=regime_names, columns=regime_names)


def regime_balanced_accuracy(
    true_labels: pd.Series,
    predicted_labels: pd.Series,
) -> float:
    """Balanced accuracy across regimes observed in true_labels."""
    cm = regime_confusion_matrix(true_labels, predicted_labels)
    matrix = cm.to_numpy()
    support = matrix.sum(axis=1)
    valid = support > 0
    if not valid.any():
        return 0.0
    recalls = np.divide(
        np.diag(matrix),
        support,
        out=np.zeros_like(support, dtype=float),
        where=valid,
    )
    return float(recalls[valid].mean())


def regime_classification_report(
    true_labels: pd.Series,
    predicted_labels: pd.Series,
) -> pd.DataFrame:
    """Per-regime precision, recall, F1, and support.

    Returns a DataFrame with one row per regime plus a 'weighted_avg' row.
    """
    cm = regime_confusion_matrix(true_labels, predicted_labels)
    matrix = cm.values

    rows: list[dict[str, str | float | int]] = []
    total_support = matrix.sum()
    weighted_p, weighted_r, weighted_f1 = 0.0, 0.0, 0.0

    for i, regime in enumerate(Regime):
        tp = matrix[i, i]
        fp = matrix[:, i].sum() - tp
        fn = matrix[i, :].sum() - tp
        support = matrix[i, :].sum()

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

        rows.append(
            {
                "regime": regime.name,
                "precision": precision,
                "recall": recall,
                "f1": f1,
                "support": int(support),
            }
        )

        weight = support / total_support if total_support > 0 else 0.0
        weighted_p += precision * weight
        weighted_r += recall * weight
        weighted_f1 += f1 * weight

    rows.append(
        {
            "regime": "weighted_avg",
            "precision": weighted_p,
            "recall": weighted_r,
            "f1": weighted_f1,
            "support": int(total_support),
        }
    )

    return pd.DataFrame(rows).set_index("regime")


def regime_macro_f1(
    true_labels: pd.Series,
    predicted_labels: pd.Series,
) -> float:
    """Macro-averaged F1 across regimes observed in true_labels."""
    report = regime_classification_report(true_labels, predicted_labels)
    supports = report.loc[[regime.name for regime in Regime], "support"]
    valid_regimes = supports[supports > 0].index
    if len(valid_regimes) == 0:
        return 0.0
    return float(report.loc[valid_regimes, "f1"].mean())


def validate_probability_frame(
    probabilities: pd.DataFrame,
    *,
    tolerance: float = 1e-6,
) -> pd.DataFrame:
    """Validate regime probability columns and return non-null rows."""
    missing = set(PROBABILITY_COLUMNS) - set(probabilities.columns)
    if missing:
        raise ValueError(f"Missing probability columns: {sorted(missing)}")

    valid = probabilities[PROBABILITY_COLUMNS].dropna()
    if valid.empty:
        return valid

    values = valid.to_numpy(dtype=float)
    if np.any(values < -tolerance) or np.any(values > 1.0 + tolerance):
        raise ValueError("Probability values must be between 0 and 1")

    row_sums = values.sum(axis=1)
    if not np.allclose(row_sums, np.ones(len(valid)), atol=tolerance):
        raise ValueError("Probability rows must sum to 1 within tolerance")

    return valid


def regime_log_loss(
    true_labels: pd.Series,
    probabilities: pd.DataFrame,
) -> float | None:
    """Multiclass log loss for valid probability rows."""
    valid_probs = validate_probability_frame(probabilities)
    if valid_probs.empty:
        return None

    aligned_true = true_labels.loc[valid_probs.index]
    name_to_idx = {regime.name: int(regime) for regime in Regime}
    true_indices = aligned_true.map(name_to_idx)
    if true_indices.isna().any():
        raise ValueError("true_labels contains unknown regime names")

    prob_array = valid_probs.to_numpy(dtype=float)
    chosen = prob_array[np.arange(len(valid_probs)), true_indices.astype(int).to_numpy()]
    return float(-np.log(np.clip(chosen, 1e-12, 1.0)).mean())


def regime_multiclass_brier_score(
    true_labels: pd.Series,
    probabilities: pd.DataFrame,
) -> float | None:
    """Multiclass Brier score for valid probability rows."""
    valid_probs = validate_probability_frame(probabilities)
    if valid_probs.empty:
        return None

    aligned_true = true_labels.loc[valid_probs.index]
    name_to_idx = {regime.name: int(regime) for regime in Regime}
    true_indices = aligned_true.map(name_to_idx)
    if true_indices.isna().any():
        raise ValueError("true_labels contains unknown regime names")

    one_hot = np.zeros((len(valid_probs), NUM_REGIMES), dtype=float)
    one_hot[np.arange(len(valid_probs)), true_indices.astype(int).to_numpy()] = 1.0
    diff = valid_probs.to_numpy(dtype=float) - one_hot
    return float(np.mean(np.sum(diff * diff, axis=1)))


def regime_calibration_table(
    true_labels: pd.Series,
    probabilities: pd.DataFrame,
    *,
    bins: int = 10,
) -> pd.DataFrame:
    """Per-regime calibration diagnostics across probability bins."""
    valid_probs = validate_probability_frame(probabilities)
    if valid_probs.empty:
        return pd.DataFrame(
            columns=["regime", "bin_left", "bin_right", "mean_predicted", "observed_freq", "count"]
        )

    aligned_true = true_labels.loc[valid_probs.index]
    edges = np.linspace(0.0, 1.0, bins + 1)
    rows: list[dict[str, str | float | int]] = []

    for regime in Regime:
        regime_name = regime.name
        regime_probs = valid_probs[f"post_prob_{regime_name}"]
        observed = (aligned_true == regime_name).astype(float)

        for left, right in pairwise(edges):
            if right == 1.0:
                mask = (regime_probs >= left) & (regime_probs <= right)
            else:
                mask = (regime_probs >= left) & (regime_probs < right)

            bucket = regime_probs[mask]
            if bucket.empty:
                continue

            rows.append(
                {
                    "regime": regime_name,
                    "bin_left": float(left),
                    "bin_right": float(right),
                    "mean_predicted": float(bucket.mean()),
                    "observed_freq": float(observed.loc[bucket.index].mean()),
                    "count": len(bucket),
                }
            )

    return pd.DataFrame(rows)


def historical_regime_statistics(
    close: pd.Series,
    inferred_regimes: pd.Series,
    *,
    horizons: tuple[int, ...] = (1, 5, 20),
) -> HistoricalRegimeStatistics:
    """Characterize inferred historical regimes without fabricating labels."""
    if not close.index.equals(inferred_regimes.index):
        raise ValueError("close and inferred_regimes must share the same index")

    valid_regimes = inferred_regimes.dropna()
    if valid_regimes.empty:
        empty = pd.DataFrame()
        return HistoricalRegimeStatistics(summary=empty, transitions=empty)

    daily_returns = close.pct_change()
    duration_rows: list[dict[str, str | float | int]] = []
    previous_regime: str | None = None
    run_length = 0

    for regime_name in valid_regimes:
        if regime_name == previous_regime:
            run_length += 1
        else:
            if previous_regime is not None:
                duration_rows.append({"regime": previous_regime, "duration": run_length})
            previous_regime = str(regime_name)
            run_length = 1
    if previous_regime is not None:
        duration_rows.append({"regime": previous_regime, "duration": run_length})

    duration_df = pd.DataFrame(duration_rows)

    # Use distinct names / numpy values: identically named Series confuse crosstab.
    transition_counts = pd.crosstab(
        valid_regimes.iloc[:-1].to_numpy(),
        valid_regimes.iloc[1:].to_numpy(),
        rownames=["from_regime"],
        colnames=["to_regime"],
        dropna=False,
    ).reindex(
        index=[regime.name for regime in Regime],
        columns=[regime.name for regime in Regime],
        fill_value=0,
    )

    transition_rates = transition_counts.div(
        transition_counts.sum(axis=1).replace(0, np.nan), axis=0
    ).fillna(0.0)

    rows: list[dict[str, str | float | int]] = []
    for horizon in horizons:
        for start in range(len(close) - horizon):
            regime_name = inferred_regimes.iloc[start]
            if pd.isna(regime_name):
                continue

            current_price = float(close.iloc[start])
            future_price = float(close.iloc[start + horizon])
            future_daily_returns = daily_returns.iloc[start + 1 : start + horizon + 1].dropna()
            if future_daily_returns.empty:
                continue

            downside = future_daily_returns[future_daily_returns < 0]
            window_prices = close.iloc[start : start + horizon + 1]
            running_peak = window_prices.cummax()
            adverse_drawdown = float((window_prices / running_peak - 1.0).min())
            rows.append(
                {
                    "regime": str(regime_name),
                    "horizon": horizon,
                    "forward_return": future_price / current_price - 1.0,
                    "realized_vol": float(future_daily_returns.std(ddof=0)),
                    "downside_vol": float(downside.std(ddof=0)) if len(downside) > 0 else 0.0,
                    # Worst peak-to-trough decline within [start, start+horizon],
                    # not just the start-to-end forward_return -- a horizon can
                    # end flat or up while still passing through a sharp dip.
                    "adverse_drawdown": adverse_drawdown,
                }
            )

    forward_df = pd.DataFrame(rows)
    if forward_df.empty:
        empty = pd.DataFrame()
        return HistoricalRegimeStatistics(summary=empty, transitions=transition_rates)

    grouped = forward_df.groupby(["regime", "horizon"], sort=False)
    summary = grouped.agg(
        count=("forward_return", "size"),
        mean_return=("forward_return", "mean"),
        median_return=("forward_return", "median"),
        realized_vol=("realized_vol", "mean"),
        downside_vol=("downside_vol", "mean"),
        # Fraction of OCCURRENCES whose horizon-level (compounded) forward
        # return was positive -- not the fraction of individual days inside
        # each window that were positive (a materially different, and
        # previously miscomputed, statistic; see
        # TestHistoricalRegimeStatistics.test_positive_return_freq_is_horizon_level_not_daily_level).
        positive_return_freq=("forward_return", lambda values: float((values > 0).mean())),
        tail_q05=("forward_return", lambda values: float(np.quantile(values, 0.05))),
        tail_q25=("forward_return", lambda values: float(np.quantile(values, 0.25))),
        mean_adverse_drawdown=("adverse_drawdown", "mean"),
        worst_adverse_drawdown=("adverse_drawdown", "min"),
    ).reset_index()

    duration_summary = (
        duration_df.groupby("regime")
        .agg(mean_duration=("duration", "mean"), median_duration=("duration", "median"))
        .reset_index()
    )
    transition_series = cast(pd.Series, transition_rates.stack())
    transition_series.name = "transition_rate"
    self_transition = (
        transition_series.reset_index()
        .query("from_regime == to_regime")
        .rename(columns={"from_regime": "regime"})[["regime", "transition_rate"]]
    )

    summary = summary.merge(duration_summary, on="regime", how="left")
    summary = summary.merge(self_transition, on="regime", how="left")
    return HistoricalRegimeStatistics(
        summary=summary, transitions=transition_rates, forward_occurrences=forward_df
    )


def _moving_block_bootstrap_mean(
    values: np.ndarray, block_size: int, rng: np.random.Generator
) -> float:
    """One resample: concatenate contiguous blocks of `block_size` consecutive
    observations (wrapping around the end), sampled with replacement, until
    reaching the original length, then take the mean. Preserves local
    serial dependence within a block; does not assume i.i.d. observations."""
    n = len(values)
    n_blocks = -(-n // block_size)  # ceil division
    starts = rng.integers(0, n, size=n_blocks)
    resampled = np.concatenate([values.take(range(s, s + block_size), mode="wrap") for s in starts])
    return float(resampled[:n].mean())


def _stationary_bootstrap_mean(
    values: np.ndarray, expected_block_size: int, rng: np.random.Generator
) -> float:
    """One resample via Politis-Romano (1994) stationary bootstrap: block
    length is geometrically distributed (memoryless restart probability
    1/expected_block_size at each step) rather than fixed, which keeps the
    resampled series itself stationary. Same intent as the moving-block
    variant -- respect serial dependence -- without picking one fixed block
    length."""
    n = len(values)
    restart_prob = 1.0 / expected_block_size
    idx = np.empty(n, dtype=int)
    idx[0] = rng.integers(0, n)
    restarts = rng.random(n) < restart_prob
    fresh_starts = rng.integers(0, n, size=n)
    for i in range(1, n):
        idx[i] = fresh_starts[i] if restarts[i] else (idx[i - 1] + 1) % n
    return float(values[idx].mean())


def block_bootstrap_mean_ci(
    values: pd.Series,
    *,
    method: str = "moving_block",
    block_size: int = 20,
    n_bootstrap: int = 1000,
    confidence: float = 0.90,
    seed: int = 0,
) -> dict[str, float | int | str | None]:
    """Block-bootstrap confidence interval for a chronologically-ordered
    series' mean (e.g. one regime's forward returns at one horizon, in the
    order they occurred). Regime-conditional forward returns are serially
    dependent -- overlapping horizons, regime persistence -- so an ordinary
    i.i.d. bootstrap would understate uncertainty; block resampling (either
    `method="moving_block"` with a fixed block length, or
    `method="stationary"` with a geometrically-distributed one) keeps
    contiguous runs intact.

    This characterizes SAMPLING uncertainty in the observed mean given the
    observed serial-dependence structure. It is not an out-of-sample test
    and does not validate the regime definitions themselves; a narrow CI
    here means the mean is stable across resamples of this same historical
    sample, not that it will hold out of sample."""
    arr = values.to_numpy(dtype=float)
    n = len(arr)
    if n < 2:
        return {
            "n": n,
            "method": method,
            "block_size": min(block_size, max(n, 1)),
            "n_bootstrap": n_bootstrap,
            "confidence": confidence,
            "mean": float(arr[0]) if n == 1 else None,
            "ci_low": None,
            "ci_high": None,
            "insufficient_data": True,
        }
    effective_block = max(1, min(block_size, n))
    rng = np.random.default_rng(seed)
    resample_fn = (
        _stationary_bootstrap_mean if method == "stationary" else _moving_block_bootstrap_mean
    )
    boot_means = np.array([resample_fn(arr, effective_block, rng) for _ in range(n_bootstrap)])
    alpha = 1.0 - confidence
    ci_low, ci_high = np.quantile(boot_means, [alpha / 2, 1.0 - alpha / 2])
    return {
        "n": n,
        "method": method,
        "block_size": effective_block,
        "n_bootstrap": n_bootstrap,
        "confidence": confidence,
        "mean": float(arr.mean()),
        "ci_low": float(ci_low),
        "ci_high": float(ci_high),
        "insufficient_data": False,
    }


def regime_bootstrap_uncertainty(
    forward_occurrences: pd.DataFrame,
    *,
    methods: tuple[str, ...] = ("moving_block", "stationary"),
    block_size: int = 20,
    n_bootstrap: int = 1000,
    confidence: float = 0.90,
    seed: int = 0,
) -> pd.DataFrame:
    """Block-bootstrap CIs on mean forward_return for every (regime, horizon)
    group in `forward_occurrences` (HistoricalRegimeStatistics.forward_occurrences),
    for each requested method. One row per (regime, horizon, method)."""
    if forward_occurrences.empty:
        return pd.DataFrame()
    rows: list[dict[str, float | int | str | None]] = []
    for (regime, horizon), group in forward_occurrences.groupby(["regime", "horizon"], sort=False):
        for method in methods:
            result = block_bootstrap_mean_ci(
                group["forward_return"],
                method=method,
                block_size=block_size,
                n_bootstrap=n_bootstrap,
                confidence=confidence,
                seed=seed,
            )
            rows.append({"regime": str(regime), "horizon": int(cast(int, horizon)), **result})
    return pd.DataFrame(rows)
