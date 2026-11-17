# Prospective forecast ledger, series `fdm-vol-v1` — protocol

**Status: DRAFT.** It becomes binding when this file is merged to `main`; the first entry is made by
the first scheduled run after that. Changes after that are dated amendments at the end of this file.

## Why

The two follow-up studies in this repository and its sibling were pre-specified, but on data that
had already been inspected. This ledger answers that limit directly: forecasts are written down
before the outcome exists, and each entry is timestamped by a service outside our control.

## Question

Out of sample, in real time: do the regime labels forecast the next week's variance better or worse
than a trailing-volatility quartile? This is the comparison of `research/vol_benchmark/` (which
found the labels worse, p = 0.012, on inspected data), repeated on data that does not exist yet.

## What is recorded, and when

A scheduled job runs every Saturday at 07:17 UTC. It fetches daily prices for SPY, QQQ, IWM, TLT and
GLD from 2015-01-01 to the latest close (Yahoo Finance, the repository's own acquisition script) and
writes one entry dated by that latest close (`as_of_date`). For each asset the entry holds:

- the regime label on `as_of_date` (frozen config
  `configs/experiments/fdm_historical_regime_study_v1.yaml`);
- the trailing-volatility quartile on `as_of_date` (`causal_volatility_bucket`, 20-day window);
- four variance forecasts for each of two horizons, the next 1 session and the next 5 sessions:
  `fdm`, `vol_bucket`, `unconditional` and `ewma`, computed exactly as in
  `research/vol_benchmark/vol_benchmark.py` with a minimum of 20 days per label.

Every forecast uses only data dated on or before `as_of_date`. The entry also records the commit of
the code that produced it, the sha256 of each input file, and the sha256 of the previous entry, so
the entries form a chain.

## Timestamping

Each entry file is stamped with OpenTimestamps (`ots stamp`), which commits its sha256 to the Bitcoin
blockchain through public calendar servers. Only the hash leaves the repository. The `.ots` proof is
committed beside the entry and upgraded by later runs once the Bitcoin attestation exists. Anyone
can check an entry with `ots verify`. The commit time on GitHub is a second, weaker witness.

## Rules

- **No overwriting.** The job refuses to write an entry whose date already exists.
- **No backfilling.** A missed week stays missing. A manual run is allowed and is labelled
  `"trigger": "manual"`; it still uses the latest close only.
- **Frozen method.** Any change to the forecasting code, the config or this protocol is an amendment
  and starts a new series id. Entries of different series are never pooled.
- **Raw prices are not committed.** Entries hold forecasts, labels and hashes only.

## Scoring (fixed now)

- **Target.** For an entry dated t and horizon h, the sum of squared daily returns over the h
  sessions after t, from prices fetched at scoring time.
- **Loss.** QLIKE, as in `vol_benchmark.qlike`.
- **Usable entries.** Entries are used in date order. An entry is dropped if fewer than 5 sessions
  separate it from the previous usable entry, so the 5-session targets never overlap.
- **Primary test.** On **2027-11-30**, once, using every usable entry with a complete 5-session
  target: the mean across the five assets of `fdm` minus `vol_bucket` QLIKE at the 5-session
  horizon, tested with `vol_benchmark.diebold_mariano` (two-sided, size 0.05). A positive
  difference means the labels are worse.
- **Minimum sample.** The test needs at least 30 usable entries. With fewer, the result is reported
  as "insufficient sample" and the test moves, once, to 2028-05-31.
- **Secondary, descriptive only.** The 1-session horizon; each asset separately; `fdm` and
  `vol_bucket` against `unconditional`; `ewma` as a scale reference.
- **Interim reports.** On 2027-01-31 and 2027-04-30 the mean losses are reported without a test and
  without any decision. They cannot change the design.

## What this can and cannot show

About 50 weekly observations give little power. The inspected-data study needed 2,261 daily
observations to detect a gap of 0.19 QLIKE. This ledger will detect only a gap several times larger,
and the report will state the minimum detectable effect from the realised standard error. A
non-rejection will not show the labels are as good as the benchmark. The ledger's main value is that
its record cannot be altered after the fact, and that it grows.

## Verifying

```bash
python research/forecast_ledger/verify_ledger.py          # hashes and chain
ots verify research/forecast_ledger/entries/<date>.json.ots
```

## Amendments

None.
