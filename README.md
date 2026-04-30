# Financial Dynamics Model

A production-grade, transparent Bayesian system-dynamics pipeline for market regime classification. Transforms raw OHLCV data into explainable regime probabilities for quantitative trading and risk management.

**Author:** Jeff Milam & Micap AI LLC

---

## 🎯 Key Highlights

✅ **80.6% accuracy** on calibrated datasets (vs 57.8% baseline)  
✅ **Fully explainable** — no black-box neural networks  
✅ **Production-ready** — 219 unit tests, live deployment verified  
✅ **Interactive demo** — Streamlit app with live data, forecasts, signals  
✅ **Multi-asset capable** — cross-asset correlation stress detection  
✅ **Regime forecasting** — k-step-ahead probabilities via matrix exponentiation  

---

## 🚀 Quick Start

### Interactive Dashboard (Recommended)

```bash
pip install -r requirements.txt
streamlit run app.py
```

Then load any ticker (SPY, QQQ, AAPL, etc.) and watch regime classification in real-time. Charts update instantly, forecasts auto-compute, signals fire as regimes change.

**Deploy to Streamlit Cloud in 2 minutes:**  
See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)

### Python API

```python
from financial_dynamics.pipeline import FinancialDynamicsPipeline
from financial_dynamics.data_loader import fetch_ohlcv

# Fetch data
df = fetch_ohlcv("SPY", period="1y", interval="1d")

# Run pipeline
pipeline = FinancialDynamicsPipeline()
results = pipeline.run(df)

# Get current regime
current = results["risk_adjusted_regime"].iloc[-1]
confidence = results["post_prob_CALM_TREND"].iloc[-1]
print(f"Current: {current} (confidence: {confidence:.1%})")

# Forecast next 10 bars
forecast = pipeline.forecast(horizon=10)
print(f"Expected duration: {forecast.expected_duration:.1f} bars")
print(f"Most likely path: {[r.name for r in forecast.most_likely_path[:5]]}")
```

### CLI Entry Point

```bash
# Run on live data
python scripts/run_pipeline.py --symbol SPY --period 1y --interval 1d

# Backtest
python scripts/run_backtest.py --data historical.csv --labels regimes.csv --rolling

# Calibrate model
python scripts/run_calibration.py --output calibrated.yaml

# Benchmark vs baselines
python scripts/run_benchmark.py --config config/default.yaml
```

---

## 📊 Pipeline Architecture

```
Raw OHLCV
    ↓
[Phase 0] Feature Engineering
  → 5D normalized features (volatility, trend, drawdown, correlation stress, shock)
    ↓
[Phase 1] Centroid Classification
  → Softmax(-distance / temperature) → regime probabilities
    ↓
[Phase 2] Bayesian Markov Transitions
  → Dirichlet-prior transition matrix updates
  → P_post = P_centroid × T[prev, :] / Z
    ↓
[Phase 3] Temporal Stabilization
  → Hysteresis + persistence + majority-vote filters
    ↓
[Phase 4] Risk Conditioning
  → Risk-Off confirmation, overextension suppression, chop-loop breaking
    ↓
Final Regime + Confidence
```

---

## 📈 Market Regimes

| Regime | Characteristics | Signal |
|--------|-----------------|--------|
| **Calm Trend** | Low vol, strong uptrend, stable | ✓ Long accumulation |
| **Volatile Trend** | High vol, directional move, recoveries | ✓ Trend-following |
| **Chop** | Low vol, mean-reverting, directionless | ✓ Range trading |
| **Risk-Off** | High vol, deep drawdowns, shock clusters | ⚠️ Hedging, defensive |

---

## 🏗️ Project Structure

```
src/financial_dynamics/
├── pipeline.py                    # Top-level orchestrator (batch + streaming)
├── types.py                       # Regime, FeatureVector, RegimeProbabilities, BarState
├── config.py                      # PipelineConfig + YAML loader
├── phase0_features/               # Feature engineering (5D)
├── phase1_regimes/                # Centroid-based classification
├── phase2_transitions/            # Markov transition learning
├── phase3_stabilization/          # Hysteresis, persistence, majority-vote
├── phase4_risk/                   # Risk overlays
├── visualization/                 # Dashboard, phase-space, trajectory
├── calibration/                   # Centroid fitting, hyperparameter tuning
├── backtesting/                   # Evaluator, metrics, rolling windows
├── benchmarks/                    # Baseline classifiers
├── data_loader.py                 # yfinance integration (single + multi-asset)
├── forecasting/                   # k-step forecasts, stationary distribution
├── signals/                       # Signal detection
└── persistence/                   # State serialization

scripts/
├── run_pipeline.py                # CLI entry point
├── run_backtest.py                # Backtesting
├── run_calibration.py             # Calibration + tuning
├── run_benchmark.py               # Benchmark vs baselines
└── generate_synthetic_data.py     # Synthetic OHLCV generator

tests/
├── test_phase*.py                 # Unit tests (219 total)
├── test_calibration.py
├── test_signals.py
├── test_forecasting.py
└── ...

config/
└── default.yaml                   # All tunable parameters

app.py                             # Streamlit interactive dashboard
DEPLOYMENT_GUIDE.md                # Deployment instructions
```

---

## 🧪 Testing

```bash
# Run all 219 tests
pytest tests/ -v

# Specific suite
pytest tests/test_phase0_features.py -v
pytest tests/test_signals.py -v
pytest tests/test_calibration.py -v
```

All tests pass with 100% coverage of core pipeline logic.

---

## ⚙️ Configuration

All parameters in `config/default.yaml`. Override as needed:

```yaml
features:
  volatility_span: 20              # EWMA span
  trend_window: 14                 # Linear regression
  drawdown_window: 60              # Rolling peak
  normalization_method: zscore     # or minmax
  feature_weights: [1.0, 1.0, ...]

regimes:
  temperature: 1.0                 # Softmax temperature
  centroids: {...}

transitions:
  prior_strength: 10.0
  learning_rate: 0.05

stabilization:
  hysteresis_threshold: 0.15
  min_persistence_bars: 5
  majority_vote_window: 10

risk:
  drawdown_threshold: 0.5
  correlation_stress_threshold: 0.6
  shock_threshold: 0.7
  riskoff_confirmation_count: 3
```

---

## 📱 Interactive Dashboard

**Live Streamlit app** with:
- Real-time price chart with regime-colored bands
- Stacked area chart of regime probabilities
- Transition matrix heatmap
- 5D feature time series
- Current regime badge + confidence score
- k-step regime forecast
- Signal feed (regime changes, Risk-Off warnings, confidence drops, stabilization)
- Data inspector (recent pipeline output)

**Deploy instantly:**
```bash
streamlit run app.py              # Local
# or to Streamlit Cloud (see DEPLOYMENT_GUIDE.md)
```

---

## 🎓 Use Cases

**Hedge Funds & Prop Traders:**
- Explainable regime filter for systematic strategies
- Position sizing ladder (scale vega/delta by regime)
- Early warning system for Risk-Off confirmation

**Quant Researchers:**
- Modular, testable regime detection component
- Learned transition matrices for strategy development
- Backtestable on multi-asset datasets

**Risk Managers:**
- Transparent regime forecasts for stress testing
- Multi-asset contagion signals
- Real-time early warnings before regime shifts

**Fintech Platforms & Robo-Advisors:**
- Client-friendly regime classification
- Explainable allocation shifts
- Automated defensive rebalancing

---

## 📦 Deployment

**Streamlit Cloud (2 minutes):**
```bash
git push origin main
# → https://share.streamlit.io → Connect repo → Deploy
```

**Vercel + Custom Domain:**
See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)

**Docker:**
```bash
docker build -t financial-dynamics .
docker run -p 8501:8501 financial-dynamics
```

---

## 📚 Documentation

- `DEPLOYMENT_GUIDE.md` — How to deploy (Streamlit Cloud, Vercel, Docker)
- `scripts/run_pipeline.py --help` — CLI options
- `tests/` — Usage examples in unit tests
- `config/default.yaml` — All tunable parameters

---

## License

MIT

---

**Author:** Jeff Milam & Micap AI LLC

Built with Python, NumPy, Pandas, SciPy, scikit-learn, Streamlit, Plotly, yfinance, Bayesian inference, Markov chains, and system dynamics.
