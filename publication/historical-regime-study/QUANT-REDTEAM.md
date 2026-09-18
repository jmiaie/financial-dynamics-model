# Red-Team Pass 1: Quantitative Correctness

Adversarial self-review focused on: are all numbers/statistics correct and correctly
computed/labeled (units, confidence levels, sample sizes)? Findings are tagged P0 (blocking) /
P1 (material) / P2 (minor/stylistic), each with "fixed before finalizing" or "not fixed,
rationale."

## Method

This pass did not just re-read the prose. For every numeric claim, one of the following
mechanical checks was actually run against the committed artifacts in this session:

1. Re-ran `scripts/generate_tables.py` and `scripts/generate_figures.py` fresh and diffed their
   output against what is quoted in `TECHNICAL-PAPER.md` (script, not memory, is the source of
   truth).
2. Programmatically extracted every 64-hex-character hash string across `SOURCE-GATE.md`,
   `reproducibility.json`, `TECHNICAL-PAPER.md`, `CASE-STUDY.md`, and `RESULT-SOURCE-MAP.md`, and
   confirmed each one is the real `sha256sum` of the file it is attached to (18 file/hash pairs
   checked individually — primary artifacts ×3, robustness artifacts ×15 — zero mismatches; two
   embedded-content hashes — the `dataset_canonical` values inside the v1/v2 manifests — and one
   `superseded_150_resamples/` file hash were confirmed by direct re-computation after an initial
   automated pass flagged them as "not found," which turned out to be because they are not
   whole-file hashes of the top-level artifact list, not because they were wrong).
3. Extracted every numeric token from the paper's §2/§3 tables and diffed against the
   script-generated `tables/primary_spy_v1.md`/`tables/robustness_cross_asset.md` (after
   normalizing Unicode minus signs and excluding section-reference tokens like "§1.5," which
   otherwise produce false positives in a naive regex diff) — zero real discrepancies found.
4. Independently recomputed the one specific claim most likely to be mis-transcribed under
   rounding (C10, SPY-v1 vs. SPY-v2 4-significant-figure agreement) directly from both JSON files
   rather than trusting the source report's restatement of it.
5. Independently re-scanned all 15 robustness artifacts' `bootstrap_records[]` for `n < 20` rather
   than trusting the supplied "174 instances" figure — the script-driven scan reproduced exactly
   174.

## Findings

### P1 — Aggregation caveat was scoped only to §2's tables, silently under-covering §3

**Finding.** The first draft of `TECHNICAL-PAPER.md` §1.5 stated the "unweighted average across
regimes" caveat for `mean_return_h*`/`median_return_h*` and pointed only at "§2's tables." But
§3's robustness table reads the identical `key_metrics.mean_return_h*` fields via the identical
aggregation, so the caveat silently under-covered half of the numbers it should have applied to.
A reader who only skimmed §3 could have taken its `ret h1`/`ret h5`/`ret h20` columns as
bar-level statistics.

**Fixed before finalizing.** §1.5's caveat now explicitly states it applies to "§2's primary
tables *and* §3's robustness table alike," and a one-line pointer was added directly above the
§3 table repeating the scope. Also clarified that `CASE-STUDY.md`'s per-regime `summary_records`
figures are a different (non-aggregated) statistic not subject to this caveat, to prevent the
opposite error (over-applying the caveat where it does not belong).

### P2 — §3 table column headers ("ret h1/h5/h20") are terse enough to misread as raw returns

**Finding.** Without a nearby label, "ret h1" could be misread as a single bar-level return
rather than the cross-regime mean aggregate it actually is (see P1 above — same root cause,
different symptom: a labeling clarity issue rather than a missing-caveat issue).

**Fixed before finalizing.** Same edit as P1 addresses this — the inline note above the §3 table
now states the columns are `mean_return_h*` explicitly, not just implicitly via a cross-reference.

### P2 — Abstract's first inline reference to the 2025 period used "2025 holdout" unqualified

**Finding.** The abstract correctly introduces the period as "a historical evaluation of 2025" on
first mention, but a later sentence in the same abstract reverted to "its 2025 holdout" without
the qualifier, three sentences later. Not a violation of the standing prohibition (the paper does
not call it an "untouched" or "clean" holdout anywhere), but an avoidable inconsistency in a
document that elsewhere insists on precise period labeling (`SOURCE-GATE.md` field 7 / its
"Period classification detail" section).

**Fixed before finalizing.** Changed to "its 2025 evaluation result" for consistency within the
abstract itself.

### P2 — DEV/VAL-period downside-vol/tail/drawdown figures in §3 have no external cross-check

**Finding.** The source report's own §5.4 table only ever published `downside_vol`,
`positive_return_freq`, `tail_q05`, and `adverse_drawdown` for the **2025 holdout** row per
symbol — it never published these columns for the dev_formation/val_2024 rows. This pack's §3
table includes all three periods for all five symbols, so the dev_formation/val_2024 cells in
those five columns are numbers this pack is the first to publish; there is no second, independent
source-report table to diff them against (unlike the 2025-holdout cells, which were verified
against the source report's own published numbers and matched exactly — see check #3 above).

**Not fixed — rationale.** This is not a defect: the task explicitly calls for tables
"regenerated by a script... against the already-frozen local artifacts," not restricted to
numbers the source report happened to already print. The dev_formation/val_2024 cells are read
by the identical script code path, from the identical `key_metrics` schema, in the identical
artifact files, as the already-verified 2025-holdout cells — there is no reason to expect a
different failure mode for one period versus another within the same file. Flagged here for
transparency rather than silently presented as if independently cross-checked twice.

### P2 — `case_study.qqq_2025.*` row IDs in `RESULT-SOURCE-MAP.md` use a bracket-selector key-path notation, not literal JSON Pointer syntax

**Finding.** Key paths like `summary_records[regime==RISK_OFF,horizon==1]` are a readable
shorthand for "the element of this array matching these field values," not valid JSON Pointer or
JMESPath syntax a reviewer could paste directly into a tool. A strict reviewer might expect an
executable path.

**Not fixed — rationale.** `CASE-STUDY.md` §Step 2–3 spells out the exact literal JSON fragment
matching that shorthand (quoting it verbatim), so the shorthand is always immediately next to its
literal resolution; introducing real JSONPath/JMESPath syntax throughout would add notation
overhead without changing what a reviewer actually needs to do (open the file, find the record
matching those field values by eye — arrays here have single-digit lengths). Documented as a
known notation choice rather than silently left ambiguous.

## Remediation update — 2026-09-18 (post-initial-publish correction)

**This is a dated correction to the P2 finding directly above ("Abstract's first inline reference
to the 2025 period used '2025 holdout' unqualified"), not a silent edit of it.** That finding's
own premise — "the abstract correctly introduces the period as 'a historical evaluation of
2025'" — is now known to be **wrong**, identified by the orchestrating session and independently
confirmed in this remediation pass: "historical evaluation" was itself a mislabel, reached by a
category error (reasoning that "2025 data existed and was in principle inspectable before the
freeze," which is true of every holdout period ever run and is not evidence for or against
holdout status). The correct classification, confirmed by reading `research/holdout-audit.md`
directly in this remediation session, is **final 2025 holdout evaluation**: the audit gives an
explicit **CLEAR** verdict ("no evidence that calendar-year 2025 market data was previously
inspected, tuned against, or used for empirical evaluation / performance claims in this
repository"), the primary config was frozen before the 2025 run
(`freeze_record.frozen_for_holdout_utc`, 2026-09-16T02:58:00Z), and the run then executed exactly
once under that frozen configuration — a textbook final holdout, and also the terminology the
source report (`research/historical-market-regime-study.md`) itself uses consistently throughout
("HOLDOUT 2025," "the holdout (2025) run").

**Scope of this correction.** Every occurrence of "historical evaluation" / "historical-evaluation"
as a period classification was replaced with "final 2025 holdout evaluation" / "2025 holdout"
across `SOURCE-GATE.md` field 7 (period classification, since renumbered — see the round-3 note
below), `TECHNICAL-PAPER.md` (abstract, §1.2, §2.3 header and body, §3, §6,
§7), `CASE-STUDY.md`, `CLAIM-REGISTER.md` C19 (the claim's *reasoning* was rewritten, not just its
label — the "data existed and was inspectable" justification was the actual defect), and
`CITATION-REDTEAM.md`. `scripts/generate_tables.py`'s `PERIOD_LABELS` dict carried the same wrong
string embedded in generated table headers — fixed at the source and the tables regenerated
(`tables/primary_spy_v1.md` and downstream files), rather than hand-editing the generated output.
A new hash-table entry (`hash_table.holdout_audit_verdict`, citing `research/holdout-audit.md`)
was added to the source-map generator so this correction's own evidentiary basis is traceable the
same way every other claim in this pack is.

**This does not change the finding's original P2 disposition retroactively** — at the time that
finding was written, the "historical evaluation" framing itself had not yet been identified as
incorrect, so the internal-consistency issue it flagged (first mention qualified, second
unqualified) was a real, if now moot, observation about a since-superseded label. It is left in
place above as the accurate record of what was found and when, per this document's own
"never silently rewrite a prior finding" convention.

## Remediation update 2 — 2026-09-18 (SOURCE-GATE.md restructured to the authoritative schema)

`SOURCE-GATE.md` was rebuilt to the program's actual Phase 0 14-field schema (a different, more
specific structure than the improvised one this pack originally used), so every `SOURCE-GATE.md
§N` reference in this document that pointed at content now living under a different number or a
named unnumbered section was updated (not silently — this note documents it). The two occurrences
above (the P2 finding's own body text, and this document's round-2 remediation note) both
referenced the old "§12" (period classification); both now point to the new field 7 plus
`SOURCE-GATE.md`'s "Period classification detail" named section, which is where that content
lives after the restructuring. No finding's substance changed as a result of this renumbering —
only the citation target.

## Summary

- P0: 0
- P1: 1 (fixed)
- P2: 4 (2 fixed, 2 not fixed with rationale) + 1 remediation update (2025 period-label category
  error, corrected 2026-09-18 at the coordinator's direction, independently confirmed against
  `research/holdout-audit.md` in this pass) + 1 further remediation update (SOURCE-GATE.md
  cross-reference repair after its schema was rebuilt to the authoritative 14-field structure,
  same date)

No fabricated, mis-transcribed, or incorrectly-labeled *number* was found in this pass. The one P1
was a scope/labeling gap in a caveat, not an incorrect number. The 2026-09-18 remediation update is
a labeling/classification correction, not a numeric one — no table value, hash, or statistic
changed as part of it.
