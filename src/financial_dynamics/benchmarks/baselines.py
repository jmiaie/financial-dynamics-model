"""Simple baseline regime classifiers for comparison against the full pipeline."""

from __future__ import annotations

from typing import Protocol

import numpy as np
import pandas as pd

from financial_dynamics.types import Regime


class BaselineClassifier(Protocol):
    """Common interface: takes OHLCV, returns regime name per bar."""

    name: str

    def classify(self, df: pd.DataFrame) -> pd.Series: ...


class VolatilityBucketClassifier:
    """Classify by realized volatility quartile.

    Lowest quartile -> CALM_TREND, mid -> CHOP, upper-mid -> VOLATILE_TREND,
    top quartile -> RISK_OFF. Trend direction is ignored.
    """

    name = "volatility_bucket"

    def __init__(self, window: int = 20):
        self.window = window

    def classify(self, df: pd.DataFrame) -> pd.Series:
        returns = df["close"].pct_change()
        vol = returns.rolling(self.window).std()

        quartiles = vol.quantile([0.25, 0.5, 0.75])
        q1, q2, q3 = quartiles.iloc[0], quartiles.iloc[1], quartiles.iloc[2]

        labels = pd.Series(index=df.index, dtype=object)
        labels[vol <= q1] = Regime.CALM_TREND.name
        labels[(vol > q1) & (vol <= q2)] = Regime.CHOP.name
        labels[(vol > q2) & (vol <= q3)] = Regime.VOLATILE_TREND.name
        labels[vol > q3] = Regime.RISK_OFF.name
        return labels


class TrendVolGridClassifier:
    """Classify on a 2x2 grid of (trend sign, vol level).

    +trend / low vol  -> CALM_TREND
    +trend / high vol -> VOLATILE_TREND
    -trend / low vol  -> CHOP
    -trend / high vol -> RISK_OFF
    """

    name = "trend_vol_grid"

    def __init__(self, vol_window: int = 20, trend_window: int = 14):
        self.vol_window = vol_window
        self.trend_window = trend_window

    def classify(self, df: pd.DataFrame) -> pd.Series:
        close = df["close"]
        returns = close.pct_change()
        vol = returns.rolling(self.vol_window).std()
        trend = close.pct_change(self.trend_window)

        vol_median = vol.median()

        labels = pd.Series(index=df.index, dtype=object)
        pos_trend = trend > 0
        high_vol = vol > vol_median

        labels[pos_trend & ~high_vol] = Regime.CALM_TREND.name
        labels[pos_trend & high_vol] = Regime.VOLATILE_TREND.name
        labels[~pos_trend & ~high_vol] = Regime.CHOP.name
        labels[~pos_trend & high_vol] = Regime.RISK_OFF.name
        return labels


class GaussianMixtureClassifier:
    """4-component Gaussian Mixture over (return, |return|, rolling vol).

    Cluster -> regime mapping is fit greedily by sorting components on
    mean volatility and assigning CALM_TREND -> CHOP -> VOLATILE_TREND -> RISK_OFF
    in increasing-vol order.
    """

    name = "gaussian_mixture"

    def __init__(self, vol_window: int = 20, random_state: int = 0):
        self.vol_window = vol_window
        self.random_state = random_state

    def classify(self, df: pd.DataFrame) -> pd.Series:
        from sklearn.mixture import GaussianMixture

        close = df["close"]
        returns = close.pct_change()
        vol = returns.rolling(self.vol_window).std()

        features = pd.DataFrame(
            {
                "return": returns,
                "abs_return": returns.abs(),
                "vol": vol,
            }
        )
        valid = features.dropna()

        gmm = GaussianMixture(
            n_components=4,
            covariance_type="full",
            random_state=self.random_state,
        )
        clusters = gmm.fit_predict(valid.values)

        vol_per_component = gmm.means_[:, 2]
        order = np.argsort(vol_per_component)
        cluster_to_regime = {
            int(order[0]): Regime.CALM_TREND.name,
            int(order[1]): Regime.CHOP.name,
            int(order[2]): Regime.VOLATILE_TREND.name,
            int(order[3]): Regime.RISK_OFF.name,
        }

        labels = pd.Series(index=df.index, dtype=object)
        labels.loc[valid.index] = [cluster_to_regime[int(c)] for c in clusters]
        return labels
