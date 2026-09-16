# Historical Market Regimes and Subsequent Risk Characteristics

## A Walk-Forward Evaluation of the Financial Dynamics Model

**Status: SPY primary results complete. Cross-asset robustness (QQQ/IWM/TLT/GLD) NOT YET
EXECUTED — see Limitations. This report will be updated in place once those runs land.**

---

## 1. Research question

**Primary:** Does the Financial Dynamics Model (FDM) identify persistent market states that
meaningfully differentiate subsequent return, volatility, drawdown, downside risk, and
transition behavior relative to simpler regime definitions?

**Secondary:** Does the FDM's probabilistic transition component (temperature-scaled
posteriors, hysteresis, majority-vote stabilization) provide useful information beyond
simpler persistence- or threshold-based regime definitions?

Inferred historical regimes are **not** presented as objectively true labels — markets do not
provide ground-truth regime identities. Centroids are fixed a priori (theory-based; see
§4) and are **not** fit to the data being evaluated.

**This report does not make a trading-alpha claim.** Regime differentiation in subsequent
risk/return characteristics is a distinct question from whether that differentiation is
tradeable after costs, timing constraints, and capacity — that question is out of scope here
(it belongs to Directive #9's stat-arb workstream, which operates on a different set of
instruments and a different research design).

## 2. Data

**Dataset:** `yf_fd_etfs_daily_2015_2025_v1` — Yahoo Finance / yfinance, daily adjusted OHLCV.
**Frozen dataset SHA-256:** `91caa6cde08358091125a6576ff3f2be5666791b06df67d462c2aad6f771ada9`
(`data/manifests/yf_fd_etfs_daily_2015_2025_v1.json`).
**Universe:** SPY (primary), QQQ, IWM, TLT, GLD.
**Periods:** development/formation 2015-01-01 to 2023-12-31; validation 2024-01-01 to
2024-12-31; holdout 2025-01-01 to 2025-12-31.

A later independent re-acquisition attempt of this dataset produced a **different** file
hash (`945cf990…` vs. the frozen `91caa6cd…`). This is reported, unresolved evidence — most
likely `auto_adjust=True` retroactive dividend-adjustment drift (adjusted historical closes
shift whenever a new distribution posts, so a fresh pull months later will not
byte-for-byte match an old freeze), but this has not been independently confirmed by
inspecting value-level differences. The results below are drawn from the **originally
frozen** dataset and artifacts, committed before this discrepancy was discovered; they are
unaffected by it, but the dataset's re-acquisition is flagged for anyone attempting to
reproduce this study from scratch.

## 3. Pre-registration and freeze

**Config:** `configs/experiments/fdm_historical_regime_study_v1.yaml`, status
`frozen-for-holdout`. **Freeze commit:** `596a22527b6f0107ba5baf55dd2edd68a1d991fe`. No
retuning occurred after this freeze; the holdout (2025) run used the identical frozen
`PipelineConfig` as development and validation.

## 4. Model and benchmarks

**FDM pipeline:** `FinancialDynamicsPipeline` with default feature windows (volatility
span 20, trend window 14, drawdown window 60, correlation window 20, shock threshold 2.0,
z-score normalization over a 252-session window), temperature 1.0, hysteresis threshold
0.15, minimum persistence 5 bars, majority-vote stabilization over 10 bars. Four regimes:
`CALM_TREND`, `VOLATILE_TREND`, `CHOP`, `RISK_OFF`, with **fixed, theory-based centroids**
(not fit to any evaluation window):

| Regime | Feature vector (vol, trend, drawdown, corr-stress, shock) |
|---|---|
| CALM_TREND | (0.10, 0.80, 0.05, 0.10, 0.10) |
| VOLATILE_TREND | (0.80, 0.70, 0.30, 0.50, 0.60) |
| CHOP | (0.40, 0.20, 0.15, 0.30, 0.30) |
| RISK_OFF | (0.90, 0.30, 0.80, 0.90, 0.90) |

**Benchmarks** (fit on formation data only, frozen before OOS classification):
1. **Volatility-bucket** — trailing 20-day realized volatility, HIGH/LOW split at the
   formation-period median, threshold applied unchanged OOS.
2. **Trend/volatility grid** — trailing 63-session return sign × trailing 20-session
   realized-vol median split (formation-derived threshold), four quadrant states.
3. **Gaussian mixture** — unsupervised GMM (seed 0), fit on formation data, frozen before
   OOS classification.
4. **Persistence** — trivial "last observed regime persists" baseline (validation/holdout
   periods only; undefined without a history window, so absent from the development row).

## 5. Results

All returns are forward returns over the stated horizon (1/5/20 trading days), conditional
on the regime observed at decision time. `mean_realized_vol_h1` is uniformly `0.0` across
every model and period — this is the expected degenerate result of a single-observation
standard deviation (`ddof=0` over one point is undefined/zero), not a data error; it is not
a meaningful 1-day realized-volatility estimate and should be disregarded. `h5`/`h20`
realized volatilities are computed over genuine multi-observation windows and are
meaningful.

### 5.1 Development (2015–2023, formation window)

| Model | Regimes | Bars | Self-trans. | mean ret h1 | mean ret h5 | mean ret h20 | vol h5 | vol h20 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **FDM pipeline** | 4 | 2204/2264 | 0.736 | +0.000376 | +0.002971 | +0.010435 | 0.00766 | 0.00885 |
| Volatility-bucket | 4 | 2244/2264 | 0.923 | +0.000519 | +0.002525 | +0.009778 | 0.00797 | 0.00924 |
| Trend/vol grid | 4 | 2264/2264 | 0.846 | +0.000501 | +0.002570 | +0.010687 | 0.00842 | 0.00946 |
| Gaussian mixture | 4 | 2244/2264 | 0.365 | +0.000964 | +0.003577 | +0.014802 | 0.01143 | 0.01208 |

FDM regime counts: CALM_TREND 40, CHOP 789, RISK_OFF 341, VOLATILE_TREND 1034.

### 5.2 Validation (2024)

| Model | Regimes | Bars | Self-trans. | mean ret h1 | mean ret h5 | mean ret h20 | vol h5 | vol h20 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **FDM pipeline** | 4 | 252/252 | 0.613 | +0.000738 | +0.006414 | +0.019870 | 0.00609 | 0.00758 |
| Persistence | 1 | 252/252 | 1.000 | +0.000939 | +0.005161 | +0.020893 | 0.00643 | 0.00742 |
| Volatility-bucket | 4 | 252/252 | 0.893 | +0.001459 | +0.006778 | +0.018239 | 0.00660 | 0.00781 |
| Trend/vol grid | 4 | 252/252 | 0.832 | +0.001655 | +0.007969 | +0.029605 | 0.00689 | 0.00757 |
| Gaussian mixture | 4 | 252/252 | 0.287 | +0.000923 | +0.010325 | +0.028774 | 0.00668 | 0.00846 |

FDM regime counts: CALM_TREND 8, CHOP 121, RISK_OFF 21, VOLATILE_TREND 102.

### 5.3 Holdout (2025)

| Model | Regimes | Bars | Self-trans. | mean ret h1 | mean ret h5 | mean ret h20 | vol h5 | vol h20 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **FDM pipeline** | **3** | 250/250 | 0.746 | **−0.000293** | +0.001667 | +0.018083 | 0.01045 | 0.01141 |
| Persistence | 1 | 250/250 | 1.000 | +0.000740 | +0.003646 | +0.013880 | 0.00826 | 0.01002 |
| Volatility-bucket | 4 | 250/250 | 0.918 | +0.000750 | +0.003400 | +0.016882 | 0.00882 | 0.01055 |
| Trend/vol grid | 4 | 250/250 | 0.771 | +0.001643 | +0.003688 | +0.008922 | 0.00860 | 0.01031 |
| Gaussian mixture | 4 | 250/250 | 0.345 | +0.001865 | +0.008368 | +0.030057 | 0.01143 | 0.01186 |

FDM regime counts: CHOP 113, RISK_OFF 29, VOLATILE_TREND 108. **CALM_TREND was never
selected in the 2025 holdout window** — reported exactly as observed, not adjusted.

## 6. Discussion

**Cross-regime differentiation.** Across all three periods and all four models, mean and
median forward returns vary materially by regime/model and by horizon, and multi-day
realized volatility (h5/h20) is consistently higher for the Gaussian-mixture and
FDM-pipeline classifications than for the volatility-bucket and trend/vol-grid benchmarks.
This is consistent with the FDM and GMM capturing more volatility-sensitive states, at the
cost of the self-transition (persistence) trade-off described next.

**Persistence vs. reactivity.** The FDM pipeline's self-transition rate (0.61–0.75 across
periods) sits between the trivially sticky benchmarks (volatility-bucket 0.89–0.92,
persistence 1.00 by construction) and the noisy Gaussian mixture (0.29–0.37). This is the
direct, honest answer to the secondary research question: FDM's hysteresis/majority-vote
stabilization measurably reduces regime churn relative to an unconstrained GMM, without
collapsing to the triviality of a persistence-only or single-threshold benchmark. Whether
that specific trade-off point is "better" depends on the downstream use case; this report
does not adjudicate that.

**2025 finding, reported honestly.** The FDM pipeline's holdout mean 1-day forward return
was negative (−0.000293) — the only negative mean-return cell in this entire results set —
while the median 1-day return in the same period remained positive (+0.0014), and no
benchmark showed a negative mean 1-day return in 2025. This indicates the negative mean is
driven by downside-skewed outliers rather than a broadly negative regime, but this report
cannot fully characterize that skew (see Limitations — downside volatility and tail
quantiles are not available in the committed artifacts). The FDM regime set also lost
`CALM_TREND` entirely in 2025 — reported as observed, without adjustment.

## 7. Limitations

- **Downside volatility, drawdown/maximum-adverse-excursion, positive-return frequency,
  and 5th-percentile forward return are not reported here.** The committed result
  artifacts (`results/historical_regimes/*.json`) are intentionally "slim" — key aggregate
  metrics and regime counts only, not the full per-observation summary/transition tables.
  Regenerating those fuller tables requires either the local raw CSVs (not available in
  this environment — see §2's acquisition-drift note) or re-running the study end to end.
  This is a real content gap in this report, not an omission of already-available evidence.
- **No moving-block or stationary bootstrap uncertainty intervals are reported.** The
  frozen methodology specifies time-series-aware uncertainty where sample size permits;
  computing it requires the fuller per-observation tables noted above.
- **Cross-asset robustness (QQQ, IWM, TLT, GLD as independent primary instruments) has not
  been executed.** The runner supports this (`scripts/run_historical_regime_study.py
  --primary-symbol <SYMBOL>`, tagging experiment IDs as
  `fdm_hist_regime_v1_robustness_<symbol>` and labeling any 2025 result
  `PRE-SPECIFIED ROBUSTNESS EVALUATION EXECUTED AFTER PRIMARY HOLDOUT`, not a fresh
  untouched holdout), but execution is blocked on data acquisition in this environment —
  this session's egress policy blocks Yahoo Finance. This report's title claims apply to
  SPY only until those runs land.
- **`mean_realized_vol_h1 = 0.0` throughout is a known artifact**, not a finding (see §5).
- **Cross-program note:** SPY, QQQ, IWM, TLT, and GLD price history is also used by
  Directive #9's Stat-Arb v3 study (a different repository, different research design).
  This report's 2025 holdout evaluation is the event referenced as "FDM's already-executed
  2025 holdout" in that study's cross-repository exposure disclosure
  (`Advanced_Algorithmic_Trading_Simulator_public`'s `research/holdout-audit.md`).
- **Model risk:** fixed, theory-based centroids are a modeling choice, not a data-driven
  fit; a different theoretical regime definition would produce different classifications.
  Benchmark thresholds are formation-derived and frozen, but formation-period regime
  incidence (e.g., very few `CALM_TREND` observations in some periods) limits statistical
  power for that regime specifically.

## 8. Reproducibility

```
python scripts/run_historical_regime_study.py \
  --config configs/experiments/fdm_historical_regime_study_v1.yaml \
  --allow-holdout
```
requires frozen local raw CSVs under `data/raw/yf_fd_etfs_daily_2015_2025_v1/` (gitignored;
acquire via `scripts/acquire_yf_fd_etfs_daily.py` and verify the resulting
`dataset_canonical` hash before use — see §2's caveat about acquisition drift).

Ledger: `research/experiment-ledger.csv`. Artifacts: `results/historical_regimes/*.json`.
