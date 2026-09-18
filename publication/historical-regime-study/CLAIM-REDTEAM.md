# Red-Team Pass 2: Claim Overreach

Adversarial self-review focused on: does any claim overreach the evidence (implies forecasting
power, hides the robustness/primary distinction, understates small-sample caveats)? Findings
tagged P0/P1/P2, each with "fixed before finalizing" or "not fixed, rationale."

## Method

Re-read every claim in `CLAIM-REGISTER.md` against its cited evidentiary basis, and separately
grepped `TECHNICAL-PAPER.md`, `CASE-STUDY.md`, and `CLAIM-REGISTER.md` for forecast/alpha/edge/
signal/predict/significant language and for every prose use of "holdout" to check none of it
reads as "untouched"/"clean" holdout even where the word "holdout" is used descriptively (e.g. in
literal artifact filenames, which are not prose claims and were left as-is). Also specifically
checked whether any evaluative language ("better," "outperforms," "superior") crept in anywhere a
purely descriptive comparison was intended, since that is the most common way a risk-
characterization study drifts toward an implicit performance claim without ever using a forecast
word.

## Findings

### P1 — "Persistence vs. reactivity" discussion dropped the source report's explicit non-adjudication of whether FDM's position is "better"

**Finding.** The source report explicitly states: "Whether that trade-off point is 'better'
depends on the downstream use case; this report does not adjudicate that." The first draft of
`TECHNICAL-PAPER.md` §2.3's "Persistence vs. reactivity" paragraph reported the same descriptive
fact (FDM's self-transition rate sits between the sticky and noisy benchmarks) but omitted this
explicit disclaimer. Nothing in the draft literally said FDM is "better," but omitting the
source's own explicit non-adjudication weakens the paper relative to its source material in
exactly the direction this pack must not weaken it (per the task's explicit instruction to
"reuse/tighten, don't weaken" limitations) — a reader could read "sits between two extremes" as
implicitly favorable (a "best of both worlds" framing) without the paper ever saying so outright.

**Fixed before finalizing.** Added a sentence restoring the explicit non-adjudication: "Whether
sitting at this particular point between the sticky and noisy extremes is desirable is a
downstream-use-case judgment this paper does not make — a consistent middle position is reported
as an observed characteristic, not as evidence that FDM is 'better' than either kind of
benchmark."

### P1 — Checked but not found: abstract does not assert forecasting power despite describing a "finding"

**Finding investigated.** The abstract's second half describes the 2025 negative-mean-return
result as "the only model whose... mean 1-day forward return was negative" — worth checking
whether this reads as implying FDM successfully "called" a downturn (a forecast-accuracy framing)
rather than a risk-characterization framing.

**Not fixed — no defect found.** The same sentence, in the same breath, states the finding's 90%
bootstrap CI "does not exclude zero for the small-sample RISK_OFF regime specifically," and the
abstract's opening sentence explicitly frames the whole paper as characterizing "subsequent risk
characteristics," not forecasts. The finding is presented and immediately qualified in one
sentence, not left to stand alone before a later disclaimer. No change made; documented here to
show the check was actually performed rather than assumed.

### P2 — `CLAIM-REGISTER.md` C8/C9's "matching pattern" language could be read as implying a shared cause across symbols

**Finding.** C8 states `CALM_TREND`'s disappearance in 2025 "matches" the SPY-v1 finding across
QQQ/IWM/TLT. The word "matches" describes a correlation in outcome, not a claim of shared cause —
but a fast reader skimming only the claim column (not the adjacent confidence/caveat column)
could take "matching pattern across 4 of 5 symbols" as itself evidence of a real market-wide 2025
regime shift.

**Not fixed — rationale.** The confidence/caveat column for both C8 and C9 already states this
directly ("a fixed-centroid classification outcome on one calendar year cannot... distinguish a
genuine market characteristic from a centroid-definition artifact" / "no statistical significance
is claimed for this split"). Table rows are read as a unit (claim + caveat together) throughout
this register by design; splitting the caveat into the claim text itself would duplicate content
already present one column over. Flagged rather than duplicated.

### P2 — Robustness-vs-primary distinction: spot-checked for silent conflation

**Finding investigated.** Specifically checked whether any sentence in `TECHNICAL-PAPER.md` §3 or
§5 states a QQQ/IWM/TLT/GLD/SPY-v2 number without an adjacent "robustness"/"post-primary"/
"characterization" qualifier somewhere in the same paragraph, which could let a skimming reader
lose track of which numbers are primary.

**Not fixed — no defect found.** Every one of §3's paragraphs opens with or restates the
robustness/non-primary status (the section header itself says "Robustness / characterization,"
the section's first sentence repeats "post-primary, robustness / characterization only," and each
subsequent finding paragraph — cross-symbol pattern, SPY-v2 consistency — repeats the
non-primary framing inline). `SOURCE-GATE.md` §13 and `CLAIM-REGISTER.md`'s "Primary or
robustness-only" column provide two further, independent places this distinction is asserted.
This redundancy is intentional, not accidental over-qualification, given how consequential this
specific distinction is to the whole pack.

### P2 — Small-sample caveats: verified they attach to the specific numbers they qualify, not just as a generic disclaimer

**Finding investigated.** A generic "small sample" disclaimer placed once at the top of a document
can be technically true while functionally useless if a reader can't tell which specific numbers
it covers. Checked whether every small-`n` claim (C9's 3-equity-instrument split, C11/C12's
regime-specific bootstrap results) states its own `n` inline rather than relying on a document-level
disclaimer.

**Not fixed — no defect found.** C9 states "3 equity instruments" inline; C11 states "n=29"
inline; C12 states "n=121" inline; `CASE-STUDY.md` traces `n=29` through every step of its
derivation. No claim in this pack relies on an undifferentiated "small sample" disclaimer without
also stating the specific sample size next to the specific number it qualifies.

## Summary

- P0: 0
- P1: 1 (fixed) + 1 investigated and cleared (no defect)
- P2: 3 investigated, 0 required changes (existing caveat placement judged sufficient in each case)

The one real P1 found in this pass was an *omission* (dropping an explicit non-adjudication
statement from the source material), not a fabricated overclaim — but the task's own instruction
to tighten rather than weaken limitations makes this a genuine, material finding, not a stylistic
one, which is why it is tagged P1 rather than P2.
