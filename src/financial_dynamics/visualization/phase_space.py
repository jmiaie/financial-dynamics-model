"""Phase-space regime color palette."""

from __future__ import annotations

from financial_dynamics.types import Regime

REGIME_COLORS = {
    Regime.CALM_TREND: "#2ecc71",
    Regime.VOLATILE_TREND: "#f39c12",
    Regime.CHOP: "#9b59b6",
    Regime.RISK_OFF: "#e74c3c",
}
