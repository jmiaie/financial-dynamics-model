"""Live data loading from Yahoo Finance via yfinance."""

from __future__ import annotations

import warnings

import pandas as pd


def validate_ohlcv_frame(
    df: pd.DataFrame,
    *,
    missing_policy: str = "raise",
    keep_extra_columns: bool = False,
) -> pd.DataFrame:
    """Validate chronology and missing-data assumptions for OHLCV research data."""
    required = {"open", "high", "low", "close", "volume"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Yahoo Finance data missing expected columns: {sorted(missing)}")

    if not isinstance(df.index, pd.DatetimeIndex):
        raise ValueError("OHLCV data must use a DatetimeIndex")
    if not df.index.is_monotonic_increasing:
        raise ValueError("OHLCV data index must be monotonic increasing")
    if df.index.has_duplicates:
        raise ValueError("OHLCV data index must not contain duplicates")

    cleaned = (
        df.copy()
        if keep_extra_columns
        else df.loc[:, ["open", "high", "low", "close", "volume"]].copy()
    )
    if keep_extra_columns:
        ordered_columns = ["open", "high", "low", "close", "volume"] + [
            col for col in cleaned.columns if col not in {"open", "high", "low", "close", "volume"}
        ]
        cleaned = cleaned.loc[:, ordered_columns]
    if cleaned.isna().any().any():
        if missing_policy == "drop":
            cleaned = cleaned.dropna()
        elif missing_policy != "raise":
            raise ValueError(f"Unsupported missing_policy '{missing_policy}'")
        else:
            raise ValueError("OHLCV data contains missing values; refusing to backfill future data")
    return cleaned


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
            "yfinance is required for live data. Install it with: pip install yfinance"
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
    return validate_ohlcv_frame(df)


def fetch_multi_asset(
    symbol: str,
    reference_symbols: list[str],
    period: str = "1y",
    interval: str = "1d",
) -> pd.DataFrame:
    """Fetch OHLCV for a primary symbol plus close prices for references.

    Reference symbols are included as columns named 'ref_{symbol}_close'.
    These columns enable cross-asset correlation stress computation
    in the feature engine.

    Args:
        symbol: Primary ticker symbol.
        reference_symbols: List of reference tickers (e.g. ["^VIX", "TLT"]).
        period: Lookback period.
        interval: Bar interval.

    Returns:
        DataFrame with primary OHLCV + ref_*_close columns.
    """
    try:
        import yfinance as yf
    except ImportError:
        raise ImportError(
            "yfinance is required for live data. Install it with: pip install yfinance"
        ) from None

    df = fetch_ohlcv(symbol, period=period, interval=interval)

    for ref_sym in reference_symbols:
        try:
            ref_ticker = yf.Ticker(ref_sym)
            ref_df = ref_ticker.history(period=period, interval=interval)
            if not ref_df.empty:
                ref_df.columns = [c.lower() for c in ref_df.columns]
                col_name = f"ref_{ref_sym.replace('^', '')}_close"
                df[col_name] = ref_df["close"].reindex(df.index)
        except (KeyError, ValueError, AttributeError) as exc:
            warnings.warn(
                f"Could not load reference symbol '{ref_sym}': {exc}",
                stacklevel=2,
            )
            continue

    return validate_ohlcv_frame(df, missing_policy="drop", keep_extra_columns=True)
