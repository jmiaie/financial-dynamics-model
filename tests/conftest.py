"""Shared test fixtures providing synthetic OHLCV data."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# Ensure src is importable
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

@pytest.fixture
def synthetic_ohlcv() -> tuple[pd.DataFrame, pd.Series]:
    """Generate a full synthetic OHLCV DataFrame with 4 regime segments."""
    from scripts.generate_synthetic_data import generate_synthetic_ohlcv
    df, labels = generate_synthetic_ohlcv(seed=42)
    return df, labels


@pytest.fixture
def calm_trend_data() -> pd.DataFrame:
    """Small DataFrame that looks like a calm uptrend."""
    rng = np.random.default_rng(100)
    n = 100
    prices = 100 + np.cumsum(np.full(n, 0.05) + rng.normal(0, 0.1, n))
    return pd.DataFrame({
        "open": prices - 0.02,
        "high": prices + abs(rng.normal(0, 0.05, n)),
        "low": prices - abs(rng.normal(0, 0.05, n)),
        "close": prices,
        "volume": rng.integers(1000, 3000, n),
    })


@pytest.fixture
def volatile_trend_data() -> pd.DataFrame:
    """Small DataFrame that looks like a volatile uptrend."""
    rng = np.random.default_rng(200)
    n = 100
    prices = 100 + np.cumsum(np.full(n, 0.15) + rng.normal(0, 1.5, n))
    return pd.DataFrame({
        "open": prices - 0.5,
        "high": prices + abs(rng.normal(0, 1.0, n)),
        "low": prices - abs(rng.normal(0, 1.0, n)),
        "close": prices,
        "volume": rng.integers(5000, 15000, n),
    })


@pytest.fixture
def chop_data() -> pd.DataFrame:
    """Small DataFrame that looks like a choppy, directionless market."""
    rng = np.random.default_rng(300)
    n = 100
    prices = 100 + np.cumsum(rng.normal(0, 0.3, n))
    # Mean-revert toward 100
    for i in range(1, n):
        prices[i] = prices[i] + (100 - prices[i]) * 0.03
    return pd.DataFrame({
        "open": prices - 0.1,
        "high": prices + abs(rng.normal(0, 0.2, n)),
        "low": prices - abs(rng.normal(0, 0.2, n)),
        "close": prices,
        "volume": rng.integers(2000, 5000, n),
    })


