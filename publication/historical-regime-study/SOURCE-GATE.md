# Source Gate

**Purpose.** This document is the single admission gate for the D10-A publication pack. Fields
1–14 below are the **authoritative Phase 0 SOURCE-GATE MATRIX schema** for this program — exactly
these 14 things, each concise, in exactly this order, nothing substituted or added. Every other
piece of provenance, methodology, and disclosure this pack needs (artifact inventories, bootstrap
sparse-cell disclosure, full period-classification reasoning, full limitations list, standing
prohibitions, reviewer instructions) is preserved in full in the **named, unnumbered sections
after field 14** — nothing was deleted in restructuring this document, only relocated. It does not
introduce any new number; every value below is either a verbatim hash produced by `sha256sum`
against a committed file, or a verbatim quotation, cited as such.

---

## 1. Repository

`jmiaie/financial-dynamics-model`

## 2. Source PR / branch

D9-A accepted evidence: **PR #13**, branch `research/historical-regime-validation` (open,
unmerged, at the time of this pack's creation). This publication pack's own branch,
`publication/historical-regime-study`, is kept **distinct** from PR #13's branch — it is created
from PR #13's branch at a specific commit (field 3) but is not the same branch and does not touch
PR #13's own commits.

## 3. Accepted HEAD

`5d01cf8e2d3334602fbd8e2b114f6bff92d78f31` — the accepted D9-A evidence base / branch point this
publication pack was created from. **This value is fixed and does not change** as this publication
pack's own commits accumulate on top of it. **This publication branch's own current HEAD is a
different, later value** — this document never asserts they are the same; see "Additional
provenance" below for how to find the current HEAD, and never assume a historical revision of this
field's value elsewhere in this pack (e.g. in git commit messages) equals the branch's current tip.

## 4. Experiment ID

`fdm_hist_regime_v1` — **SPY-v1 is the sole primary experiment/result.** The v2 ETF runs
(QQQ/IWM/TLT/GLD + a second SPY run) are post-primary robustness/characterization only, under
experiment IDs `fdm_hist_regime_v1_robustness_{symbol}_{period}` — never a second primary, never
equal-status to SPY-v1. Full primacy reasoning: "Primacy statement (full)" below.

## 5. Dataset IDs

Primary: `yf_fd_etfs_daily_2015_2025_v1`. Robustness: `yf_fd_etfs_daily_2015_2025_v2`.

## 6. Dataset SHA / frozen identity

Primary v1 `dataset_canonical`: `91caa6cde08358091125a6576ff3f2be5666791b06df67d462c2aad6f771ada9`.
Robustness v2 `dataset_canonical`: `94ea2886772afc7adcbf070bf1563a59295c1e7b1f837e157dfe5880c5b12582`.
**v2 does not hash-match v1** for SPY, QQQ, IWM, or TLT; GLD alone matches byte-for-byte;
robustness v2 never replaces or restates primary SPY-v1. Full provenance: "Dataset provenance
detail" below.

## 7. 2025 / holdout status

**FINAL 2025 HOLDOUT EVALUATION.** Pre-study audit **CLEAR** (`research/holdout-audit.md`); the
primary config was frozen before this evaluation; the 2025 run then executed exactly once under
that frozen configuration. **Never** "HISTORICAL EVALUATION" for D9-A's primary 2025 result — that
was a category error in an earlier version of this pack, corrected 2026-09-18 (dated remediation
note: `QUANT-REDTEAM.md`). Full reasoning and the period-classification table: "Period
classification detail" below.

## 8. Final config SHA

`configs/experiments/fdm_historical_regime_study_v1.yaml`, sha256
`299b1ed0dffc77afc685721c27a261a61b6a7ef1d1a1734af2062cfba5001b16`. Full config detail (freeze
commit, freeze timestamp, robustness config): "Config detail" below.

## 9. Primary artifact path

`results/historical_regimes/fdm_hist_regime_v1_holdout_2025.json`. Full primary artifact inventory
(all three periods, dev/val/holdout): "Primary artifact inventory (full)" below.

## 10. Result artifact SHA

`7595a3474e839dc3e62def6687a9e7f3ad497aba5bfce711111fff2547f68937` (sha256 of the field-9 file).

## 11. Independent review status

External program-audit citation, accepted by Phase 0, **not independently re-derived or
re-verified by this pack's authors**:

> "Directive #9 Final Four-Stream Independent Program Audit — SIGN-OFF YES; P0=0; P1=0;
> HISTORICAL EMPIRICAL VALIDATION COMPLETE / ACCEPTED."

Full citation detail and framing: "Independent review status — full citation detail" below.

## 12. Primary finding

SPY 2025 FDM `mean_return_h1` ≈ **−0.00029295**; `CALM_TREND` was not selected in the 2025 holdout;
the study characterizes **subsequent risk characteristics** conditional on inferred states — not
true regime labels, and not directional forecast accuracy. v2 robustness numbers are never
elevated to primary status. Full results tables: `TECHNICAL-PAPER.md` §2.

## 13. Primary null / negative finding

**No statistically validated predictive edge was demonstrated by the primary study.** Earlier,
stronger predictive/alpha interpretations are withdrawn. This pack does **not** say proven alpha,
directional forecasting success, true latent regime recovery, or economically significant trading
edge — see the bootstrap evidence in `TECHNICAL-PAPER.md` §4 and `CASE-STUDY.md` (QQQ `RISK_OFF`'s
negative mean does not survive resampling at 90% confidence).

## 14. Primary limitation

Fixed, theory-based centroids with no ground-truth regime labels; primary v1 artifacts are
intentionally slim and lack several richer robustness metrics (downside vol, tail quantiles,
adverse drawdown, bootstrap CIs); `mean_return_h*`/`median_return_h*` are unweighted
regime-level averages, not bar-level statistics; v1/v2 dataset mismatch for 4 of 5 symbols; sparse
robustness bootstrap cells may use an effective block size below the requested 20 (174 verified
instances). Full limitations list: "Known limitations / caveats (full)" below.

---

# Additional provenance, methodology, and disclosure

Everything below is **unnumbered** by design (so future SOURCE-GATE schema changes cannot silently
break a numbered cross-reference again) and should be cited elsewhere in this pack by these
section names, not by a number.

## Additional provenance

- Immediate parent of the accepted HEAD (field 3): `6297e3c5046554a85bb81fff0e2abd742aa8dc89`
  ("D9-A: fix positive_return_freq metric, add SPY-v2 post-primary characterization").
- This publication branch (`publication/historical-regime-study`) was created from the accepted
  HEAD in field 3 (not from `main`; `main` does not contain this evidence while PR #13 is open and
  unmerged).
- **Current branch HEAD:** this publication pack has its own commit history on top of field 3's
  accepted HEAD (multiple publication-content commits as of this writing). This document
  deliberately does **not** hardcode that current HEAD value, because it changes with every
  publication-pack commit and a stale hardcoded value here would silently become wrong exactly the
  way an earlier version of this field did. To find the actual current HEAD: `git log --oneline -1`
  on this branch, or the HEAD SHA reported in the pull request itself, or `D10-STATUS.md`'s most
  recent remediation-round note (updated each round with that round's resulting HEAD).
- Experiment ID detail: primary `fdm_hist_regime_v1` (SPY, v1 dataset); secondary
  `fdm_hist_regime_v1_robustness_{symbol}_{period}` for `symbol` in `{spy, qqq, iwm, tlt, gld}` and
  `period` in `{dev_formation, val_2024, holdout_2025}` — 15 artifacts total. SPY's entry in this
  secondary set is the post-primary characterization run (source report §5.5), never a second
  primary.

## Program background

This is a **Directive #10-A (D10-A)** publication/communication deliverable. D10 is authorized as
a write-up phase for already-accepted, already-computed evidence; it performs **no new empirical
work** (no retraining, no retuning, no re-acquisition, no re-running any evaluation period, no
alteration of any existing result artifact). The evidence it packages was produced under
**Directive #9-A (D9-A)**, the historical-regime-validation research/remediation stream in this
repository, tracked upstream in `jmiaie/quant-research-portfolio` Issue #3. D9-A's own
defect-remediation work is recorded on PR #13 / branch `research/historical-regime-validation` and
in `research/historical-market-regime-study.md`, which this pack summarizes and repackages for
external readers without modification.

## Primary artifact inventory (full)

| Period | Path | sha256 |
|---|---|---|
| Development / formation (2015–2023) | `results/historical_regimes/fdm_hist_regime_v1_dev_formation.json` | `81a32e5362d81d630a5fb7e34cd807399b19562ca6586f40ae63aa90c0428b35` |
| Validation (2024) | `results/historical_regimes/fdm_hist_regime_v1_val_2024.json` | `fd89ee1551acad2a8474dce5494ae097a6c3af32057b9113a5877c862f3c56a6` |
| Holdout (2025) | `results/historical_regimes/fdm_hist_regime_v1_holdout_2025.json` | `7595a3474e839dc3e62def6687a9e7f3ad497aba5bfce711111fff2547f68937` |

The holdout-file hash matches field 10 above exactly; the dev_formation and val_2024 hashes were
computed independently in the original build of this pack (`sha256sum`) and re-verified in every
subsequent remediation round via `scripts/verify_pack.py`.

These three artifacts are intentionally **slim**: each `models[i]` entry carries `regime_counts`
and `key_metrics` only (`summary_records_omitted: true`, `transition_records_omitted: true`, per
`results/historical_regimes/README.md`). No `bootstrap_records`, `downside_vol`, `tail_q05`, or
`adverse_drawdown` fields exist in these three files — see "Known limitations / caveats (full)"
below.

## Secondary / robustness artifact inventory

All paths are `results/historical_regimes/fdm_hist_regime_v1_robustness_{symbol}_{period}.json`.
**None of these is, restates, or substitutes for the SPY-v1 primary result** (field 9/10 above).

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

## Dataset provenance detail

- **v1 (primary, SPY and all committed primary artifacts):** `yf_fd_etfs_daily_2015_2025_v1`.
  `dataset_canonical` sha256 (from `data/manifests/yf_fd_etfs_daily_2015_2025_v1.json`,
  `sha256.dataset_canonical` field): `91caa6cde08358091125a6576ff3f2be5666791b06df67d462c2aad6f771ada9`
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

## Config detail

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

## Methodology

**Model.** `FinancialDynamicsPipeline` (`src/financial_dynamics/pipeline.py:53`), default feature
windows (volatility span 20, trend window 14, drawdown window 60, correlation window 20, shock
threshold 2.0, z-score normalization over a 252-session window), temperature 1.0, hysteresis
threshold 0.15, minimum persistence 5 bars, majority-vote stabilization over 10 bars, seed 0.
Four regimes — `CALM_TREND`, `VOLATILE_TREND`, `CHOP`, `RISK_OFF` — classified against **fixed,
theory-based centroids** (not fit to any evaluation window; see the source report §4 for the
exact centroid vectors).

**Benchmarks**, all fit on data through the end of the history window recorded in each artifact (not formation alone where a validation year is available). That cutoff is period-dependent: `history_period.end_inclusive` is `2023-12-31` in the `val_2024` artifacts (formation only — the 2024 evaluation year is out of sample) and `2024-12-31` in the `holdout_2025` artifacts (formation plus validation — 2025 is out of sample); the `dev_formation` artifacts record no history window. The cutoff is never inside the window being evaluated and frozen before OOS classification
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
that framing throughout (see `CLAIM-REGISTER.md`).

## Bootstrap / uncertainty detail

**Requested parameterization:** block length 20 **regime occurrences**, not trading days (`effective_block = max(1, min(block_size, n))`; see §4.1 of `TECHNICAL-PAPER.md`), `n_bootstrap=1000`, confidence
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

**Verified scope.** A full scan of all `bootstrap_records[]` rows across all 15
robustness/characterization artifacts (both bootstrap methods, all four benchmark models plus the FDM pipeline where present — the
development artifacts contain no `persistence` model) finds **174 rows** with `n < 20` (`generate_tables.py`'s `gen_bootstrap_sparse_cell_table`;
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
and have no bootstrap fields ("Primary artifact inventory (full)" above).

## Known limitations / caveats (full)

Reproduced in substance from `research/historical-market-regime-study.md` §7, not softened:

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
- Bootstrap CIs exist for the robustness runs only, not for SPY's primary v1 result, for the same
  re-run-avoidance reason.
- Cross-asset robustness runs on a v2 dataset that does not hash-match v1 for four of five
  symbols ("Dataset provenance detail" above); the root cause is disclosed as unresolved, not
  assumed.
- `mean_realized_vol_h1 = 0.0` throughout is a known artifact of a single-observation
  standard deviation, not a finding.
- Fixed, theory-based centroids are a modeling choice; a different theoretical regime definition
  would produce different classifications. Formation-period regime incidence (e.g. very few
  `CALM_TREND` observations in some periods) limits statistical power for that regime.
- Cross-program note: this study's 2025 holdout is the event referenced as "FDM's already-executed
  2025 holdout" in a different repository's (`Advanced_Algorithmic_Trading_Simulator_public`)
  cross-repository exposure disclosure.

## Independent review status — full citation detail

> "Directive #9 Final Four-Stream Independent Program Audit — SIGN-OFF YES; P0=0; P1=0;
> HISTORICAL EMPIRICAL VALIDATION COMPLETE / ACCEPTED."

This text is reproduced exactly as supplied to this pack's authors, attributed as an external
citation (the "Grokbot four-stream independent audit"), accepted by Phase 0 of this program.
**This pack's authors did not have access to that audit and did not independently re-derive or
verify its sign-off**; it is quoted here as a citation of record, not as a claim this document
itself substantiates.

## Period classification detail

| Period | Dates | Label (use exactly this, everywhere in this pack) |
|---|---|---|
| Development / formation | 2015-01-01 to 2023-12-31 | **DEVELOPMENT / FORMATION** — used to fit benchmark thresholds and freeze configuration; not held out. |
| Validation | 2024-01-01 to 2024-12-31 | **VALIDATION** — evaluated before the final freeze; used to confirm the frozen configuration behaved reasonably, not to retune after inspection. |
| Holdout | 2025-01-01 to 2025-12-31 | **FINAL 2025 HOLDOUT EVALUATION.** Pre-study audit CLEAR (`research/holdout-audit.md`, verdict: "no evidence that calendar-year 2025 market data was previously inspected, tuned against, or used for empirical evaluation / performance claims in this repository"); the config was frozen (`freeze_record.frozen_for_holdout_utc`, 2026-09-16T02:58:00Z, "Config detail" above) before the 2025 run; the run then executed exactly once under that frozen configuration. That CLEAR-audit + freeze-then-single-execution sequence is what establishes holdout status — not the fact that 2025 market data existed and was in principle inspectable, which is true of every holdout period and is not itself evidence for or against holdout status (that was a category error in an earlier version of this pack; see the dated correction note in `QUANT-REDTEAM.md`). This label does **not** assert the period is "pristine," "untouched across every possible prior human exposure," or "prospective live-market validation" — only what the audit and freeze record directly support. |

## Primacy statement (full)

**SPY-v1 (the three artifacts in "Primary artifact inventory (full)" above) is the sole primary
result** of this study. SPY-v2 (the post-primary characterization run described in the source
report's §5.5) and the QQQ/IWM/TLT/GLD v2 robustness runs (§5.4, "Secondary / robustness artifact
inventory" above) are explicitly **post-primary / robustness / characterization only**. They are
never described in this pack as equal-status to SPY-v1, as a replacement primary, as a second
observation of the primary result, or as validating or invalidating it. Where SPY-v1 and SPY-v2
agree numerically (e.g. `mean_return_h1` in the 2025 period, matching to 4 significant figures
despite non-bit-identical input data), this pack reports that agreement as a factual consistency
observation, not as proof of either result.

## Standing prohibitions

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
  "READY FOR INDEPENDENT D10 REVIEW. NO MERGE. NO D11." (see `D10-STATUS.md`).
- **One narrow, explicitly authorized exception to "new files only under this directory":**
  `.github/workflows/publication-pack.yml`, added 2026-09-18 at the coordinating session's
  explicit direction (see `D10-STATUS.md`'s remediation-round notes) so this pack has its own CI
  verification gate, since `ci.yml` never runs on a PR targeting a non-`main` base branch. That
  workflow only checks out the repo, installs dependencies, and runs verification against
  already-committed files (`scripts/verify_pack.py`, `ruff`, `mypy`). Note that
  `scripts/verify_pack.py` is not read-only with respect to the working tree: it regenerates
  `tables/` and `figures/` in place in order to compare them against the committed bytes, and restores
them on **every** path — including a non-zero generator exit or a byte mismatch, both of which were
  forced and confirmed to restore the tracked figures (2026-09-18). Committed figures are deleted before
  regeneration so a no-op generator cannot be scored against the file's own stale bytes, and an empty
  committed-figure set is now a FAILURE rather than a skip. The workflow itself commits nothing, publishes nothing, and does not touch
  either of the two named publish workflows above.

## Reviewer instructions

To check any value in fields 1–14 or any relocated section above: every hash is independently
re-verifiable — with `sha256sum` against the named file at the branch's current HEAD, except the
two `dataset_canonical` entries, which are canonical hashes of the manifests' constituent file
hashes rather than hashes of the manifest files (see `RESULT-SOURCE-MAP.md`); every number
elsewhere in this pack traces to one of these files via `RESULT-SOURCE-MAP.md` and
`tables/source_map.json` (see that document's own "How to check a number" section). Running
`python publication/historical-regime-study/scripts/verify_pack.py` re-derives and re-checks every
hash cited in this document, confirms `tables/`/`figures/` regenerate byte-identically, and
confirms every `CLAIM-REGISTER.md` citation resolves — the same offline, no-rerun check this pack's
own CI workflow runs on every push.
