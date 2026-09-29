"""Generate synthetic OHLCV data with known regime segments for testing.

Each regime is engineered to produce distinct signatures across all 5
feature dimensions (volatility, trend, drawdown, kurtosis, shock).

Crucially, volatility levels deliberately OVERLAP between regime pairs:
  - Calm Trend & Chop have similar vol (differentiated by trend strength)
  - Volatile Trend & Risk-Off have similar vol (differentiated by drawdown,
    kurtosis, and shock)

This forces multi-feature classifiers to outperform single-factor vol-bucket
baselines.
"""

import numpy as np
import pandas as pd


def generate_synthetic_ohlcv(
    n_calm: int = 80,
    n_volatile: int = 60,
    n_chop: int = 60,
    n_riskoff: int = 40,
    n_cycles: int = 1,
    seed: int = 42,
) -> tuple[pd.DataFrame, pd.Series]:
    """Generate OHLCV data with four distinct regime segments.

    Args:
        n_calm: Bars per calm-trend segment.
        n_volatile: Bars per volatile-trend segment.
        n_chop: Bars per chop segment.
        n_riskoff: Bars per risk-off segment.
        n_cycles: Number of full regime cycles to generate.
        seed: Random seed for reproducibility.

    Returns:
        df: DataFrame with columns [open, high, low, close, volume]
        labels: Series with the true regime label per bar
    """
    rng = np.random.default_rng(seed)
    segments: list[list[float]] = []
    labels: list[str] = []
    price = 100.0

    for _ in range(n_cycles):
        price = _generate_calm_trend(rng, price, n_calm, segments, labels)
        price = _generate_volatile_trend(rng, price, n_volatile, segments, labels)
        price = _generate_chop(rng, price, n_chop, segments, labels)
        price = _generate_riskoff(rng, price, n_riskoff, segments, labels)

    df = pd.DataFrame(segments, columns=["open", "high", "low", "close", "volume"])
    df.index = pd.date_range("2024-01-01", periods=len(df), freq="h")
    df.index.name = "timestamp"

    return df, pd.Series(labels, index=df.index, name="regime")


def _generate_calm_trend(
    rng: np.random.Generator,
    price: float,
    n: int,
    segments: list,
    labels: list,
) -> float:
    """Calm Trend: consistent positive drift, moderate vol, no shocks.

    Vol overlap zone with Chop (~0.007 std). Distinguished by:
      - Strong positive trend strength (vs Chop's near-zero)
      - Near-zero drawdown (vs Chop's oscillating drawdowns)
      - Low kurtosis, low shock (like Chop)
    """
    for _ in range(n):
        ret = 0.0015 + rng.normal(0, 0.007)
        ret = np.clip(ret, -0.015, 0.025)
        close = price * (1 + ret)
        high = max(price, close) * (1 + abs(rng.normal(0, 0.002)))
        low = min(price, close) * (1 - abs(rng.normal(0, 0.002)))
        vol = rng.integers(1500, 4000)
        segments.append([price, high, low, close, vol])
        labels.append("CALM_TREND")
        price = close
    return price


def _generate_volatile_trend(
    rng: np.random.Generator,
    price: float,
    n: int,
    segments: list,
    labels: list,
) -> float:
    """Volatile Trend: strong uptrend with large swings, occasional pullbacks.

    Vol overlap zone with Risk-Off (~0.020 std). Distinguished by:
      - Positive trend (vs Risk-Off's negative)
      - Moderate drawdown with recoveries (vs Risk-Off's deep sustained drawdown)
      - Low kurtosis — returns are wide but normally distributed (vs Risk-Off's fat tails)
      - Low-moderate shock (vs Risk-Off's clustered shocks)
    """
    for i in range(n):
        ret = 0.003 + rng.normal(0, 0.020)
        if i % 15 < 4:
            ret -= 0.012
        close = price * (1 + ret)
        spread = abs(close - price)
        high = max(price, close) + spread * rng.uniform(0.1, 0.4)
        low = min(price, close) - spread * rng.uniform(0.1, 0.4)
        vol = rng.integers(5000, 14000)
        segments.append([price, high, low, close, vol])
        labels.append("VOLATILE_TREND")
        price = close
    return price


def _generate_chop(
    rng: np.random.Generator,
    price: float,
    n: int,
    segments: list,
    labels: list,
) -> float:
    """Chop: mean-reverting, directionless market.

    Vol overlap zone with Calm Trend (~0.008 std). Distinguished by:
      - Near-zero trend strength (frequent reversals vs Calm's steady rise)
      - Small oscillating drawdowns from direction changes
      - Low kurtosis, low shock (like Calm Trend)
    """
    anchor = price
    direction = 1.0
    for _ in range(n):
        if rng.random() < 0.18:
            direction *= -1
        drift = direction * 0.002
        ret = drift + rng.normal(0, 0.008)
        ret = np.clip(ret, -0.025, 0.025)
        close = price * (1 + ret)
        close = close + (anchor - close) * 0.07
        high = max(price, close) * (1 + abs(rng.normal(0, 0.003)))
        low = min(price, close) * (1 - abs(rng.normal(0, 0.003)))
        vol = rng.integers(2000, 5000)
        segments.append([price, high, low, close, vol])
        labels.append("CHOP")
        price = close
    return price


def _generate_riskoff(
    rng: np.random.Generator,
    price: float,
    n: int,
    segments: list,
    labels: list,
) -> float:
    """Risk-Off: crash with shock clusters, deep drawdowns, fat tails.

    Vol overlap zone with Volatile Trend (~0.020 std baseline). Distinguished by:
      - Negative trend (sustained decline)
      - Deep drawdown from peak (no recovery, just deeper)
      - High kurtosis — injected shock clusters create fat tails
      - High shock intensity — extreme |returns| relative to recent std
    """
    for _ in range(n):
        if rng.random() < 0.25:
            shock = rng.choice([-0.06, -0.07, -0.05, 0.035])
            ret = shock + rng.normal(0, 0.015)
        elif rng.random() < 0.12:
            ret = rng.uniform(0.005, 0.02)
        else:
            ret = -0.004 + rng.normal(0, 0.018)
        close = price * (1 + ret)
        high = price * (1 + abs(rng.normal(0, 0.010)))
        low_spread = abs(ret) * price if ret < 0 else 0
        low = min(price, close) - low_spread * rng.uniform(0.1, 0.3)
        vol = rng.integers(12000, 45000)
        segments.append([price, high, low, close, vol])
        labels.append("RISK_OFF")
        price = close
    return price


if __name__ == "__main__":
    df, labels = generate_synthetic_ohlcv()
    print(f"Generated {len(df)} bars")
    print(f"\nRegime distribution:\n{labels.value_counts()}")
    print(f"\nPrice range: {df['close'].min():.2f} - {df['close'].max():.2f}")
    df.to_csv("synthetic_ohlcv.csv")
    labels.to_csv("synthetic_labels.csv")
    print("Saved to synthetic_ohlcv.csv and synthetic_labels.csv")
