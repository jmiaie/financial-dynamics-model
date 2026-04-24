"""Live data loading from Yahoo Finance via yfinance."""

from __future__ import annotations

import pandas as pd


def fetch_ohlcv(
    symbol: str,
    period: str = "1y",
    interval: str = "1d",
) -> pd.DataFrame:
    """Fetch OHLCV data from Yahoo Finance.

    Args:
        symbol: Ticker symbol (e.g. "SPY", "AAPL").
        period: Lookback period (e.g. "6mo", "1y", "5y").
        interval: Bar interval (e.g. "1d", "1h", "5m").

    Returns:
        DataFrame with lowercase columns [open, high, low, close, volume]
        and a DatetimeIndex.

    Raises:
        ImportError: If yfinance is not installed.
        ValueError: If no data is returned for the given symbol/period.
    """
    try:
        import yfinance as yf
    except ImportError:
        raise ImportError(
            "yfinance is required for live data. "
            "Install it with: pip install yfinance"
        ) from None

    ticker = yf.Ticker(symbol)
    df = ticker.history(period=period, interval=interval)

    if df.empty:
        raise ValueError(
            f"No data returned for symbol '{symbol}' "
            f"with period='{period}', interval='{interval}'. "
            f"Check that the ticker is valid."
        )

    df.columns = [c.lower() for c in df.columns]

    required = {"open", "high", "low", "close", "volume"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(
            f"Yahoo Finance data missing expected columns: {sorted(missing)}"
        )

    return df[["open", "high", "low", "close", "volume"]]
