"""Majority vote filter -- rolling mode over a window of regime assignments."""

from __future__ import annotations

from collections import Counter, deque

from financial_dynamics.types import Regime


class MajorityVoteFilter:
    """Rolling majority vote over the last N regime assignments.

    Returns the most frequently occurring regime in the window.
    Ties are broken in favor of the most recent assignment.
    """

    def __init__(self, window: int = 10):
        self.window = window
        self._buffer: deque[Regime] = deque(maxlen=window)

    def apply(self, regime: Regime) -> Regime:
        """Add regime to the rolling buffer and return the majority."""
        self._buffer.append(regime)
        counts = Counter(self._buffer)
        max_count = max(counts.values())
        candidates = [r for r, c in counts.items() if c == max_count]
        if len(candidates) == 1:
            return candidates[0]
        for r in reversed(self._buffer):
            if r in candidates:
                return r
        return candidates[0]

    def reset(self) -> None:
        self._buffer.clear()
