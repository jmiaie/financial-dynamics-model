"""Signal and alert layer -- transforms regime outputs into actionable events."""

from financial_dynamics.signals.detector import (
    SignalDetector,
    Signal,
    SignalType,
)

__all__ = [
    "SignalDetector",
    "Signal",
    "SignalType",
]
