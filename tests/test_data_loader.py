"""Tests for the live data loader module."""

from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

from financial_dynamics.data_loader import fetch_ohlcv


@pytest.fixture
def mock_yf_data() -> pd.DataFrame:
    """Realistic mock Yahoo Finance response."""
    n = 50
    rng = np.random.default_rng(42)
    dates = pd.date_range("2024-01-01", periods=n, freq="D")
    prices = 100 + np.cumsum(rng.normal(0, 1, n))
    return pd.DataFrame(
        {
            "Open": prices - 0.5,
            "High": prices + abs(rng.normal(0, 0.5, n)),
            "Low": prices - abs(rng.normal(0, 0.5, n)),
            "Close": prices,
            "Volume": rng.integers(1_000_000, 5_000_000, n),
            "Dividends": np.zeros(n),
            "Stock Splits": np.zeros(n),
        },
        index=dates,
    )


class TestFetchOhlcv:
    @patch("financial_dynamics.data_loader.yf", create=True)
    def test_returns_correct_columns(self, mock_yf, mock_yf_data):
        mock_ticker = MagicMock()
        mock_ticker.history.return_value = mock_yf_data

        with patch.dict("sys.modules", {"yfinance": mock_yf}):
            mock_yf.Ticker.return_value = mock_ticker
            df = fetch_ohlcv("SPY", period="6mo")

        assert list(df.columns) == ["open", "high", "low", "close", "volume"]
        assert len(df) == 50

    @patch("financial_dynamics.data_loader.yf", create=True)
    def test_strips_extra_columns(self, mock_yf, mock_yf_data):
        mock_ticker = MagicMock()
        mock_ticker.history.return_value = mock_yf_data

        with patch.dict("sys.modules", {"yfinance": mock_yf}):
            mock_yf.Ticker.return_value = mock_ticker
            df = fetch_ohlcv("AAPL")

        assert "dividends" not in df.columns
        assert "stock splits" not in df.columns

    @patch("financial_dynamics.data_loader.yf", create=True)
    def test_passes_period_and_interval(self, mock_yf, mock_yf_data):
        mock_ticker = MagicMock()
        mock_ticker.history.return_value = mock_yf_data

        with patch.dict("sys.modules", {"yfinance": mock_yf}):
            mock_yf.Ticker.return_value = mock_ticker
            fetch_ohlcv("SPY", period="2y", interval="1h")

        mock_ticker.history.assert_called_once_with(period="2y", interval="1h")

    @patch("financial_dynamics.data_loader.yf", create=True)
    def test_empty_data_raises_value_error(self, mock_yf):
        mock_ticker = MagicMock()
        mock_ticker.history.return_value = pd.DataFrame()

        with patch.dict("sys.modules", {"yfinance": mock_yf}):
            mock_yf.Ticker.return_value = mock_ticker
            with pytest.raises(ValueError, match="No data returned"):
                fetch_ohlcv("INVALID_TICKER_XYZ")

    def test_missing_yfinance_raises_import_error(self):
        with patch.dict("sys.modules", {"yfinance": None}):
            with pytest.raises(ImportError, match="yfinance is required"):
                fetch_ohlcv("SPY")

    @patch("financial_dynamics.data_loader.yf", create=True)
    def test_output_compatible_with_pipeline(self, mock_yf, mock_yf_data):
        mock_ticker = MagicMock()
        mock_ticker.history.return_value = mock_yf_data

        with patch.dict("sys.modules", {"yfinance": mock_yf}):
            mock_yf.Ticker.return_value = mock_ticker
            df = fetch_ohlcv("SPY")

        from financial_dynamics.pipeline import FinancialDynamicsPipeline

        pipeline = FinancialDynamicsPipeline()
        results = pipeline.run(df)
        assert len(results) == len(df)
        assert "risk_adjusted_regime" in results.columns
