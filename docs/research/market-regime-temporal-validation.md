# Market Regime Temporal Validation

## 1. Research Question
Can the Financial Dynamics Model recover synthetic regime structure and characterize historical market states under chronology-safe validation without overstating real-world predictive certainty?

## 2. Economic Hypothesis
If the feature pipeline captures persistent differences in volatility, trend, drawdown pressure, cross-asset stress, and shock intensity, then inferred regimes should separate synthetic states with labeled metrics and historical states with distinct forward return and risk distributions.

## 3. Model Overview
The model maps normalized features into centroid-based regime probabilities, updates them with a Bayesian transition model, stabilizes noisy transitions, and applies risk overlays before emitting the final regime.

## 4. Data
- Synthetic validation uses fixture/generated OHLCV with known regime labels.
- Historical validation should use a configurable small universe such as SPY, QQQ, IWM, TLT, GLD, and optionally BTC-USD.
- Live downloads pass through chronology validation: monotonic index, duplicate rejection, explicit missing-data handling, and no future backfill.

## 5. Feature Construction
Features are generated from rolling or exponentially weighted information available at each timestamp: volatility, trend strength, drawdown pressure, correlation stress, and shock intensity.

## 6. Decision-Time Information
Temporal evaluation uses only information available strictly before or at the prediction timestamp. Formation data fits centroids, validation data tunes hyperparameters, and the final test window is evaluated once with frozen configuration.

## 7. Synthetic Validation
Synthetic regime-recovery results should be labeled explicitly as synthetic. Relevant metrics include accuracy, balanced accuracy, per-class precision/recall/F1, macro F1, confusion matrix, log loss, multiclass Brier score, calibration tables, and sample counts.

## 8. Historical Validation
Historical validation should not invent ground-truth CALM_TREND / CHOP / RISK_OFF labels. Instead, evaluate inferred regimes by forward returns, realized volatility, downside volatility, positive-return frequency, tail quantiles, duration, and transition behavior.

## 9. Temporal Split Design
Use `TemporalSplit` to create non-overlapping formation / validation / test windows with monotonic boundaries. The default split is 60/20/20, but ratios are configurable.

## 10. Walk-Forward Methodology
Use `TemporalValidator.walk_forward()` for genuine prior-only evaluation. In expanding mode, each step fits on all prior data and evaluates the next unseen block. Rolling mode is supported when a fixed training window is preferred.

## 11. Benchmarks
Compare against the same untouched out-of-sample windows using:
- persistence baseline
- volatility-bucket baseline
- trend + volatility grid baseline
- Gaussian mixture baseline

These baselines must be fit only on prior windows and must not be selected or tuned on the final test period.

## 12. Evaluation Metrics
- Synthetic: accuracy, balanced accuracy, macro F1, confusion matrix, log loss, Brier score, calibration diagnostics, sample counts.
- Historical: forward return means/medians, realized vol, downside vol, positive-return frequency, tail quantiles, duration, self-transition rates, transition matrices.

## 13. Results
Results pending reproducible historical run. Synthetic outputs can be summarized once generated with the chronology-safe utilities.

## 14. Sensitivity Analysis
Use `SensitivityAnalyzer` to sweep temperature, transition learning rate, hysteresis threshold, persistence settings, feature windows, and centroid perturbations. Report median performance, dispersion, and failure regions rather than only best-case outcomes.

## 15. Limitations
- Synthetic labels are abstractions, not market truth.
- Historical regimes may not align cleanly with discrete categories.
- Temporal stability in one sample does not guarantee transportability to future regimes.

## 16. Failure Modes
- Structural breaks or sudden policy shifts
- Feature drift and normalization drift
- Regime collapse into one persistent state
- Over-stabilization masking genuine turning points
- Benchmark performance dominating during simple trend/volatility episodes

## 17. Model Risk
Key model risks include label abstraction, nonstationarity, structural breaks, drift, arbitrary regime count, centroid and hyperparameter sensitivity, persistence bias from stabilization, sampling-frequency dependence, calibration drift, survivorship/universe effects, synthetic-real gap, repeated-testing overfit, multiple-testing risk, and the gap between economic significance and tradable alpha. Trading-overlay costs should be modeled separately.

## 18. Conclusions
The upgraded workflow is designed to support defensible research claims by separating synthetic regime recovery from historical regime characterization and by reserving final out-of-sample periods for untouched evaluation.

## 19. Reproduction Instructions
```python
from financial_dynamics.calibration import TemporalCalibrator, TemporalSplit, TemporalValidator
from financial_dynamics.backtesting import historical_regime_statistics

split = TemporalSplit.from_frame(df, formation_ratio=0.6, validation_ratio=0.2, test_ratio=0.2)
calibration = TemporalCalibrator().calibrate(df, labels, split=split)
walk_forward = TemporalValidator().walk_forward(df, labels, initial_train_size=252, step_size=21)
historical = historical_regime_statistics(df["close"], calibration.final_test_result.pipeline_results["risk_adjusted_regime"])
```

Store small reproducible outputs under `results/synthetic/`, `results/temporal_validation/`, `results/walk_forward/`, `results/benchmarks/`, and `results/historical_regimes/` with metadata covering config version, time period, universe, methodology, timestamp, and whether the artifact is synthetic or historical.
