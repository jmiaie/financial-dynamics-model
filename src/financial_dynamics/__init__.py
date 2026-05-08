"""Financial Dynamics Model - System Dynamics applied to financial time series."""

__version__ = "1.0.0"

from financial_dynamics.types import (
    Regime,
    REGIME_NAMES,
    NUM_REGIMES,
    FeatureVector,
    RegimeProbabilities,
    BarState,
)
from financial_dynamics.pipeline import FinancialDynamicsPipeline
from financial_dynamics.signals import Signal, SignalDetector, SignalType
from financial_dynamics.forecasting import RegimeForecast

__all__ = [
    "Regime",
    "REGIME_NAMES",
    "NUM_REGIMES",
    "FeatureVector",
    "RegimeProbabilities",
    "BarState",
    "FinancialDynamicsPipeline",
    "Signal",
    "SignalDetector",
    "SignalType",
    "RegimeForecast",
]
