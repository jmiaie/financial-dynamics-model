"""Pure-function indicator computations for Phase 0 feature engineering.

Each function accepts pandas Series and returns pandas Series.
No internal state -- purely functional.
"""

import numpy as np
import pandas as pd


def compute_ewma_volatility(returns: pd.Series, span: int = 20) -> pd.Series:
    """EWMA of squared returns -- measures realized volatility.

    Args:
        returns: Log or simple returns series.
        span: EWMA span parameter (higher = smoother).

    Returns:
        Series of annualized volatility estimates (sqrt of EWMA variance).
    """
    squared = returns ** 2
    ewma_var = squared.ewm(span=span, min_periods=span).mean()
    return np.sqrt(ewma_var)


def compute_trend_strength(close: pd.Series, window: int = 14) -> pd.Series:
    """Normalized slope of linear regression over a rolling window.

    The slope is normalized by dividing by the mean price in the window,
    giving a scale-independent trend measure. Positive = uptrend,
    negative = downtrend. Absolute value used for strength.

    Returns:
        Series with normalized absolute trend strength.
    """
    def _regression_slope(y: np.ndarray) -> float:
        if len(y) < 2 or np.isnan(y).any():
            return np.nan
        x = np.arange(len(y), dtype=float)
        x_mean = x.mean()
        y_mean = y.mean()
        denom = np.sum((x - x_mean) ** 2)
        if denom == 0:
            return 0.0
        slope = np.sum((x - x_mean) * (y - y_mean)) / denom
        return abs(slope / y_mean) if y_mean != 0 else 0.0

    return close.rolling(window, min_periods=window).apply(_regression_slope, raw=True)


def compute_drawdown_pressure(close: pd.Series, window: int = 60) -> pd.Series:
    """Current drawdown depth relative to rolling peak.

    Returns:
        Series in [0, 1] where 0 = at peak, 1 = maximum historical drawdown.
    """
    rolling_max = close.rolling(window, min_periods=1).max()
    drawdown = (rolling_max - close) / rolling_max
    return drawdown.clip(lower=0.0)


def compute_correlation_stress(returns: pd.Series, window: int = 20) -> pd.Series:
    """Rolling excess kurtosis of returns as a single-asset proxy for
    correlation stress / systemic risk.

    High kurtosis (fat tails) indicates clustered volatility and
    potential systemic stress.

    Returns:
        Series of rolling excess kurtosis values.
    """
    kurt = returns.rolling(window, min_periods=window).kurt()
    # Fat tails only; platykurtic values are not meaningful here
    return kurt.clip(lower=0.0)


def compute_cross_asset_stress(
    returns: pd.Series,
    reference_returns: dict[str, pd.Series],
    window: int = 20,
) -> pd.Series:
    """Rolling cross-asset correlation stress.

    Measures how strongly the primary asset co-moves with reference assets.
    High absolute correlation across references signals systemic stress
    (contagion / flight-to-safety).

    Args:
        returns: Primary asset returns.
        reference_returns: Dict mapping reference name to its returns Series.
        window: Rolling correlation window.

    Returns:
        Series of mean absolute rolling correlation across all references.
    """
    if not reference_returns:
        return compute_correlation_stress(returns, window)

    corrs = []
    for ref_returns in reference_returns.values():
        aligned = pd.DataFrame({"primary": returns, "ref": ref_returns}).dropna()
        if len(aligned) < window:
            continue
        rolling_corr = aligned["primary"].rolling(window, min_periods=window).corr(aligned["ref"])
        corrs.append(rolling_corr.abs().reindex(returns.index))

    if not corrs:
        return compute_correlation_stress(returns, window)

    stacked = pd.concat(corrs, axis=1)
    return stacked.mean(axis=1).clip(lower=0.0)


def compute_shock_intensity(returns: pd.Series, window: int = 20) -> pd.Series:
    """Standardized residual: |r_t| / rolling_std.

    Measures how extreme the current return is relative to recent history.

    Returns:
        Series of standardized absolute returns (Z-scores).
    """
    rolling_std = returns.rolling(window, min_periods=window).std()
    rolling_mean = returns.rolling(window, min_periods=window).mean()
    shock = (returns - rolling_mean).abs() / (rolling_std + 1e-10)
    return shock
