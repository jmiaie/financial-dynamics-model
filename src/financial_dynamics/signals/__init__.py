"""Signal and alert layer -- transforms regime outputs into actionable events."""

from financial_dynamics.signals.detector import (
    Signal,
    SignalDetector,
    SignalType,
)

__all__ = [
    "Signal",
    "SignalDetector",
    "SignalType",
]
