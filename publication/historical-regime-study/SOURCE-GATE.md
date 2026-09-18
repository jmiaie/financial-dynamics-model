# Source Gate

**Purpose.** This document is the single admission gate for the D10-A publication pack: every
downstream document in `publication/historical-regime-study/` traces back to the facts recorded
here. It does not introduce any new number; every value below is either a verbatim hash produced
by `sha256sum` against a committed file at the accepted HEAD, or a verbatim quotation, cited as
such.

---

## 1. Program / directive citation and this study's place in it

This is a **Directive #10-A (D10-A)** publication/communication deliverable. D10 is authorized as
a write-up phase for already-accepted, already-computed evidence; it performs **no new empirical
work** (no retraining, no retuning, no re-acquisition, no re-running any evaluation period, no
alteration of any existing result artifact). The evidence it packages was produced under
**Directive #9-A (D9-A)**, the historical-regime-validation research/remediation stream in this
repository (`financial-dynamics-model`), tracked upstream in `jmiaie/quant-research-portfolio`
Issue #3. D9-A's own defect-remediation work is recorded on branch
`research/historical-regime-validation` (PR #13, open at the time of this pack's creation) and in
`research/historical-market-regime-study.md`, which this pack summarizes and repackages for
external readers without modification.

## 2. Repository + accepted HEAD SHA + immediate parent

- Repository: `financial-dynamics-model` (local clone at `/home/user/financial-dynamics-model`)
- Accepted HEAD SHA (this pack's base commit): `5d01cf8e2d3334602fbd8e2b114f6bff92d78f31`
  ("D9-A: raise block-bootstrap resample count from 150 to 1000 (required standard)")
- Immediate parent: `6297e3c5046554a85bb81fff0e2abd742aa8dc89`
  ("D9-A: fix positive_return_freq metric, add SPY-v2 post-primary characterization")
- Branch for this pack: `publication/historical-regime-study`, created from the accepted HEAD
  above (not from `main`; `main` does not contain this evidence at the time of writing since PR
  #13 is still open and unmerged).
- Verified directly in this session: `git log --oneline -1` on this branch reports
  `5d01cf8 D9-A: raise block-bootstrap resample count from 150 to 1000 (required standard)`;
  `git rev-parse HEAD~1` reports `6297e3c5046554a85bb81fff0e2abd742aa8dc89`.

## 3. Experiment ID(s) in scope

- **Primary:** `fdm_hist_regime_v1` (SPY, `yf_fd_etfs_daily_2015_2025_v1` dataset).
- **Secondary / robustness / characterization:** `fdm_hist_regime_v1_robustness_{symbol}_{period}`
  for `symbol` in `{spy, qqq, iwm, tlt, gld}` and `period` in
  `{dev_formation, val_2024, holdout_2025}` (15 artifacts total; SPY's entry here is the
  post-primary characterization run, §5.5 of the source report, never a second primary).

## 4. Dataset ID(s) + `dataset_canonical` sha256

- **v1 (primary, SPY and all committed primary artifacts):** `yf_fd_etfs_daily_2015_2025_v1`.
  `dataset_canonical` sha256 (from `data/manifests/yf_fd_etfs_daily_2015_2025_v1.json`,
  `sha256.dataset_canonical` field):
  `91caa6cde08358091125a6576ff3f2be5666791b06df67d462c2aad6f771ada9`
  (manifest file itself, whole-file sha256:
  `e969413cd8dc6ec45697c6da34196355c6f7cfeb031a5f16584b22a88dd60344`).
- **v2 (robustness only, QQQ/IWM/TLT/GLD + SPY post-primary characterization):**
  `yf_fd_etfs_daily_2015_2025_v2`. `dataset_canonical` sha256:
  `94ea2886772afc7adcbf070bf1563a59295c1e7b1f837e157dfe5880c5b12582`
  (manifest file whole-file sha256: `8e55e45f4054ae28f48ae5e69d6979b1033c3f67f061a18b1531b93d552a3e8c`).
- **v2 does NOT hash-match v1 for SPY, QQQ, IWM, or TLT.** Per-file sha256 comparison in
  `data/manifests/yf_fd_etfs_daily_2015_2025_v2_PROVENANCE.md`
  (sha256 `8c23009abd5dee1930a02d1ec0011a78c21d9cfa41075be4ac8106976df3b83d`): **GLD alone** matches
  byte-for-byte between v1 and v2 (GLD pays no distributions, so its raw-close series is
  bit-reproducible across retrievals; the other four carry dividend adjustment, which is not).
  The true v1 raw payload for QQQ/IWM/TLT/GLD was never committed (`data/raw/` is gitignored) and
  is confirmed unrecoverable (owner confirmation, 2026-09-17, per the provenance file) — so this
  mismatch **cannot be root-caused further** and is not papered over: v2 is adopted as the input
  for robustness/characterization only, explicitly disclosed as non-bit-identical to v1, and
  SPY's own v1 primary result is untouched by this fact.

## 5. Config path(s) + sha256

- **Primary (frozen-for-holdout):** `configs/experiments/fdm_historical_regime_study_v1.yaml`,
  sha256 = `299b1ed0dffc77afc685721c27a261a61b6a7ef1d1a1734af2062cfba5001b16`.
  Freeze commit `596a22527b6f0107ba5baf55dd2edd68a1d991fe` ("D9-A: FINAL CONFIGURATION FROZEN for
  holdout"); freeze timestamp `2026-09-16T02:58:00Z` (`freeze_record.frozen_for_holdout_utc` in
  the config file). `status: frozen-for-holdout` and `constraints.no_retune_after_freeze: true`
  are both present in the committed file as read directly.
- **Robustness/characterization:**
  `configs/experiments/fdm_historical_regime_study_v2_robustness.yaml`,
  sha256 = `6e1044b4e46ae297f52efcd2b2a09d981d6a71d702fe2b58fd8a73ff9e746b4b`. Per the source
  report, methodology is byte-identical to the frozen v1 config (same centroids, same feature
  windows, same frozen knobs) — only the input dataset differs.

## 6. Primary artifact paths + sha256 (all three, hashed independently in this session)

| Period | Path | sha256 |
|---|---|---|
| Development / formation (2015–2023) | `results/historical_regimes/fdm_hist_regime_v1_dev_formation.json` | `81a32e5362d81d630a5fb7e34cd807399b19562ca6586f40ae63aa90c0428b35` |
| Validation (2024) | `results/historical_regimes/fdm_hist_regime_v1_val_2024.json` | `fd89ee1551acad2a8474dce5494ae097a6c3af32057b9113a5877c862f3c56a6` |
| Holdout (2025) | `results/historical_regimes/fdm_hist_regime_v1_holdout_2025.json` | `7595a3474e839dc3e62def6687a9e7f3ad497aba5bfce711111fff2547f68937` |

The holdout-file hash matches the value supplied in this task's ground truth exactly; the
dev_formation and val_2024 hashes were computed independently in this session (`sha256sum`) and
were not separately supplied — both are reported here as directly observed.

These three artifacts are intentionally **slim**: each `models[i]` entry carries `regime_counts`
and `key_metrics` only (`summary_records_omitted: true`, `transition_records_omitted: true`, per
`results/historical_regimes/README.md`). No `bootstrap_records`, `downside_vol`, `tail_q05`, or
`adverse_drawdown` fields exist in these three files — see item 10 (limitations).

## 7. Secondary / robustness artifact paths (all 15, explicitly non-primary)

All paths are `results/historical_regimes/fdm_hist_regime_v1_robustness_{symbol}_{period}.json`.
**None of these is, restates, or substitutes for the SPY-v1 primary result (item 6).**

| Symbol | Period | sha256 |
|---|---|---|
| SPY | dev_formation | `d7cfd94cf9029f201caac0a4dbe826b2473dfbe107c1a05629486155241963ae` |
| SPY | val_2024 | `ca2dc4574b4f6cb7cedb2c43554ae2226d90a92ccdaa96f200578bc1e8b75759` |
| SPY | holdout_2025 | `b9705206cb1ce8f27f2e4627879bb3f9feb8618f34882e1f8c32b4c2647500b7` |
| QQQ | dev_formation | `0d20fb114c671f37c2afcf9f9ffb733a9e7cd2fad4456ac5bfa8b7df8c47f08c` |
| QQQ | val_2024 | `325bb10004e54a7a8fe31407b0f64d312cc6e6bc1f1b368ae906e84877c68559` |
| QQQ | holdout_2025 | `7af9c81baf9ee89568969323a53cfa35483a2d74580ea16f5ff532e45dbc867d` |
| IWM | dev_formation | `6c2bc977bf717a6a072993abb679427207c77372914a74268567a25122c0d8e5` |
| IWM | val_2024 | `bc5a25cf7a244857f90bd9388210a9e4757a0357ecbc35e34507a0b06dcf67ae` |
| IWM | holdout_2025 | `244190c6ea0485d5cc3a2eb23a42a968b05a74da5023f0710f509ee8e6a34785` |
| TLT | dev_formation | `be7c9281381b21a5d711aef69aefbe2df2e4722e4b686d2c2965a1e8cb49f3fe` |
| TLT | val_2024 | `cdf644beb2436779ec16c5e7402ca4ac8291ad1e4f64857b9207ffe256bd02f4` |
| TLT | holdout_2025 | `ec814ac9812fbcfe322e21c35e489a30c2a7203a7d4621ad8b9dc302b8df0828` |
| GLD | dev_formation | `55db000677bc007c0af04affec7de1eabc821ceb2a72091c82840f98c83a83e5` |
| GLD | val_2024 | `c7b8fe49fa67c18a18105d9fb5f0d547498f57569133757013849beacbd7c137` |
| GLD | holdout_2025 | `cb9c04ba4ed4760c3738177f0a46e9c9744f5f61c280fe5a4071a75410e7308f` |

Pre-fix (150-resample) versions of all 15 files are preserved, not deleted, at
`results/historical_regimes/superseded_150_resamples/`; this pack does not use their numbers
except in `CASE-STUDY.md`, where one is cited explicitly as the superseded value for contrast.

## 8. Methodology summary

**Model.** `FinancialDynamicsPipeline` (`src/financial_dynamics/pipeline.py:53`), default feature
windows (volatility span 20, trend window 14, drawdown window 60, correlation window 20, shock
threshold 2.0, z-score normalization over a 252-session window), temperature 1.0, hysteresis
threshold 0.15, minimum persistence 5 bars, majority-vote stabilization over 10 bars, seed 0.
Four regimes — `CALM_TREND`, `VOLATILE_TREND`, `CHOP`, `RISK_OFF` — classified against **fixed,
theory-based centroids** (not fit to any evaluation window; see the source report §4 for the
exact centroid vectors).

**Benchmarks**, all fit on formation data only and frozen before OOS classification
(`src/financial_dynamics/benchmarks/baselines.py`):
- `PersistenceClassifier` (line 40) — trivial "last observed regime persists."
- `VolatilityBucketClassifier` (line 73) — trailing 20-day realized-volatility quartile buckets.
- `TrendVolGridClassifier` (line 128) — trailing 14-session return sign × 20-session vol median
  split, four quadrant states.
- Gaussian mixture — unsupervised GMM, seed 0, fit on formation data.

**Metrics.** `historical_regime_statistics` and `regime_bootstrap_uncertainty`
(`src/financial_dynamics/backtesting/metrics.py:269` and `:486`) compute, per (regime, horizon)
group: `count`, `mean_return`, `median_return`, `realized_vol`, `downside_vol`,
`positive_return_freq` (fraction of **occurrences** whose horizon-level compounded forward return
was positive — corrected 2026-09-17; regression test
`tests/test_backtesting.py::TestHistoricalRegimeStatistics::test_positive_return_freq_is_horizon_level_not_daily_level`),
`tail_q05`/`tail_q25`, `mean_adverse_drawdown`/`worst_adverse_drawdown` (intra-horizon
peak-to-trough decline, not just start-to-end return), `mean_duration`/`median_duration`, and
`transition_rate` (self-transition). Runner script: `scripts/run_historical_regime_study.py`.

**Scope of the primary claim.** This study characterizes **subsequent risk characteristics**
conditional on regime (volatility, tail risk, drawdown, self-transition persistence) — it is
**not** a directional-forecast-accuracy or trading-alpha claim. The source report states this
explicitly in its Research Question section and repeats it in Limitations; this pack preserves
that framing throughout (see CLAIM-REGISTER.md).

## 9. Bootstrap methodology + sparse-cell effective-block-size disclosure

**Requested parameterization:** block length 20 trading days, `n_bootstrap=1000`, confidence
90%, both `moving_block` and `stationary` methods, fixed `seed=0`
(`block_bootstrap_mean_ci`/`regime_bootstrap_uncertainty`,
`src/financial_dynamics/backtesting/metrics.py:428` and `:486`; default arguments in the function
signatures match what was actually run and recorded in every artifact's
`bootstrap_records[].n_bootstrap`).

**Sparse-cell mechanism, disclosed explicitly.** `block_bootstrap_mean_ci` computes
`effective_block = max(1, min(block_size, n))` (line 465) and reports **that** (possibly-reduced)
value back in each record's own `"block_size"` field (line 476) — it does **not** always
literally equal the requested 20. When a regime's occurrence count `n` at a given horizon is
smaller than 20, the effective block used for that resampling is `n` itself (or `n` at that
horizon), not the nominal 20.

**Verified scope, this session.** A full scan of all `bootstrap_records[]` rows across all 15
robustness/characterization artifacts (both bootstrap methods, all five benchmark models where
present) finds **174 rows** with `n < 20` (`generate_tables.py`'s `gen_bootstrap_sparse_cell_table`;
full row-by-row listing in `tables/bootstrap_sparse_cells_full.md`).

**Two concrete, independently re-verified examples:**
1. `results/historical_regimes/fdm_hist_regime_v1_robustness_gld_dev_formation.json`,
   `financial_dynamics_pipeline` model, `CALM_TREND`, horizon 1: `regime_counts.CALM_TREND = 12`,
   `bootstrap_records[].n = 12`, `bootstrap_records[].block_size = 12` (not 20).
2. `results/historical_regimes/fdm_hist_regime_v1_robustness_gld_holdout_2025.json`,
   `volatility_bucket` **benchmark** model (not the FDM pipeline; that model's own `CALM_TREND`
   count in this file is `n=11`, itself already below 20), `CALM_TREND`, horizon 1:
   `regime_counts.CALM_TREND = 4`, `bootstrap_records[].n = 4`, `bootstrap_records[].block_size = 4`.

This disclosure applies **only** to the 15 robustness/characterization artifacts, which are the
only artifacts carrying `bootstrap_records` at all — the three SPY-v1 primary artifacts are slim
and have no bootstrap fields (item 6).

## 10. Known limitations / caveats (reproduced from the source report, not softened)

Verbatim in substance from `research/historical-market-regime-study.md` §7:

- Downside volatility, drawdown/maximum-adverse-excursion, positive-return frequency, and
  5th-percentile forward return are **still not reported for SPY's primary v1 result itself**;
  the v1 artifacts remain intentionally slim, and regenerating those fuller tables from the
  primary v1 dataset would require either the lost v1 raw CSVs or re-running the primary study,
  which this program does not do.
- `mean_return_h*`/`median_return_h*` are **unweighted averages across each period's observed
  regimes** of that regime's own mean/median, not bar-level statistics of the raw return series —
  a regime with 5 bars and one with 500 bars contribute equally. This limits mean-vs-median or
  model-vs-model comparisons; an earlier report draft drew an unsupported downside-skew
  conclusion from this comparison, which is retracted in the source report.
- Bootstrap CIs exist for the §5.4/§5.5 robustness runs only, not for SPY's primary v1 result,
  for the same re-run-avoidance reason.
- Cross-asset robustness runs on a v2 dataset that does not hash-match v1 for four of five
  symbols (item 4); the root cause is disclosed as unresolved, not assumed.
- `mean_realized_vol_h1 = 0.0` throughout is a known artifact of a single-observation
  standard deviation, not a finding.
- Fixed, theory-based centroids are a modeling choice; a different theoretical regime definition
  would produce different classifications. Formation-period regime incidence (e.g. very few
  `CALM_TREND` observations in some periods) limits statistical power for that regime.
- Cross-program note: this study's 2025 holdout is the event referenced as "FDM's already-executed
  2025 holdout" in a different repository's (`Advanced_Algorithmic_Trading_Simulator_public`)
  cross-repository exposure disclosure.

## 11. Program sign-off citation (external citation, reproduced verbatim — not independently re-verified in this pack)

> "Directive #9 Final Four-Stream Independent Program Audit — SIGN-OFF YES; P0=0; P1=0;
> HISTORICAL EMPIRICAL VALIDATION COMPLETE / ACCEPTED."

This text is reproduced exactly as supplied to this pack's authors, attributed as an external
citation (the "Grokbot four-stream independent audit"). **This pack's authors did not have access
to that audit and did not independently re-derive or verify its sign-off**; it is quoted here as
a citation of record, not as a claim this document itself substantiates.

## 12. Period classification table

| Period | Dates | Label (use exactly this, everywhere in this pack) |
|---|---|---|
| Development / formation | 2015-01-01 to 2023-12-31 | **DEVELOPMENT / FORMATION** — used to fit benchmark thresholds and freeze configuration; not held out. |
| Validation | 2024-01-01 to 2024-12-31 | **VALIDATION** — evaluated before the final freeze; used to confirm the frozen configuration behaved reasonably, not to retune after inspection. |
| Holdout | 2025-01-01 to 2025-12-31 | **HISTORICAL EVALUATION** (evaluated once, after the freeze, on data not seen during formation/validation). **Never** described as "untouched holdout" or "clean holdout" — 2025 data existed and was in principle inspectable before the freeze date (2026-09-16); "historical evaluation" is the accurate label and is used throughout this pack. |

## 13. Primacy statement

**SPY-v1 (the three artifacts in item 6) is the sole primary result** of this study. SPY-v2 (the
post-primary characterization run described in the source report's §5.5) and the QQQ/IWM/TLT/GLD
v2 robustness runs (§5.4, item 7 above) are explicitly **post-primary / robustness /
characterization only**. They are never described in this pack as equal-status to SPY-v1, as a
replacement primary, as a second observation of the primary result, or as validating or
invalidating it. Where SPY-v1 and SPY-v2 agree numerically (e.g. `mean_return_h1` in the 2025
period, item matches to 4 significant figures despite non-bit-identical input data), this pack
reports that agreement as a factual consistency observation, not as proof of either result.

## 14. Standing prohibitions in force for this publication pack

- No retraining, retuning, re-acquisition of data, or re-running of any evaluation period.
- No modification of any existing result artifact, config, dataset manifest, or source file under
  `results/`, `configs/`, `src/`, `data/`, or the existing `research/historical-market-regime-study.md`.
- No modification of `research/experiment-ledger.csv` (append-only program convention; out of
  scope for this docs-only pack).
- This pack is **draft-only**: it does not merge its own pull request, does not touch `main`, and
  does not touch PR #13 (`research/historical-regime-validation`) except as this PR's read-only
  base branch.
- No external publication of any kind (no npm/pypi publish, no website deploy, no use of
  `.github/workflows/mirror-to-public.yml` or `.github/workflows/publish.yml`).
- No start of any Directive #11 work. This pack's terminal state is
  "READY FOR INDEPENDENT REVIEW. NO MERGE. NO D11." (see `D10-STATUS.md`).
