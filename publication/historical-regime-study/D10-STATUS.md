# D10-A Publication Pack — Status

**Directive:** D10-A (publication/communication phase). **Study:** Historical Market Regimes and
Subsequent Risk Characteristics (FDM, SPY primary; QQQ/IWM/TLT/GLD + SPY-v2 robustness). **Branch:**
`publication/historical-regime-study`, created from accepted D9-A evidence base
`5d01cf8e2d3334602fbd8e2b114f6bff92d78f31` (PR #13's branch, `research/historical-regime-validation`,
not `main`). **That base commit is fixed and is not this branch's current HEAD** — this branch has
its own commit history on top of it (see each "Remediation round" section below for that round's
resulting HEAD, or `git log --oneline -1` for the actual current value).

## Final Directive #10 program sign-off — 2026-09-23

**This section is current. It supersedes every "sign-off pending" statement in this
file**, including the reconciliation-phase lifecycle conclusion and program-state
lines recorded below, which are retained unedited as the historical record.

An independent clean-room review of the live four-stream D10 heads concluded
`DIRECTIVE #10 PUBLICATION PACK SIGN-OFF: YES`, with final counts **P0 = 0, P1 = 0,
P2 = 3, P3 = 14** and this lane's verdict **ACCEPT-WITH-RESIDUALS**. No accepted
dataset, configuration, manifest, result artifact, experiment identity, ledger row,
table, figure, estimate, interval or finding was found to have changed.

D10 publication-pack program sign-off for D10-A is therefore **COMPLETE** as of
**2026-09-23**.

| Final closure record | Value |
| --- | --- |
| Independently signed reconciliation head | `d5e45eed9d01df09150ee07f3450c067ad6f90f1` |
| Current `main` merge head | `5eccc478d633c474c3003f8b4534040cead51027` |
| Merge tree vs signed head | **Byte-identical — zero changed files.** `git diff --name-only d5e45eed9d01df09150ee07f3450c067ad6f90f1 5eccc478d633c474c3003f8b4534040cead51027` returns empty (re-measured 2026-09-23). The integration carried the reviewed tree forward unchanged. |
| Accepted evidence changed by integration | **None.** No rerun, retrain, refit, retune, reacquire, or result replacement was performed. |
| Administrative status | Closure **packaged, not merged**. This section is a status record; it is **not merge authorization**, and it does not decide whether Directive #10 is formally closed. |

### What this sign-off does not assert

It records that the publication pack on `main` is the independently reviewed pack.
**Explicitly refused claims.** This section does **not** assert any of the following
phrases, or their substance: "predictive edge"; "alpha"; "economic significance";
deployment, production or live-trading approval; or prospective/live validation. The pack's regime-conditional results are descriptive of the historical sample studied; no out-of-sample, forward-looking or tradeable-performance claim is made or implied.

### Preserved findings and classifications

- The accepted D9-A evidence base `5d01cf8e2d3334602fbd8e2b114f6bff92d78f31` and every
  finding, number, table, figure and limitation the pack records.
- The corrected 2026-09-21 integration record: the pack reached `main` as **direct
  commits only**, and PR #15's merge `2f403dad18` is **not an ancestor of `main`**.
- The disclosed integration nuance that none of `main`'s seven merge commits touches
  any path under `publication/`.

### Residual register — preserved, not closed

Sign-off does **not** imply zero remaining maintenance work, and this closure change
does not silently close any residual. The independent review recorded:

**P2 (disclosed, open)**

1. The pack verifier does not restore original figure bytes on every failure path
   (it still fails closed). **Deliberately not touched by this closure change.**

**P3 (shared register, disclosed, open)**

- FDM formation/development explanatory prose and early publication-commit ordering;
- Stat-Arb canonical source-gate presentation and stale superseded-ledger-row count;
- Options stale source-map manifest-hash instruction;
- Sentiment combined-model margin wording and majority-baseline model description;
- the shared reconciliation-baseline table omission (**corrected in this round**) and the
  A/B/C workflow-trigger prose (**corrected in this round**) — the only two shared
  administrative items authorized for correction in this round.

### Supersession wording

The reconciliation-phase conclusions **"INTEGRATED ON MAIN / FINAL D10 PROGRAM
SIGN-OFF PENDING"** and **"Final D10 program sign-off remains PENDING"** are
superseded by this statement:

> **D10 publication-pack program sign-off is complete as of 2026-09-23 at merged
> head `5eccc478d633c474c3003f8b4534040cead51027`, on the independently signed head `d5e45eed9d01df09150ee07f3450c067ad6f90f1`, with the merge tree
> byte-identical to that signed head and the P2/P3 residuals above preserved and
> undisputed.**

The superseded wording is retained verbatim below as the reconciliation-phase
record rather than rewritten.

---

## Post-review integration status

This publication pack was originally authored and reviewed under a
no-merge / stop-at-independent-review instruction. That language is preserved
below as a historical record of the authoring phase.

The pack has subsequently been integrated into `main`. This integration does
not, by itself, constitute Directive #10 program sign-off.

Current lifecycle status: **SUPERSEDED 2026-09-23 — see "Final Directive #10
program sign-off" at the top of this file.** As recorded at the 2026-09-21
reconciliation, this cell read **"INTEGRATED ON MAIN / FINAL D10 PROGRAM
SIGN-OFF PENDING."** That wording is retained here as the reconciliation-phase
record rather than rewritten.

| Integration record | Value |
| --- | --- |
| Accepted D9 head | `5d01cf8e2d3334602fbd8e2b114f6bff92d78f31` |
| Cleared publication head / accepted publication ancestor | `7c1208106378203e0b6dbe5ce513c659bcd07b2c` (PR #15 head) |
| `main` head at the reconciliation baseline (frozen 2026-09-21; a reference point, not a permanently-current value — verify with `git ls-remote <repo> refs/heads/main`)  `2b0a919e4500dabda3c0b6430494361a50d36e4f` — restored 2026-09-23; this cell was left blank at reconciliation. |
| Integration path | **Corrected 2026-09-21 — the merge chain previously recorded here was inaccurate.** Measured on `main` (`2b0a919e`): the pack's cleared head `7c12081` and its sibling pack commits (`3b69508` → `1539cf3` → `3d7143d` → `6f339d8` → `7c12081`) sit on `main`'s own history, followed by the direct post-review remediation rounds `9996200` → `fa53d2a` → `c5ba8e3` → `2b0a919e`. PR **#15** (`publication/historical-regime-study` → `research/historical-regime-validation`, merge `2f403dad18`, 2026-09-18T13:23:04Z) is **not an ancestor of `main`**: `git merge-base --is-ancestor 2f403dad18 2b0a919e` exits 1, and `git merge-base 2f403dad18 2b0a919e` is `7c1208106378` — the two histories share the cleared publication commit as their merge base, they do not chain. PR **#12**'s merge (`e3a6393`, research line → `main`) **is** an ancestor of `main` (`--is-ancestor` exits 0), but it predates the pack: `git merge-base --is-ancestor e3a6393 5d01cf8` exits 0, so it cannot have carried the pack. The earlier wording — the pack "merged via PR #15 … that line merged to `main` via PR #12" — read as an unbroken merge chain into `main`; no such chain exists. Corrected rather than silently swapped, per the append-only rule. |
| Relevant pull requests | #15 (pack, merged), #12 (line → `main`, merged); #13, #14 remain open (PR hygiene inventory) |
| Exact-head CI evidence | At exact `main` head `2b0a919e`: CI run `35401861654` (success) — https://github.com/jmiaie/financial-dynamics-model/actions/runs/35401861654 ; Publication Pack (D10-A) run `35386559835` (success) — https://github.com/jmiaie/financial-dynamics-model/actions/runs/35386559835 . `Mirror to Public Repo` run `35401861672` failed (non-destructive `403`; investigated separately, see the FDM mirror-workflow review). |
| Exact-head CI evidence — remediation branch | `reconcile/d10-a-lifecycle`. **Corrected 2026-09-23 — "Both workflows run on every push to this branch" was not accurate.** Measured against the workflow definitions at `main` (`5eccc478`) and against the runs actually recorded on this branch: the repository `CI` workflow triggers on `push` only for `main`, and on `pull_request` targeting `main`; the `Publication Pack (D10-A)` workflow triggers on `push` only for `publication/historical-regime-study`, and on `pull_request` for changes under `publication/historical-regime-study/**`. **Neither workflow has a `push` trigger covering this reconciliation branch**: the branch carries **4 runs, all of them `pull_request`** (`CI` ×2, `Publication Pack (D10-A)` ×2) and **zero `push` runs**. Verification of a reconciliation head therefore occurs through the **PR event**, not through the push — the two runs listed immediately below are `pull_request` runs. Most recent completed runs, at commit `85fd0fdb4a` — the commit immediately preceding this edit: `CI` run `35660172282` (success) — https://github.com/jmiaie/financial-dynamics-model/actions/runs/35660172282 ; `Publication Pack (D10-A)` run `35660172275` (success) — https://github.com/jmiaie/financial-dynamics-model/actions/runs/35660172275 . |
| Diff from accepted D9 is publication-only | **Yes** — `git diff --name-status 5d01cf8e 2b0a919e` yields only `.github/workflows/publication-pack.yml` (added) and `publication/historical-regime-study/**`. No accepted empirical source, configuration, dataset manifest, research report, or result artifact appears in that diff. |
| Disclosed integration nuance | **Corrected 2026-09-21.** The pack reached `main` as **direct commits only**. None of `main`'s seven merge commits touches any path under `publication/`: `git log --oneline --merges 2b0a919e` lists seven (`e3a6393`, `49b9c84`, `a292300`, `7a6a5d5`, `eee7403`, `1ea2e7b`, `8d4fa9b`), and `git diff --name-only <merge>^1 <merge> -- publication/` is empty for every one. The earlier wording said the pack arrived "partly through PR merges"; that is not accurate and is superseded here. No accepted artifact changed on either route. |

*(Superseded 2026-09-23 for D10 only: D10 publication-pack program sign-off is now
complete — see "Final Directive #10 program sign-off" at the top of this
file. The D9 and D11–D13 wording below is unchanged and remains current.)*

**Current program state.** D9: COMPLETE / ACCEPTED. D10: TECHNICALLY
INTEGRATED / FORMAL SIGN-OFF PENDING. D11: PARTIALLY STARTED THROUGH THE
PUBLIC HUB / NOT FORMALLY ACTIVATED. D12: DRAFTED / BLOCKED BY D11 HIRING
EVIDENCE. D13: DRAFTED / NOT YET JUSTIFIED.

**Superseded 2026-09-23 — an authoritative D10 publication-pack program
sign-off has since been issued; see "Final Directive #10 program sign-off" at
the top of this file. The paragraph below is the reconciliation-phase record,
retained unedited.** No authoritative
`DIRECTIVE #10 PUBLICATION PACK SIGN-OFF: YES` has been issued for this pack.
A D9 program sign-off is not a D10 program sign-off. This section records
integration state only: it is not a sign-off, and it does not strengthen,
weaken, or restate any finding, number, or claim in the pack.

### How to read the rest of this directory

Every "no merge", "no pull request merged", "draft PR only", "not on `main`",
"not from `main`", "no external publication", and "READY FOR INDEPENDENT
(D10) REVIEW" statement preserved below, or elsewhere in this directory, is
**authoring-phase language** kept deliberately as the contemporaneous record
(append-only history; the historical record is not rewritten). Where such a
statement could be read as describing the *current* lifecycle state, this
section supersedes it; the statement itself is left unedited. The
machine-readable `reproducibility.json` field `merge` is likewise left
byte-unchanged on purpose, so the pack's own hash and regeneration gates stay
valid at the recorded tip.

*Repository visibility note:* the host repository is public, so this pack is
world-readable on `main`. No PyPI/npm release, website deployment, or other
external-service publication was performed.

---

*Post-review integration section added 2026-09-21 as documentation-only
reconciliation. No empirical artifact, configuration, dataset manifest,
experiment identity, ledger row, number, or finding was changed; no
rerun, retune, or reacquisition was performed.*

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
| 9 | Citation check resolved 19 of the 35 identifiers present (lowercase-only pattern skipped `*`/uppercase forms) and resolved wildcards by prefix only | Pattern widened and wildcard matching moved to `fnmatch` glob semantics; the check now reports and resolves all 35 identifiers matched by the pattern (abbreviated suffix citations such as `.median_ret_h1`, which the pattern does not match, are now cited in full in `CLAIM-REGISTER.md`) |
| 10 | Workflow described as running "read-only verification" | `SOURCE-GATE.md` now states that `verify_pack.py` regenerates `tables/`/`figures/` in place to compare against the committed bytes and restores them; the workflow itself commits and publishes nothing |

Re-verified after this round: `verify_pack.py` → **all 5 checks pass** under the pinned
interpreter, **35 citation identifiers resolved**, both figures regenerated and
byte-identical, generated tables byte-identical to committed. With matplotlib absent the
figure check now **fails closed** (1/5 failed: `['figures']`) where it previously reported a
full pass — that false-pass path is closed permanently, not just noted.

---

## Remediation round 5 — 2026-09-18 (independent re-review of `9996200`)

A second, independent re-review (separate clean-room clone at `9996200`, separate reviewer
session) returned **13 further defects in D10-A**. All 13 are addressed here. Two of them were
regressions introduced by round 4 itself, which is worth stating plainly: the round-4 edits fixed
the words they targeted and, in two places, generalised the replacement too far.

| # | Defect from the re-review | Disposition in this round |
|---|---|---|
| 1 | Round 4 replaced "formation only" with "through 2024-12-31" **universally**; the validation artifacts actually record `history_period.end_inclusive = 2023-12-31` | `TECHNICAL-PAPER.md`, `SOURCE-GATE.md`: cutoff stated as period-dependent (`2023-12-31` for `val_2024`, `2024-12-31` for `holdout_2025`, no history window for `dev_formation`), with the invariant that it is never inside the evaluated window |
| 2 | Round 4 claimed the effective-block-equals-`n` setting degenerates the interval in **all 174** rows; true only for moving-block | `TECHNICAL-PAPER.md`: measured split stated — 81 moving-block rows collapse to zero width, 81 stationary rows keep non-zero width (worked example given), 12 flagged `insufficient_data` |
| 3 | `reproducibility.json` still labelled the block length in trading days | Key renamed to `requested_block_length_regime_occurrences` and a `…_note` added; the key is referenced nowhere else in the repo, so no hash or citation broke |
| 4 | An **empty** committed-figure set was skipped and reported green, so deleting both tracked PNGs passed | `scripts/verify_pack.py`: `CheckFailure` ("Refusing to report a PASS on an empty figure set") |
| 5 | The C1 claim excluded `dev_formation` but quoted its GMM value (0.365) in a two-period range | `CLAIM-REGISTER.md`: range corrected to 0.287–0.345 (`val_2024`+`holdout_2025`), with the 0.365 attributed to `dev_formation` |
| 6 | The §3 coverage claim was as universal as the §2 one it replaced | `RESULT-SOURCE-MAP.md`: 135 metric cells mapped; `n_regimes_observed`/`evaluated_bars`/`total_bars` have no individual row (45 scalars / 30 displayed cells) |
| 7 | `.median_ret_h1` was an abbreviated suffix citation the verifier cannot match, so "all 35" was not a complete inventory | `CLAIM-REGISTER.md` now cites the full row id; the check resolves **36** identifiers; the round-4 claim is scoped to pattern-matched identifiers |
| 8 | Hash instructions conflated `dataset_canonical` field values with whole-file hashes | `RESULT-SOURCE-MAP.md` (framing, step 4, and a note under the table) and `SOURCE-GATE.md`: the two rows are named as the exception, with the manifests' own `sha256sum` values given |
| 9 | The preview promise ("first 10 rows") did not match the 10-row preview | `RESULT-SOURCE-MAP.md`: preview described as 2 map rows + 5 case-study rows + 3 hash rows |
| 10 | A per-regime CI for a different symbol was presented as evidence about the primary result's cross-regime mean | `TECHNICAL-PAPER.md`: SPY-v2's own `RISK_OFF` horizon-1 record quoted (`n=29`, mean −0.003479, both intervals include zero), with the explicit caveat that a per-regime interval is not a CI for the cross-regime mean |
| 11 | "loss of `CALM_TREND`" was generalised to four symbols | `TECHNICAL-PAPER.md`: three of four (QQQ, IWM, TLT at zero; GLD retains it with 11) |
| 12 | "all five benchmark models" | `SOURCE-GATE.md`: four benchmarks plus the FDM pipeline, with the development artifacts noted as having no `persistence` model |
| 13 | "restores them" was true of the tested path only — a non-zero generator exit did not restore | `scripts/verify_pack.py`: restore moved into `finally`, so it runs on every path; `SOURCE-GATE.md` states the verified scope |

### Evidence for the instrument fixes (forced failures, not assertions)

| Run | Result |
|---|---|
| `d10a-regime/.venv/bin/python scripts/verify_pack.py` | `RESULT: all 5 check(s) passed`; `PASS: all 36 citation identifiers in CLAIM-REGISTER.md resolve`; tree left clean |
| `/usr/bin/python3 scripts/verify_pack.py` (no matplotlib) | `RESULT: 1/5 check(s) failed: ['figures']`, exit 1; tracked figures restored |
| Both tracked PNGs deleted, then verifier run | `FAIL [figures]: no committed figures/*.png found … Refusing to report a PASS on an empty figure set`, exit 1 (this run was **green** before round 5) |
| Generator forced to `SystemExit(3)` | `FAIL [figures]: generate_figures.py exited non-zero`, exit 1, **both figures restored** (`git status` shows no figure deletions) |

Values added to the paper this round were measured in-session before being written: GMM
self-transition `0.286853` (`val_2024`) / `0.344565` (`holdout_2025`) / `0.364944`
(`dev_formation`); 81/81/12 sparse split; QQQ `val_2024` volatility-bucket `CALM_TREND` h20
stationary interval `[-0.024217, +0.047039]` (width `0.071255`, `n=19`); 2025 `holdout`
`CALM_TREND` counts QQQ 0 / IWM 0 / TLT 0 / GLD 11; 135 robustness rows and 469 total
`source_map` rows.

No empirical reruns, no re-acquisition, no frozen-value changes, no hub or Issue #3 edits. The
remediation is a normal follow-up commit.

---

## READY FOR INDEPENDENT D10 REVIEW. NO MERGE. NO D11.

*(Authoring-phase heading — 2026-09-18. Superseded as a statement of current state: the pack is now integrated on `main`. See "Post-review integration status" at the top of this file.)*
