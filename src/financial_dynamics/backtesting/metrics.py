"""Regime classification and historical-characterization metrics."""

from __future__ import annotations

from dataclasses import dataclass
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

    transition_counts = pd.crosstab(
        valid_regimes.iloc[:-1],
        valid_regimes.iloc[1:],
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
            rows.append(
                {
                    "regime": str(regime_name),
                    "horizon": horizon,
                    "forward_return": future_price / current_price - 1.0,
                    "realized_vol": float(future_daily_returns.std(ddof=0)),
                    "downside_vol": float(downside.std(ddof=0)) if len(downside) > 0 else 0.0,
                    "positive_return_freq": float((future_daily_returns > 0).mean()),
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
        positive_return_freq=("positive_return_freq", "mean"),
        tail_q05=("forward_return", lambda values: float(np.quantile(values, 0.05))),
        tail_q25=("forward_return", lambda values: float(np.quantile(values, 0.25))),
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
    return HistoricalRegimeStatistics(summary=summary, transitions=transition_rates)
