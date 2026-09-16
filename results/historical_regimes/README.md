# Historical regime study artifacts (Directive #9)

JSON summaries produced by `scripts/run_historical_regime_study.py` from frozen local data only.

| Experiment ID | Period | Notes |
|---|---|---|
| `fdm_hist_regime_v1_dev_formation` | 2015–2023 | Formation/dev characterization |
| `fdm_hist_regime_v1_val_2024` | 2024 | Validation OOS (history=formation) |
| `fdm_hist_regime_v1_holdout_2025` | 2025 | Holdout only after config freeze |

Committed JSON files are **slim** (key metrics + regime counts + config snapshot). Full per-bar summary/transition tables are omitted to keep git small; re-run the study script on frozen local CSVs to regenerate. See `research/experiment-ledger.csv` for paths + SHA-256.
