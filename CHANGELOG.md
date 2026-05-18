# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-05-18

### Added

- **Core Pipeline** — 5-phase Bayesian system-dynamics pipeline for market regime classification
  - Phase 0: Feature engineering (EWMA volatility, trend strength, drawdown pressure, correlation stress, shock intensity)
  - Phase 1: Softmax centroid-based regime classification
  - Phase 2: Dirichlet-Bayesian Markov transition learning
  - Phase 3: Temporal stabilization (hysteresis, persistence, majority vote)
  - Phase 4: Risk conditioning (Risk-Off confirmation, overextension suppression, chop-loop breaking)
- **4 Market Regimes** — Calm Trend, Volatile Trend, Chop, Risk-Off
- **Streaming + Batch** — `pipeline.run(df)` for batch, `pipeline.step(bar)` for streaming
- **Regime Forecasting** — k-step-ahead probabilities via transition matrix exponentiation
- **Signal Detection** — regime changes, Risk-Off warnings, confidence drops, stabilization events
- **Interactive Dashboard** — Streamlit app with live yfinance data, regime-colored price charts, probability areas, transition matrix heatmaps, feature time series
- **3D Phase-Space Attractor Field** — 12-layer interactive Plotly visualization with regime basins, Markov flow arrows, PCA loadings, velocity trajectory, covariance ellipsoids, stationary halos, vol isosurface
- **Backtesting** — rolling-window evaluation with accuracy, F1, confusion matrix metrics
- **Calibration** — centroid fitting, hyperparameter tuning, grid search
- **Benchmarks** — comparison against baseline classifiers
- **Multi-asset Support** — cross-asset correlation stress detection via yfinance
- **229 Unit Tests** — full coverage of core pipeline, stress tests, numerical stability
- **PyPI Package** — `pip install financial-dynamics` with optional extras `[data]`, `[dashboard]`, `[all]`
- **Docker Support** — Dockerfile with health checks
- **Multi-language Documentation** — English, Chinese, Japanese, Korean, Spanish, Portuguese
- **CI/CD** — GitHub Actions for testing (Python 3.10-3.13), linting, build verification, automated PyPI publishing

[1.0.0]: https://github.com/jmiaie/financial-dynamics-model/releases/tag/v1.0.0
