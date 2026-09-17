# Superseded: pre-`positive_return_freq`-fix artifacts

These 12 files are the QQQ/IWM/TLT/GLD v2 cross-asset-robustness artifacts
(`dev_formation`/`val_2024`/`holdout_2025` × 4 symbols) as originally
committed on 2026-09-17, **before** a metric-definition defect was fixed in
`positive_return_freq` (independent review, tracker Issue #3).

**The defect**: `positive_return_freq` was computed as the fraction of
individual *daily* returns positive inside each forward window, then
averaged across occurrences -- not the fraction of *occurrences* whose
horizon-level (compounded) `forward_return` was positive, which is what the
name means everywhere else in this report (alongside `mean_return`,
`median_return`, `tail_q05`) and what Directive #9 requires. See
`src/financial_dynamics/backtesting/metrics.py`'s `historical_regime_statistics`
and `tests/test_backtesting.py::TestHistoricalRegimeStatistics::test_positive_return_freq_is_horizon_level_not_daily_level`
for the fix and a deterministic regression test proving the two definitions
diverge.

**Why this is a mechanical-defect fix, not a retune-on-observed-outcomes**:
every other statistic in these artifacts (`mean_return`, `realized_vol`,
`downside_vol`, `tail_q05`, `adverse_drawdown`, transitions, durations,
bootstrap CIs) is unaffected and unchanged by the fix -- only
`positive_return_freq`'s own formula was wrong. Nothing about the model,
methodology, universe, or dataset changed. These artifacts were also never
claimed as an untouched final holdout to begin with -- they are pre-
specified robustness / post-primary characterization (§5.4 of
`research/historical-market-regime-study.md`), executed *after* SPY-v1's own
primary holdout evaluation. SPY-v1's own primary result is untouched by this
fix and is not regenerated.

**Preserved here, not deleted**, per this program's audit-trail convention.
The corrected replacements live at their original paths in
`results/historical_regimes/` (same filenames, new `positive_return_freq`
values, everything else unchanged); the experiment ledger
(`research/experiment-ledger.csv`) is append-only, so the original rows for
these experiment IDs remain in its history alongside the new ones.
