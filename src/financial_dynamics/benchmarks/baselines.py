"""Simple baseline regime classifiers for comparison against the full pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

import numpy as np
import pandas as pd

from financial_dynamics.types import Regime

if TYPE_CHECKING:
    from sklearn.mixture import GaussianMixture


class BaselineClassifier(Protocol):
    """Common interface for benchmarks that can be fit on prior data only."""

    name: str
    lookback_bars: int

    def fit(
        self,
        df: pd.DataFrame,
        labels: pd.Series | None = None,
    ) -> BaselineClassifier: ...

    def predict(
        self,
        df: pd.DataFrame,
        *,
        history_df: pd.DataFrame | None = None,
    ) -> pd.Series: ...

    def classify(self, df: pd.DataFrame) -> pd.Series: ...


@dataclass
class PersistenceClassifier:
    """Persist the last observed training regime through the evaluation window."""

    name: str = "persistence"
    lookback_bars: int = 0
    last_label: str | None = None

    def fit(
        self,
        df: pd.DataFrame,
        labels: pd.Series | None = None,
    ) -> PersistenceClassifier:
        if labels is None or labels.dropna().empty:
            raise ValueError("PersistenceClassifier requires non-empty training labels")
        self.last_label = str(labels.dropna().iloc[-1])
        return self

    def predict(
        self,
        df: pd.DataFrame,
        *,
        history_df: pd.DataFrame | None = None,
    ) -> pd.Series:
        if self.last_label is None:
            raise ValueError("PersistenceClassifier must be fit before predict")
        return pd.Series(self.last_label, index=df.index, dtype=object)

    def classify(self, df: pd.DataFrame) -> pd.Series:
        if self.last_label is None:
            return pd.Series(index=df.index, dtype=object)
        return self.predict(df)


class VolatilityBucketClassifier:
    """Classify by train-fit realized-volatility buckets."""

    name = "volatility_bucket"

    def __init__(self, window: int = 20):
        self.window = window
        self.lookback_bars = window + 1
        self._thresholds: tuple[float, float, float] | None = None

    def fit(
        self,
        df: pd.DataFrame,
        labels: pd.Series | None = None,
    ) -> VolatilityBucketClassifier:
        returns = df["close"].pct_change()
        vol = returns.rolling(self.window).std().dropna()
        if vol.empty:
            raise ValueError("Not enough training data to fit volatility buckets")
        quartiles = vol.quantile([0.25, 0.5, 0.75])
        self._thresholds = (
            float(quartiles.iloc[0]),
            float(quartiles.iloc[1]),
            float(quartiles.iloc[2]),
        )
        return self

    def predict(
        self,
        df: pd.DataFrame,
        *,
        history_df: pd.DataFrame | None = None,
    ) -> pd.Series:
        if self._thresholds is None:
            raise ValueError("VolatilityBucketClassifier must be fit before predict")
        q1, q2, q3 = self._thresholds
        vol = (
            _contextual_series(df, history_df, self.lookback_bars)["close"]
            .pct_change()
            .rolling(self.window)
            .std()
        )
        vol = vol.iloc[-len(df) :]

        labels = pd.Series(index=df.index, dtype=object)
        labels[vol <= q1] = Regime.CALM_TREND.name
        labels[(vol > q1) & (vol <= q2)] = Regime.CHOP.name
        labels[(vol > q2) & (vol <= q3)] = Regime.VOLATILE_TREND.name
        labels[vol > q3] = Regime.RISK_OFF.name
        return labels

    def classify(self, df: pd.DataFrame) -> pd.Series:
        return self.fit(df).predict(df)


class TrendVolGridClassifier:
    """Classify on a 2x2 grid of train-fit volatility and observed trend sign."""

    name = "trend_vol_grid"

    def __init__(self, vol_window: int = 20, trend_window: int = 14):
        self.vol_window = vol_window
        self.trend_window = trend_window
        self.lookback_bars = max(vol_window, trend_window) + 1
        self._vol_median: float | None = None

    def fit(
        self,
        df: pd.DataFrame,
        labels: pd.Series | None = None,
    ) -> TrendVolGridClassifier:
        returns = df["close"].pct_change()
        vol = returns.rolling(self.vol_window).std().dropna()
        if vol.empty:
            raise ValueError("Not enough training data to fit trend/vol thresholds")
        self._vol_median = float(vol.median())
        return self

    def predict(
        self,
        df: pd.DataFrame,
        *,
        history_df: pd.DataFrame | None = None,
    ) -> pd.Series:
        if self._vol_median is None:
            raise ValueError("TrendVolGridClassifier must be fit before predict")

        context = _contextual_series(df, history_df, self.lookback_bars)["close"]
        returns = context.pct_change()
        vol = returns.rolling(self.vol_window).std().iloc[-len(df) :]
        trend = context.pct_change(self.trend_window).iloc[-len(df) :]

        labels = pd.Series(index=df.index, dtype=object)
        pos_trend = trend > 0
        high_vol = vol > self._vol_median

        labels[pos_trend & ~high_vol] = Regime.CALM_TREND.name
        labels[pos_trend & high_vol] = Regime.VOLATILE_TREND.name
        labels[~pos_trend & ~high_vol] = Regime.CHOP.name
        labels[~pos_trend & high_vol] = Regime.RISK_OFF.name
        return labels

    def classify(self, df: pd.DataFrame) -> pd.Series:
        return self.fit(df).predict(df)


class GaussianMixtureClassifier:
    """4-component Gaussian mixture fit on train data, predicted OOS."""

    name = "gaussian_mixture"

    def __init__(self, vol_window: int = 20, random_state: int = 0):
        self.vol_window = vol_window
        self.random_state = random_state
        self.lookback_bars = vol_window + 1
        self._gmm: GaussianMixture | None = None
        self._cluster_to_regime: dict[int, str] = {}

    def fit(
        self,
        df: pd.DataFrame,
        labels: pd.Series | None = None,
    ) -> GaussianMixtureClassifier:
        from sklearn.mixture import GaussianMixture

        features = _gaussian_features(df["close"], self.vol_window).dropna()
        if len(features) < 4:
            raise ValueError("Not enough training data to fit Gaussian mixture benchmark")

        gmm = GaussianMixture(
            n_components=4,
            covariance_type="full",
            random_state=self.random_state,
        )
        gmm.fit(features.to_numpy())

        vol_per_component = gmm.means_[:, 2]
        order = np.argsort(vol_per_component)
        self._cluster_to_regime = {
            int(order[0]): Regime.CALM_TREND.name,
            int(order[1]): Regime.CHOP.name,
            int(order[2]): Regime.VOLATILE_TREND.name,
            int(order[3]): Regime.RISK_OFF.name,
        }
        self._gmm = gmm
        return self

    def predict(
        self,
        df: pd.DataFrame,
        *,
        history_df: pd.DataFrame | None = None,
    ) -> pd.Series:
        if self._gmm is None:
            raise ValueError("GaussianMixtureClassifier must be fit before predict")

        context = _contextual_series(df, history_df, self.lookback_bars)
        features = _gaussian_features(context["close"], self.vol_window)
        valid = features.dropna()
        labels = pd.Series(index=df.index, dtype=object)

        if valid.empty:
            return labels

        clusters = self._gmm.predict(valid.to_numpy())
        target_index = predicted_index = valid.index.intersection(df.index)
        predicted = pd.Series(
            [self._cluster_to_regime[int(cluster)] for cluster in clusters],
            index=valid.index,
            dtype=object,
        )
        labels.loc[target_index] = predicted.loc[predicted_index]
        return labels

    def classify(self, df: pd.DataFrame) -> pd.Series:
        return self.fit(df).predict(df)


def _contextual_series(
    df: pd.DataFrame,
    history_df: pd.DataFrame | None,
    lookback_bars: int,
) -> pd.DataFrame:
    if history_df is None or history_df.empty or lookback_bars <= 0:
        return df
    return pd.concat([history_df.iloc[-lookback_bars:], df], axis=0)


def _gaussian_features(close: pd.Series, vol_window: int) -> pd.DataFrame:
    returns = close.pct_change()
    vol = returns.rolling(vol_window).std()
    return pd.DataFrame(
        {
            "return": returns,
            "abs_return": returns.abs(),
            "vol": vol,
        },
        index=close.index,
    )
