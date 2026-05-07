"""Regime overextension rebalancing -- suppresses prolonged regimes."""

from __future__ import annotations

from collections import Counter

import numpy as np

from financial_dynamics.types import Regime, NUM_REGIMES
from financial_dynamics._utils import safe_renormalize


class OverextensionRebalancer:
    """Detects when a regime has persisted beyond its expected duration
    and applies a suppression factor to its probability."""

    def __init__(self, window: int = 50, decay: float = 0.02) -> None:
        self.window = window
        self.decay = decay
        self._history: list[Regime] = []

    def compute_suppression(self, probs: np.ndarray) -> np.ndarray:
        """Apply overextension suppression to probability vector.

        If the dominant regime has been active for too many of the
        recent bars, its probability is reduced and redistributed.

        Returns:
            Adjusted probability vector summing to 1.0.
        """
        if len(self._history) < self.window:
            return probs.copy()

        recent = self._history[-self.window:]
        counts = Counter(recent)
        adjusted = probs.copy()

        for regime in Regime:
            fraction = counts.get(regime, 0) / self.window
            expected = 1.0 / NUM_REGIMES
            if fraction > expected * 2:
                excess = fraction - expected
                suppression = max(1.0 - self.decay * excess * self.window, 0.1)
                adjusted[int(regime)] *= suppression

        return safe_renormalize(adjusted)

    def record(self, regime: Regime) -> None:
        """Append a regime observation; caps history at 2× window to bound memory."""
        self._history.append(regime)
        if len(self._history) > self.window * 2:
            self._history = self._history[-self.window * 2:]

    def reset(self) -> None:
        self._history.clear()
