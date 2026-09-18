# D10-A Publication Pack — Status

**Directive:** D10-A (publication/communication phase). **Study:** Historical Market Regimes and
Subsequent Risk Characteristics (FDM, SPY primary; QQQ/IWM/TLT/GLD + SPY-v2 robustness). **Base
commit:** `5d01cf8e2d3334602fbd8e2b114f6bff92d78f31` on `publication/historical-regime-study`,
based on PR #13's branch (`research/historical-regime-validation`), not `main`.

## Deliverables checklist

| # | Deliverable | Path | Status |
|---|---|---|---|
| 1 | Source Gate (14 numbered fields) | `SOURCE-GATE.md` | Done |
| 2 | Technical paper | `TECHNICAL-PAPER.md` | Done |
| 3 | Result-source traceability map | `RESULT-SOURCE-MAP.md` (+ `tables/source_map.json`, `tables/source_map_full.md`, 469 rows) | Done |
| 4 | Machine-readable reproducibility record | `reproducibility.json` | Done |
| 5 | Worked case study | `CASE-STUDY.md` | Done |
| 6 | Claim register (19 claims) | `CLAIM-REGISTER.md` | Done |
| 7a | Red-team: quantitative correctness | `QUANT-REDTEAM.md` | Done |
| 7b | Red-team: claim overreach | `CLAIM-REDTEAM.md` | Done |
| 7c | Red-team: citation integrity | `CITATION-REDTEAM.md` | Done |
| 8 | This status document | `D10-STATUS.md` | Done |
| 9a | Script-generated tables | `tables/*.md`, `tables/*.json` (7 files, all produced by `scripts/generate_tables.py`, none hand-typed) | Done |
| 9b | Script-generated figures | `figures/qqq_2025_holdout_bootstrap_ci_h1.png`, `figures/sparse_cell_effective_block_sizes.png` (matplotlib 3.11.2 available in `/tmp/fdm-venv`; both produced by `scripts/generate_figures.py`) | Done — matplotlib was available, so figures were generated, not skipped |
| 9c | Generator scripts | `scripts/generate_tables.py`, `scripts/generate_figures.py`, `scripts/verify_pack.py` (deterministic, offline, re-runnable against the frozen local artifacts; ruff-clean and mypy-clean) | Done |
| 10 | Publication-pack CI workflow (added in this remediation round) | `.github/workflows/publication-pack.yml` — validates the pack itself (hashes, table/figure reproducibility, citation integrity, no-rerun self-audit, lint, typecheck); never invokes the empirical study runner or acquisition script | Done |

All 9 original deliverable categories are present, plus the CI workflow added in this remediation
round. No deliverable was omitted or degraded.

## Red-team findings — full tally

Three genuine adversarial passes were performed (not a pro-forma "zero issues found" pass — see
each document for the specific mechanical checks actually run, including hash-by-hash
cross-verification of all 18 file/hash pairs cited, an exhaustive re-scan of all 174 sparse-cell
bootstrap rows rather than trusting the supplied count, and a scripted diff of every citation in
`CLAIM-REGISTER.md` against the real `source_map.json` row IDs).

| Pass | P0 | P1 | P2 | Resolution |
|---|---:|---:|---:|---|
| `QUANT-REDTEAM.md` | 0 | 1 | 4 | P1 fixed. P2: 2 fixed, 2 left with explicit rationale (no defect, a documented scope/notation choice). |
| `CLAIM-REDTEAM.md` | 0 | 2 | 3 | P1: 1 fixed (restored a dropped non-adjudication caveat), 1 investigated and cleared (no defect found — abstract already self-qualifies). P2: all 3 investigated and cleared (existing caveat placement judged sufficient in each case; no changes required). |
| `CITATION-REDTEAM.md` | 1 | 2 | 0 | P0 fixed: a real, correctly-computed number (QQQ 2025 `VOLATILE_TREND` bootstrap CI, also used in a figure) had no traceable row in the source map — extended the generator script to add it, re-ran, and confirmed zero unresolved citations. P1×2 fixed: citation-format inconsistencies (an abbreviated row-ID range, and a bare field-path citation with no corresponding hash-table row). |
| **Total** | **1** | **5** | **7** | **7 fixed outright; 1 P1 and 5 P2 resolved by investigation (either a real minor item left with stated rationale, or confirmed as no defect after a genuine check) — zero findings left as an unaddressed real defect.** |

No P0 or P1 finding was left uncorrected as an actual defect. Every "not fixed" disposition in the
three red-team documents states either (a) an explicit rationale for why the current form is
correct as-is (2 cases, both P2, in `QUANT-REDTEAM.md`), or (b) that the item was investigated and
no defect was actually present (1 P1 + 3 P2, in `CLAIM-REDTEAM.md`) — never "found a real problem
and chose to leave it."

## Remediation round — 2026-09-18 (post-initial-publish corrections)

Two required fixes, requested by the orchestrating session after independent review of the
initially published pack, both confirmed real:

1. **2025 period-label category error (P1).** The pack originally labeled the 2025 period
   "HISTORICAL EVALUATION" on the reasoning that "2025 data existed and was in principle
   inspectable before the freeze" — true of every holdout period ever run, and not itself evidence
   for or against holdout status. Corrected to **"FINAL 2025 HOLDOUT EVALUATION"**, grounded
   instead in `research/holdout-audit.md`'s explicit **CLEAR** verdict (no evidence of prior
   empirical inspection of 2025 data anywhere in this repository) combined with the config freeze
   preceding the single 2025 run — read and confirmed directly in this session. Every occurrence
   was fixed: `SOURCE-GATE.md` §12, `TECHNICAL-PAPER.md` (abstract, §1.2, §2.3, §3, §6, §7),
   `CASE-STUDY.md`, `CLAIM-REGISTER.md` C19 (the claim's *reasoning* was rewritten, not just
   relabeled), `CITATION-REDTEAM.md`, and the embedded label string in
   `scripts/generate_tables.py`'s `PERIOD_LABELS` (fixed at the source and tables regenerated, not
   hand-edited). `QUANT-REDTEAM.md` got a new dated remediation note rather than a silent rewrite
   of its prior (now-superseded-premise) P2 finding. A new `hash_table.holdout_audit_verdict`
   source-map row was added so the correction's own evidentiary basis is traceable like every
   other claim in this pack.
2. **Dedicated publication-pack CI workflow (required, not previously present).** Added
   `.github/workflows/publication-pack.yml`, triggered on pushes to this branch and on any PR
   touching `publication/historical-regime-study/**` regardless of base branch (unlike `ci.yml`,
   which only fires on PRs into `main` — the reason PR #15 originally showed zero checks). It runs
   `scripts/verify_pack.py` (a new script: re-verifies every hash cited in `SOURCE-GATE.md` against
   the real files, confirms `generate_tables.py`/`generate_figures.py` reproduce the committed
   `tables/`/`figures/` output, confirms every `CLAIM-REGISTER.md` citation resolves in
   `tables/source_map.json`, and self-audits that neither generator script invokes
   `scripts/run_historical_regime_study.py` or `scripts/acquire_yf_fd_etfs_daily.py`), plus `ruff
   check` and `mypy` on the pack's scripts. All steps were run and passed locally in this session
   before pushing (see below).

This fix uncovered one real, secondary defect while building the hash-verification check: two
`tables/source_map.json` rows (the `dataset_canonical` embedded-field citations) were conflating
"whole-file sha256" with "value of an embedded field" under one `sha256` column, which a naive
whole-file re-verification would have wrongly flagged as an inconsistency. Fixed properly by
adding a `kind` field (`whole_file_sha256` vs `field_value`) to the `SourceMap` schema in
`generate_tables.py`, rather than special-casing row IDs in the checker.

## Independent verification performed in this session (not just re-reading the source report)

- Confirmed branch (`publication/historical-regime-study`) and commit
  (`5d01cf8e2d3334602fbd8e2b114f6bff92d78f31`, parent `6297e3c5046554a85bb81fff0e2abd742aa8dc89`)
  directly via `git log`/`git rev-parse`.
- Recomputed sha256 for all three primary artifacts, all 15 robustness artifacts, both dataset
  manifests, the v2 provenance file, and both configs, and confirmed every hash cited anywhere in
  this pack against those recomputed values (18 file/hash pairs checked programmatically with
  zero mismatches; see `QUANT-REDTEAM.md` check #2).
- Read `src/financial_dynamics/backtesting/metrics.py` directly to confirm the sparse-cell
  effective-block-size mechanism (`effective_block = max(1, min(block_size, n))`,
  `block_bootstrap_mean_ci` lines 465/476) and independently re-scanned all 15 robustness
  artifacts' `bootstrap_records[]`, finding exactly 174 rows with `n < 20` — matching, not merely
  restating, the count supplied at task start.
- Independently recomputed the SPY-v1-vs-SPY-v2 4-significant-figure agreement claim (C10) from
  both raw JSON files rather than trusting the source report's restatement.
- Traced the QQQ 2025 `RISK_OFF` case study end-to-end against the live artifact and against its
  `superseded_150_resamples/` predecessor, confirming the point estimate is byte-identical across
  the 150-vs-1000-resample regeneration and only the CI bounds moved.
- Ran the full existing test suite before and is re-confirmed after this pack's script edits (see
  below) — 321 tests, all passing, unchanged from baseline.

## Final checks (run in this session)

```
source /tmp/fdm-venv/bin/activate && cd /home/user/financial-dynamics-model
python -m pytest tests/ -q          # 321 passed, 0 failed (baseline == post-pack; no test touches publication/)
ruff check .                        # 19 pre-existing errors, all outside publication/historical-regime-study/
                                     # (scripts/run_pipeline.py etc.); publication/historical-regime-study/scripts/
                                     # is independently ruff-clean
mypy src/                           # Success: no issues found in 53 source files (unchanged from baseline)
python publication/historical-regime-study/scripts/verify_pack.py  # all 5 checks passed (hashes, tables,
                                     # figures byte-identical, citations, no-rerun)
ruff check publication/historical-regime-study/scripts/            # All checks passed!
mypy publication/historical-regime-study/scripts/ --ignore-missing-imports  # Success: no issues found in 3 source files
```

Every step in `.github/workflows/publication-pack.yml` (dependency install, `verify_pack.py`,
`ruff check`, `mypy`) was run locally in this exact sequence before pushing, per the "validate the
workflow's own steps locally first" instruction. The actual GitHub Actions run triggered by the
push is reported in the follow-up message to the orchestrating session (run ID, head SHA, and
each job's conclusion).

`git status` / `git diff --stat` confirm only new, untracked files under
`publication/historical-regime-study/` — zero bytes changed in any file under `results/`,
`configs/`, `src/`, `data/`, or the existing `research/historical-market-regime-study.md`.

## Standing prohibitions — confirmed in force

- No empirical rerun of any kind was performed. Every number in this pack was read from an
  already-committed artifact; the two generator scripts perform no network access and write only
  under `publication/historical-regime-study/`.
- No existing artifact, config, source file, or dataset manifest was modified.
- `research/experiment-ledger.csv` was not touched.
- This pull request is opened as a **draft** against PR #13's own branch
  (`research/historical-regime-validation`), not `main`; it is not merged by this session.
- Nothing was published externally (no npm/pypi publish, no website deploy, no use of
  `.github/workflows/mirror-to-public.yml` or `.github/workflows/publish.yml`).
- No Directive #11 work of any kind was started.

---

## READY FOR INDEPENDENT REVIEW. NO MERGE. NO D11.
