"""Persistence filter -- requires N consecutive bars before confirming a regime change."""

from __future__ import annotations

from financial_dynamics.types import Regime


class PersistenceFilter:
    """Requires a new regime candidate to persist for min_bars consecutive
    bars before the regime change is confirmed."""

    def __init__(self, min_bars: int = 5) -> None:
        self.min_bars = min_bars
        self._confirmed_regime: Regime | None = None
        self._candidate: Regime | None = None
        self._candidate_count: int = 0

    def apply(self, candidate_regime: Regime) -> Regime:
        """Track consecutive appearances of the candidate regime.

        Returns the confirmed regime. A new regime is only confirmed
        after appearing for min_bars consecutive bars.
        """
        if self._confirmed_regime is None:
            self._confirmed_regime = candidate_regime
            self._candidate = candidate_regime
            self._candidate_count = 1
            return candidate_regime

        if candidate_regime == self._confirmed_regime:
            self._candidate = candidate_regime
            self._candidate_count = 0
            return self._confirmed_regime

        # Different regime proposed
        if candidate_regime == self._candidate:
            self._candidate_count += 1
        else:
            self._candidate = candidate_regime
            self._candidate_count = 1

        if self._candidate_count >= self.min_bars:
            self._confirmed_regime = candidate_regime
            self._candidate_count = 0
            return candidate_regime

        return self._confirmed_regime

    def reset(self) -> None:
        self._confirmed_regime = None
        self._candidate = None
        self._candidate_count = 0
