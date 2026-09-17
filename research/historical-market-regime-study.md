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

**Original acquisition/freeze:** `retrieval_timestamp_utc: 2026-09-16T02:36:57Z`,
`freeze_timestamp_utc: 2026-09-16T02:37:02Z` (same manifest file as above).

A later independent re-acquisition attempt of this dataset, made within the same working
session — hours, not months, after the original freeze; a prior version of this report
said "a fresh pull months later," which was an unverified guess unsupported by the actual
timeline and is retracted — produced a **different** file hash (`945cf990…` vs. the frozen
`91caa6cd…`). A reviewing agent (relayed via the user; not independently reproduced in this
session, since no re-acquired CSVs are available in this environment to check directly)
reported that a byte-level diff attributes GLD's mismatch entirely to line-ending
differences, while the other four symbols' mismatches remain unexplained. This session
cannot independently confirm that claim either. Given how little time elapsed between
acquisitions, `auto_adjust=True` retroactive dividend-adjustment drift is a weaker
candidate explanation than it would be for a genuinely stale re-pull, and is no longer
offered as the "most likely" cause — it is not ruled out for the four unexplained symbols,
just no longer asserted as probable. The results below are drawn from the **originally
frozen** dataset and artifacts, committed before this discrepancy was discovered; they are
unaffected by it, but the root cause of four of the five symbols' hash mismatches remains
genuinely unresolved, and the dataset's re-acquisition is flagged for anyone attempting to
reproduce this study from scratch.

## 3. Pre-registration and freeze

**Config:** `configs/experiments/fdm_historical_regime_study_v1.yaml`, status
`frozen-for-holdout`. **Freeze commit:** `596a22527b6f0107ba5baf55dd2edd68a1d991fe`
("D9-A: FINAL CONFIGURATION FROZEN for holdout"), an ancestor of this branch that
modifies exactly this config file to the frozen state evaluated below (verified via
`git merge-base --is-ancestor` against a full, unshallowed clone — not assumed).
**Freeze timestamp:** `2026-09-16T02:58:00Z` (`freeze_record.frozen_for_holdout_utc`
in the config file itself). A prior version of this report claimed this hash "does
not exist anywhere in this repository's git history and was fabricated"; that claim
was itself wrong — reached from an incomplete/shallow local check at the time — and
is retracted here. The commit is real and its diff is exactly the freeze: nothing
else changed alongside it.

**Correction to the audit trail, not just this report's text:** checking this
repository's git history directly (`git show 4fda3ba:research/historical-market-regime-study.md`)
confirms the *original* first-draft report already cited this exact hash correctly.
There was never a fabricated freeze-commit hash in this report at any point — the
"fabricated" characterization was itself an error, introduced by an earlier relayed
review and then compounded, not by anything actually wrong in this report's own
history. `research/experiment-ledger.csv`'s `fdm_hist_regime_v1_report_SUPERSEDED_FACTUAL_ERRORS`
row's notes list "a fabricated freeze-commit hash" among that superseded version's
defects; that specific item in those notes is now known to be false and is flagged
here rather than edited in place, since that row is preserved verbatim as an
immutable audit-trail entry.

**Freeze chronology, assessed directly from git log (not just "a commit exists"):**
the freeze commit's author timestamp is `2026-09-16T03:01:12Z`, about 3 minutes
after the `freeze_record` field's own `02:58:00Z` — consistent with the field being
stamped by a freeze script moments before the resulting file was `git add`/`git
commit`-ed, not a discrepancy worth flagging further. Every commit on this branch
after the freeze commit (`f0ad092` through `8158395`, all within the same working
session, followed by unrelated CI/tooling fixes the next day: `9d51855`, `3f248ab`,
`ab72cc9`) only adds the study module, runner, tests, and DEV/validation/holdout
result artifacts — none of them touches
`configs/experiments/fdm_historical_regime_study_v1.yaml` again. No retuning
occurred after this freeze per `constraints.no_retune_after_freeze: true`; the
holdout (2025) run used the identical frozen `PipelineConfig` as development and
validation.

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
1. **Volatility-bucket** — trailing 20-day realized volatility, split into formation-period
   **quartiles** (Q1/Q2/Q3), mapped to the four regime labels in increasing-volatility
   order (≤Q1 → CALM_TREND, Q1–Q2 → CHOP, Q2–Q3 → VOLATILE_TREND, >Q3 → RISK_OFF),
   thresholds frozen from formation and applied unchanged OOS. (An earlier version of this
   report incorrectly described this as a binary HIGH/LOW median split; corrected to match
   `VolatilityBucketClassifier` in `src/financial_dynamics/benchmarks/baselines.py`.)
2. **Trend/volatility grid** — trailing **14**-session return sign × trailing 20-session
   realized-vol median split (both formation-derived), four quadrant states. (An earlier
   version of this report incorrectly stated a 63-session trend window; corrected to match
   `TrendVolGridClassifier`'s `trend_window: int = 14` default in the same file.)
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

**Important methodological caveat on `mean_return_h*` and `median_return_h*`:** these are
**unweighted averages across each period's observed regimes** of that regime's own mean
(resp. median) forward return — i.e. "the average, across regimes, of each regime's mean
return," not a bar-level statistic over the raw day-by-day return series, and not weighted
by how many days each regime was observed. A regime with 5 observed bars and a regime with
500 observed bars contribute equally to these aggregates. This materially limits what can
be inferred from comparing a period's `mean_return_h1` against its `median_return_h1`: the
two columns are computed the same way but over each regime's mean vs. median respectively,
not the mean and median of one common underlying distribution, so a mean-vs-median
comparison here does not by itself indicate distributional skew (see §6, where an earlier
version of this report drew exactly that unsupported conclusion).

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
median forward returns vary materially by regime/model and by horizon. Multi-day realized
volatility (h20) is **highest for the Gaussian-mixture classification in every period**
(DEV 0.01208, VAL 0.00846, holdout 0.01186, each the maximum of that period's row). At h5
this holds in DEV (0.01143) and holdout (0.01143) but **not** in VAL 2024, where the
trend/vol-grid benchmark's h5 volatility (0.00689) marginally exceeds GMM's (0.00668) — an
exception a prior version of this report missed while correcting a different, broader
overclaim about GMM. The FDM pipeline's relative position is **not** consistent across
periods, contrary to an earlier version of this report, which incorrectly claimed FDM was
"consistently higher" than the volatility-bucket and trend/vol-grid benchmarks: in DEV, FDM
has the **lowest** h5/h20 volatility of all four models (0.00766/0.00885); in VAL 2024, FDM
has the lowest h5 volatility of all five models (0.00609) while its h20 volatility
(0.00758) sits in the middle of the pack (above persistence and trend/vol-grid, below
volatility-bucket and GMM); only in the 2025 holdout is FDM's volatility elevated above all
three non-GMM benchmarks (persistence, volatility-bucket, trend/vol-grid) at both h5 and
h20, while still below GMM. No single directional claim about FDM's volatility level
relative to the simpler benchmarks holds across all three periods, and even GMM's
volatility is the outright highest of the four models in 5 of 6 period-horizon cells, not
all 6 — the one exception (VAL 2024, h5) is real and should not be smoothed over.

**Persistence vs. reactivity.** The FDM pipeline's self-transition rate (0.61–0.75 across
periods) sits between the trivially sticky benchmarks (volatility-bucket 0.89–0.92,
persistence 1.00 by construction) and the noisy Gaussian mixture (0.29–0.37), consistently
in every period. However, GMM is a structurally different, unrelated clustering model —
not an ablation of FDM with its hysteresis/majority-vote stabilization components removed
— so this comparison alone cannot isolate how much of that gap is attributable
specifically to FDM's stabilization mechanism versus other structural differences between
the two approaches (e.g. fixed centroid-distance classification vs. unsupervised
clustering). An earlier version of this report attributed the gap directly to "FDM's
hysteresis/majority-vote stabilization," which overstated what a comparison against an
unrelated model can support; establishing that specific causal link would require an
ablation of FDM itself (e.g. running the pipeline with hysteresis/majority-vote disabled)
as a control, which this report does not include. What the evidence does support without
that caveat: FDM's self-transition rate sits between the sticky simple benchmarks and the
noisy GMM, consistently across all three periods. Whether that trade-off point is "better"
depends on the downstream use case; this report does not adjudicate that.

**2025 finding, reported honestly.** The FDM pipeline's holdout mean 1-day forward return
was negative (−0.000293) — the only negative mean-return cell in this entire results set —
while the corresponding `median_return_h1` aggregate remained positive (+0.0014), and no
benchmark showed a negative `mean_return_h1` in 2025. Given the methodological caveat in
§5 (both figures are unweighted averages across regimes' own mean/median returns, not
statistics of one common day-level return distribution), this mean/median contrast does
**not** by itself establish that the negative mean is driven by downside-skewed outliers —
an earlier version of this report drew that conclusion, which overstated what these two
aggregates can support, and it is retracted. What is genuinely established is narrower:
FDM was the only model whose `mean_return_h1` aggregate was negative in the 2025 holdout.
Characterizing whether that reflects broadly negative returns, a few large negative days,
or an artifact of which regimes were observed and how they are weighted in this
aggregation would require the bar-level return distribution and per-regime breakdowns this
report does not have access to (see Limitations). The FDM regime set also lost
`CALM_TREND` entirely in 2025 — reported as observed, without adjustment.

## 7. Limitations

- **Downside volatility, drawdown/maximum-adverse-excursion, positive-return frequency,
  and 5th-percentile forward return are not reported here.** The committed result
  artifacts (`results/historical_regimes/*.json`) are intentionally "slim" — key aggregate
  metrics and regime counts only, not the full per-observation summary/transition tables.
  Regenerating those fuller tables requires either the local raw CSVs (not available in
  this environment — see §2's acquisition-drift note) or re-running the study end to end.
  This is a real content gap in this report, not an omission of already-available evidence.
- **`mean_return_h*` and `median_return_h*` are unweighted averages across regimes, not
  bar-level statistics of the raw return series.** See §5's methodological caveat. This
  limits how far any mean-vs-median or model-vs-model comparison in this report can be
  pushed without the fuller per-observation tables noted above; an earlier version of this
  report drew a downside-skew conclusion from this comparison that the aggregation method
  does not support (corrected in §6).
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
