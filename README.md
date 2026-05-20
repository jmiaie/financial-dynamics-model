<div align="center">

# Financial Dynamics Model

### Bayesian System-Dynamics Pipeline for Market Regime Classification

[![PyPI version](https://img.shields.io/pypi/v/financial-dynamics?color=0d7377&style=flat-square)](https://pypi.org/project/financial-dynamics/)
[![Python](https://img.shields.io/pypi/pyversions/financial-dynamics?style=flat-square)](https://pypi.org/project/financial-dynamics/)
[![CI](https://img.shields.io/github/actions/workflow/status/jmiaie/financial-dynamics-model/ci.yml?style=flat-square&label=CI)](https://github.com/jmiaie/financial-dynamics-model/actions)
[![License: MIT](https://img.shields.io/badge/license-MIT-0d7377.svg?style=flat-square)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-275%20passed-0d7377?style=flat-square)](#testing)
[![Downloads](https://img.shields.io/pypi/dm/financial-dynamics?color=0d7377&style=flat-square)](https://pypi.org/project/financial-dynamics/)
[![Coverage](https://img.shields.io/badge/coverage-98%25-0d7377?style=flat-square)](#testing)
[![mypy](https://img.shields.io/badge/type%20checked-mypy-0d7377?style=flat-square)](https://mypy-lang.org/)
[![Streamlit](https://img.shields.io/badge/demo-live-0d7377?style=flat-square&logo=streamlit)](https://financial-dynamics-model.streamlit.app)

**Transforms raw OHLCV data into explainable regime probabilities for quantitative trading and risk management.**

[Live Demo](https://financial-dynamics-model.streamlit.app) &nbsp;|&nbsp; [Documentation](#documentation) &nbsp;|&nbsp; [Install](#installation) &nbsp;|&nbsp; [API Reference](#python-api)

**[English](README.md)** &nbsp;|&nbsp; [中文](docs/README_zh.md) &nbsp;|&nbsp; [日本語](docs/README_ja.md) &nbsp;|&nbsp; [한국어](docs/README_ko.md) &nbsp;|&nbsp; [Español](docs/README_es.md) &nbsp;|&nbsp; [Português](docs/README_pt.md)

---

<table>
<tr>
<td align="center"><strong>80.6%</strong><br><sub>Accuracy</sub></td>
<td align="center"><strong>275</strong><br><sub>Unit Tests</sub></td>
<td align="center"><strong>5</strong><br><sub>Pipeline Phases</sub></td>
<td align="center"><strong>4</strong><br><sub>Market Regimes</sub></td>
<td align="center"><strong>12</strong><br><sub>3D Viz Layers</sub></td>
</tr>
</table>

</div>

---

## Why Financial Dynamics?

Most regime detection tools are either black-box neural networks or simplistic threshold rules. Financial Dynamics sits in the sweet spot: **fully transparent Bayesian inference** with **production-grade engineering**.

Every probability is traceable. Every transition is explainable. Every signal has a clear mathematical origin.

```
                         ┌─────────────────────────────────┐
                         │     Financial Dynamics Model     │
                         └────────────────┬────────────────┘
                                          │
              ┌───────────────────────────┼───────────────────────────┐
              │                           │                           │
     ┌────────▼────────┐        ┌────────▼────────┐        ┌────────▼────────┐
     │   Python API    │        │   Streamlit App  │        │    CLI Tools    │
     │                 │        │                  │        │                 │
     │ pipeline.run()  │        │  Interactive 3D  │        │  run_pipeline   │
     │ pipeline.step() │        │  Live Charts     │        │  run_backtest   │
     │ pipeline.fore-  │        │  Signal Feed     │        │  run_calibrate  │
     │   cast()        │        │  Forecasts       │        │  run_benchmark  │
     └─────────────────┘        └──────────────────┘        └─────────────────┘
```

---

## Installation

```bash
# Core library
pip install financial-dynamics

# With live data (yfinance)
pip install financial-dynamics[data]

# Full dashboard (Streamlit + Plotly + yfinance)
pip install financial-dynamics[dashboard]

# Everything including dev tools
pip install financial-dynamics[all]
```

Or from source:

```bash
git clone https://github.com/jmiaie/financial-dynamics-model.git
cd financial-dynamics-model
pip install -e ".[all]"
```

---

## Quick Start

### Interactive Dashboard

```bash
streamlit run app.py
```

Load any ticker (SPY, QQQ, AAPL, BTC-USD) and watch regime classification in real-time. Charts update instantly, forecasts auto-compute, signals fire as regimes shift.

> **Try it now:** [financial-dynamics-model.streamlit.app](https://financial-dynamics-model.streamlit.app)

### Python API

```python
from financial_dynamics import FinancialDynamicsPipeline
from financial_dynamics.data_loader import fetch_ohlcv

# Fetch data & run pipeline
df = fetch_ohlcv("SPY", period="1y", interval="1d")
pipeline = FinancialDynamicsPipeline()
results = pipeline.run(df)

# Current regime + confidence
current = results["risk_adjusted_regime"].iloc[-1]
confidence = results["post_prob_CALM_TREND"].iloc[-1]
print(f"Regime: {current} ({confidence:.1%} confidence)")

# Forecast next 10 bars
forecast = pipeline.forecast(horizon=10)
print(f"Expected duration: {forecast.expected_duration:.1f} bars")
print(f"Path: {' → '.join(r.name for r in forecast.most_likely_path[:5])}")
```

### CLI

```bash
# Installed command (after pip install)
fdm SPY --period 1y --forecast 20
fdm AAPL --period 2y --interval 1d

# Or via module
python -m financial_dynamics SPY
python -m financial_dynamics --version

# Advanced scripts
python scripts/run_backtest.py --data historical.csv --labels regimes.csv --rolling
python scripts/run_calibration.py --output calibrated.yaml
python scripts/run_benchmark.py --config config/default.yaml
```

---

## Pipeline Architecture

<div align="center">

```
 ╔══════════════════════════════════════════════════════════════╗
 ║                     RAW OHLCV DATA                          ║
 ╚══════════════════════════╦═══════════════════════════════════╝
                            ▼
 ┌──────────────────────────────────────────────────────────────┐
 │  PHASE 0 │ Feature Engineering                              │
 │          │ 5D normalized: vol · trend · drawdown · corr · shock │
 └──────────────────────────┬───────────────────────────────────┘
                            ▼
 ┌──────────────────────────────────────────────────────────────┐
 │  PHASE 1 │ Centroid Classification                          │
 │          │ P(Sᵢ|Xₜ) = exp(−‖Xₜ − Cᵢ‖ / τ) / Z             │
 └──────────────────────────┬───────────────────────────────────┘
                            ▼
 ┌──────────────────────────────────────────────────────────────┐
 │  PHASE 2 │ Bayesian Markov Transitions                      │
 │          │ P_post = P_centroid × T[prev, :] / Z              │
 │          │ Dirichlet prior · online learning                 │
 └──────────────────────────┬───────────────────────────────────┘
                            ▼
 ┌──────────────────────────────────────────────────────────────┐
 │  PHASE 3 │ Temporal Stabilization                           │
 │          │ Hysteresis · persistence · majority vote          │
 └──────────────────────────┬───────────────────────────────────┘
                            ▼
 ┌──────────────────────────────────────────────────────────────┐
 │  PHASE 4 │ Risk Conditioning                                │
 │          │ Risk-Off confirmation · overextension · chop loop │
 └──────────────────────────┬───────────────────────────────────┘
                            ▼
 ╔══════════════════════════════════════════════════════════════╗
 ║              REGIME + CONFIDENCE + FORECAST                  ║
 ╚══════════════════════════════════════════════════════════════╝
```

</div>

---

## Market Regimes

<table>
<tr>
<th width="180">Regime</th>
<th>Characteristics</th>
<th width="60">Feature Signature</th>
<th width="140">Trading Signal</th>
</tr>
<tr>
<td>
  <strong>Calm Trend</strong><br>
  <sub>Low risk, directional</sub>
</td>
<td>Low volatility, strong uptrend, minimal drawdown, stable correlations</td>
<td><code>[0.1, 0.8, 0.05, 0.1, 0.1]</code></td>
<td>Long accumulation</td>
</tr>
<tr>
<td>
  <strong>Volatile Trend</strong><br>
  <sub>High energy, directional</sub>
</td>
<td>High volatility, directional momentum, recoveries from dips</td>
<td><code>[0.8, 0.7, 0.3, 0.5, 0.6]</code></td>
<td>Trend-following</td>
</tr>
<tr>
<td>
  <strong>Chop</strong><br>
  <sub>Low energy, directionless</sub>
</td>
<td>Low volatility, weak trend, mean-reverting, range-bound</td>
<td><code>[0.4, 0.2, 0.15, 0.3, 0.3]</code></td>
<td>Range trading</td>
</tr>
<tr>
<td>
  <strong>Risk-Off</strong><br>
  <sub>High risk, defensive</sub>
</td>
<td>High volatility, deep drawdowns, shock clusters, stress contagion</td>
<td><code>[0.9, 0.3, 0.8, 0.9, 0.9]</code></td>
<td>Hedging / defensive</td>
</tr>
</table>

---

## 3D Phase-Space Attractor Field

The interactive 3D visualization projects the 5D feature space onto 3 principal components, revealing the geometric structure of market regimes:

<table>
<tr>
<td width="50%">

**Structural Layers**
- Regime basins of attraction (convex hulls)
- 1.5&sigma; covariance ellipsoids
- Markov transition flow arrows
- PCA loading vectors (feature axes)
- Centroid markers with labels

</td>
<td width="50%">

**Dynamic Layers**
- Velocity-encoded trajectory (teal &rarr; red)
- Regime shift markers at transition points
- Stationary-distribution halos
- Volatility danger-zone isosurface
- Exponential-decay comet trail

</td>
</tr>
</table>

> **10 interactive toggles** — enable/disable each layer independently. Drag to rotate, scroll to zoom, hover for details.

---

## Configuration

All parameters in [`config/default.yaml`](config/default.yaml):

```yaml
features:
  volatility_span: 20          # EWMA lookback
  trend_window: 14             # Linear regression window
  drawdown_window: 60          # Rolling peak window
  normalization_method: zscore # zscore | minmax

regimes:
  temperature: 1.0             # Softmax temperature (lower = sharper)

transitions:
  prior_strength: 10.0         # Dirichlet prior concentration
  learning_rate: 0.05          # Bayesian update speed

stabilization:
  hysteresis_threshold: 0.15   # Min probability gap to flip
  min_persistence_bars: 5      # Bars before confirming change
  majority_vote_window: 10     # Rolling vote window

risk:
  riskoff_confirmation_count: 3  # Stressors needed for Risk-Off
  overextension_decay: 0.02      # Regime fatigue rate
```

---

## Testing

**275 tests** across **24 test files** — 98% coverage (90% minimum enforced in CI).

```bash
make test            # run full suite
make test-quick      # fast run
make coverage        # with HTML report
make lint            # ruff check
make typecheck       # mypy (zero errors)
make format          # auto-format
make all             # lint + typecheck + test + build
```

**Property-based testing** with [Hypothesis](https://hypothesis.readthedocs.io/) — 14 tests verify numerical invariants (probability normalization, transition matrix rows, feature bounds).

| Profile | Examples | Use case |
|---------|----------|----------|
| `dev` | 50 | Local iteration — fast feedback |
| `ci` | 500 | CI pipeline — thorough coverage |

```bash
HYPOTHESIS_PROFILE=ci pytest           # thorough run
pytest tests/test_phase0_features.py   # feature engineering
pytest tests/test_pipeline_integration.py  # end-to-end
pytest tests/test_stress.py            # numerical stability
pytest tests/test_visualization.py     # 3D rendering
```

**Code quality:** mypy type checking with zero errors, pre-commit hooks (ruff, formatting, type checks) for consistent quality on every commit.

<details>
<summary><strong>Test Coverage by Module</strong></summary>

| Module | Tests | Coverage |
|--------|------:|---------|
| Phase 0 — Features | 35 | Core pipeline |
| Phase 1 — Regimes | 20 | Core pipeline |
| Phase 2 — Transitions | 25 | Core pipeline |
| Phase 3 — Stabilization | 30 | Core pipeline |
| Phase 4 — Risk | 22 | Core pipeline |
| Pipeline Integration | 18 | End-to-end |
| Visualization | 16 | 2D + 3D |
| Signals | 12 | Detection |
| Stress / Numerical | 20 | Edge cases |
| Hypothesis (property) | 14 | Numerical invariants |
| Calibration + Others | 31 | Tooling |

</details>

---

## Project Structure

```
src/financial_dynamics/
├── pipeline.py                  # Orchestrator (batch + streaming)
├── types.py                     # Regime, FeatureVector, BarState
├── config.py                    # Typed config + YAML loader
├── phase0_features/             # EWMA vol, trend, drawdown, corr, shock
├── phase1_regimes/              # Softmax centroid classification
├── phase2_transitions/          # Dirichlet-Bayesian Markov learning
├── phase3_stabilization/        # Hysteresis, persistence, majority vote
├── phase4_risk/                 # Risk-Off confirmation, overextension
├── visualization/               # 2D/3D phase-space, dashboard, trajectory
├── calibration/                 # Centroid fitting, hyperparameter tuning
├── backtesting/                 # Rolling-window evaluation
├── benchmarks/                  # Baseline classifiers
├── forecasting/                 # k-step regime forecasts
├── signals/                     # Regime change / risk detection
├── data_loader.py               # yfinance integration
└── persistence/                 # State serialization

examples/
├── quickstart.py                # Basic regime classification
├── streaming.py                 # Real-time bar-by-bar processing
├── multi_asset.py               # Cross-asset stress detection
├── backtesting.py               # Accuracy evaluation with labeled data
├── forecasting.py               # k-step regime predictions
└── signals.py                   # Regime change & risk signal detection

app.py                           # Streamlit interactive dashboard
config/default.yaml              # All tunable parameters
```

---

## Examples

```bash
python examples/quickstart.py                          # Classify SPY regimes
python examples/quickstart.py --symbol AAPL --period 2y
python examples/streaming.py                           # Bar-by-bar streaming
python examples/multi_asset.py --refs QQQ,IWM,TLT,GLD # Cross-asset stress
python examples/backtesting.py                         # Accuracy on synthetic data
python examples/forecasting.py --horizon 20            # Regime forecast
python examples/signals.py --symbol QQQ                # Signal detection
```

---

## Use Cases

<table>
<tr>
<td width="50%">

**Hedge Funds & Prop Desks**
- Explainable regime filter for systematic strategies
- Position sizing by regime (scale vega/delta)
- Early warning for Risk-Off confirmation

**Quant Researchers**
- Modular, testable regime detection
- Learned transition matrices
- Multi-asset backtesting

</td>
<td width="50%">

**Risk Management**
- Transparent regime forecasts for stress tests
- Multi-asset contagion signals
- Real-time pre-shift warnings

**Fintech & Robo-Advisors**
- Client-friendly regime labels
- Explainable allocation shifts
- Automated defensive rebalancing

</td>
</tr>
</table>

---

## Deployment

<details>
<summary><strong>Streamlit Cloud (2 minutes)</strong></summary>

```bash
git push origin main
```
Then: [share.streamlit.io](https://share.streamlit.io) &rarr; Connect repo &rarr; Deploy

</details>

<details>
<summary><strong>Docker</strong></summary>

```bash
docker build -t financial-dynamics .
docker run -d -p 8501:8501 --restart unless-stopped financial-dynamics
```

</details>

<details>
<summary><strong>Custom Domain (fdm.micapai.com)</strong></summary>

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for Porkbun DNS + Streamlit Cloud setup.

</details>

---

## API Reference

<details>
<summary><strong>Core Classes</strong></summary>

| Class | Import | Description |
|-------|--------|-------------|
| `FinancialDynamicsPipeline` | `financial_dynamics` | Main orchestrator — `.run(df)` for batch, `.step(bar)` for streaming |
| `PipelineConfig` | `financial_dynamics.config` | Typed configuration with YAML loading |
| `Regime` | `financial_dynamics.types` | `IntEnum`: CALM_TREND, VOLATILE_TREND, CHOP, RISK_OFF |
| `BarState` | `financial_dynamics.types` | Per-bar state flowing through all 5 phases |
| `FeatureVector` | `financial_dynamics.types` | 5D normalized feature vector (vol, trend, drawdown, corr, shock) |
| `RegimeProbabilities` | `financial_dynamics.types` | Probability distribution with `.dominant`, `.confidence` |
| `SignalDetector` | `financial_dynamics.signals` | Detects regime changes, Risk-Off warnings, confidence drops |
| `RegimeForecast` | `financial_dynamics.forecasting` | k-step-ahead regime predictions from transition matrix |

</details>

<details>
<summary><strong>Key Methods</strong></summary>

| Method | Returns | Description |
|--------|---------|-------------|
| `pipeline.run(df)` | `DataFrame` | Batch process OHLCV DataFrame through all 5 phases |
| `pipeline.step(bar)` | `BarState` | Process a single bar (streaming mode) |
| `pipeline.forecast(horizon)` | `RegimeForecast` | k-step regime probability forecast |
| `pipeline.get_state_report()` | `StateReport` | Current bar count, warmup status, transition matrix |
| `pipeline.reset()` | `None` | Reset all internal state for a fresh run |
| `fetch_ohlcv(symbol)` | `DataFrame` | Load OHLCV data from Yahoo Finance |
| `fetch_multi_asset(symbol, refs)` | `DataFrame` | OHLCV + cross-asset reference close prices |
| `detector.check(bar_state)` | `list[Signal]` | Check for actionable signals on a bar |
| `save_state(pipeline, path)` | `None` | Serialize pipeline state to JSON |
| `load_state(path)` | `Pipeline` | Restore pipeline from saved state |

</details>

<details>
<summary><strong>Output Columns</strong></summary>

`pipeline.run(df)` returns a DataFrame with these columns:

| Column | Type | Description |
|--------|------|-------------|
| `feat_volatility` | float | Normalized EWMA volatility |
| `feat_trend` | float | Normalized trend strength |
| `feat_drawdown` | float | Normalized drawdown pressure |
| `feat_corr_stress` | float | Normalized correlation stress |
| `feat_shock` | float | Normalized shock intensity |
| `raw_prob_{REGIME}` | float | Phase 1 centroid probabilities |
| `post_prob_{REGIME}` | float | Phase 2 Bayesian posterior probabilities |
| `stabilized_regime` | str | Phase 3 temporally stabilized regime |
| `risk_adjusted_regime` | str | Phase 4 final regime assignment |
| `risk_overlays` | dict | Risk conditioning flags applied |

</details>

---

## Documentation

| Resource | Description |
|----------|-------------|
| [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) | Streamlit Cloud, Docker, custom domain |
| [STREAMLIT_QUICK_START.md](STREAMLIT_QUICK_START.md) | Run the dashboard locally |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Development setup, code style, architecture |
| [CHANGELOG.md](CHANGELOG.md) | Release notes and version history |
| [config/default.yaml](config/default.yaml) | All tunable parameters |

---

## Contributing

Contributions welcome. Please open an issue first to discuss major changes.

```bash
git clone https://github.com/jmiaie/financial-dynamics-model.git
cd financial-dynamics-model
pip install -e ".[all]"
pre-commit install
make all                # lint + typecheck + test + build
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for code style, architecture guide, and testing conventions.

---

## License

[MIT](LICENSE) — Jeff Milam & [Micap.AI](https://micap.ai)

---

<div align="center">

**Built by [Micap.AI](https://micap.ai)**

<sub>Python · NumPy · Pandas · SciPy · scikit-learn · Streamlit · Plotly · yfinance · Bayesian inference · Markov chains</sub>

<br>

[![GitHub stars](https://img.shields.io/github/stars/jmiaie/financial-dynamics-model?style=social)](https://github.com/jmiaie/financial-dynamics-model)

</div>
