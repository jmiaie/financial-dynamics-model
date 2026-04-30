# Financial Dynamics Model

## Overview

The Financial Dynamics Model is a system-dynamics-based approach to financial regime classification that transforms raw OHLCV data into stable, structurally-informed probability distributions over four market regimes: **Calm Trend**, **Volatile Trend**, **Chop**, and **Risk-Off**.

## Architecture

A 5-phase pipeline:

1. **Phase 0: Feature Engineering** — 5 normalized indicators (volatility, trend strength, drawdown pressure, cross-asset correlation stress, shock intensity)
2. **Phase 1: Regime Classification** — Centroid-based softmax mapping to regime probabilities
3. **Phase 2: Markov Transitions** — Bayesian-updated transition matrix with multiplicative posterior fusion
4. **Phase 3: Stabilization** — Hysteresis, persistence, and majority-vote filters to prevent regime flickering
5. **Phase 4: Risk Conditioning** — Risk-Off confirmation, overextension rebalancing, chop suppression overlays

## Key Features

- **Multi-feature regime classification** — 5D feature space captures trend, volatility, drawdown, systemic stress, and shocks
- **Calibration framework** — Data-driven centroid fitting + hyperparameter grid search (57.8% → 80.6% accuracy on synthetic data)
- **Live data integration** — Real OHLCV via yfinance with optional multi-asset correlation stress
- **Backtesting framework** — Accuracy, confusion matrix, F1, rolling-window evaluation
- **Regime forecasting** — k-step-ahead predictions and stationary distribution via transition matrix
- **Signal layer** — Actionable alerts on regime changes, Risk-Off warnings, confidence drops, stabilization
- **Persistence layer** — Save/load learned transition matrices and normalizer state
- **Full backward compatibility** — Works with both single-asset and multi-asset data

## Results

- **Calibrated pipeline: 80.6% accuracy** vs volatility-bucket baseline (77.7%) on synthetic data with deliberate regime vol overlap
- **219 unit tests** covering all phases
- **Real-time streaming** and batch modes
- **Portfolio-ready** for both live deployment and historical research

## Installation

```bash
pip install -r requirements.txt
python scripts/run_pipeline.py --symbol SPY --reference-symbols ^VIX TLT
```

## Next Steps

- Train on real labeled regime segments to improve centroid fit
- Add regime-specific Sharpe/Sortino metrics for ex-post validation
- Multi-timeframe ensemble (1h/4h/1d aggregation)
- Regime-aware position sizing and hedging recommendations
