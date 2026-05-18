"""Financial Dynamics Model - System Dynamics applied to financial time series."""

__version__ = "1.0.0"

from financial_dynamics.forecasting import RegimeForecast
from financial_dynamics.pipeline import FinancialDynamicsPipeline
from financial_dynamics.signals import Signal, SignalDetector, SignalType
from financial_dynamics.types import (
    NUM_REGIMES,
    REGIME_NAMES,
    BarState,
    FeatureVector,
    Regime,
    RegimeProbabilities,
)

__all__ = [
    "NUM_REGIMES",
    "REGIME_NAMES",
    "BarState",
    "FeatureVector",
    "FinancialDynamicsPipeline",
    "Regime",
    "RegimeForecast",
    "RegimeProbabilities",
    "Signal",
    "SignalDetector",
    "SignalType",
]
