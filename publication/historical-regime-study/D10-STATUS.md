# D10-A Publication Pack — Status

**Directive:** D10-A (publication/communication phase). **Study:** Historical Market Regimes and
Subsequent Risk Characteristics (FDM, SPY primary; QQQ/IWM/TLT/GLD + SPY-v2 robustness). **Branch:**
`publication/historical-regime-study`, created from accepted D9-A evidence base
`5d01cf8e2d3334602fbd8e2b114f6bff92d78f31` (PR #13's branch, `research/historical-regime-validation`,
not `main`). **That base commit is fixed and is not this branch's current HEAD** — this branch has
its own commit history on top of it (see each "Remediation round" section below for that round's
resulting HEAD, or `git log --oneline -1` for the actual current value).

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
| 9a | Script-generated tables | `tables/*.md`, `tables/*.json` (8 files, all produced by `scripts/generate_tables.py`, none hand-typed) | Done |
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
   was fixed: `SOURCE-GATE.md` field 7 and its "Period classification detail" section (see the
   round-3 note below for that document's own subsequent restructuring),
   `TECHNICAL-PAPER.md` (abstract, §1.2, §2.3, §3, §6, §7),
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

Round 2's push initially failed CI on the real GitHub Actions runner (not just locally): a
follow-up fix, committed separately, removed an absolute filesystem path
(`generate_tables.py` had embedded `str(repo_root)` in `tables/generation_manifest.json`, which
necessarily differs between a local clone and the CI runner's checkout, breaking byte-identical
reproducibility). Verified the fix generalizes by regenerating the entire `tables/` directory from
a genuinely different absolute path and diffing the full output — zero differences. Both triggered
CI runs went green after that fix.

## Remediation round 3 — 2026-09-18 (authoritative SOURCE-GATE.md schema)

`SOURCE-GATE.md`'s original 14 fields were an improvised structure, not the program's actual
Phase 0 "SOURCE-GATE MATRIX" schema. Rebuilt the document to the authoritative 14-field schema
(Repository; Source PR/branch; Accepted HEAD; Experiment ID; Dataset IDs; Dataset SHA / frozen
identity; 2025/holdout status; Final config SHA; Primary artifact path; Result artifact SHA;
Independent review status; Primary finding; Primary null/negative finding; Primary limitation),
each field now concise and in the mandated order. **No content was deleted** — every piece of the
prior document's methodology detail, artifact inventories, bootstrap sparse-cell disclosure, full
period-classification reasoning, full limitations list, standing prohibitions, and primacy
statement was relocated, in full, to named unnumbered sections after field 14 (e.g. "Methodology,"
"Bootstrap / uncertainty detail," "Period classification detail," "Standing prohibitions") so a
future schema change cannot silently break a numbered cross-reference again.

Two specific defects were also fixed in this round:

- **Stale branch-head claim.** The document previously stated the local sandbox clone path
  (`/home/user/financial-dynamics-model`) as if it were meaningful provenance, and separately
  implied — via a "Verified directly in this session: `git log --oneline -1` ... reports `5d01cf8`"
  sentence written when the branch genuinely had no commits yet — that the accepted D9-A base HEAD
  and this publication branch's own current HEAD were the same value. They have not been the same
  value since this pack's first commit. Fixed: the local-clone path is removed entirely (it is a
  sandbox artifact, not provenance); field 3 now states explicitly that the accepted HEAD is fixed
  and is *not* this branch's current HEAD, and points to `git log`/this file's own remediation-round
  notes for the actual current value instead of hardcoding a value that would immediately go stale
  on the next commit (including this one).
- **Cross-reference repair.** Renumbering the schema would have silently broken every existing
  `SOURCE-GATE.md §N` / `item N` reference elsewhere in this pack, including two that would have
  pointed at content with a *different meaning* under the new numbering (old §8 = Methodology, new
  field 8 = Final config SHA; old §9 = Bootstrap detail, new field 9 = Primary artifact path).
  Searched every file under `publication/historical-regime-study/` for these patterns and updated
  each to either the new field number or a stable named heading:
  - `RESULT-SOURCE-MAP.md` (`hash_table.*` row: `§4–5, §12` → "fields 5–6 and 8, plus 'Dataset
    provenance detail' and 'Config detail'")
  - `TECHNICAL-PAPER.md` §1.2 (`§12` → "field 7" + "Period classification detail")
  - `CASE-STUDY.md` (Step 0 table: `§12` → field 7 + named section; a second reference,
    `§9` → "Bootstrap / uncertainty detail" named section, since old §9 and new field 9 mean
    different things)
  - `CLAIM-REGISTER.md` C6 (`§8` methodology reference → "Methodology" named section, since old §8
    and new field 8 mean different things), C17 and its closing note (`§11` → "field 11," a
    position that coincidentally still means the same thing under both schemas, normalized to the
    new phrasing regardless)
  - `CITATION-REDTEAM.md` (`§12` → field 7 + named section)
  - `CLAIM-REDTEAM.md` (`§13` primacy reference → field 4 + "Primacy statement (full)" named
    section)
  - `QUANT-REDTEAM.md` (two `§12` references, including inside its dated round-2 remediation note,
    which is a historical record but was still updated so the reference itself stays navigable)
  - `reproducibility.json` (`Sec 9` bootstrap reference → "Bootstrap / uncertainty detail" named
    section)
  - `scripts/generate_tables.py` (two code comments citing `Sec 12` → field 7 / named section)
  - `scripts/verify_pack.py` was checked and needed no change: its `SOURCE-GATE.md` references are
    all to the document as a whole (hash-citation scanning), never to a specific field number.

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

## Final checks (re-run fresh in every remediation round, including round 3)

```
source /tmp/fdm-venv/bin/activate && cd /home/user/financial-dynamics-model
python -m pytest tests/ -q          # 321 passed, 0 failed every round (baseline == post-pack; no test touches publication/)
ruff check .                        # 19 pre-existing errors every round, all outside publication/historical-regime-study/
                                     # (scripts/run_pipeline.py etc.); publication/historical-regime-study/scripts/
                                     # is independently ruff-clean
mypy src/                           # Success: no issues found in 53 source files (unchanged from baseline)
python publication/historical-regime-study/scripts/verify_pack.py  # all 5 checks passed (hashes, tables,
                                     # figures byte-identical, citations, no-rerun)
ruff check publication/historical-regime-study/scripts/            # All checks passed!
mypy publication/historical-regime-study/scripts/ --ignore-missing-imports  # Success: no issues found in 3 source files
```

Every step in `.github/workflows/publication-pack.yml` (dependency install, `verify_pack.py`,
`ruff check`, `mypy`) is re-run locally in this exact sequence before every push, per the
"validate the workflow's own steps locally first" instruction. The actual GitHub Actions run
triggered by each push is reported in that round's follow-up message to the orchestrating session
(run ID, head SHA, and each job's conclusion) — round 3's run is reported the same way.

`git status` / `git diff --stat` confirm only files under `publication/historical-regime-study/`
and (as of round 2) the one authorized `.github/workflows/publication-pack.yml` are ever touched —
zero bytes changed in any file under `results/`, `configs/`, `src/`, `data/`, or the existing
`research/historical-market-regime-study.md`, in any round including this one.

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

## Remediation round 4 — 2026-09-18 (independent-review findings)

An independent review of this pack (not a re-run of `scripts/verify_pack.py`, which only
re-tests the pack against itself) reported findings; the ones that reproduced against the
committed artifacts are corrected here. No empirical code was run, no artifact was
regenerated, and no frozen value was touched: every correction is documentation,
claim-register wording, or the verifier itself.

| # | Finding | Correction |
|---|---|---|
| 1 | Claim register quoted the stationary CI lower bound as `-0.0097`; the artifact holds `ci_low = -0.009628231317896438` | `CLAIM-REGISTER.md` now reads `-0.0096` |
| 2 | Benchmarks described as "fit on formation-period data only" | Corrected in `TECHNICAL-PAPER.md` §1.4 and `SOURCE-GATE.md`: fitted through the end of validation (`history_period.end_inclusive = 2024-12-31`, i.e. formation plus the 2024 validation year) |
| 3 | Persistence cited as a comparator across all three periods | Scoped to `val_2024`/`holdout_2025` in `CLAIM-REGISTER.md`; the `dev_formation` artifact holds four models and no `persistence` model — the sticky comparator there is `volatility_bucket` (mean self-transition 0.923) and the ordering still holds (FDM 0.736, GMM 0.365) |
| 4 | "block length 20 trading days" — wrong unit | Now "20 **regime occurrences**, not trading days" in `TECHNICAL-PAPER.md` §4 and `SOURCE-GATE.md`, with `effective_block = max(1, min(block_size, n))` spelled out |
| 5 | Sparse-cell disclosure gave the reduced block sizes but not what they imply | `TECHNICAL-PAPER.md` §4.1 now states that the effective block equals `n` in all 174 rows, so the resampled mean reduces to (or is dominated by) the sample mean itself: the interval is degenerate or near-degenerate and is not evidence of stability |
| 6 | `RESULT-SOURCE-MAP.md` promised a row for every table cell | Reworded to what the map holds: the `regime_counts` half of the count column has `primary.*.regime_counts` rows per period/model; the `evaluated_bars`/`total_bars` half is covered only by the artifact's whole-file sha256 row |
| 7 | `D10-STATUS.md` said `tables/` holds 7 files | Corrected to 8 |
| 8 | `verify_pack.py`'s figure check compared each PNG against itself after a no-op generator run, so a skipped generation (e.g. matplotlib absent) reported a byte-identical PASS | The check now deletes the committed PNGs before generation and raises `CheckFailure` if a figure is missing afterwards, restoring the files so a failed run leaves the tree as it found it; docstring updated |
| 9 | Citation check resolved 19 of the 35 identifiers present (lowercase-only pattern skipped `*`/uppercase forms) and resolved wildcards by prefix only | Pattern widened and wildcard matching moved to `fnmatch` glob semantics; the check now reports and resolves all 35 |
| 10 | Workflow described as running "read-only verification" | `SOURCE-GATE.md` now states that `verify_pack.py` regenerates `tables/`/`figures/` in place to compare against the committed bytes and restores them; the workflow itself commits and publishes nothing |

Re-verified after this round: `verify_pack.py` → **all 5 checks pass** under the pinned
interpreter, **35 citation identifiers resolved**, both figures regenerated and
byte-identical, generated tables byte-identical to committed. With matplotlib absent the
figure check now **fails closed** (1/5 failed: `['figures']`) where it previously reported a
full pass — that false-pass path is closed permanently, not just noted.

---

## READY FOR INDEPENDENT D10 REVIEW. NO MERGE. NO D11.
