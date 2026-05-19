"""Regime classification metrics."""

from __future__ import annotations

import numpy as np
import pandas as pd

from financial_dynamics.types import NUM_REGIMES, Regime


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
        f1 = (2 * precision * recall / (precision + recall)
              if (precision + recall) > 0 else 0.0)

        rows.append({
            "regime": regime.name,
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "support": int(support),
        })

        weight = support / total_support if total_support > 0 else 0.0
        weighted_p += precision * weight
        weighted_r += recall * weight
        weighted_f1 += f1 * weight

    rows.append({
        "regime": "weighted_avg",
        "precision": weighted_p,
        "recall": weighted_r,
        "f1": weighted_f1,
        "support": int(total_support),
    })

    return pd.DataFrame(rows).set_index("regime")
