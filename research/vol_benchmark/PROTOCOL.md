# Regime labels versus a trailing-volatility bucket — frozen protocol

Status: **frozen before any result was computed.** The commit that adds this file, the code in
this directory and `tests/test_vol_benchmark.py` is the design freeze; its push time is the freeze
time. The dataset named below was requested before the freeze, and its files were not opened until
after it. Any later change is recorded under *Amendments*, dated, with its reason.

Scope: new files only (`research/vol_benchmark/`, `tests/test_vol_benchmark.py`,
`results/vol_benchmark/`). No frozen artifact, config, manifest, result JSON, publication-pack file
or source module is changed, and the published study is not re-run or re-interpreted.

## 1. Question

The published study describes forward risk by regime. It never tested whether the regime labels
carry more information about forward risk than the simplest alternative with the same number of
groups: a quartile bucket of trailing realised volatility. The portfolio hub now states that this
comparison "has not been tested". This study runs it.

**Primary question.** As a forecaster of next-day variance, are the four FDM regime labels better
than, worse than, or indistinguishable from four trailing-volatility quartile buckets?

## 2. Classification

**PREVIOUSLY INSPECTED / HISTORICAL EVALUATION.** Every date in 2015–2025 has been seen in the
published study, and the model configuration was frozen after looking at 2015–2024. Nothing here is
a holdout. What is pre-specified is this comparison: its forecasts, loss, test and decision rule.

## 3. Data

- Dataset `yf_fd_etfs_daily_2015_2025_v3`: SPY, QQQ, IWM, TLT, GLD, daily, 2015-01-01 to
  2025-12-31, acquired from Yahoo Finance with `scripts/acquire_yf_fd_etfs_daily.py` at its default
  parameters. The raw files are held privately; the report records the manifest's
  `dataset_canonical` hash.
- This is a new acquisition. Yahoo restates adjusted prices, so it is not expected to hash-match
  the v1 or v2 snapshots used by the published study, and no number here is comparable
  digit-for-digit with the published tables.

## 4. Models

Each asset in turn is the primary series; the other four are the reference series, as in the
published robustness runs. For each primary asset, with r_t the close-to-close return:

| Name | Definition |
|---|---|
| `fdm` | `risk_adjusted_regime` from `FinancialDynamicsPipeline` under the frozen config `configs/experiments/fdm_historical_regime_study_v1.yaml`, run once over the whole panel. |
| `vol_bucket` | Quartile of the trailing 20-day standard deviation of returns at t, against the quartiles of that statistic over all days up to t − 1 (at least 252 of them). |
| `unconditional` | No labels. Reference. |
| `ewma` | RiskMetrics EWMA variance, decay 0.94, seeded with the first 20 squared returns. Reference. |

**Variance forecast from labels.** The target for horizon h is y_t = r²_{t+1} + … + r²_{t+h}. For
`fdm` and `vol_bucket`, the forecast at t is the mean of y_s over all s ≤ t − h whose label equals
the label at t, if there are at least 20 such days; otherwise the mean of y_s over all s ≤ t − h.
`unconditional` is always that second quantity. `ewma` is h times the EWMA variance at t. Every
forecast uses only information available at the close of day t.

Both label schemes therefore get the same treatment: four groups, the same expanding estimator,
the same fallback. The comparison isolates the information in the labels.

## 5. Evaluation

- **Loss.** QLIKE, y / f + ln f, with f floored at 1e-10. Lower is better. QLIKE ranks variance
  forecasts consistently when the target is a noisy proxy such as squared returns (Patton 2011).
- **Window.** The first 504 rows of each asset are burn-in and are never scored. A day is scored
  only if all four forecasts and the target exist.
- **Horizons.** 1 day (primary), 5 and 20 days (secondary).
- **Pooling.** For each date present for all five assets, average each model's loss across the
  assets. This gives one loss series per model and respects the cross-asset correlation.
- **Test.** Diebold-Mariano on the loss differential d_t = QLIKE(`fdm`) − QLIKE(`vol_bucket`), with
  a Newey-West variance (Bartlett kernel, lag = max(h − 1, floor(4 (n/100)^(2/9)))) and a normal
  reference distribution. Two-sided.

## 6. Precondition

**P1 (causality of the labels).** For each primary asset, the labels from running the pipeline on
the first 1,500 rows must equal the first 1,500 labels from the full run. If any label differs, the
labels are not causal, the comparison is not valid as designed, and the report stops at that
finding.

## 7. Decision rule (primary)

Pooled series, 1-day horizon, two-sided test at the 5% level:

| Outcome | Reading |
|---|---|
| mean d < 0 and p < 0.05 | The FDM labels forecast next-day variance better than a volatility bucket. |
| mean d > 0 and p < 0.05 | A volatility bucket forecasts next-day variance better than the FDM labels. |
| p ≥ 0.05 | No detectable difference. The report states the minimum detectable effect. |

There is exactly one primary test. Everything else is secondary and is reported without a claim of
significance unless stated: per-asset results at 1 day (Holm-adjusted across the five assets), the
5- and 20-day horizons, each label scheme against `unconditional`, and each against `ewma`.

**Interpretation rules, fixed now.**

- I1. A result of "no detectable difference" is reported with the minimum detectable effect,
  2.8 × SE of the pooled mean differential, in QLIKE units and as a share of the volatility
  bucket's own gain over `unconditional`. It is not reported as "the labels are as good as".
- I2. If `vol_bucket` does not beat `unconditional` in the pooled 1-day series (mean differential
  not below zero), the benchmark itself is uninformative on this sample, and the report says so
  before discussing the primary test.
- I3. A result in favour of either scheme is a statement about next-day variance forecasting on
  five liquid ETFs. It is not a statement about returns, trading value or other assets.
- I4. `ewma` is a reference for scale. Neither label scheme is expected to beat it, and losing to
  it is not a finding against either.

## 8. Sensitivity (secondary, pre-specified)

The whole analysis is repeated with a minimum of 60 days per label in place of 20. If the primary
outcome differs between the two, the report gives both and treats the result as not robust.

## 9. Outputs

- `results/vol_benchmark/vol_benchmark.json`: every number in the report.
- `research/vol_benchmark/REPORT.md`: the outcome under section 7, the secondary results, the
  precondition check, and limits.

## Amendments

None.
