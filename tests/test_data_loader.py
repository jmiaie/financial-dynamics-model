"""Tests for the live data loader module."""

import warnings
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

from financial_dynamics.data_loader import fetch_multi_asset, fetch_ohlcv


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
        with (
            patch.dict("sys.modules", {"yfinance": None}),
            pytest.raises(ImportError, match="yfinance is required"),
        ):
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

    @patch("financial_dynamics.data_loader.yf", create=True)
    def test_missing_columns_raises_value_error(self, mock_yf):
        mock_ticker = MagicMock()
        bad_df = pd.DataFrame({"Price": [1, 2, 3]}, index=pd.date_range("2024-01-01", periods=3))
        mock_ticker.history.return_value = bad_df

        with patch.dict("sys.modules", {"yfinance": mock_yf}):
            mock_yf.Ticker.return_value = mock_ticker
            with pytest.raises(ValueError, match="missing expected columns"):
                fetch_ohlcv("SPY")


class TestFetchMultiAsset:
    @pytest.fixture
    def mock_ref_data(self) -> pd.DataFrame:
        n = 50
        rng = np.random.default_rng(99)
        dates = pd.date_range("2024-01-01", periods=n, freq="D")
        prices = 50 + np.cumsum(rng.normal(0, 0.5, n))
        return pd.DataFrame(
            {
                "Open": prices - 0.3,
                "High": prices + abs(rng.normal(0, 0.3, n)),
                "Low": prices - abs(rng.normal(0, 0.3, n)),
                "Close": prices,
                "Volume": rng.integers(500_000, 2_000_000, n),
            },
            index=dates,
        )

    @patch("financial_dynamics.data_loader.yf", create=True)
    def test_returns_primary_plus_ref_columns(self, mock_yf, mock_yf_data, mock_ref_data):
        primary_ticker = MagicMock()
        primary_ticker.history.return_value = mock_yf_data
        ref_ticker = MagicMock()
        ref_ticker.history.return_value = mock_ref_data

        def ticker_factory(sym):
            if sym == "SPY":
                return primary_ticker
            return ref_ticker

        with patch.dict("sys.modules", {"yfinance": mock_yf}):
            mock_yf.Ticker = ticker_factory
            df = fetch_multi_asset("SPY", ["TLT", "GLD"])

        assert "open" in df.columns
        assert "ref_TLT_close" in df.columns
        assert "ref_GLD_close" in df.columns

    @patch("financial_dynamics.data_loader.yf", create=True)
    def test_caret_stripped_from_ref_names(self, mock_yf, mock_yf_data, mock_ref_data):
        primary_ticker = MagicMock()
        primary_ticker.history.return_value = mock_yf_data
        ref_ticker = MagicMock()
        ref_ticker.history.return_value = mock_ref_data

        def ticker_factory(sym):
            if sym == "SPY":
                return primary_ticker
            return ref_ticker

        with patch.dict("sys.modules", {"yfinance": mock_yf}):
            mock_yf.Ticker = ticker_factory
            df = fetch_multi_asset("SPY", ["^VIX"])

        assert "ref_VIX_close" in df.columns

    @patch("financial_dynamics.data_loader.yf", create=True)
    def test_failed_ref_warns_and_continues(self, mock_yf, mock_yf_data):
        primary_ticker = MagicMock()
        primary_ticker.history.return_value = mock_yf_data
        bad_ticker = MagicMock()
        bad_ticker.history.side_effect = ValueError("API error")

        def ticker_factory(sym):
            if sym == "SPY":
                return primary_ticker
            return bad_ticker

        with patch.dict("sys.modules", {"yfinance": mock_yf}):
            mock_yf.Ticker = ticker_factory
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                df = fetch_multi_asset("SPY", ["BAD_TICKER"])

        assert any("Could not load reference symbol" in str(warning.message) for warning in w)
        assert list(df.columns) == ["open", "high", "low", "close", "volume"]

    @patch("financial_dynamics.data_loader.yf", create=True)
    def test_empty_ref_data_skipped(self, mock_yf, mock_yf_data):
        primary_ticker = MagicMock()
        primary_ticker.history.return_value = mock_yf_data
        empty_ticker = MagicMock()
        empty_ticker.history.return_value = pd.DataFrame()

        def ticker_factory(sym):
            if sym == "SPY":
                return primary_ticker
            return empty_ticker

        with patch.dict("sys.modules", {"yfinance": mock_yf}):
            mock_yf.Ticker = ticker_factory
            df = fetch_multi_asset("SPY", ["EMPTY"])

        assert "ref_EMPTY_close" not in df.columns

    def test_missing_yfinance_raises_import_error(self):
        with (
            patch.dict("sys.modules", {"yfinance": None}),
            pytest.raises(ImportError, match="yfinance is required"),
        ):
            fetch_multi_asset("SPY", ["TLT"])
