# Red-Team Pass 3: Citation Integrity

Adversarial self-review focused on: does every claim actually trace to a real file/field per
`RESULT-SOURCE-MAP.md`; is there any orphaned or unverifiable claim? Findings tagged P0/P1/P2,
each with "fixed before finalizing" or "not fixed, rationale."

## Method

This pass was mechanical, not a re-read. A script extracted every backtick-quoted,
dot-separated identifier from `CLAIM-REGISTER.md` (candidate row-ID citations) and checked each
one against the literal set of `row_id` values in the freshly-regenerated `tables/source_map.json`
(467 rows), resolving wildcard-style references (`prefix.*`) against any row starting with that
prefix. Any candidate that resolved to nothing was treated as a potential orphaned citation and
individually investigated (not assumed to be a false positive) until either fixed or confirmed as
a non-row-ID reference (e.g. a literal JSON field path quoted in prose, not a `RESULT-SOURCE-MAP.md`
row ID).

## Findings

### P0 — `CLAIM-REGISTER.md` C12 cited a row-ID pattern (`robustness.qqq.holdout_2025`) that does not exist in the source map for the specific numbers it backs

**Finding.** C12 makes a specific numeric claim (QQQ 2025 `VOLATILE_TREND`, n=121, mean +0.0021,
both 90% bootstrap CIs excluding zero) and cited `` `robustness.qqq.holdout_2025` bootstrap
records for `VOLATILE_TREND`, horizon 1 `` as its evidentiary basis. But the `robustness.*`
row-ID namespace only ever covered `key_metrics` aggregate fields (self-transition, mean returns,
downside vol, etc.) — it never covered individual regime-level `bootstrap_records` entries other
than `RISK_OFF` (which the `case_study.qqq_2025.*` namespace covers). **The specific numbers C12
asserts — and the same numbers as quoted in `TECHNICAL-PAPER.md` §4.2 and drawn in
`figures/qqq_2025_holdout_bootstrap_ci_h1.png` — had no row in `RESULT-SOURCE-MAP.md`'s
traceability system at all.** This is exactly the class of defect this red-team pass exists to
catch: a real, verifiable number (confirmed correct against the underlying artifact) that was
nonetheless an orphaned citation in the traceability document meant to let a reviewer check it in
30 seconds. Tagged P0 because it is a genuine gap in the pack's core traceability guarantee, not
a stylistic issue — a reviewer following `RESULT-SOURCE-MAP.md`'s own instructions ("find the
matching row_id... open the file... confirm it matches") would have failed at step 1 for this
specific, publicly quoted number.

**Fixed before finalizing.** Extended `scripts/generate_tables.py`'s case-study generator to add
source-map rows for every horizon-1 bootstrap record in the QQQ 2025 holdout file, not just
`RISK_OFF` (new row IDs: `case_study.qqq_2025.bootstrap_volatile_trend_moving_block`,
`case_study.qqq_2025.bootstrap_volatile_trend_stationary`, and the equivalent `CHOP` rows).
Re-ran the generator (467 rows, up from 461) and updated C12's evidentiary-basis column to cite
the real row IDs. Re-ran the mechanical orphan check after the fix: zero unresolved citations
remain.

### P1 — C13's citation format (`sparse_cell.0` through `sparse_cell.173`) implied a literal, lookup-able row ID that does not exist in that exact form

**Finding.** The actual row-ID format for sparse-cell rows is
`sparse_cell.<index>.<symbol>.<period>.<model>.<regime>.h<horizon>.<method>` — a reviewer
searching `tables/source_map.json` for the literal string `sparse_cell.0` (as C13's text
suggested) would not find an exact match, only a prefix match, and might reasonably conclude the
citation was broken rather than merely abbreviated.

**Fixed before finalizing.** Rewrote C13's evidentiary-basis column to show the actual full
row-ID pattern with real first/last examples
(`sparse_cell.0.SPY.val_2024.financial_dynamics_pipeline.CALM_TREND.h1.moving_block` through
`sparse_cell.173.GLD.holdout_2025.trend_vol_grid.CHOP.h20.stationary`), so the citation is
reproducible by direct string match, not just by prefix reasoning.

### P1 — C19 cited a JSON/YAML field path directly rather than a `RESULT-SOURCE-MAP.md` row ID, inconsistent with every other row in the register

**Finding.** C19 (the "historical evaluation" labeling claim) cited
`` freeze_record.frozen_for_holdout_utc `` as a literal field path with no corresponding
`hash_table.*` row — every other claim in the register cites a `RESULT-SOURCE-MAP.md` row ID, so
this was an inconsistent citation style that also meant the underlying config file's hash was not
independently pinned anywhere a reviewer could check it via the standard row-ID lookup.

**Fixed before finalizing.** Added `hash_table.freeze_record_frozen_for_holdout_utc` and
`hash_table.config_v1_status` rows to the generator (reading the field directly from the YAML
config via `pyyaml`, already a project dependency) and updated C19 to cite them alongside the
existing `hash_table.config_v1_primary` whole-file hash.

## Verification after fixes

Re-running the mechanical check (extract every backtick-quoted dot-separated identifier from
`CLAIM-REGISTER.md`, resolve against `tables/source_map.json`'s 467 row IDs, including wildcard
prefixes) now returns **zero unresolved citations** — every claim's evidentiary basis is a real,
resolvable row.

A second check — diffing every numeric token in `TECHNICAL-PAPER.md` §2/§3's tables against the
freshly-regenerated `tables/primary_spy_v1.md`/`tables/robustness_cross_asset.md` — found zero
values present in the generated tables but absent from the paper (after normalizing Unicode minus
signs), i.e. no hand-transcription drift between the script's output and the prose.

## Summary

- P0: 1 (found and fixed — a genuinely orphaned citation for a publicly quoted number)
- P1: 2 (found and fixed — citation-format inconsistencies that would have cost a reviewer time
  even though the underlying numbers were correct)
- P2: 0

This is the pass that surfaced the most serious finding in the entire red-team exercise. The
underlying number (QQQ `VOLATILE_TREND` bootstrap CI) was never wrong — it was correctly computed
and correctly quoted in both the paper and the figure — but it was not traceable through
`RESULT-SOURCE-MAP.md` as that document's own stated purpose promises, which is precisely the
kind of gap a citation-integrity pass exists to catch rather than a correctness pass (which would
have found nothing wrong, since the number itself was fine).
