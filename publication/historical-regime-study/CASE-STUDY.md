# Case Study: QQQ, 2025 Holdout, `RISK_OFF`, Horizon 1 Bootstrap CI

This is one fully worked example, end-to-end, of how a single reported number — the 90%
moving-block bootstrap confidence interval on QQQ's `RISK_OFF` regime's mean 1-day forward return
in the 2025 holdout window — was produced, citing the exact file and field at each step. It is
the example referenced in `TECHNICAL-PAPER.md` §4.2 and mapped row-by-row in
`RESULT-SOURCE-MAP.md` under the `case_study.qqq_2025.*` row IDs.

**Status reminder:** this is a robustness/characterization result (QQQ, `yf_fd_etfs_daily_2015_2025_v2`
dataset) — not the SPY-v1 primary result. It is chosen as the worked example specifically because
the SPY-v1 primary artifacts carry no bootstrap fields at all (§6 of the technical paper), so no
comparably complete worked example exists for SPY's own primary numbers.

## Step 0 — Inputs

| Input | Value | Source |
|---|---|---|
| Symbol | QQQ | `results/historical_regimes/fdm_hist_regime_v1_robustness_qqq_holdout_2025.json`, `primary_symbol` field |
| Dataset | `yf_fd_etfs_daily_2015_2025_v2` | same file, `dataset_id` field |
| Config | `configs/experiments/fdm_historical_regime_study_v2_robustness.yaml`, sha256 `6e1044b4e46ae297f52efcd2b2a09d981d6a71d702fe2b58fd8a73ff9e746b4b` | same file, `config_path` field |
| Period | 2025-01-01 to 2025-12-31 (final 2025 holdout evaluation; see `SOURCE-GATE.md` field 7 and its "Period classification detail" section) | same file, `period` field |
| Model | `financial_dynamics_pipeline` (FDM), seed 0 | same file, `models[0].model` and `seed` fields |
| Artifact | `results/historical_regimes/fdm_hist_regime_v1_robustness_qqq_holdout_2025.json` | sha256 `7af9c81baf9ee89568969323a53cfa35483a2d74580ea16f5ff532e45dbc867d` |

## Step 1 — Raw regime classification (conceptual; per-bar series not in this artifact)

Each trading session in the 2025 window is classified into one of `{CALM_TREND, VOLATILE_TREND,
CHOP, RISK_OFF}` by `FinancialDynamicsPipeline` (`src/financial_dynamics/pipeline.py:53`), using
the frozen centroids and feature windows recorded verbatim in this artifact's own
`pipeline_config_snapshot` field (volatility span 20, trend window 14, drawdown window 60,
correlation window 20, shock threshold 2.0, z-score normalization over 252 sessions, temperature
1.0, hysteresis threshold 0.15, minimum persistence 5 bars, majority-vote stabilization over 10
bars). **The per-bar day-by-day regime label series itself is not stored in the committed
artifact** — only the resulting aggregate counts and statistics are (this is a deliberate
git-size convention; see `results/historical_regimes/README.md`). This case study therefore
starts its verifiable chain at the aggregate `regime_counts`, which is the first field actually
committed to the repository:

```
models[model==financial_dynamics_pipeline].regime_counts = {"CHOP": 100, "RISK_OFF": 29, "VOLATILE_TREND": 121}
```

evaluated over `evaluated_bars = 250` of `total_bars = 250` for the 2025 window. `RISK_OFF` was
selected on 29 of the 250 sessions.

## Step 2 — Forward-return computation for each `RISK_OFF` occurrence

For every session classified `RISK_OFF`, `historical_regime_statistics`
(`src/financial_dynamics/backtesting/metrics.py:269`) computes the 1-trading-day forward return
`future_price / current_price - 1.0` (line 340) from the underlying QQQ close-price series (not
itself re-derivable from this artifact, which stores only the resulting statistics, not the raw
price series). These 29 forward returns are aggregated (not individually stored) into the
`summary_records` entry for `(regime="RISK_OFF", horizon=1)`:

```json
{
  "regime": "RISK_OFF",
  "horizon": 1,
  "count": 29,
  "mean_return": -0.004303386237159056,
  "median_return": -0.000042617491711305355,
  "positive_return_freq": 0.4827586206896552,
  "tail_q05": -0.04322862920935162,
  "tail_q25": -0.01800842506960687,
  "mean_adverse_drawdown": -0.009853250844778092,
  "worst_adverse_drawdown": -0.062108960931021584,
  "mean_duration": 3.2222222222222223,
  "median_duration": 2.0,
  "transition_rate": 0.6896551724137931
}
```

(`models[model==financial_dynamics_pipeline].summary_records[regime==RISK_OFF,horizon==1]` in the
artifact above.) `count = 29` matches `regime_counts.RISK_OFF = 29` from Step 1, confirming every
`RISK_OFF` occurrence in this period contributed exactly one forward-return observation at
horizon 1 (no observations were dropped for missing forward data at this horizon).

**Reading the headline number:** `mean_return = -0.004303386237159056` ≈ **−0.0043** — this is the
number quoted in `TECHNICAL-PAPER.md` §4.2 as "`RISK_OFF`'s mean forward return (n=29) is
−0.0043."

## Step 3 — Block-bootstrap resampling of the 29 forward returns

`regime_bootstrap_uncertainty` (`src/financial_dynamics/backtesting/metrics.py:486`) takes the
chronologically-ordered `forward_return` values behind the Step 2 summary (the underlying
`forward_occurrences` DataFrame — itself not persisted to the JSON artifact, only its resulting
`bootstrap_records` are) and calls `block_bootstrap_mean_ci` (line 428) once per method:

- **Requested parameterization:** `block_size=20`, `n_bootstrap=1000`, `confidence=0.90`, `seed=0`.
- **Effective block size actually used:** `n = 29 ≥ 20`, so `effective_block = max(1, min(20, 29))
  = 20` — this is one of the **non**-sparse cells (contrast with the sparse-cell disclosure in
  `SOURCE-GATE.md`'s "Bootstrap / uncertainty detail" section, which covers cells where `n < 20`).
- For `method="moving_block"`: 1000 resamples are drawn by concatenating contiguous 20-observation
  blocks (wrapping at the series end) with replacement until the resampled series reaches length
  29, and each resample's mean is recorded (`_moving_block_bootstrap_mean`, line 394).
- For `method="stationary"`: 1000 resamples are drawn using a geometrically-distributed block
  length with restart probability `1/20` (Politis–Romano stationary bootstrap;
  `_stationary_bootstrap_mean`, line 408).
- The 90% CI for each method is the [5th, 95th] percentile of that method's 1000 resampled means
  (`np.quantile(boot_means, [0.05, 0.95])`, line 472).

Both records, exactly as committed:

```json
{
  "regime": "RISK_OFF", "horizon": 1, "n": 29, "method": "moving_block",
  "block_size": 20, "n_bootstrap": 1000, "confidence": 0.9,
  "mean": -0.004303386237159056,
  "ci_low": -0.01004536744273186, "ci_high": 0.0014388538325926755,
  "insufficient_data": false
}
{
  "regime": "RISK_OFF", "horizon": 1, "n": 29, "method": "stationary",
  "block_size": 20, "n_bootstrap": 1000, "confidence": 0.9,
  "mean": -0.004303386237159056,
  "ci_low": -0.009628231317896438, "ci_high": 0.0011103796925377824,
  "insufficient_data": false
}
```

(`models[model==financial_dynamics_pipeline].bootstrap_records[regime==RISK_OFF,horizon==1,method==...]`
in the same artifact.) Note `mean` here is byte-identical to `summary_records`'s `mean_return`
from Step 2 (`-0.004303386237159056` in both) — the bootstrap function recomputes the same
point estimate from the same underlying values before resampling, as a consistency check.

**Reading the headline CI:** rounding `ci_low=-0.01004536744273186` and
`ci_high=0.0014388538325926755` to 4 decimal places gives **[−0.0100, +0.0014]** — the interval
quoted in `TECHNICAL-PAPER.md` §4.2. It **includes zero**, which is the entire substance of the
claim: the negative point estimate does not survive resampling at 90% confidence.

## Step 4 — Contrast: what this looked like before the 2026-09-18 resample-count correction

The same cell, computed identically except for `n_bootstrap=150` (the pre-correction value),
preserved at `results/historical_regimes/superseded_150_resamples/fdm_hist_regime_v1_robustness_qqq_holdout_2025.json`
(sha256 `5808f6480552b77c7eca47e480c51a0fdf1353453e0ee78a7e338d10504db8ba`):

```json
{
  "regime": "RISK_OFF", "horizon": 1, "n": 29, "method": "moving_block",
  "block_size": 20, "n_bootstrap": 150, "confidence": 0.9,
  "mean": -0.004303386237159056,
  "ci_low": -0.009664024493675141, "ci_high": 0.00146222223537839,
  "insufficient_data": false
}
```

Point estimate (`mean`) and `n` are byte-identical to Step 3's current record; only `ci_low`,
`ci_high`, and `n_bootstrap` differ ([−0.0097, +0.0015] at 150 resamples vs. [−0.0100, +0.0014] at
1000). The qualitative conclusion — the interval includes zero — is unchanged by the resample
count; the bounds themselves moved by less than 0.0004 in either direction. This confirms
`TECHNICAL-PAPER.md` §4.3's claim that "every point estimate ... is byte-identical" between the
two resample counts, verified here for this specific cell.

## Summary chain

```
regime_counts.RISK_OFF = 29
  -> summary_records[RISK_OFF, h1].count = 29   (consistency check: matches)
  -> summary_records[RISK_OFF, h1].mean_return = -0.004303386237159056
  -> bootstrap_records[RISK_OFF, h1, moving_block].mean = -0.004303386237159056  (consistency check: matches)
  -> bootstrap_records[RISK_OFF, h1, moving_block].{ci_low, ci_high} = [-0.01005, +0.00144]
  -> reported in TECHNICAL-PAPER.md Sec 4.2 as: mean -0.0043, 90% CI [-0.0100, +0.0014]
```

Every arrow above is a field-to-field mapping within one committed, hashed JSON file (plus one
cross-file consistency contrast against its superseded predecessor in Step 4); none of it required
re-running any script or accessing any file outside `results/historical_regimes/`.
