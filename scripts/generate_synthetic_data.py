"""Generate synthetic OHLCV data with known regime segments for testing."""

import numpy as np
import pandas as pd


def generate_synthetic_ohlcv(
    n_calm: int = 80,
    n_volatile: int = 60,
    n_chop: int = 60,
    n_riskoff: int = 40,
    seed: int = 42,
) -> tuple[pd.DataFrame, pd.Series]:
    """Generate OHLCV data with four distinct regime segments.

    Returns:
        df: DataFrame with columns [open, high, low, close, volume]
        labels: Series with the true regime label per bar
    """
    rng = np.random.default_rng(seed)

    segments = []
    labels = []

    # --- Calm Trend: low volatility, steady uptrend ---
    price = 100.0
    for _ in range(n_calm):
        ret = 0.001 + rng.normal(0, 0.005)
        close = price * (1 + ret)
        high = close * (1 + abs(rng.normal(0, 0.002)))
        low = price * (1 - abs(rng.normal(0, 0.002)))
        vol = rng.integers(1000, 3000)
        segments.append([price, high, low, close, vol])
        labels.append("CALM_TREND")
        price = close

    # --- Volatile Trend: high volatility, strong uptrend ---
    for _ in range(n_volatile):
        ret = 0.003 + rng.normal(0, 0.025)
        close = price * (1 + ret)
        high = max(price, close) * (1 + abs(rng.normal(0, 0.01)))
        low = min(price, close) * (1 - abs(rng.normal(0, 0.01)))
        vol = rng.integers(5000, 15000)
        segments.append([price, high, low, close, vol])
        labels.append("VOLATILE_TREND")
        price = close

    # --- Chop: medium volatility, no trend (mean-reverting) ---
    anchor = price
    for _ in range(n_chop):
        ret = rng.normal(0, 0.012)
        close = price * (1 + ret)
        # Mean-revert toward anchor
        close = close + (anchor - close) * 0.05
        high = max(price, close) * (1 + abs(rng.normal(0, 0.005)))
        low = min(price, close) * (1 - abs(rng.normal(0, 0.005)))
        vol = rng.integers(2000, 6000)
        segments.append([price, high, low, close, vol])
        labels.append("CHOP")
        price = close

    # --- Risk-Off: spike volatility, crash ---
    for _ in range(n_riskoff):
        ret = -0.008 + rng.normal(0, 0.04)
        close = price * (1 + ret)
        high = price * (1 + abs(rng.normal(0, 0.015)))
        low = close * (1 - abs(rng.normal(0, 0.02)))
        vol = rng.integers(15000, 40000)
        segments.append([price, high, low, close, vol])
        labels.append("RISK_OFF")
        price = close

    df = pd.DataFrame(segments, columns=["open", "high", "low", "close", "volume"])
    df.index = pd.date_range("2024-01-01", periods=len(df), freq="h")
    df.index.name = "timestamp"

    return df, pd.Series(labels, index=df.index, name="regime")


if __name__ == "__main__":
    df, labels = generate_synthetic_ohlcv()
    print(f"Generated {len(df)} bars")
    print(f"\nRegime distribution:\n{labels.value_counts()}")
    print(f"\nPrice range: {df['close'].min():.2f} - {df['close'].max():.2f}")
    df.to_csv("synthetic_ohlcv.csv")
    labels.to_csv("synthetic_labels.csv")
    print("Saved to synthetic_ohlcv.csv and synthetic_labels.csv")
