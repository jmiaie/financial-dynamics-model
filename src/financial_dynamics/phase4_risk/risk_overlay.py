"""Phase 4: Risk Conditioning Engine -- applies risk overlays to stabilized output."""

from __future__ import annotations

import numpy as np

from financial_dynamics.config import RiskConfig
from financial_dynamics.types import BarState, Regime, RegimeProbabilities, NUM_REGIMES
from financial_dynamics._utils import safe_renormalize
from financial_dynamics.phase4_risk.overextension import OverextensionRebalancer
from financial_dynamics.phase4_risk.chop_suppression import ChopDominanceSuppressor


class RiskConditioningEngine:
    """Phase 4: Applies risk conditioning overlays to the stabilized regime.

    Three overlays:
    1. Risk-Off confirmation: requires confluence of multiple stressors
    2. Overextension rebalancing: suppresses prolonged regimes
    3. Chop dominance suppression: breaks Calm-Chop loops
    """

    def __init__(self, config: RiskConfig | None = None) -> None:
        self.config = config or RiskConfig()
        self._overextension = OverextensionRebalancer(
            window=self.config.overextension_window,
            decay=self.config.overextension_decay,
        )
        self._chop_suppressor = ChopDominanceSuppressor(
            window=self.config.chop_penalty_window,
            penalty=self.config.chop_penalty_factor,
        )

    def update(self, bar_state: BarState) -> BarState:
        """Apply risk overlays to produce final regime assignment.

        Reads bar_state.stabilized_regime, bar_state.features,
        and bar_state.posterior_probabilities.
        Writes bar_state.risk_adjusted_regime and bar_state.risk_overlays.
        """
        if bar_state.stabilized_regime is None:
            return bar_state

        probs = bar_state.posterior_probabilities or bar_state.raw_probabilities
        if probs is None:
            bar_state.risk_adjusted_regime = bar_state.stabilized_regime
            return bar_state

        adjusted_probs = probs.probs.copy()
        overlays: dict[str, bool] = {}

        riskoff_confirmed = self._check_riskoff_confirmation(bar_state)
        overlays["riskoff_confirmed"] = riskoff_confirmed

        if bar_state.stabilized_regime == Regime.RISK_OFF and not riskoff_confirmed:
            adjusted_probs[int(Regime.RISK_OFF)] *= 0.3
            adjusted_probs = safe_renormalize(adjusted_probs)

        adjusted_probs = self._overextension.compute_suppression(adjusted_probs)
        self._overextension.record(bar_state.stabilized_regime)

        adjusted_probs = self._chop_suppressor.compute_penalty(adjusted_probs)
        self._chop_suppressor.record(bar_state.stabilized_regime)

        final_regime = Regime(int(np.argmax(adjusted_probs)))

        if riskoff_confirmed and probs[Regime.RISK_OFF] > 0.2:
            final_regime = Regime.RISK_OFF
            overlays["forced_riskoff"] = True

        bar_state.risk_adjusted_regime = final_regime
        bar_state.risk_overlays = overlays
        return bar_state

    def _check_riskoff_confirmation(self, bar_state: BarState) -> bool:
        """Check if enough stressors confirm a Risk-Off transition.

        Stressors checked:
        - High drawdown pressure
        - High correlation stress
        - High shock intensity
        - High volatility
        """
        if bar_state.features is None:
            return False

        f = bar_state.features
        stressor_count = 0

        if f.drawdown_pressure > self.config.drawdown_threshold:
            stressor_count += 1
        if f.correlation_stress > self.config.correlation_stress_threshold:
            stressor_count += 1
        if f.shock_intensity > self.config.shock_threshold:
            stressor_count += 1
        if f.volatility > 0.7:
            stressor_count += 1

        return stressor_count >= self.config.riskoff_confirmation_count

    def reset(self) -> None:
        self._overextension.reset()
        self._chop_suppressor.reset()
