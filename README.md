# Ominnow Private

**Author:** Jeff Milam & Micap AI LLC

## Financial Dynamics Model

A system dynamics model applied to financial time series. Transforms raw OHLCV data through a 5-phase pipeline to produce a structurally informed probability distribution over four market regimes.

### Market Regimes

- **Calm Trend** -- Low volatility, strong directional movement
- **Volatile Trend** -- High volatility with directional bias
- **Chop** -- Directionless, mean-reverting price action
- **Risk-Off** -- Systemic stress with drawdown and shock confluence

### Pipeline Architecture

```
OHLCV Bar
  -> Phase 0: Feature Engineering (5D vector: volatility, trend, drawdown, correlation stress, shock)
  -> Phase 1: Centroid-Based Regime Classification (softmax probability mapping)
  -> Phase 2: Markov Transition Learning (Bayesian Dirichlet-updated 4x4 matrix)
  -> Phase 3: Temporal Stabilization (hysteresis + persistence + majority vote)
  -> Phase 4: Risk Conditioning (Risk-Off confirmation, overextension rebalancing, chop suppression)
  -> Final Output: Risk-adjusted regime assignment with probability distribution
```

### Usage

```bash
# Install dependencies
pip install -r requirements.txt

# Run on synthetic data
python scripts/run_pipeline.py

# Run tests
pip install -r requirements-dev.txt
python -m pytest tests/ -v
```

### Project Structure

```
src/financial_dynamics/
    types.py              # Regime enum, FeatureVector, RegimeProbabilities, BarState
    config.py             # Typed config dataclasses + YAML loader
    pipeline.py           # Top-level orchestrator (batch + streaming)
    phase0_features/      # EWMA volatility, trend strength, drawdown, kurtosis, shock
    phase1_regimes/       # Centroid softmax probability mapping
    phase2_transitions/   # Bayesian Dirichlet transition matrix
    phase3_stabilization/ # Hysteresis, persistence, majority vote filters
    phase4_risk/          # Risk-Off confirmation, overextension, chop suppression
    visualization/        # Phase-space projection, trajectory, vector field, dashboard
```
