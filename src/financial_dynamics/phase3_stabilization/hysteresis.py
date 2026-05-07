"""Hysteresis filter -- prevents regime flipping unless probability gap exceeds threshold."""

from __future__ import annotations

from financial_dynamics.types import Regime, RegimeProbabilities


class HysteresisFilter:
    """Prevents regime transitions unless the new regime's probability
    exceeds the current regime's probability by at least `threshold`."""

    def __init__(self, threshold: float = 0.15) -> None:
        self.threshold = threshold

    def apply(
        self,
        current_regime: Regime,
        probabilities: RegimeProbabilities,
    ) -> Regime:
        """Return the regime to use after applying hysteresis.

        If the highest-probability regime differs from current but the gap
        is less than threshold, the current regime is maintained.
        """
        candidate = probabilities.dominant
        if candidate == current_regime:
            return current_regime

        gap = probabilities[candidate] - probabilities[current_regime]
        if gap > self.threshold:
            return candidate
        return current_regime
