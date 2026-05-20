"""Centroid fitting from labeled training data."""

from __future__ import annotations

import pandas as pd

from financial_dynamics.config import PipelineConfig
from financial_dynamics.pipeline import FinancialDynamicsPipeline
from financial_dynamics.types import Regime

FEATURE_COLUMNS = [
    "feat_volatility",
    "feat_trend",
    "feat_drawdown",
    "feat_corr_stress",
    "feat_shock",
]


def fit_centroids(
    features: pd.DataFrame,
    labels: pd.Series,
) -> dict[str, list[float]]:
    """Compute data-driven centroids by averaging features per labeled regime.

    Args:
        features: DataFrame with the 5 normalized feature columns
                  (feat_volatility, feat_trend, feat_drawdown,
                  feat_corr_stress, feat_shock).
        labels: Series of regime name strings aligned with features.

    Returns:
        Dict mapping regime name -> centroid vector (list of 5 floats),
        suitable for assignment to RegimeConfig.centroids.

    Regimes with zero observations in the training data fall back to
    the column-wise mean across all bars.
    """
    missing = set(FEATURE_COLUMNS) - set(features.columns)
    if missing:
        raise ValueError(f"features DataFrame missing required columns: {sorted(missing)}")

    valid = features[FEATURE_COLUMNS].dropna()
    aligned_labels = labels.loc[valid.index]

    fallback = valid.mean().values

    centroids: dict[str, list[float]] = {}
    for regime in Regime:
        mask = aligned_labels == regime.name
        if mask.sum() == 0:
            centroids[regime.name] = fallback.tolist()
        else:
            centroids[regime.name] = valid[mask].mean().values.tolist()

    return centroids


def fit_centroids_from_pipeline(
    df: pd.DataFrame,
    labels: pd.Series,
    config: PipelineConfig | None = None,
) -> dict[str, list[float]]:
    """Run the pipeline on training data, then fit centroids from the
    normalized features it produces.

    The existing centroid configuration is used only to extract features;
    the returned centroids replace those.
    """
    pipeline = FinancialDynamicsPipeline(config)
    results = pipeline.run(df)
    return fit_centroids(results, labels)
