# Launching: Financial Dynamics Model

Just shipped a transparent, production-grade regime classifier for quantitative trading and research.

## The Gap
Most quant shops use either naive heuristics (vol quartiles, trend signs) or neural nets they can't explain. There's no middle ground: transparent, calibrated, multi-feature regime detection at scale.

## What We Built
A 5-phase system-dynamics pipeline that maps raw OHLCV → stable regime probabilities:

**Phase 0:** 5D feature engineering (volatility, trend, drawdown, cross-asset stress, shocks)
**Phase 1:** Centroid-based softmax classification  
**Phase 2:** Bayesian-learned Markov transition matrix  
**Phase 3:** Temporal stabilization (hysteresis + persistence + majority vote)  
**Phase 4:** Risk overlays (Risk-Off confirmation, overextension suppression, chop loops)

## The Numbers
- **80.6% accuracy** (calibrated) vs 77.7% single-factor baseline
- **219 unit tests** — all passing
- **Live integration** — yfinance, streaming/batch modes, multi-asset support
- **k-step forecasting** via matrix exponentiation
- **Actionable signals** — regime changes, Risk-Off alerts, confidence drops, stabilization events

## Why It Matters
✓ **Transparent:** Every number is explainable—feature definitions, centroid values, transition probs  
✓ **Calibrated:** Fits centroids from labeled data; grid-searches hyperparameters on backtest accuracy  
✓ **Modular:** Each phase independently testable; swap components without breaking others  
✓ **Deployment-ready:** Persistence layer, live data pipelines, real-time streaming  

## For Traders/Researchers
Use this as a regime filter for:
- Entry/exit logic (favor trades aligned with current + forecasted regime)
- Position sizing (scale up in Calm Trend, down in Risk-Off)
- Hedging rules (strengthen hedges when Risk-Off probability > threshold)

## For Quant Teams
- Replace ad-hoc regime logic with a calibrated standard
- Backtest across multiple assets/timeframes without rebuilding
- Export learned transition matrices for downstream strategies

## For Risk Management
- Explainable regime forecasts for stress testing
- Multi-asset contagion signals (cross-asset correlation stress)
- Early warnings before regime shifts

---

**Open-sourced on GitHub.** Production-ready. Looking for feedback from hedge funds, prop shops, and quant researchers.

**Authors:** Jeff Milam & Micap AI LLC  
**Tech:** Python, NumPy, Pandas, SciPy, Bayesian inference, Markov chains, system dynamics  
**Status:** 219 tests passing, live deployment verified

#QuantTrading #Fintech #RegimeDetection #SystemDynamics #Backtesting
