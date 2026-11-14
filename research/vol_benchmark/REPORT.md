# Regime labels versus a trailing-volatility bucket — report

Frozen design: [`PROTOCOL.md`](PROTOCOL.md) (commit `74998ef`, pushed 2026-11-14T18:28:52Z, before
any result was computed). Results: `results/vol_benchmark/vol_benchmark.json`. No amendments.

## Summary

**A four-bucket quartile of trailing 20-day volatility forecasts next-day variance better than the
four FDM regime labels.** On the pooled five-ETF series (2,261 scored days, 2017–2025), the FDM
labels' QLIKE loss is higher by 0.173 (SE 0.069, z = 2.50, two-sided p = 0.012). Under the
pre-specified decision rule this is the outcome "a volatility bucket forecasts next-day variance
better than the FDM labels". The result is the same with the stricter minimum of 60 days per label
(difference 0.169, p = 0.014), and the sign is the same for all five assets.

The regime labels do carry some information. They improve on using no labels at all by 0.040 QLIKE
(p = 0.066 at 1 day, p = 0.031 at 5 days), which is about 19% of the improvement the volatility
bucket delivers (0.213, p = 0.010).

This is a statement about forecasting next-day variance on five liquid ETFs. It says nothing about
returns or trading value.

**Classification: PREVIOUSLY INSPECTED / HISTORICAL EVALUATION.** Every date had already been seen
in the published study. Only this comparison was pre-specified.

## Precondition

P1 passed for all five assets: the labels from a run on the first 1,500 rows equal the first 1,500
labels of the full run (0 mismatches in 1,500 for each asset). The labels are causal in the sense
the comparison needs.

## Primary result (pooled, 1-day horizon)

| Model | Mean QLIKE (lower is better) |
|---|---:|
| `ewma` (reference) | −8.1647 |
| `vol_bucket` | −8.0825 |
| `fdm` | −7.9094 |
| `unconditional` (reference) | −7.8697 |

| Comparison | Mean difference | SE | z | p |
|---|---:|---:|---:|---:|
| **`fdm` − `vol_bucket` (primary)** | **+0.1730** | 0.0692 | 2.50 | **0.012** |
| `vol_bucket` − `unconditional` | −0.2128 | 0.0827 | −2.57 | 0.010 |
| `fdm` − `unconditional` | −0.0398 | 0.0216 | −1.84 | 0.066 |
| `vol_bucket` − `ewma` | +0.0823 | 0.0362 | 2.27 | 0.023 |
| `fdm` − `ewma` | +0.2553 | 0.1026 | 2.49 | 0.013 |

n = 2,261 dates; Newey-West lag 7. A positive difference means the first model is worse.

Interpretation rules from the protocol:

- **I2.** The volatility bucket beats `unconditional`, so the benchmark is informative on this
  sample and the primary test means something.
- **I4.** EWMA is better than both label schemes, as expected. It is a reference for scale.
- **I1 (context for the size of the test).** The minimum detectable effect was 0.194 QLIKE, which is
  91% of the volatility bucket's own gain over `unconditional`. The test was only able to see a
  large gap, and the gap is large: the FDM labels recover about a fifth of what a volatility bucket
  recovers.

## Secondary results

**By asset, 1-day horizon.** All five differences have the same sign. Only QQQ is significant after
the Holm adjustment across the five assets.

| Asset | `fdm` − `vol_bucket` | z | p | Holm p |
|---|---:|---:|---:|---:|
| SPY | +0.2922 | 2.25 | 0.024 | 0.073 |
| QQQ | +0.2023 | 3.12 | 0.002 | 0.009 |
| IWM | +0.1628 | 1.96 | 0.050 | 0.101 |
| TLT | +0.1234 | 1.82 | 0.069 | 0.101 |
| GLD | +0.0843 | 2.39 | 0.017 | 0.068 |

**Longer horizons, pooled.**

| Horizon | n | `fdm` − `vol_bucket` | z | p | `fdm` − `unconditional` | p |
|---|---:|---:|---:|---:|---:|---:|
| 5 days | 2,257 | +0.1465 | 2.26 | 0.024 | −0.0400 | 0.031 |
| 20 days | 2,242 | +0.0695 | 1.46 | 0.145 | −0.0059 | 0.670 |

At 20 days there is no detectable difference between the two schemes, and neither beats
`unconditional` (volatility bucket: −0.075, p = 0.144). Overlapping 20-day targets leave little
independent information.

**Sensitivity (minimum 60 days per label).** Pooled 1-day difference +0.1694, SE 0.0692, z = 2.45,
p = 0.014. The primary outcome is unchanged, so the result is robust to that choice.

## An observation that was not pre-specified

The four FDM labels are far from evenly used. `CALM_TREND` was assigned on 25 to 48 of roughly
2,766 days, depending on the asset, so the scheme works in practice with three groups, and
`VOLATILE_TREND` alone covers 42–52% of days. The volatility quartiles are close to even by
construction. Coarser effective grouping may explain part of the gap. This was noticed after the
run and was not tested; it is a lead for a follow-up, not a finding.

## What this changes

- The portfolio hub describes the comparison as "not tested". It has now been tested, on the terms
  above: for next-day variance, the regime labels are worse than a volatility quartile and slightly
  better than no labels.
- The published study's descriptive tables are not affected. They report risk by regime; they made
  no claim about a benchmark.
- It does not show the regime model is useless. The labels were not built to forecast variance, and
  other uses (returns, drawdown, persistence) were not tested here.

## Limits

- **Not a holdout.** All data had been inspected before. The comparison was pre-specified; the
  data were not unseen.
- **New data snapshot.** Dataset `yf_fd_etfs_daily_2015_2025_v3`, acquired 2026-11-14 from Yahoo
  Finance (yfinance 1.7.0), `dataset_canonical`
  `d971a21ad6dfc1974bf012f70c9ffb1d848ca6acb2cd2c48056c30d13ddfcee7`. It does not hash-match the v1
  or v2 snapshots behind the published study, because Yahoo restates adjusted prices. The raw files
  are held privately and are not in this repository.
- **No second-source check.** A cross-check against Stooq was attempted and failed: Stooq returned
  a browser-verification page to the automated request. The snapshot rests on Yahoo alone.
- **One loss function.** QLIKE with squared daily returns as the variance proxy. Other losses or a
  realised-variance proxy from intraday data could rank the schemes differently.
- **One benchmark design.** A 20-day window and quartile cut-offs, fixed in advance. Other windows
  were not tried.
- **Five correlated assets.** Pooling averages the daily losses across assets before testing, which
  respects the correlation but leaves one series of 2,261 days.
- **Normal reference distribution** for the Diebold-Mariano statistic, with Newey-West errors.

## Reproduce

```bash
python scripts/acquire_yf_fd_etfs_daily.py --dataset-id yf_fd_etfs_daily_2015_2025_v3
python research/vol_benchmark/run_vol_benchmark.py \
    --raw-dir data/raw/yf_fd_etfs_daily_2015_2025_v3 \
    --manifest data/manifests/yf_fd_etfs_daily_2015_2025_v3.json
```

A fresh acquisition will not hash-match the snapshot used here, so the numbers may differ in late
decimal places. `pytest tests/test_vol_benchmark.py` checks the forecasting and test code on
synthetic data, including that no forecast uses future information.
