# Historical Market Regimes and Subsequent Risk Characteristics

## A Walk-Forward Evaluation of the Financial Dynamics Model

**Status:** D10-A publication pack, draft, for independent review. Repackages already-accepted,
already-computed D9-A evidence for external readers. Performs no new empirical work. See
`SOURCE-GATE.md` for the full provenance record and `D10-STATUS.md` for pack status.

---

## Abstract

We evaluate whether the Financial Dynamics Model (FDM) — a Bayesian regime-classification
pipeline using fixed, theory-based centroids over five market features (volatility, trend
strength, drawdown pressure, correlation stress, shock intensity) — identifies market states that
meaningfully differentiate **subsequent risk characteristics**: forward-return dispersion,
realized and downside volatility, tail risk, adverse drawdown, and self-transition persistence.
This is explicitly **not** a directional-forecast-accuracy or trading-alpha claim; regime
differentiation in subsequent risk/return characteristics is a distinct question from whether
that differentiation is tradeable after costs, and that question is out of scope here. The
primary evaluation uses SPY over three walk-forward periods — development/formation
(2015–2023), validation (2024), and a historical evaluation of 2025 — against four benchmark
classifiers (persistence, volatility-bucket, trend/volatility grid, Gaussian mixture). A
secondary, explicitly post-primary robustness evaluation repeats the same frozen methodology on
QQQ, IWM, TLT, and GLD (plus a second SPY run) on a separately acquired dataset that is disclosed
as not bit-identical to the primary dataset for four of the five symbols. The FDM pipeline shows
a self-transition rate that sits consistently between the sticky simple benchmarks and a noisy
Gaussian-mixture baseline across all three periods, and its 2025 evaluation result is the only model whose
mean 1-day forward return was negative in that period — a finding whose 90% block-bootstrap
confidence interval, examined in the robustness runs, does not exclude zero for the small-sample
`RISK_OFF` regime specifically. All reported numbers trace to committed JSON artifacts; the
mapping is in `RESULT-SOURCE-MAP.md`.

## 1. Data and methodology

### 1.1 Dataset

Primary results use `yf_fd_etfs_daily_2015_2025_v1` (Yahoo Finance / yfinance 1.7.0, daily
adjusted OHLCV), frozen 2026-09-16, `dataset_canonical` sha256
`91caa6cde08358091125a6576ff3f2be5666791b06df67d462c2aad6f771ada9`
(`data/manifests/yf_fd_etfs_daily_2015_2025_v1.json`). Universe: SPY (primary), QQQ, IWM, TLT,
GLD. A later re-acquisition attempt within the same working session produced a different hash for
four of the five symbols (SPY, QQQ, IWM, TLT); GLD alone matched byte-for-byte, consistent with —
but not proven to be caused by — dividend-adjustment recomputation on retrieval, since the
original v1 raw payload for the four affected symbols is confirmed unrecoverable and no
byte-level diff against it is possible. This re-acquired data is used **only** for the robustness
section (§3) under a separate dataset ID, `yf_fd_etfs_daily_2015_2025_v2`
(`dataset_canonical` sha256 `94ea2886772afc7adcbf070bf1563a59295c1e7b1f837e157dfe5880c5b12582`),
and never substitutes for or is merged into the primary SPY-v1 result.

### 1.2 Periods

| Period | Dates | Role |
|---|---|---|
| Development / formation | 2015-01-01 – 2023-12-31 | Fits benchmark thresholds; freezes configuration |
| Validation | 2024-01-01 – 2024-12-31 | Evaluated before the final freeze |
| Holdout | 2025-01-01 – 2025-12-31 | **Historical evaluation**, run once after the freeze |

The 2025 period is referred to throughout this paper as **historical evaluation**, not
"untouched" or "clean" holdout: the data existed and was in principle inspectable before the
2026-09-16 freeze date. See `SOURCE-GATE.md` §12.

### 1.3 Model

`FinancialDynamicsPipeline` (`src/financial_dynamics/pipeline.py`) classifies each session into
one of four regimes — `CALM_TREND`, `VOLATILE_TREND`, `CHOP`, `RISK_OFF` — using fixed,
theory-based centroids over five z-scored features (252-session normalization window; feature
windows: volatility span 20, trend window 14, drawdown window 60, correlation window 20, shock
threshold 2.0). Classification uses temperature-scaled posteriors (temperature 1.0), hysteresis
(threshold 0.15), a minimum-persistence floor (5 bars), and majority-vote stabilization (10-bar
window); seed 0. Centroids are **not fit to any evaluation window** — they are a modeling choice,
not a data-driven fit (see §6, Limitations).

### 1.4 Benchmarks

All benchmark thresholds are fit on formation-period data only and frozen before out-of-sample
classification (`src/financial_dynamics/benchmarks/baselines.py`):

- **Persistence** (`PersistenceClassifier`) — trivially repeats the last observed regime; defined
  only where a history window exists, so absent from the development row.
- **Volatility-bucket** (`VolatilityBucketClassifier`) — trailing 20-day realized-volatility
  quartiles from formation, mapped to the four regime labels in increasing-volatility order.
- **Trend/volatility grid** (`TrendVolGridClassifier`) — trailing 14-session return sign ×
  20-session realized-vol median split (both formation-derived), four quadrant states.
- **Gaussian mixture** — unsupervised GMM (seed 0), fit on formation data, frozen before OOS
  classification.

### 1.5 Metrics

`historical_regime_statistics` (`src/financial_dynamics/backtesting/metrics.py:269`) computes,
per (regime, forward horizon ∈ {1, 5, 20} trading days) group: mean and median forward return,
realized volatility, downside volatility, positive-return frequency (the fraction of
**occurrences** whose horizon-level compounded forward return was positive — corrected
2026-09-17; see §4.4), 5th/25th-percentile tail returns, mean and worst intra-horizon adverse
drawdown, mean/median regime duration, and self-transition rate.

**Important aggregation caveat, applies everywhere in this paper a `mean ret h*`/`ret h*`/`median
ret h*` column appears (§2's primary tables *and* §3's robustness table alike — both are read from
the same `key_metrics.mean_return_h*`/`median_return_h*` fields).** These figures are **unweighted
averages, across a period's observed regimes, of each regime's own mean (resp. median) forward
return** — not a bar-level statistic over the raw day-by-day return series, and not weighted by
how many days each regime was observed. A regime with 5 observed bars and one with 500 contribute
equally to that average. This limits how far a mean-vs-median comparison at this level can be
pushed: the two columns are computed the same way but over each regime's mean vs. median
respectively, not the mean and median of one common underlying distribution, so their difference
does not by itself indicate distributional skew. (The per-regime `summary_records` fields quoted
in `CASE-STUDY.md`, e.g. `mean_return` for one specific (regime, horizon) pair, are **not** subject
to this caveat — it applies only to the cross-regime `key_metrics` aggregates used in §2 and §3.)

**A known degenerate artifact:** `mean_realized_vol_h1` is uniformly `0.0` across every model and
period in every table below — the expected result of a single-observation standard deviation
(`ddof=0` over one point is zero), not a data error and not a meaningful 1-day volatility
estimate. `h5`/`h20` realized volatilities are computed over genuine multi-observation windows
and are meaningful.

## 2. Primary results — SPY-v1 (sole primary result)

All three tables below are generated by `scripts/generate_tables.py` directly from the committed,
intentionally-slim primary artifacts (`results/historical_regimes/fdm_hist_regime_v1_*.json`;
see `RESULT-SOURCE-MAP.md` for exact field paths). These artifacts carry `regime_counts` and
`key_metrics` only — no bootstrap intervals and no downside-volatility/tail/drawdown fields exist
for the primary SPY-v1 result (§6, Limitations).

### 2.1 Development / formation (2015–2023)

| Model | Regimes | Bars | Self-trans. | mean ret h1 | mean ret h5 | mean ret h20 | median ret h1 | median ret h5 | median ret h20 | vol h5 | vol h20 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| FDM pipeline | 4 | 2204/2264 | 0.736 | 0.000376 | 0.002971 | 0.010435 | 0.000720 | 0.004870 | 0.013776 | 0.00766 | 0.00885 |
| Volatility-bucket | 4 | 2244/2264 | 0.923 | 0.000519 | 0.002525 | 0.009778 | 0.000596 | 0.004647 | 0.016887 | 0.00797 | 0.00924 |
| Trend/vol grid | 4 | 2264/2264 | 0.846 | 0.000501 | 0.002570 | 0.010687 | 0.000792 | 0.004950 | 0.017790 | 0.00842 | 0.00946 |
| Gaussian mixture | 4 | 2244/2264 | 0.365 | 0.000964 | 0.003577 | 0.014802 | 0.001085 | 0.005634 | 0.020055 | 0.01143 | 0.01208 |

FDM regime counts: CALM_TREND 40, CHOP 789, RISK_OFF 341, VOLATILE_TREND 1034.

### 2.2 Validation (2024)

| Model | Regimes | Bars | Self-trans. | mean ret h1 | mean ret h5 | mean ret h20 | median ret h1 | median ret h5 | median ret h20 | vol h5 | vol h20 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| FDM pipeline | 4 | 252/252 | 0.613 | 0.000738 | 0.006414 | 0.019870 | 0.001194 | 0.007623 | 0.023115 | 0.00609 | 0.00758 |
| Persistence | 1 | 252/252 | 1.000 | 0.000939 | 0.005161 | 0.020893 | 0.001093 | 0.006207 | 0.026770 | 0.00643 | 0.00742 |
| Volatility-bucket | 4 | 252/252 | 0.893 | 0.001459 | 0.006778 | 0.018239 | 0.001362 | 0.006823 | 0.020467 | 0.00660 | 0.00781 |
| Trend/vol grid | 4 | 252/252 | 0.832 | 0.001655 | 0.007969 | 0.029605 | 0.002525 | 0.011145 | 0.035284 | 0.00689 | 0.00757 |
| Gaussian mixture | 4 | 252/252 | 0.287 | 0.000923 | 0.010325 | 0.028774 | 0.000740 | 0.011775 | 0.031278 | 0.00668 | 0.00846 |

FDM regime counts: CALM_TREND 8, CHOP 121, RISK_OFF 21, VOLATILE_TREND 102.

### 2.3 Historical evaluation (2025)

| Model | Regimes | Bars | Self-trans. | mean ret h1 | mean ret h5 | mean ret h20 | median ret h1 | median ret h5 | median ret h20 | vol h5 | vol h20 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **FDM pipeline** | **3** | 250/250 | 0.746 | **−0.000293** | 0.001667 | 0.018083 | 0.001407 | 0.005089 | 0.020006 | 0.01045 | 0.01141 |
| Persistence | 1 | 250/250 | 1.000 | 0.000740 | 0.003646 | 0.013880 | 0.001376 | 0.005828 | 0.019192 | 0.00826 | 0.01002 |
| Volatility-bucket | 4 | 250/250 | 0.918 | 0.000750 | 0.003400 | 0.016882 | 0.001203 | 0.005929 | 0.027246 | 0.00882 | 0.01055 |
| Trend/vol grid | 4 | 250/250 | 0.771 | 0.001643 | 0.003688 | 0.008922 | 0.002706 | 0.007447 | 0.007955 | 0.00860 | 0.01031 |
| Gaussian mixture | 4 | 250/250 | 0.345 | 0.001865 | 0.008368 | 0.030057 | 0.002310 | 0.009853 | 0.036033 | 0.01143 | 0.01186 |

FDM regime counts: CHOP 113, RISK_OFF 29, VOLATILE_TREND 108. **`CALM_TREND` was never selected
by the FDM pipeline in the 2025 historical-evaluation window** — reported exactly as observed,
not adjusted.

**Cross-regime differentiation.** Mean and median forward returns vary materially by
regime/model and horizon across all three periods. Multi-day (h20) realized volatility is highest
for the Gaussian-mixture classification in every period (0.01208 / 0.00846 / 0.01186). The FDM
pipeline's own relative volatility ranking is **not** consistent across periods: it has the
lowest h5/h20 volatility of all four models in development (0.00766/0.00885); in validation it
has the lowest h5 volatility (0.00609) while its h20 sits mid-pack; only in the 2025 evaluation is
its volatility elevated above the three non-GMM benchmarks at both h5 and h20, while remaining
below GMM. No single directional claim about FDM's volatility level relative to the simpler
benchmarks holds across all three periods.

**Persistence vs. reactivity.** FDM's self-transition rate (0.613–0.746 across the three periods)
sits consistently between the trivially sticky benchmarks (volatility-bucket 0.893–0.923,
persistence 1.000 by construction) and the noisier Gaussian mixture (0.287–0.365). Because GMM is
a structurally different, unrelated clustering model rather than an ablation of FDM with
hysteresis/majority-vote removed, this comparison alone cannot isolate how much of the gap is
attributable specifically to FDM's stabilization mechanism; that would require an ablation this
study does not include. Whether sitting at this particular point between the sticky and noisy
extremes is desirable is a downstream-use-case judgment this paper does not make — a consistent
middle position is reported as an observed characteristic, not as evidence that FDM is
"better" than either kind of benchmark.

**The 2025 finding.** FDM's historical-evaluation mean 1-day forward return was negative
(−0.000293) — the only negative mean-return cell in this entire primary results set — while the
corresponding median remained positive (+0.0014), and no benchmark showed a negative
`mean_return_h1` in 2025. Given the aggregation caveat above (both figures are unweighted
averages across regimes' own mean/median, not statistics of one common day-level distribution),
this mean/median contrast does **not** by itself establish that the negative mean is driven by
downside-skewed outliers. What is established: FDM was the only model whose 2025
`mean_return_h1` aggregate was negative, and its regime set also lost `CALM_TREND` entirely that
year.

## 3. Robustness / characterization — cross-asset (QQQ, IWM, TLT, GLD) and SPY-v2

**Status: post-primary, robustness / characterization only. Never a replacement for, or second
observation of, the SPY-v1 primary result in §2.** These runs use the same, unmodified frozen
methodology (`configs/experiments/fdm_historical_regime_study_v2_robustness.yaml`, byte-identical
in every methodological knob to the v1 primary config) applied to the separately acquired
`yf_fd_etfs_daily_2015_2025_v2` dataset, which does not hash-match v1 for SPY, QQQ, IWM, or TLT
(§1.1). The SPY row below is a second, non-bit-identical run of SPY through this same pipeline —
included only because it is the sole source of downside-volatility/tail/drawdown metrics for SPY
at all (§6) — and does not alter or restate SPY-v1's own frozen result.

*(`ret h1`/`ret h5`/`ret h20` are `mean_return_h*` — the same unweighted cross-regime average
described in §1.5's aggregation caveat, which applies to this table exactly as it does to §2's.)*

| Symbol | Period | Regimes | Bars | Self-trans. | ret h1 | ret h5 | ret h20 | downside vol h20 | pos-ret freq h20 | tail q05 h20 | adverse DD mean h20 | adverse DD worst h20 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| SPY | dev_formation | 4 | 2204/2264 | 0.736 | 0.000376 | 0.002971 | 0.010435 | 0.00534 | 0.6640 | -0.0554 | -0.0346 | -0.3099 |
| SPY | val_2024 | 4 | 252/252 | 0.613 | 0.000738 | 0.006413 | 0.019870 | 0.00501 | 0.8216 | -0.0139 | -0.0300 | -0.0841 |
| SPY | holdout_2025 | 3 | 250/250 | 0.746 | -0.000293 | 0.001667 | 0.018083 | 0.00689 | 0.7196 | -0.0665 | -0.0422 | -0.1372 |
| QQQ | dev_formation | 4 | 2204/2264 | 0.692 | 0.000716 | 0.005256 | 0.015604 | 0.00701 | 0.6980 | -0.0643 | -0.0464 | -0.2856 |
| QQQ | val_2024 | 4 | 252/252 | 0.556 | 0.000249 | 0.004687 | 0.012360 | 0.00754 | 0.6976 | -0.0483 | -0.0478 | -0.1356 |
| QQQ | holdout_2025 | 3 | 250/250 | 0.752 | -0.000439 | 0.002380 | 0.021542 | 0.00935 | 0.7139 | -0.0859 | -0.0571 | -0.1569 |
| IWM | dev_formation | 4 | 2204/2264 | 0.674 | 0.000461 | 0.002613 | 0.005129 | 0.00692 | 0.5516 | -0.0851 | -0.0526 | -0.4078 |
| IWM | val_2024 | 3 | 252/252 | 0.593 | 0.000882 | 0.005211 | 0.015960 | 0.00663 | 0.6742 | -0.0411 | -0.0429 | -0.1007 |
| IWM | holdout_2025 | 3 | 250/250 | 0.740 | -0.000528 | 0.004899 | 0.020357 | 0.00724 | 0.7030 | -0.0860 | -0.0484 | -0.1630 |
| TLT | dev_formation | 4 | 2204/2264 | 0.680 | -0.000303 | 0.000581 | 0.001841 | 0.00502 | 0.5436 | -0.0660 | -0.0363 | -0.1573 |
| TLT | val_2024 | 4 | 252/252 | 0.575 | -0.000755 | -0.002086 | -0.004378 | 0.00519 | 0.4898 | -0.0434 | -0.0452 | -0.0736 |
| TLT | holdout_2025 | 3 | 250/250 | 0.590 | 0.001272 | 0.002144 | 0.005375 | 0.00427 | 0.5114 | -0.0268 | -0.0324 | -0.0738 |
| GLD | dev_formation | 4 | 2204/2264 | 0.603 | 0.000067 | 0.000932 | 0.007291 | 0.00497 | 0.5485 | -0.0571 | -0.0342 | -0.1253 |
| GLD | val_2024 | 4 | 252/252 | 0.637 | 0.002780 | 0.002784 | 0.008316 | 0.00691 | 0.5538 | -0.0337 | -0.0432 | -0.0812 |
| GLD | holdout_2025 | 4 | 250/250 | 0.603 | 0.002259 | 0.014719 | 0.048581 | 0.00629 | 0.8898 | -0.0054 | -0.0367 | -0.1013 |

(Full table with `positive_return_freq` correction context: `tables/robustness_cross_asset.md`.)

**Cross-symbol pattern, reported factually.** `CALM_TREND` disappeared from the 2025 evaluation
window in QQQ, IWM, and TLT (each drops to 3 observed regimes), matching SPY's own 2025 finding
(§2.3); GLD is the exception, retaining `CALM_TREND` (11 observations). This is a
fixed-centroid classification outcome on one calendar year across a non-bit-identical dataset —
it does not by itself distinguish a genuine 2025 market characteristic from a centroid-definition
artifact. QQQ and IWM's `mean_return_h1` are negative in the 2025 window (−0.000439, −0.000528),
the same sign as SPY's headline 2025 finding (−0.000293); TLT and GLD are positive
(+0.001272, +0.002259) — consistent with an equity-specific rather than universal 2025 pattern,
but three equity instruments remains a small sample, and this pack does not claim statistical
significance for that split (§4 addresses the bootstrap evidence directly on QQQ's `RISK_OFF`
cell).

**SPY-v2 consistency observation.** SPY-v2's 2025 `mean_return_h1` is −0.00029294, against
SPY-v1's own primary figure of −0.00029295 — agreement to 4 significant figures despite the two
datasets not being bit-identical. This is reported as a consistency observation on
independently-sourced data, not as validation of either result, and not as a second primary
observation.

## 4. Bootstrap uncertainty and the sparse-cell disclosure

Block-bootstrap confidence intervals exist **only** for the 15 robustness/characterization
artifacts (§3); the three SPY-v1 primary artifacts are intentionally slim and carry no bootstrap
fields (§6). Two methods are computed for every (regime, horizon) cell: `moving_block` (fixed
block length) and `stationary` (Politis–Romano geometrically-distributed block length), each with
requested block length 20 trading days, `n_bootstrap=1000`, 90% confidence, fixed `seed=0`
(`block_bootstrap_mean_ci`/`regime_bootstrap_uncertainty`,
`src/financial_dynamics/backtesting/metrics.py`).

**This characterizes sampling uncertainty in the observed mean given the observed
serial-dependence structure. It is not an out-of-sample test and does not validate the regime
definitions themselves.**

### 4.1 Sparse-cell effective block-size disclosure

The bootstrap function computes `effective_block = max(1, min(block_size, n))` and reports that
(possibly-reduced) value back in the record's own `block_size` field — **it does not always
literally equal the requested 20.** A full scan of all `bootstrap_records[]` rows across all 15
robustness/characterization artifacts finds **174 rows** where the regime's occurrence count `n`
at that horizon is below 20, and every one of those rows reports an `effective_block` equal to
that smaller `n` (never 20). Two concrete examples, independently re-verified in this session:

- `fdm_hist_regime_v1_robustness_gld_dev_formation.json`, FDM pipeline, `CALM_TREND`, horizon 1:
  `n=12`, reported `block_size=12`.
- `fdm_hist_regime_v1_robustness_gld_holdout_2025.json`, **volatility-bucket benchmark** (not the
  FDM pipeline), `CALM_TREND`, horizon 1: `n=4`, reported `block_size=4`.

Full listing of all 174 rows: `tables/bootstrap_sparse_cells_full.md`. A histogram of effective
block sizes across these rows is at `figures/sparse_cell_effective_block_sizes.png` (see
`D10-STATUS.md` if matplotlib was unavailable at generation time).

### 4.2 Representative example — QQQ 2025, horizon 1

`RISK_OFF`'s mean 1-day forward return (n=29) is **−0.0043**, but its 90% moving-block CI is
**[−0.0100, +0.0014]** — the negative mean does not survive resampling at this confidence level
given how few `RISK_OFF` occurrences were observed. `VOLATILE_TREND` (n=121) is more stable: mean
**+0.0021**, CI **[+0.0008, +0.0037]**, entirely positive and excluding zero. See
`CASE-STUDY.md` for a full field-by-field trace of this example and
`figures/qqq_2025_holdout_bootstrap_ci_h1.png` for the corresponding forest plot.

### 4.3 Bootstrap resample count

All 15 robustness/characterization artifacts were regenerated at 1000 resamples (from an earlier
150-resample run); a full field-level diff confirms only `bootstrap_records[].{ci_low, ci_high,
n_bootstrap}` and `created_utc` changed between the two — every point estimate (`mean`, `n`,
regime classifications, `positive_return_freq`, downside vol, tail q05, adverse drawdown) is
byte-identical. The pre-fix, 150-resample artifacts are preserved, not deleted, at
`results/historical_regimes/superseded_150_resamples/`.

### 4.4 `positive_return_freq` correction

This column was corrected 2026-09-17: it previously reported the fraction of individual *daily*
returns positive inside each 20-day forward window (a day-level statistic), which is a different
quantity from what the name means everywhere else in this report. It is now
`mean(forward_return_h20 > 0)` — the fraction of 20-day windows whose *compounded* forward return
was itself positive, matching `mean_return`/`median_return`/`tail_q05`. Only this column changed;
`downside_vol`, `tail_q05`, and the adverse-drawdown columns are unaffected. Regression test:
`tests/test_backtesting.py::TestHistoricalRegimeStatistics::test_positive_return_freq_is_horizon_level_not_daily_level`.
The pre-fix values are preserved at `results/historical_regimes/superseded_positive_return_freq_fix/`.

## 5. Discussion

The FDM pipeline's regime classifications differentiate subsequent risk characteristics from the
simpler benchmarks in a way that is neither uniform nor trivial: its self-transition rate
occupies a consistent middle ground between sticky and noisy alternatives across all three
periods, but its relative *volatility* ranking among the benchmarks is period-dependent, and its
one distinguishing 2025 finding (a negative mean 1-day forward return, unique among all five
models in the primary result) is, on the closest bootstrap evidence available (QQQ's analogous
`RISK_OFF` cell in the robustness runs), not distinguishable from a zero effect at 90% confidence
given the small number of `RISK_OFF` occurrences that year. This is not a failure of the study —
it is the correct and honest reading of a small-sample regime cell under resampling that respects
serial dependence, and it is the reason this pack treats the 2025 finding as reported rather than
as confirmed.

The cross-asset robustness runs (§3) extend the same pattern (loss of `CALM_TREND` in 2025,
negative 1-day returns specific to the equity instruments) across four additional symbols on an
independently acquired, non-bit-identical dataset, which strengthens the *descriptive* case that
something changed in 2025 classification behavior without establishing a *causal* one (a
fixed-centroid classification outcome on one calendar year cannot, by itself, distinguish a
genuine market regime shift from a centroid-definition artifact interacting with that year's
price action).

## 6. Limitations

Reproduced in substance from `research/historical-market-regime-study.md` §7, tightened rather
than weakened:

- **SPY-v1's primary artifacts remain intentionally slim.** Downside volatility,
  drawdown/maximum-adverse-excursion, positive-return frequency, 5th-percentile forward return,
  and bootstrap confidence intervals are **not reported for SPY's primary v1 result itself** — only
  for the §3 robustness runs (including the SPY-v2 post-primary run). Regenerating those fuller
  tables from the primary v1 dataset would require either the lost v1 raw CSVs or re-running the
  primary study end to end; this program does neither.
- **`mean_return_h*`/`median_return_h*` are unweighted averages across regimes**, not bar-level
  statistics of the raw return series (§1.5). This limits how far any mean-vs-median or
  model-vs-model comparison in §2 can be pushed.
- **Bootstrap CIs characterize sampling uncertainty only.** They are not an out-of-sample test and
  do not validate the regime definitions themselves (§4); a narrow CI means the mean is stable
  under resampling of the same historical sample, not that it will hold out of sample.
- **Cross-asset robustness (§3) runs on a dataset that does not hash-match the primary dataset**
  for SPY, QQQ, IWM, and TLT. The true v1 payload for these symbols is confirmed unrecoverable, so
  the magnitude and full cause of the divergence cannot be established beyond "GLD (no
  dividends) matches; the dividend-paying symbols do not" — a pattern consistent with, but not
  proof of, dividend-adjustment recomputation drift.
- **`mean_realized_vol_h1 = 0.0` throughout is a known artifact**, not a finding (§1.5).
- **Model risk:** fixed, theory-based centroids are a modeling choice, not a data-driven fit; a
  different theoretical regime definition would produce different classifications. Formation-period
  regime incidence (e.g. very few `CALM_TREND` observations in some periods) limits statistical
  power for that regime specifically, and is the direct cause of the sparse-cell effective-block
  reduction disclosed in §4.1.
- **Cross-program note:** SPY, QQQ, IWM, TLT, and GLD price history is also used by a different
  repository's stat-arb research design; this study's 2025 evaluation is the event referenced as
  "FDM's already-executed 2025 holdout" in that study's cross-repository exposure disclosure.

## 7. Conclusion

The Financial Dynamics Model's regime classifications differentiate subsequent **risk
characteristics** — self-transition persistence consistently, volatility level
period-dependently, and one small-sample tail finding in the 2025 evaluation whose statistical
robustness is itself limited by the number of observations available. This paper makes no
forecast-accuracy or trading-alpha claim: it characterizes what regime membership says about the
distribution of subsequent outcomes, not whether that information is exploitable after costs,
timing constraints, and capacity. Every number in this paper traces to a committed artifact via
`RESULT-SOURCE-MAP.md`; the claims made from those numbers are enumerated and scoped individually
in `CLAIM-REGISTER.md`.
