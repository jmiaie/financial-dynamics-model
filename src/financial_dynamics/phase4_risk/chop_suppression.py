"""Chop dominance suppression -- penalizes prolonged Calm-Chop oscillation loops."""

from __future__ import annotations

from collections import deque

import numpy as np

from financial_dynamics.types import Regime, NUM_REGIMES
from financial_dynamics.phase4_risk._utils import safe_renormalize


class ChopDominanceSuppressor:
    """Detects prolonged Calm-Chop oscillation patterns and penalizes
    Chop probability to break the loop and force structural movement."""

    def __init__(self, window: int = 30, penalty: float = 0.1):
        self.window = window
        self.penalty = penalty
        self._history: deque[Regime] = deque(maxlen=window)

    def compute_penalty(self, probs: np.ndarray) -> np.ndarray:
        """Apply Chop dominance penalty if Calm-Chop loop detected.

        Detects when the last N bars alternate predominantly between
        Calm Trend and Chop regimes without visiting higher-stress states.

        Returns:
            Adjusted probability vector summing to 1.0.
        """
        if len(self._history) < self.window:
            return probs.copy()

        calm_chop_count = sum(
            1 for r in self._history
            if r in (Regime.CALM_TREND, Regime.CHOP)
        )
        ratio = calm_chop_count / len(self._history)

        if ratio < 0.8:
            return probs.copy()

        adjusted = probs.copy()
        adjusted[int(Regime.CHOP)] *= max(1.0 - self.penalty * 3, 0.05)
        adjusted[int(Regime.CALM_TREND)] *= max(1.0 - self.penalty, 0.2)

        # Boost Volatile Trend slightly to encourage structural movement
        adjusted[int(Regime.VOLATILE_TREND)] *= (1.0 + self.penalty * 2)

        return safe_renormalize(adjusted)

    def record(self, regime: Regime) -> None:
        self._history.append(regime)

    def reset(self) -> None:
        self._history.clear()
